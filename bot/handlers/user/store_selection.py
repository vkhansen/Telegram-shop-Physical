"""
Brand and branch selection handler.

Customer flow:
1. User taps Shop → sees list of active brands
2. User picks a brand → if 1 branch, auto-select it
3. If multiple branches:
   - GPS available → auto-select nearest branch
   - No GPS → show branch list
4. User browses that brand's menu
"""
import math
from decimal import Decimal

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot.database.methods.create import save_cart_snapshot
from bot.database.methods.delete import clear_cart, remove_items_from_cart
from bot.database.methods.read import get_all_brands, get_brand, get_cart_items, get_stores_for_brand
from bot.database.methods.update import bulk_update_cart_store
from bot.database.models.main import BranchInventory, Goods
from bot.database.main import Database
from bot.i18n import localize
from bot.keyboards.inline import back, brand_switch_confirm_keyboard, simple_buttons, store_switch_confirm_keyboard
from bot.states import ShopStates
from bot.utils.cart_stub import build_cart_stub, format_cart_stub, get_cart_stub_data, inject_cart_stub

router = Router()


def _haversine(lat1, lng1, lat2, lng2) -> float:
    """Calculate distance in km between two GPS points."""
    R = 6371
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (math.sin(d_lat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(d_lng / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@router.callback_query(F.data == "shop")
async def brand_picker(call: CallbackQuery, state: FSMContext):
    """Show list of active brands. If only one brand exists, auto-select it."""
    brands = get_all_brands(active_only=True)

    if not brands:
        await call.message.edit_text(
            localize("shop.no_brands"),
            reply_markup=back("back_to_menu"),
        )
        return

    # Single brand → auto-select
    if len(brands) == 1:
        brand = brands[0]
        await state.update_data(current_brand_id=brand['id'], current_brand_name=brand['name'])
        await _select_branch_or_proceed(call, state, brand['id'])
        return

    # Multiple brands → show picker
    buttons = []
    for b in brands:
        label = b['name']
        if b.get('description'):
            label += f" — {b['description'][:40]}"
        buttons.append((label, f"select_brand_{b['id']}"))

    buttons.append((localize("btn.back"), "back_to_menu"))

    # Card 21: prepend persistent cart stub if cart has items (serves as
    # reminder when browsing a different brand).
    text = inject_cart_stub(localize("shop.brands.title"), build_cart_stub(call.from_user.id))
    await call.message.edit_text(
        text,
        reply_markup=simple_buttons(buttons, per_row=1),
    )
    await state.set_state(ShopStates.selecting_brand)


@router.callback_query(F.data.startswith("select_brand_"))
async def select_brand(call: CallbackQuery, state: FSMContext):
    """User selected a brand. Card 21: guard if active cart belongs to a different brand."""
    brand_id = int(call.data.replace("select_brand_", ""))
    brand = get_brand(brand_id)
    if not brand or not brand['is_active']:
        await call.answer(localize("shop.brand_unavailable"), show_alert=True)
        return

    # Card 21 Phase 4: check for cross-brand cart conflict
    cart_data = get_cart_stub_data(call.from_user.id)
    if cart_data and cart_data['brand_id'] and cart_data['brand_id'] != brand_id:
        current_brand_name = cart_data['brand_name'] or str(cart_data['brand_id'])
        warning_text = localize("shop.brand_switch.warning").format(
            n=cart_data['item_count'],
            total=cart_data['total'],
            current_brand=current_brand_name,
            new_brand=brand['name'],
        )
        await state.update_data(pending_brand_id=brand_id)
        await state.set_state(ShopStates.confirming_brand_switch)
        await call.message.edit_text(
            warning_text,
            reply_markup=brand_switch_confirm_keyboard(brand_id),
        )
        return

    await state.update_data(current_brand_id=brand['id'], current_brand_name=brand['name'])
    await _select_branch_or_proceed(call, state, brand['id'])


async def _select_branch_or_proceed(call: CallbackQuery, state: FSMContext, brand_id: int):
    """If brand has 1 store → auto-select; multiple → GPS or list."""
    stores = get_stores_for_brand(brand_id, active_only=True)

    if not stores:
        # No stores — proceed without store context (menu-only brand)
        await state.update_data(current_store_id=None)
        await _show_categories(call, state)
        return

    if len(stores) == 1:
        # Single branch → auto-select
        store = stores[0]
        await state.update_data(current_store_id=store['id'], current_store_name=store['name'])
        await _show_categories(call, state)
        return

    # Multiple branches → try GPS auto-select
    data = await state.get_data()
    user_lat = data.get('user_latitude')
    user_lng = data.get('user_longitude')

    if user_lat and user_lng:
        # Auto-select nearest branch
        nearest = min(
            [s for s in stores if s.get('latitude') and s.get('longitude')],
            key=lambda s: _haversine(user_lat, user_lng, s['latitude'], s['longitude']),
            default=None,
        )
        if nearest:
            await state.update_data(current_store_id=nearest['id'], current_store_name=nearest['name'])
            await _show_categories(call, state)
            return

    # Show branch list
    buttons = []
    for s in stores:
        label = s['name']
        if s.get('address'):
            label += f" — {s['address'][:50]}"
        buttons.append((label, f"select_branch_{s['id']}"))

    buttons.append((localize("btn.back"), "shop"))

    # Card 21: prepend persistent cart stub if cart has items
    text = inject_cart_stub(localize("shop.branches.title"), build_cart_stub(call.from_user.id))
    await call.message.edit_text(
        text,
        reply_markup=simple_buttons(buttons, per_row=1),
    )
    await state.set_state(ShopStates.selecting_branch)


@router.callback_query(F.data.startswith("select_branch_"))
async def select_branch(call: CallbackQuery, state: FSMContext):
    """User selected a branch. Card 21: check availability of cart items at new store."""
    store_id = int(call.data.replace("select_branch_", ""))

    # Verify the store belongs to the current brand
    data = await state.get_data()
    brand_id = data.get('current_brand_id')
    if not brand_id:
        await call.answer(localize("shop.error.brand_required"), show_alert=True)
        return

    stores = get_stores_for_brand(brand_id, active_only=True)
    store = next((s for s in stores if s['id'] == store_id), None)
    if not store:
        await call.answer(localize("shop.error.branch_unavailable"), show_alert=True)
        return

    # Card 21 Phase 5: availability check when switching stores with an active cart
    cart_items = await get_cart_items(call.from_user.id)
    current_store_id = data.get('current_store_id')

    if cart_items and current_store_id != store_id:
        unavailable = _check_unavailable_items(cart_items, store_id)
        if unavailable:
            item_list = "\n".join(f"• {name}" for name in unavailable)
            warning_text = localize("shop.store_switch.unavailable").format(
                n=len(unavailable),
                store_name=store['name'],
                items=item_list,
            )
            await state.update_data(
                pending_store_id=store_id,
                pending_store_name=store['name'],
                unavailable_items=unavailable,
            )
            await state.set_state(ShopStates.confirming_store_switch)
            await call.message.edit_text(
                warning_text,
                reply_markup=store_switch_confirm_keyboard(store_id),
            )
            return

        # All items available: silently update store on cart rows
        bulk_update_cart_store(call.from_user.id, store_id)

    await state.update_data(current_store_id=store['id'], current_store_name=store['name'])
    await _show_categories(call, state)


@router.callback_query(F.data == "switch_brand")
async def switch_brand(call: CallbackQuery, state: FSMContext):
    """Switch to a different brand. Clears brand/store state."""
    await state.update_data(
        current_brand_id=None,
        current_brand_name=None,
        current_store_id=None,
        current_store_name=None,
    )
    await brand_picker(call, state)


async def _show_categories(call: CallbackQuery, state: FSMContext):
    """Show categories for the selected brand. Delegates to shop_and_goods handler."""
    from bot.handlers.user.shop_and_goods import show_brand_categories
    await show_brand_categories(call, state)


# ---------------------------------------------------------------------------
# Card 21 Phase 4: brand-switch save / delete / stay callbacks
# ---------------------------------------------------------------------------

def _serialize_cart_items(cart_items: list) -> tuple[list, Decimal]:
    """Convert get_cart_items result into SavedCart items_json format."""
    items_json = []
    total = Decimal(0)
    for ci in cart_items:
        unit_price = ci['price']
        total += unit_price * ci['quantity']
        items_json.append({
            "name": ci['item_name'],
            "quantity": ci['quantity'],
            "modifiers": ci.get('selected_modifiers'),
            "unit_price": str(unit_price),
        })
    return items_json, total


@router.callback_query(F.data.startswith("save_cart:"))
async def save_cart_callback(call: CallbackQuery, state: FSMContext):
    """Save current cart snapshot then proceed to the pending brand."""
    pending_brand_id = int(call.data.split(":")[1])
    user_id = call.from_user.id

    cart_items = await get_cart_items(user_id)
    cart_stub_data = get_cart_stub_data(user_id)
    brand_id = cart_stub_data['brand_id'] if cart_stub_data else None
    store_id = cart_stub_data['store_id'] if cart_stub_data else None

    if cart_items and brand_id:
        items_json, total = _serialize_cart_items(cart_items)
        save_cart_snapshot(user_id, brand_id, store_id, items_json, total)

    await clear_cart(user_id)

    brand = get_brand(pending_brand_id)
    if not brand or not brand['is_active']:
        await call.answer(localize("shop.brand_unavailable"), show_alert=True)
        await state.set_state(None)
        return

    await call.answer(localize("shop.brand_switch.saved"), show_alert=False)
    await state.update_data(
        current_brand_id=brand['id'],
        current_brand_name=brand['name'],
        pending_brand_id=None,
    )
    await state.set_state(None)
    await _select_branch_or_proceed(call, state, brand['id'])


@router.callback_query(F.data.startswith("delete_cart:"))
async def delete_cart_callback(call: CallbackQuery, state: FSMContext):
    """Delete current cart then proceed to the pending brand."""
    pending_brand_id = int(call.data.split(":")[1])
    user_id = call.from_user.id

    await clear_cart(user_id)

    brand = get_brand(pending_brand_id)
    if not brand or not brand['is_active']:
        await call.answer(localize("shop.brand_unavailable"), show_alert=True)
        await state.set_state(None)
        return

    await call.answer(localize("shop.brand_switch.deleted"), show_alert=False)
    await state.update_data(
        current_brand_id=brand['id'],
        current_brand_name=brand['name'],
        pending_brand_id=None,
    )
    await state.set_state(None)
    await _select_branch_or_proceed(call, state, brand['id'])


@router.callback_query(F.data == "stay_brand")
async def stay_brand_callback(call: CallbackQuery, state: FSMContext):
    """User chose to stay on their current brand. Re-render brand categories."""
    await state.set_state(None)
    await state.update_data(pending_brand_id=None)
    # Navigate back to current brand's categories
    from bot.handlers.user.shop_and_goods import show_brand_categories
    await show_brand_categories(call, state)


# ---------------------------------------------------------------------------
# Card 21 Phase 5: store-switch callbacks
# ---------------------------------------------------------------------------

def _check_unavailable_items(cart_items: list, store_id: int) -> list[str]:
    """Return list of item names from cart that are unavailable at store_id.

    CRITICAL: 'prepared' items have unlimited stock (stock_quantity=0 = unlimited
    per CLAUDE.md) and must NEVER be flagged as unavailable.
    """
    unavailable = []
    with Database().session() as session:
        for ci in cart_items:
            # Fetch item type first — prepared items skip inventory check
            good = session.query(Goods).filter_by(name=ci['item_name']).first()
            if good and good.item_type == 'prepared':
                continue  # unlimited stock, always available

            inv = session.query(BranchInventory).filter_by(
                store_id=store_id,
                item_name=ci['item_name'],
            ).first()
            if not inv or inv.stock_quantity < ci['quantity']:
                unavailable.append(ci['item_name'])
    return unavailable


@router.callback_query(F.data.startswith("switch_and_remove:"))
async def switch_and_remove_callback(call: CallbackQuery, state: FSMContext):
    """Remove unavailable items then switch cart to the new store."""
    store_id = int(call.data.split(":")[1])
    user_id = call.from_user.id

    data = await state.get_data()
    unavailable = data.get('unavailable_items', [])
    store_name = data.get('pending_store_name', '')

    if unavailable:
        remove_items_from_cart(user_id, unavailable)

    bulk_update_cart_store(user_id, store_id)

    await state.update_data(
        current_store_id=store_id,
        current_store_name=store_name,
        pending_store_id=None,
        pending_store_name=None,
        unavailable_items=None,
    )
    await state.set_state(None)
    await _show_categories(call, state)


@router.callback_query(F.data == "stay_store")
async def stay_store_callback(call: CallbackQuery, state: FSMContext):
    """User chose to stay at their current store."""
    await state.update_data(
        pending_store_id=None,
        pending_store_name=None,
        unavailable_items=None,
    )
    await state.set_state(None)
    await _show_categories(call, state)
