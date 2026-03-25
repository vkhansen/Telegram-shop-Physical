"""
Admin Order Management Handler (Card 9).

Provides:
- List all orders (filterable by status)
- View order details
- Change order status (with transition validation)
- Kitchen/rider group notifications on status change
- Delivery photo enforcement for dead drop orders
"""
from datetime import UTC, datetime

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.config.env import EnvKeys
from bot.database import Database
from bot.database.models import Permission
from bot.database.models.main import Order, OrderItem
from bot.filters import HasPermissionFilter
from bot.i18n import localize
from bot.keyboards.inline import back, simple_buttons
from bot.logger_mesh import audit_logger
from bot.states.user_state import AdminOrderStates
from bot.utils.delivery_types import needs_delivery_photo
from bot.utils.order_status import get_allowed_transitions, is_valid_transition
from bot.utils.constants import STATUS_EMOJI

router = Router()

PAGE_SIZE = 8


# ── Order list ────────────────────────────────────────────────────────

@router.callback_query(F.data == "order_management", HasPermissionFilter(permission=Permission.SHOP_MANAGE))
async def order_management_handler(call: CallbackQuery, state: FSMContext):
    """Show order management menu with status filters."""
    await state.clear()
    actions = [
        (localize("admin.orders.filter_all"), "orders_filter_all"),
        (localize("admin.orders.filter_active"), "orders_filter_active"),
        ("⏳ Pending", "orders_filter_pending"),
        ("🔒 Reserved", "orders_filter_reserved"),
        ("✅ Confirmed", "orders_filter_confirmed"),
        ("🍳 Preparing", "orders_filter_preparing"),
        ("📦 Ready", "orders_filter_ready"),
        ("🚗 Out for Delivery", "orders_filter_out_for_delivery"),
        ("✅ Delivered", "orders_filter_delivered"),
        (localize("btn.back"), "console"),
    ]
    await call.message.edit_text(
        localize("admin.orders.list_title"),
        reply_markup=simple_buttons(actions, per_row=2),
    )


@router.callback_query(F.data.startswith("orders_filter_"), HasPermissionFilter(permission=Permission.SHOP_MANAGE))
async def orders_filter_handler(call: CallbackQuery, state: FSMContext):
    """List orders filtered by status."""
    filter_key = call.data.replace("orders_filter_", "")

    with Database().session() as session:
        query = session.query(Order).order_by(Order.created_at.desc())

        if filter_key == "active":
            query = query.filter(Order.order_status.in_([
                "pending", "reserved", "confirmed", "preparing", "ready", "out_for_delivery"
            ]))
        elif filter_key != "all":
            query = query.filter(Order.order_status == filter_key)

        orders = query.limit(PAGE_SIZE).all()

        if not orders:
            await call.message.edit_text(
                localize("admin.orders.empty"),
                reply_markup=back("order_management"),
            )
            return

        buttons = []
        for order in orders:
            emoji = STATUS_EMOJI.get(order.order_status, "")
            label = f"{emoji} {order.order_code} - {order.order_status}"
            buttons.append((label, f"admin_order_{order.id}"))

        buttons.append((localize("btn.back"), "order_management"))

        await call.message.edit_text(
            localize("admin.orders.list_title"),
            reply_markup=simple_buttons(buttons, per_row=1),
        )


# ── Order detail ──────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("admin_order_"), HasPermissionFilter(permission=Permission.SHOP_MANAGE))
async def order_detail_handler(call: CallbackQuery, state: FSMContext):
    """Show detailed order view with status change options."""
    order_id = int(call.data.replace("admin_order_", ""))

    with Database().session() as session:
        order = session.query(Order).filter_by(id=order_id).first()
        if not order:
            await call.answer("Order not found", show_alert=True)
            return

        items = session.query(OrderItem).filter_by(order_id=order.id).all()
        items_text = "\n".join(
            f"  - {it.item_name} x{it.quantity} = {it.price * it.quantity} {EnvKeys.PAY_CURRENCY}"
            for it in items
        ) or "N/A"

        detail = (
            f"<b>Order {order.order_code}</b>\n\n"
            f"Status: <b>{STATUS_EMOJI.get(order.order_status, '')} {order.order_status}</b>\n"
            f"Payment: {order.payment_method}\n"
            f"Total: {order.total_price} {EnvKeys.PAY_CURRENCY}\n"
            f"Phone: {order.phone_number}\n"
            f"Address: {order.delivery_address}\n"
            f"Type: {order.delivery_type}\n"
        )
        if order.delivery_note:
            detail += f"Note: {order.delivery_note}\n"
        if order.google_maps_link:
            detail += f"GPS: {order.google_maps_link}\n"
        if order.driver_id:
            detail += f"Driver: {order.driver_id}\n"
        detail += f"\nItems:\n{items_text}\n"

        # Build action buttons
        buttons = []
        allowed = get_allowed_transitions(order.order_status)
        for next_status in sorted(allowed):
            emoji = STATUS_EMOJI.get(next_status, "")
            buttons.append((
                f"{emoji} → {next_status}",
                f"order_status_{order.id}_{next_status}",
            ))

        buttons.append((localize("btn.back"), "order_management"))

        await call.message.edit_text(
            detail,
            reply_markup=simple_buttons(buttons, per_row=1),
        )


# ── Status change ─────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("order_status_"), HasPermissionFilter(permission=Permission.SHOP_MANAGE))
async def order_status_change_handler(call: CallbackQuery, state: FSMContext):
    """Change order status with validation and notifications."""
    # LOGIC-15 fix: Use prefix removal for robust parsing of multi-word statuses
    # e.g., "order_status_42_out_for_delivery" → id=42, status="out_for_delivery"
    rest = call.data.removeprefix("order_status_")
    order_id_str, new_status = rest.split("_", 1)
    order_id = int(order_id_str)

    with Database().session() as session:
        order = session.query(Order).filter_by(id=order_id).first()
        if not order:
            await call.answer("Order not found", show_alert=True)
            return

        # Validate transition
        if not is_valid_transition(order.order_status, new_status):
            await call.answer(
                localize("admin.orders.invalid_transition",
                         current=order.order_status, new=new_status),
                show_alert=True,
            )
            return

        # Card 4: Dead drop photo enforcement
        if new_status == "delivered" and needs_delivery_photo(order):
            await state.update_data(delivery_photo_order_id=order.id)
            await state.set_state(AdminOrderStates.waiting_delivery_photo)
            await call.message.edit_text(
                localize("delivery.photo.upload_prompt"),
                reply_markup=back(f"admin_order_{order.id}"),
            )
            return

        old_status = order.order_status
        order.order_status = new_status

        # Set timestamps
        if new_status == "delivered":
            order.completed_at = datetime.now(UTC)
            # Set post-delivery chat window (Card 15)
            from bot.handlers.user.delivery_chat_handler import set_post_delivery_window
            set_post_delivery_window(session, order)

        session.commit()

        audit_logger.info(
            f"Admin {call.from_user.id} changed order {order.order_code} "
            f"status: {old_status} → {new_status}"
        )

        # Send notifications
        await _send_status_notifications(call.bot, order, new_status, session)

        await call.answer(
            localize("admin.orders.status_changed",
                     order_id=order.order_code, new_status=new_status),
        )

        # Re-show order detail
        await order_detail_handler(call, state)


# ── Delivery photo upload (Card 4) ───────────────────────────────────

@router.message(AdminOrderStates.waiting_delivery_photo, F.photo)
async def delivery_photo_received(message: Message, state: FSMContext):
    """Handle delivery photo upload for dead drop orders."""
    data = await state.get_data()
    order_id = data.get("delivery_photo_order_id")

    if not order_id:
        await state.clear()
        return

    photo_file_id = message.photo[-1].file_id

    with Database().session() as session:
        order = session.query(Order).filter_by(id=order_id).first()
        if not order:
            await state.clear()
            return

        # Save delivery photo
        order.delivery_photo = photo_file_id
        order.delivery_photo_at = datetime.now(UTC)
        order.delivery_photo_by = message.from_user.id

        # Now mark as delivered
        order.order_status = "delivered"
        order.completed_at = datetime.now(UTC)

        from bot.handlers.user.delivery_chat_handler import set_post_delivery_window
        set_post_delivery_window(session, order)

        session.commit()

        audit_logger.info(
            f"Admin {message.from_user.id} uploaded delivery photo and "
            f"marked order {order.order_code} as delivered"
        )

        # Send delivery photo to customer
        from bot.payments.notifications import send_delivery_photo_to_customer
        await send_delivery_photo_to_customer(order)

        # Send status notifications
        await _send_status_notifications(message.bot, order, "delivered", session)

    await state.clear()
    await message.answer(
        localize("delivery.photo.received") + "\n" +
        localize("admin.orders.status_changed", order_id=order.order_code, new_status="delivered"),
        reply_markup=back("order_management"),
    )


# ── Kitchen / Rider group buttons (Card 9) ────────────────────────────

@router.callback_query(F.data.startswith("kitchen_preparing_"))
async def kitchen_start_preparing(call: CallbackQuery):
    """Kitchen marks order as preparing."""
    try:
        order_id = int(call.data.replace("kitchen_preparing_", ""))
    except (ValueError, TypeError):
        await call.answer("Invalid order", show_alert=True)
        return

    with Database().session() as session:
        order = session.query(Order).filter_by(id=order_id).with_for_update().first()
        if not order or not is_valid_transition(order.order_status, "preparing"):
            await call.answer("Cannot change status", show_alert=True)
            return

        order.order_status = "preparing"
        session.commit()

        # Notify customer
        await _notify_customer_status(call.bot, order)

        await call.answer("Status: Preparing")
        await call.message.edit_text(
            call.message.text + "\n\n🍳 <b>PREPARING</b>",
        )


@router.callback_query(F.data.startswith("kitchen_ready_"))
async def kitchen_mark_ready(call: CallbackQuery):
    """Kitchen marks order as ready."""
    try:
        order_id = int(call.data.replace("kitchen_ready_", ""))
    except (ValueError, TypeError):
        await call.answer("Invalid order", show_alert=True)
        return

    with Database().session() as session:
        order = session.query(Order).filter_by(id=order_id).with_for_update().first()
        if not order or not is_valid_transition(order.order_status, "ready"):
            await call.answer("Cannot change status", show_alert=True)
            return

        order.order_status = "ready"
        session.commit()

        # Notify rider group
        await _send_rider_notification(call.bot, order, session)
        # Notify customer
        await _notify_customer_status(call.bot, order)

        await call.answer("Status: Ready")
        await call.message.edit_text(
            call.message.text + "\n\n📦 <b>READY FOR PICKUP</b>",
        )


@router.callback_query(F.data.startswith("rider_picked_"))
async def rider_picked_up(call: CallbackQuery):
    """Rider marks order as out for delivery."""
    try:
        order_id = int(call.data.replace("rider_picked_", ""))
    except (ValueError, TypeError):
        await call.answer("Invalid order", show_alert=True)
        return

    with Database().session() as session:
        order = session.query(Order).filter_by(id=order_id).with_for_update().first()
        if not order or not is_valid_transition(order.order_status, "out_for_delivery"):
            await call.answer("Cannot change status", show_alert=True)
            return

        # Assign driver if not yet set
        if not order.driver_id:
            order.driver_id = call.from_user.id

        order.order_status = "out_for_delivery"
        session.commit()

        # Notify customer + prompt GPS
        await _notify_customer_status(call.bot, order)
        try:
            from bot.handlers.user.delivery_chat_handler import prompt_customer_gps
            await prompt_customer_gps(call.bot, order)
        except Exception:
            pass

        await call.answer("Status: Out for Delivery")
        await call.message.edit_text(
            call.message.text + "\n\n🚗 <b>OUT FOR DELIVERY</b>",
        )


@router.callback_query(F.data.startswith("rider_delivered_"))
async def rider_mark_delivered(call: CallbackQuery):
    """Rider marks order as delivered."""
    try:
        order_id = int(call.data.replace("rider_delivered_", ""))
    except (ValueError, TypeError):
        await call.answer("Invalid order", show_alert=True)
        return

    with Database().session() as session:
        order = session.query(Order).filter_by(id=order_id).with_for_update().first()
        if not order or not is_valid_transition(order.order_status, "delivered"):
            await call.answer("Cannot change status", show_alert=True)
            return

        order.order_status = "delivered"
        order.completed_at = datetime.now(UTC)

        from bot.handlers.user.delivery_chat_handler import set_post_delivery_window
        set_post_delivery_window(session, order)

        session.commit()

        await _notify_customer_status(call.bot, order)

        await call.answer("Status: Delivered")
        await call.message.edit_text(
            call.message.text + "\n\n✅ <b>DELIVERED</b>",
        )


# ── Internal notification helpers ─────────────────────────────────────

async def _send_status_notifications(bot: Bot, order: Order, new_status: str, session):
    """Send notifications based on status change."""
    try:
        if new_status == "confirmed":
            await _send_kitchen_notification(bot, order, session)
        elif new_status == "ready":
            await _send_rider_notification(bot, order, session)
        elif new_status == "out_for_delivery":
            await _notify_customer_status(bot, order)
            try:
                from bot.handlers.user.delivery_chat_handler import prompt_customer_gps
                await prompt_customer_gps(bot, order)
            except Exception:
                pass
        elif new_status == "delivered" or new_status in ("preparing", "ready"):
            await _notify_customer_status(bot, order)
    except Exception as e:
        audit_logger.warning(f"Failed to send notification for order {order.order_code}: {e}")


async def _send_kitchen_notification(bot: Bot, order: Order, session):
    """Send formatted order to kitchen group (Card 9). Uses per-branch group if available."""
    from bot.database.models.main import Goods, Store

    # Per-branch kitchen group takes priority
    kitchen_group_id = None
    if order.store_id:
        store = session.query(Store).filter_by(id=order.store_id).first()
        if store and store.kitchen_group_id:
            kitchen_group_id = str(store.kitchen_group_id)

    # Fallback to env var
    if not kitchen_group_id:
        kitchen_group_id = EnvKeys.KITCHEN_GROUP_ID

    if not kitchen_group_id:
        return

    items = session.query(OrderItem).filter_by(order_id=order.id).all()

    item_lines = []
    prep_times = []
    for it in items:
        # Build modifier text
        if it.selected_modifiers:
            mod_parts = []
            for gk, sel in it.selected_modifiers.items():
                if isinstance(sel, list):
                    mod_parts.append(f"{gk}: {', '.join(sel)}")
                else:
                    mod_parts.append(f"{gk}: {sel}")
            mod_text = " | " + "; ".join(mod_parts)
        else:
            mod_text = ""

        item_lines.append(f"  - {it.item_name} x{it.quantity}{mod_text}")

        # Look up prep time from Goods
        goods = session.query(Goods).filter(Goods.name == it.item_name).first()
        prep = goods.prep_time_minutes if goods and goods.prep_time_minutes else None
        if prep:
            prep_times.append(prep * it.quantity)

    items_text = "\n".join(item_lines) or "N/A"

    # Calculate total prep time (parallel kitchen work = max of all items)
    max_prep_time = max(prep_times) if prep_times else None
    now = datetime.now(UTC)

    prep_info = ""
    if max_prep_time is not None:
        from datetime import timedelta
        estimated_ready = now + timedelta(minutes=max_prep_time)
        prep_info = (
            f"\n⏱ Prep time: {max_prep_time} min\n"
            f"🕐 Est. ready: {estimated_ready.strftime('%H:%M UTC')}"
        )
        # Update order with prep estimates
        order.total_prep_time_minutes = max_prep_time
        order.estimated_ready_at = estimated_ready
        session.flush()

    text = (
        f"🔔 <b>New Order: {order.order_code}</b>\n\n"
        f"Items:\n{items_text}\n\n"
        f"Note: {order.delivery_note or 'None'}\n"
        f"Type: {order.delivery_type}"
        f"{prep_info}"
    )

    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=localize("kitchen.btn.start_preparing"),
            callback_data=f"kitchen_preparing_{order.id}",
        )],
        [InlineKeyboardButton(
            text=localize("kitchen.btn.mark_ready"),
            callback_data=f"kitchen_ready_{order.id}",
        )],
    ])

    try:
        sent = await bot.send_message(int(kitchen_group_id), text, reply_markup=kb)
        order.kitchen_group_message_id = sent.message_id
        session.commit()
    except Exception as e:
        audit_logger.warning(f"Failed to send kitchen notification: {e}")


async def _send_rider_notification(bot: Bot, order: Order, session):
    """Send order details to rider group (Card 9). Uses per-branch group if available."""
    from bot.database.models.main import Store

    # Per-branch rider group takes priority
    rider_group_id = None
    if order.store_id:
        store = session.query(Store).filter_by(id=order.store_id).first()
        if store and store.rider_group_id:
            rider_group_id = str(store.rider_group_id)

    # Fallback to env var
    if not rider_group_id:
        rider_group_id = EnvKeys.RIDER_GROUP_ID

    if not rider_group_id:
        return

    text = (
        f"📦 <b>Order Ready: {order.order_code}</b>\n\n"
        f"Address: {order.delivery_address}\n"
        f"Phone: {order.phone_number}\n"
        f"Type: {order.delivery_type}\n"
        f"Payment: {order.payment_method}\n"
        f"Total: {order.total_price} {EnvKeys.PAY_CURRENCY}\n"
    )
    if order.google_maps_link:
        text += f"GPS: {order.google_maps_link}\n"
    if order.delivery_note:
        text += f"Note: {order.delivery_note}\n"

    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=localize("rider.btn.picked_up"),
            callback_data=f"rider_picked_{order.id}",
        )],
        [InlineKeyboardButton(
            text=localize("rider.btn.delivered"),
            callback_data=f"rider_delivered_{order.id}",
        )],
    ])

    try:
        sent = await bot.send_message(int(rider_group_id), text, reply_markup=kb)
        order.rider_group_message_id = sent.message_id
        session.commit()
    except Exception as e:
        audit_logger.warning(f"Failed to send rider notification: {e}")


async def _notify_customer_status(bot: Bot, order: Order):
    """Send status update notification to customer."""
    status_key = f"order.status.{order.order_status}"
    if order.order_status == "delivered":
        status_key = "order.status.delivered_notify"

    try:
        message = localize(status_key, order_code=order.order_code)
        await bot.send_message(order.buyer_id, message)
    except Exception as e:
        audit_logger.warning(f"Failed to notify customer for order {order.order_code}: {e}")
