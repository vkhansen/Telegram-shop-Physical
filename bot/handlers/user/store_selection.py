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

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot.database.methods.read import get_all_brands, get_brand, get_stores_for_brand
from bot.i18n import localize
from bot.keyboards.inline import back, simple_buttons
from bot.states import ShopStates

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

    await call.message.edit_text(
        localize("shop.brands.title"),
        reply_markup=simple_buttons(buttons, per_row=1),
    )
    await state.set_state(ShopStates.selecting_brand)


@router.callback_query(F.data.startswith("select_brand_"))
async def select_brand(call: CallbackQuery, state: FSMContext):
    """User selected a brand."""
    brand_id = int(call.data.replace("select_brand_", ""))
    brand = get_brand(brand_id)
    if not brand or not brand['is_active']:
        await call.answer(localize("shop.brand_unavailable"), show_alert=True)
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

    await call.message.edit_text(
        localize("shop.branches.title"),
        reply_markup=simple_buttons(buttons, per_row=1),
    )
    await state.set_state(ShopStates.selecting_branch)


@router.callback_query(F.data.startswith("select_branch_"))
async def select_branch(call: CallbackQuery, state: FSMContext):
    """User selected a branch."""
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
