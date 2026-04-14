from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.database import Database
from bot.database.models.main import CustomerInfo, Goods
from bot.database.methods import get_cart_items, calculate_cart_total, add_to_cart, remove_from_cart, clear_cart
from bot.keyboards import back, simple_buttons, modifier_group_keyboard
from bot.i18n import localize
from bot.config import EnvKeys
from bot.states import CartStates, OrderStates, ModifierSelectionFSM
from bot.handlers.other import is_safe_item_name
from bot.utils.message_utils import safe_edit_text
from bot.utils.tracking import track_event, track_conversion
from bot.utils.modifiers import validate_modifier_selection, calculate_item_price
from bot.utils.cart_stub import build_cart_stub, inject_cart_stub, flash_cart_added

router = Router()


def _format_selected_modifiers(selected_modifiers: dict, modifiers_schema: dict) -> str:
    """Format selected modifiers for display in cart (Card 8)."""
    if not selected_modifiers or not modifiers_schema:
        return ""
    parts = []
    for group_key, selection in selected_modifiers.items():
        group = modifiers_schema.get(group_key)
        if not group:
            continue
        options = group.get("options", [])
        label = group.get("label", group_key)
        if isinstance(selection, list):
            chosen = [o.get("label", o["id"]) for o in options if o["id"] in selection]
            if chosen:
                parts.append(f"{label}: {', '.join(chosen)}")
        else:
            chosen = next((o.get("label", o["id"]) for o in options if o["id"] == selection), None)
            if chosen:
                parts.append(f"{label}: {chosen}")
    return "; ".join(parts)


def _get_modifier_group_keys(modifiers_schema: dict) -> list[str]:
    """Return ordered list of modifier group keys."""
    return list(modifiers_schema.keys()) if modifiers_schema else []


async def _show_modifier_group(call: CallbackQuery, state: FSMContext,
                                item_name: str, group_key: str,
                                modifiers_schema: dict, selected: dict):
    """Show a single modifier group's options to the user."""
    group = modifiers_schema[group_key]
    label = group.get("label", group_key)
    required = group.get("required", False)
    group_type = group.get("type", "single")

    req_text = localize("modifier.required") if required else localize("modifier.optional")
    title = localize("modifier.select_title", label=label) + f" {req_text}"

    # Get already-selected options for this group (for multi-choice toggle display)
    current_selection = selected.get(group_key, [])
    if not isinstance(current_selection, list):
        current_selection = [current_selection] if current_selection else []

    markup = modifier_group_keyboard(item_name, group_key, group, selected=current_selection)

    await safe_edit_text(call.message, title, reply_markup=markup)


@router.callback_query(F.data.startswith('add_to_cart_'))
async def add_to_cart_handler(call: CallbackQuery, state: FSMContext):
    """
    Handle adding item to cart from item details page.
    If item has modifiers, start modifier selection flow (Card 8).
    """
    # Extract item name from callback data: add_to_cart_{item_name}
    item_name = call.data[len('add_to_cart_'):]

    # Validate item name
    if not is_safe_item_name(item_name):
        await call.answer(localize("errors.invalid_item_name"), show_alert=True)
        return

    user_id = call.from_user.id

    # Check if item has modifiers (Card 8)
    with Database().session() as session:
        good = session.query(Goods).filter_by(name=item_name).first()
        modifiers_schema = good.modifiers if good else None

    if modifiers_schema:
        # Start modifier selection flow
        group_keys = _get_modifier_group_keys(modifiers_schema)
        await state.set_state(ModifierSelectionFSM.selecting_modifiers)
        await state.update_data(
            mod_item_name=item_name,
            mod_schema=modifiers_schema,
            mod_group_keys=group_keys,
            mod_current_index=0,
            mod_selected={},
        )
        # Show the first modifier group
        await _show_modifier_group(call, state, item_name, group_keys[0], modifiers_schema, {})
        await call.answer()
        return

    # No modifiers - add directly
    _cart_data = await state.get_data()
    success, message = await add_to_cart(user_id, item_name, quantity=1,
                                          brand_id=_cart_data.get('current_brand_id'))

    if success:
        track_event("cart_add", user_id, {"item": item_name, "quantity": 1})
        track_conversion("customer_journey", "cart_add", user_id)
        await call.answer(localize("cart.add_success", item_name=item_name), show_alert=False)
        # Flash animation only for text messages — photo item details can't be
        # edited via edit_text, so the toast above is the user feedback there.
        if not call.message.photo:
            with Database().session() as session:
                good = session.query(Goods).filter_by(name=item_name).first()
                item_total = good.price if good else 0
            settle_text = inject_cart_stub(call.message.text or "", build_cart_stub(user_id))
            await flash_cart_added(
                call.message, item_name, 1, item_total,
                settle_text, call.message.reply_markup, user_id,
            )
    else:
        await call.answer(localize("cart.add_error", message=message), show_alert=True)


@router.callback_query(F.data.startswith("mod_sel:"), ModifierSelectionFSM.selecting_modifiers)
async def modifier_option_selected(call: CallbackQuery, state: FSMContext):
    """Handle user selecting a modifier option (Card 8)."""
    # Parse: mod_sel:{item_name}:{group_key}:{opt_id}
    parts = call.data.split(":", 3)
    if len(parts) != 4:
        await call.answer()
        return
    _, item_name, group_key, opt_id = parts

    data = await state.get_data()
    modifiers_schema = data.get("mod_schema", {})
    group_keys = data.get("mod_group_keys", [])
    current_index = data.get("mod_current_index", 0)
    selected = data.get("mod_selected", {})

    group = modifiers_schema.get(group_key, {})
    group_type = group.get("type", "single")

    if group_type == "multi":
        # Toggle option in multi-choice list
        current = selected.get(group_key, [])
        if not isinstance(current, list):
            current = [current] if current else []
        if opt_id in current:
            current.remove(opt_id)
        else:
            current.append(opt_id)
        selected[group_key] = current
        await state.update_data(mod_selected=selected)

        # Re-display same group with updated selections
        await _show_modifier_group(call, state, item_name, group_key, modifiers_schema, selected)
        opt_label = next((o.get("label", o["id"]) for o in group.get("options", []) if o["id"] == opt_id), opt_id)
        await call.answer(localize("modifier.selected", choice=opt_label))
    else:
        # Single-choice: record and advance
        selected[group_key] = opt_id
        await state.update_data(mod_selected=selected, mod_current_index=current_index + 1)

        opt_label = next((o.get("label", o["id"]) for o in group.get("options", []) if o["id"] == opt_id), opt_id)
        await call.answer(localize("modifier.selected", choice=opt_label))

        # Advance to next group or finish
        next_index = current_index + 1
        if next_index < len(group_keys):
            await _show_modifier_group(call, state, item_name, group_keys[next_index], modifiers_schema, selected)
        else:
            await _finish_modifier_selection(call, state, selected)


@router.callback_query(F.data.startswith("mod_done:"), ModifierSelectionFSM.selecting_modifiers)
async def modifier_group_done(call: CallbackQuery, state: FSMContext):
    """Handle 'Done' button for multi-choice modifier group (Card 8)."""
    parts = call.data.split(":", 2)
    if len(parts) != 3:
        await call.answer()
        return
    _, item_name, group_key = parts

    data = await state.get_data()
    modifiers_schema = data.get("mod_schema", {})
    group_keys = data.get("mod_group_keys", [])
    current_index = data.get("mod_current_index", 0)
    selected = data.get("mod_selected", {})

    # Validate required group has selection
    group = modifiers_schema.get(group_key, {})
    if group.get("required") and not selected.get(group_key):
        await call.answer(localize("modifier.required"), show_alert=True)
        return

    # Advance to next group
    next_index = current_index + 1
    await state.update_data(mod_current_index=next_index)

    if next_index < len(group_keys):
        await _show_modifier_group(call, state, item_name, group_keys[next_index], modifiers_schema, selected)
        await call.answer()
    else:
        await _finish_modifier_selection(call, state, selected)


@router.callback_query(F.data == "mod_cancel", ModifierSelectionFSM.selecting_modifiers)
async def modifier_cancel(call: CallbackQuery, state: FSMContext):
    """Cancel modifier selection flow (Card 8)."""
    await state.clear()
    await call.answer(localize("cart.add_cancelled"))
    await call.message.edit_text(
        localize("modifier.cancelled"),
        reply_markup=back("back_to_menu")
    )


async def _finish_modifier_selection(call: CallbackQuery, state: FSMContext, selected: dict):
    """Validate and add item with modifiers to cart (Card 8)."""
    data = await state.get_data()
    item_name = data.get("mod_item_name", "")
    modifiers_schema = data.get("mod_schema", {})
    user_id = call.from_user.id

    # Validate
    is_valid, error_msg = validate_modifier_selection(modifiers_schema, selected)
    if not is_valid:
        await call.answer(error_msg, show_alert=True)
        return

    # Clean up empty selections
    clean_selected = {}
    for k, v in selected.items():
        if v:  # Skip empty lists / None
            clean_selected[k] = v

    # Clear FSM state
    await state.clear()

    # Add to cart with modifiers
    success, message = await add_to_cart(user_id, item_name, quantity=1,
                                          selected_modifiers=clean_selected or None,
                                          brand_id=data.get('current_brand_id'))

    if success:
        track_event("cart_add", user_id, {"item": item_name, "quantity": 1, "modifiers": clean_selected})
        track_conversion("customer_journey", "cart_add", user_id)
        await call.answer(localize("cart.add_success", item_name=item_name), show_alert=False)
        with Database().session() as session:
            good = session.query(Goods).filter_by(name=item_name).first()
            unit_price = (
                calculate_item_price(good.price, good.modifiers, clean_selected or None)
                if good else 0
            )
        settle_text = inject_cart_stub(
            localize("cart.add_success", item_name=item_name),
            build_cart_stub(user_id),
        )
        await flash_cart_added(
            call.message, item_name, 1, unit_price,
            settle_text, back("back_to_menu"), user_id,
        )
    else:
        await call.answer(localize("cart.add_error", message=message), show_alert=True)


@router.callback_query(F.data == "view_cart")
async def view_cart_handler(call: CallbackQuery, state: FSMContext):
    """
    Display user's shopping cart
    """
    user_id = call.from_user.id
    cart_items = await get_cart_items(user_id)

    if not cart_items:
        await call.message.edit_text(
            localize("cart.empty"),
            reply_markup=back("back_to_menu")
        )
        return

    # Calculate total once (avoid duplicate DB query)
    total = sum(item['total'] for item in cart_items)

    track_event("cart_view", user_id, {"items_count": len(cart_items), "total": float(total)})

    # Build cart display
    text = localize("cart.title")

    for item in cart_items:
        text += f"<b>{item['item_name']}</b>\n"
        # Show selected modifiers if present (Card 8)
        if item.get('selected_modifiers') and item.get('modifiers_schema'):
            mod_text = _format_selected_modifiers(item['selected_modifiers'], item['modifiers_schema'])
            if mod_text:
                text += localize("cart.item.modifiers", modifiers=mod_text) + "\n"
        text += localize("cart.item.price_format", price=item['price'], currency=EnvKeys.PAY_CURRENCY, quantity=item['quantity']) + "\n"
        text += localize("cart.item.subtotal_format", subtotal=item['total'], currency=EnvKeys.PAY_CURRENCY) + "\n\n"

    text += localize("cart.total_format", total=total, currency=EnvKeys.PAY_CURRENCY)

    # Build keyboard
    buttons = []
    for item in cart_items:
        buttons.append((localize("btn.remove_item", item_name=item['item_name']), f"remove_cart_{item['cart_id']}"))

    buttons.extend([
        (localize("btn.clear_cart"), "clear_cart"),
        (localize("btn.proceed_checkout"), "checkout_cart"),
        (localize("btn.back"), "back_to_menu")
    ])

    markup = simple_buttons(buttons, per_row=1)

    await safe_edit_text(call.message, text, reply_markup=markup)
    await state.set_state(CartStates.viewing_cart)


@router.callback_query(F.data.startswith('remove_cart_'))
async def remove_cart_item_handler(call: CallbackQuery, state: FSMContext):
    """
    Remove specific item from cart
    """
    cart_id = int(call.data[len('remove_cart_'):])
    user_id = call.from_user.id

    success, message = await remove_from_cart(cart_id, user_id)

    if success:
        track_event("cart_remove", user_id, {"cart_id": cart_id})
        # Refresh cart view
        await view_cart_handler(call, state)
        await call.answer(localize("cart.removed_success"), show_alert=False)
    else:
        await call.answer(localize("cart.add_error", message=message), show_alert=True)


@router.callback_query(F.data == "clear_cart")
async def clear_cart_handler(call: CallbackQuery):
    """
    Clear all items from cart
    """
    user_id = call.from_user.id

    success, message = await clear_cart(user_id)

    if success:
        track_event("cart_clear", user_id)
        await call.message.edit_text(
            localize("cart.cleared_success"),
            reply_markup=back("back_to_menu")
        )
        await call.answer()
    else:
        await call.answer(localize("cart.add_error", message=message), show_alert=True)


@router.callback_query(F.data == "checkout_cart")
async def checkout_cart_handler(call: CallbackQuery, state: FSMContext):
    """
    Start checkout process - collect delivery information
    """
    user_id = call.from_user.id
    cart_items = await get_cart_items(user_id)

    if not cart_items:
        await call.answer(localize("cart.empty_alert"), show_alert=True)
        return

    track_event("checkout_start", user_id)
    track_conversion("customer_journey", "checkout_start", user_id)

    # Check if user has customer info saved
    with Database().session() as session:
        customer_info = session.query(CustomerInfo).filter_by(
            telegram_id=user_id
        ).first()

        if customer_info and customer_info.delivery_address and customer_info.phone_number:
            # User has saved info, show summary and ask to confirm or edit
            text = (
                localize("cart.summary_title") +
                localize("cart.saved_delivery_info") +
                localize("cart.delivery_address", address=customer_info.delivery_address) +
                localize("cart.delivery_phone", phone=customer_info.phone_number)
            )
            if customer_info.delivery_note:
                text += localize("cart.delivery_note", note=customer_info.delivery_note)

            text += localize("cart.use_info_question")

            buttons = [
                (localize("btn.use_saved_info"), "confirm_delivery_info"),
                (localize("btn.update_info"), "update_delivery_info"),
                (localize("btn.back_to_cart"), "view_cart")
            ]

            await call.message.edit_text(text, reply_markup=simple_buttons(buttons, per_row=1))
        else:
            # No saved info, start collecting — show location method choice
            from bot.handlers.user.order_handler import show_location_method_choice
            await show_location_method_choice(call.message, state, edit=True)


@router.callback_query(F.data == "update_delivery_info")
async def update_delivery_info_handler(call: CallbackQuery, state: FSMContext):
    """Start flow to update delivery information"""
    from bot.handlers.user.order_handler import show_location_method_choice
    await show_location_method_choice(call.message, state, edit=True)


@router.callback_query(F.data == "confirm_delivery_info")
async def confirm_delivery_info_handler(call: CallbackQuery, state: FSMContext):
    """User confirmed using saved delivery info, check for bonuses then proceed to payment"""
    user_id = call.from_user.id

    # Load saved delivery info from CustomerInfo and save to state
    with Database().session() as session:
        customer_info = session.query(CustomerInfo).filter_by(telegram_id=user_id).first()

        if not customer_info or not customer_info.delivery_address or not customer_info.phone_number:
            await call.answer(localize("cart.no_saved_info"), show_alert=True)
            return

        # Save delivery info to state so it can be used when creating the order
        await state.update_data(
            delivery_address=customer_info.delivery_address,
            phone_number=customer_info.phone_number,
            delivery_note=customer_info.delivery_note or ""
        )

    # Import here to avoid circular imports
    from bot.handlers.user.order_handler import check_and_ask_about_bonus
    await call.message.delete()
    await check_and_ask_about_bonus(call.message, state, user_id=user_id, from_callback=True)
