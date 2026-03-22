"""
Driver-Customer Chat Relay with Recording (Card 13 + Card 15).

Provides a relayed chat between driver and customer during active deliveries.
All messages are recorded in the delivery_chat_messages table for audit.

Card 15 additions:
- Customer can send single GPS or live GPS during delivery
- Chat session lifecycle (active from confirmed through post-delivery window)
- Live location edit events captured and logged
- All GPS points logged with is_live_location flag

Flow:
- Driver sends message in rider group -> bot relays to customer with "Driver:" prefix
- Customer replies via bot -> bot relays to rider group with "Customer:" prefix
- All messages (text, photo, location) are logged
- Driver can share live location -> forwarded to customer for tracking
- Customer can share static or live location -> forwarded to rider group for driver
"""
from datetime import datetime, timedelta, timezone

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.enums.chat_type import ChatType
from aiogram.fsm.context import FSMContext

from bot.config.env import EnvKeys
from bot.database import Database
from bot.database.models.main import DeliveryChatMessage, Order
from bot.i18n import localize
from bot.keyboards.inline import delivery_gps_choice_keyboard
from bot.logger_mesh import logger
from bot.states.user_state import DeliveryChatStates

router = Router()


# ---------------------------------------------------------------------------
# Chat session lifecycle (Card 15)
# ---------------------------------------------------------------------------

def is_chat_active(order: Order) -> bool:
    """Check if the chat session is still active for this order."""
    if order.order_status in ('confirmed', 'preparing', 'ready', 'out_for_delivery'):
        return True
    if order.order_status == 'delivered' and order.chat_post_delivery_until:
        now = datetime.now(timezone.utc)
        deadline = order.chat_post_delivery_until
        # Handle naive datetimes (e.g. from SQLite) by assuming UTC
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
        return now < deadline
    return False


def open_chat_session(session, order: Order):
    """Mark the chat session as opened on the order."""
    db_order = session.query(Order).filter_by(id=order.id).first()
    if db_order and not db_order.chat_opened_at:
        db_order.chat_opened_at = datetime.now(timezone.utc)


def close_chat_session(session, order: Order):
    """Mark the chat session as closed."""
    db_order = session.query(Order).filter_by(id=order.id).first()
    if db_order and not db_order.chat_closed_at:
        db_order.chat_closed_at = datetime.now(timezone.utc)


def set_post_delivery_window(session, order: Order):
    """Set the post-delivery chat window when order is delivered."""
    db_order = session.query(Order).filter_by(id=order.id).first()
    if db_order:
        minutes = EnvKeys.POST_DELIVERY_CHAT_MINUTES
        db_order.chat_post_delivery_until = datetime.now(timezone.utc) + timedelta(minutes=minutes)


# ---------------------------------------------------------------------------
# Customer GPS prompt (Card 15)
# ---------------------------------------------------------------------------

async def prompt_customer_gps(bot, order: Order, locale: str = None):
    """
    Send GPS choice prompt to customer when order goes out_for_delivery.
    Customer can choose: static location, live location, or skip.
    """
    text = localize("delivery.gps.prompt", locale=locale, order_code=order.order_code)
    await bot.send_message(
        order.buyer_id,
        text,
        reply_markup=delivery_gps_choice_keyboard(locale=locale),
    )


async def handle_customer_static_location(bot, order: Order, message: Message):
    """
    Handle customer sharing a static GPS location during delivery.
    Forwards to rider group and logs it.
    """
    rider_group_id = EnvKeys.RIDER_GROUP_ID
    if not rider_group_id:
        return

    loc_lat = message.location.latitude
    loc_lng = message.location.longitude

    # Forward to rider group
    await bot.send_location(
        int(rider_group_id),
        latitude=loc_lat,
        longitude=loc_lng
    )
    await bot.send_message(
        int(rider_group_id),
        f"📍 <b>Customer location ({order.order_code})</b>"
    )

    # Log in audit trail
    with Database().session() as session:
        open_chat_session(session, order)
        chat_msg = DeliveryChatMessage(
            order_id=order.id,
            sender_id=message.from_user.id,
            sender_role="customer",
            location_lat=loc_lat,
            location_lng=loc_lng,
            is_live_location=False,
            telegram_message_id=message.message_id,
        )
        session.add(chat_msg)
        session.commit()


async def handle_customer_live_location(bot, order: Order, message: Message):
    """
    Handle customer sharing live GPS location during delivery.
    Forwards to rider group so driver can track customer in real-time.
    """
    rider_group_id = EnvKeys.RIDER_GROUP_ID
    if not rider_group_id:
        return

    loc_lat = message.location.latitude
    loc_lng = message.location.longitude

    # Forward live location to rider group
    await bot.forward_message(
        int(rider_group_id),
        message.chat.id,
        message.message_id
    )
    await bot.send_message(
        int(rider_group_id),
        f"📡 <b>Customer LIVE location ({order.order_code})</b>\n"
        f"This pin updates in real-time."
    )

    # Store live location message ID on order
    with Database().session() as session:
        open_chat_session(session, order)
        db_order = session.query(Order).filter_by(id=order.id).first()
        if db_order:
            db_order.customer_live_location_message_id = message.message_id

        chat_msg = DeliveryChatMessage(
            order_id=order.id,
            sender_id=message.from_user.id,
            sender_role="customer",
            location_lat=loc_lat,
            location_lng=loc_lng,
            is_live_location=True,
            live_location_update_count=0,
            telegram_message_id=message.message_id,
        )
        session.add(chat_msg)
        session.commit()


async def handle_live_location_update(bot, order: Order, message: Message, sender_role: str):
    """
    Handle an edited_message event for a live location update (Card 15).
    Captures every GPS point update from both driver and customer live locations.
    """
    loc_lat = message.location.latitude
    loc_lng = message.location.longitude

    with Database().session() as session:
        # Count previous updates for this live location session
        prev_count = session.query(DeliveryChatMessage).filter_by(
            order_id=order.id,
            sender_id=message.from_user.id,
            is_live_location=True,
        ).count()

        chat_msg = DeliveryChatMessage(
            order_id=order.id,
            sender_id=message.from_user.id,
            sender_role=sender_role,
            location_lat=loc_lat,
            location_lng=loc_lng,
            is_live_location=True,
            live_location_update_count=prev_count,
            telegram_message_id=message.message_id,
        )
        session.add(chat_msg)
        session.commit()


# ---------------------------------------------------------------------------
# Shared relay helper (Card 13, enhanced Card 15)
# ---------------------------------------------------------------------------

async def _relay_message(bot, order: Order, message: Message,
                         target_chat_id: int, sender_role: str,
                         sender_label: str, sender_emoji: str,
                         live_location_field: str):
    """
    Relay a message (text/photo/location) to target_chat_id and record it.

    Args:
        bot: Bot instance
        order: Active order
        message: Source message to relay
        target_chat_id: Chat ID to relay to
        sender_role: 'driver' or 'customer' (for audit log)
        sender_label: Display label (e.g. 'Driver', 'Customer')
        sender_emoji: Emoji prefix for text relay
        live_location_field: Order attribute to store live location msg ID
    """
    with Database().session() as session:
        open_chat_session(session, order)

        msg_text = None
        photo_id = None
        loc_lat = None
        loc_lng = None
        is_live = False

        if message.text:
            msg_text = message.text
            await bot.send_message(
                target_chat_id,
                f"{sender_emoji} <b>{sender_label} ({order.order_code}):</b>\n{msg_text}"
            )

        elif message.photo:
            photo_id = message.photo[-1].file_id
            caption = f"{sender_emoji} <b>{sender_label} ({order.order_code}):</b>"
            if message.caption:
                caption += f"\n{message.caption}"
                msg_text = message.caption
            await bot.send_photo(target_chat_id, photo_id, caption=caption)

        elif message.location:
            loc_lat = message.location.latitude
            loc_lng = message.location.longitude

            if message.location.live_period:
                is_live = True
                await bot.forward_message(
                    target_chat_id,
                    message.chat.id,
                    message.message_id
                )
                await bot.send_message(
                    target_chat_id,
                    f"📡 <b>{sender_label} LIVE location ({order.order_code})</b>\n"
                    f"This pin updates in real-time."
                )
                db_order = session.query(Order).filter_by(id=order.id).first()
                if db_order:
                    setattr(db_order, live_location_field, message.message_id)
            else:
                await bot.send_location(
                    target_chat_id,
                    latitude=loc_lat,
                    longitude=loc_lng
                )
                await bot.send_message(
                    target_chat_id,
                    f"📍 <b>{sender_label} location ({order.order_code})</b>"
                )

        # Record in audit log
        chat_msg = DeliveryChatMessage(
            order_id=order.id,
            sender_id=message.from_user.id,
            sender_role=sender_role,
            message_text=msg_text,
            photo_file_id=photo_id,
            location_lat=loc_lat,
            location_lng=loc_lng,
            is_live_location=is_live,
            live_location_update_count=0 if is_live else None,
            telegram_message_id=message.message_id,
        )
        session.add(chat_msg)
        session.commit()


# ---------------------------------------------------------------------------
# Driver -> Customer relay (Card 13, enhanced Card 15)
# ---------------------------------------------------------------------------

async def relay_driver_to_customer(bot, order: Order, message: Message):
    """Relay a message from driver to customer and record it."""
    if not is_chat_active(order):
        return

    await _relay_message(
        bot, order, message,
        target_chat_id=order.buyer_id,
        sender_role="driver",
        sender_label="Driver",
        sender_emoji="🛵",
        live_location_field="driver_live_location_message_id",
    )


# ---------------------------------------------------------------------------
# Customer -> Driver relay (Card 13, enhanced Card 15)
# ---------------------------------------------------------------------------

async def relay_customer_to_driver(bot, order: Order, message: Message):
    """Relay a message from customer to driver/rider group and record it."""
    rider_group_id = EnvKeys.RIDER_GROUP_ID
    if not rider_group_id:
        await message.answer(localize("order.delivery.chat_unavailable"))
        return

    # Check chat session is still active (Card 15)
    if not is_chat_active(order):
        await message.answer(localize("delivery.chat.session_closed"))
        # Still log the message for admin audit even after session closes
        with Database().session() as session:
            chat_msg = DeliveryChatMessage(
                order_id=order.id,
                sender_id=message.from_user.id,
                sender_role="customer",
                message_text=message.text if message.text else None,
                telegram_message_id=message.message_id,
            )
            session.add(chat_msg)
            session.commit()
        return

    await _relay_message(
        bot, order, message,
        target_chat_id=int(rider_group_id),
        sender_role="customer",
        sender_label="Customer",
        sender_emoji="👤",
        live_location_field="customer_live_location_message_id",
    )


# ---------------------------------------------------------------------------
# Driver live location prompt (Card 13)
# ---------------------------------------------------------------------------

async def start_driver_live_location(bot, order: Order, driver_id: int):
    """
    Instruct driver to share live location for the delivery duration.

    The driver shares live location in the rider group -> bot forwards to customer.
    Telegram live location auto-expires after the set period (max 8 hours).
    """
    rider_group_id = EnvKeys.RIDER_GROUP_ID
    if not rider_group_id:
        return

    await bot.send_message(
        int(rider_group_id),
        f"📍 <b>Order {order.order_code}</b>\n"
        f"Please share your live location for this delivery.\n"
        f"Tap 📎 → Location → Share Live Location"
    )


# ---------------------------------------------------------------------------
# Chat history (Card 13, enhanced Card 15)
# ---------------------------------------------------------------------------

async def get_chat_history(order_id: int) -> list[dict]:
    """
    Get all recorded chat messages for an order including GPS metadata.

    Returns:
        List of message dicts with sender_role, message_text, photo_file_id,
        location data, live location flags, and timestamps.
    """
    with Database().session() as session:
        messages = session.query(DeliveryChatMessage).filter_by(
            order_id=order_id
        ).order_by(DeliveryChatMessage.created_at).all()

        return [
            {
                "sender_role": msg.sender_role,
                "sender_id": msg.sender_id,
                "message_text": msg.message_text,
                "photo_file_id": msg.photo_file_id,
                "location_lat": msg.location_lat,
                "location_lng": msg.location_lng,
                "is_live_location": msg.is_live_location,
                "live_location_update_count": msg.live_location_update_count,
                "created_at": msg.created_at.isoformat() if msg.created_at else None,
            }
            for msg in messages
        ]


async def get_location_trail(order_id: int, sender_role: str = None) -> list[dict]:
    """
    Get all GPS points for an order, optionally filtered by sender role (Card 15).
    Useful for rendering a delivery route or customer movement on a map.

    Returns:
        List of {lat, lng, sender_role, is_live, timestamp} dicts in chronological order.
    """
    with Database().session() as session:
        query = session.query(DeliveryChatMessage).filter(
            DeliveryChatMessage.order_id == order_id,
            DeliveryChatMessage.location_lat.isnot(None),
        )
        if sender_role:
            query = query.filter(DeliveryChatMessage.sender_role == sender_role)
        query = query.order_by(DeliveryChatMessage.created_at)

        return [
            {
                "lat": msg.location_lat,
                "lng": msg.location_lng,
                "sender_role": msg.sender_role,
                "is_live": msg.is_live_location,
                "update_num": msg.live_location_update_count,
                "timestamp": msg.created_at.isoformat() if msg.created_at else None,
            }
            for msg in query.all()
        ]


# ===========================================================================
# WIRED HANDLER: Rider Group Message Listener (Card 13)
# ===========================================================================

@router.message(F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))
async def rider_group_message_listener(message: Message):
    """
    Listen for messages in the rider group and relay them to the customer.

    LOGIC-37 note: This handler matches all group messages due to aiogram
    filter limitations. The early return below minimizes overhead.
    """
    rider_group_id = EnvKeys.RIDER_GROUP_ID
    if not rider_group_id:
        return

    # LOGIC-37 fix: Early return ASAP to minimize DB queries for non-rider-group messages
    if str(message.chat.id) != str(rider_group_id):
        return

    # Ignore bot's own messages
    if message.from_user and message.from_user.is_bot:
        return

    # Ignore commands
    if message.text and message.text.startswith('/'):
        return

    sender_id = message.from_user.id

    # Find an active order for this driver
    with Database().session() as session:
        # First try: order assigned to this driver
        order = session.query(Order).filter(
            Order.driver_id == sender_id,
            Order.order_status == 'out_for_delivery',
        ).order_by(Order.created_at.desc()).first()

        if not order:
            # Fallback: any active out_for_delivery order (driver_id not yet assigned)
            order = session.query(Order).filter(
                Order.order_status == 'out_for_delivery',
            ).order_by(Order.created_at.desc()).first()

        if not order:
            return

        # Assign driver_id if not yet set
        if not order.driver_id:
            order.driver_id = sender_id
            session.commit()

        try:
            await relay_driver_to_customer(message.bot, order, message)
        except Exception as e:
            logger.error(f"Failed to relay driver message for order {order.order_code}: {e}")


# ===========================================================================
# WIRED HANDLER: Customer Chat Initiation (Card 13)
# ===========================================================================

@router.callback_query(F.data.startswith("chat_with_driver_"))
async def start_customer_chat(call: CallbackQuery, state: FSMContext):
    """
    Customer taps 'Chat with Driver' button on their active order.
    Enters the delivery chat FSM state.
    """
    order_id = int(call.data.replace("chat_with_driver_", ""))

    with Database().session() as session:
        order = session.query(Order).filter(
            Order.id == order_id,
            Order.buyer_id == call.from_user.id,
        ).first()

        if not order or not is_chat_active(order):
            await call.answer(
                localize("order.delivery.chat_no_active_delivery"),
                show_alert=True
            )
            return

        rider_group_id = EnvKeys.RIDER_GROUP_ID
        if not rider_group_id:
            await call.answer(
                localize("order.delivery.chat_unavailable"),
                show_alert=True
            )
            return

        await state.update_data(chat_order_id=order.id)

    await call.answer()
    await state.set_state(DeliveryChatStates.chatting_with_driver)
    await call.message.answer(localize("order.delivery.chat_started"))


# ===========================================================================
# WIRED HANDLER: Customer Reply Detection in Chat Mode (Card 13)
# ===========================================================================

@router.message(DeliveryChatStates.chatting_with_driver, F.text == "/endchat")
async def end_customer_chat(message: Message, state: FSMContext):
    """Customer ends the delivery chat session."""
    await state.clear()
    await message.answer(localize("order.delivery.chat_ended"))


@router.message(DeliveryChatStates.chatting_with_driver, F.chat.type == ChatType.PRIVATE)
async def customer_chat_message(message: Message, state: FSMContext):
    """
    Handle customer messages while in delivery chat mode.
    Relays text, photo, or location to the rider group.
    """
    data = await state.get_data()
    order_id = data.get("chat_order_id")

    if not order_id:
        await state.clear()
        await message.answer(localize("order.delivery.chat_no_active_delivery"))
        return

    with Database().session() as session:
        order = session.query(Order).filter(
            Order.id == order_id,
        ).first()

        if not order or not is_chat_active(order):
            await state.clear()
            await message.answer(localize("order.delivery.chat_no_active_delivery"))
            return

        try:
            await relay_customer_to_driver(message.bot, order, message)
            await message.answer(localize("order.delivery.chat_message_sent"))
        except Exception as e:
            logger.error(f"Failed to relay customer message for order {order.order_code}: {e}")
            await message.answer(localize("order.delivery.chat_unavailable"))


# ===========================================================================
# WIRED HANDLER: GPS Choice Callbacks (Card 15)
# ===========================================================================

@router.callback_query(F.data == "delivery_gps_static")
async def gps_choice_static(call: CallbackQuery, state: FSMContext):
    """Customer chose to send a single static location."""
    await call.answer()
    await call.message.edit_text(localize("delivery.gps.static_sent"))

    # Set state to expect a location message
    await state.set_state(DeliveryChatStates.waiting_customer_gps_choice)
    await state.update_data(gps_mode="static")

    # Prompt user to tap the attachment -> location
    await call.message.answer(
        "📎 Tap the attachment icon → Location → Send your current location"
    )


@router.callback_query(F.data == "delivery_gps_live")
async def gps_choice_live(call: CallbackQuery, state: FSMContext):
    """Customer chose to share live location."""
    await call.answer()
    await call.message.edit_text(localize("delivery.gps.live_started"))

    await state.set_state(DeliveryChatStates.waiting_customer_gps_choice)
    await state.update_data(gps_mode="live")

    await call.message.answer(
        "📎 Tap the attachment icon → Location → Share Live Location"
    )


@router.callback_query(F.data == "delivery_gps_skip")
async def gps_choice_skip(call: CallbackQuery, state: FSMContext):
    """Customer chose to skip GPS sharing."""
    await call.answer()
    await call.message.edit_text(localize("delivery.gps.skipped"))

    # Enter chat mode directly
    data = await state.get_data()
    order_id = data.get("chat_order_id")
    if order_id:
        await state.set_state(DeliveryChatStates.chatting_with_driver)
    else:
        await state.clear()


@router.message(DeliveryChatStates.waiting_customer_gps_choice, F.location)
async def handle_gps_choice_location(message: Message, state: FSMContext):
    """Handle the location message after customer chose static or live GPS."""
    data = await state.get_data()
    gps_mode = data.get("gps_mode", "static")
    order_id = data.get("chat_order_id")

    if not order_id:
        await state.clear()
        await message.answer(localize("order.delivery.chat_no_active_delivery"))
        return

    with Database().session() as session:
        order = session.query(Order).filter_by(id=order_id).first()
        if not order:
            await state.clear()
            return

        if message.location.live_period or gps_mode == "live":
            await handle_customer_live_location(message.bot, order, message)
            await message.answer(localize("delivery.gps.live_started"))
        else:
            await handle_customer_static_location(message.bot, order, message)
            await message.answer(localize("delivery.gps.static_sent"))

    # Transition to chat mode
    await state.set_state(DeliveryChatStates.chatting_with_driver)


# ===========================================================================
# WIRED HANDLER: Live Location Edit Events (Card 15)
# ===========================================================================

@router.edited_message(F.location, F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))
async def edited_location_rider_group(message: Message):
    """
    Capture live location updates from driver in the rider group.
    Telegram sends edited_message events when a live location pin moves.
    """
    rider_group_id = EnvKeys.RIDER_GROUP_ID
    if not rider_group_id or str(message.chat.id) != str(rider_group_id):
        return

    if message.from_user and message.from_user.is_bot:
        return

    sender_id = message.from_user.id

    with Database().session() as session:
        order = session.query(Order).filter(
            Order.driver_id == sender_id,
            Order.order_status.in_(['out_for_delivery', 'delivered']),
        ).order_by(Order.created_at.desc()).first()

        if not order:
            return

        try:
            await handle_live_location_update(message.bot, order, message, "driver")
        except Exception as e:
            logger.error(f"Failed to log driver live location update for order {order.order_code}: {e}")


@router.edited_message(F.location, F.chat.type == ChatType.PRIVATE)
async def edited_location_customer(message: Message):
    """
    Capture live location updates from customer in private chat.
    Telegram sends edited_message events when a live location pin moves.
    Relays the updated position to the rider group.
    """
    sender_id = message.from_user.id

    with Database().session() as session:
        order = session.query(Order).filter(
            Order.buyer_id == sender_id,
            Order.customer_live_location_message_id.isnot(None),
            Order.order_status.in_(['out_for_delivery', 'confirmed', 'preparing', 'ready']),
        ).order_by(Order.created_at.desc()).first()

        if not order:
            return

        try:
            await handle_live_location_update(message.bot, order, message, "customer")

            # Also relay updated location to rider group
            rider_group_id = EnvKeys.RIDER_GROUP_ID
            if rider_group_id:
                await message.bot.send_location(
                    int(rider_group_id),
                    latitude=message.location.latitude,
                    longitude=message.location.longitude,
                )
        except Exception as e:
            logger.error(f"Failed to log customer live location update for order {order.order_code}: {e}")
