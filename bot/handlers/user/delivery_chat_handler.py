"""
Driver-Customer Chat Relay with Recording (Card 13).

Provides a relayed chat between driver and customer during active deliveries.
All messages are recorded in the delivery_chat_messages table for audit.

Flow:
- Driver sends message in rider group → bot relays to customer with "Driver:" prefix
- Customer replies via bot → bot relays to rider group with "Customer:" prefix
- All messages (text, photo, location) are logged
- Driver can share live location → forwarded to customer for tracking
"""
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from bot.database import Database
from bot.database.models.main import Order, DeliveryChatMessage
from bot.config.env import EnvKeys
from bot.i18n import localize
from bot.logger_mesh import logger

router = Router()


async def relay_driver_to_customer(bot, order: Order, message: Message):
    """
    Relay a message from driver to customer and record it.

    Args:
        bot: Bot instance
        order: Active order being delivered
        message: Driver's message to relay
    """
    with Database().session() as session:
        # Determine message content
        msg_text = None
        photo_id = None
        loc_lat = None
        loc_lng = None

        if message.text:
            msg_text = message.text
            # Send to customer
            await bot.send_message(
                order.buyer_id,
                f"🛵 <b>Driver ({order.order_code}):</b>\n{msg_text}"
            )

        elif message.photo:
            photo_id = message.photo[-1].file_id
            caption = f"🛵 <b>Driver ({order.order_code}):</b>"
            if message.caption:
                caption += f"\n{message.caption}"
                msg_text = message.caption
            await bot.send_photo(order.buyer_id, photo_id, caption=caption)

        elif message.location:
            loc_lat = message.location.latitude
            loc_lng = message.location.longitude

            if message.location.live_period:
                # Live location — forward directly so customer gets real-time updates
                await bot.forward_message(
                    order.buyer_id,
                    message.chat.id,
                    message.message_id
                )
                # Store the live location message ID on order for tracking
                db_order = session.query(Order).filter_by(id=order.id).first()
                if db_order:
                    db_order.driver_live_location_message_id = message.message_id
            else:
                # Static location
                await bot.send_location(
                    order.buyer_id,
                    latitude=loc_lat,
                    longitude=loc_lng
                )
                await bot.send_message(
                    order.buyer_id,
                    f"📍 <b>Driver location ({order.order_code})</b>"
                )

        # Record in audit log
        chat_msg = DeliveryChatMessage(
            order_id=order.id,
            sender_id=message.from_user.id,
            sender_role="driver",
            message_text=msg_text,
            photo_file_id=photo_id,
            location_lat=loc_lat,
            location_lng=loc_lng,
            telegram_message_id=message.message_id,
        )
        session.add(chat_msg)
        session.commit()


async def relay_customer_to_driver(bot, order: Order, message: Message):
    """
    Relay a message from customer to driver/rider group and record it.

    Args:
        bot: Bot instance
        order: Active order
        message: Customer's message to relay
    """
    rider_group_id = EnvKeys.RIDER_GROUP_ID
    if not rider_group_id:
        await message.answer(localize("order.delivery.chat_unavailable"))
        return

    with Database().session() as session:
        msg_text = None
        photo_id = None
        loc_lat = None
        loc_lng = None

        if message.text:
            msg_text = message.text
            await bot.send_message(
                int(rider_group_id),
                f"👤 <b>Customer ({order.order_code}):</b>\n{msg_text}"
            )

        elif message.photo:
            photo_id = message.photo[-1].file_id
            caption = f"👤 <b>Customer ({order.order_code}):</b>"
            if message.caption:
                caption += f"\n{message.caption}"
                msg_text = message.caption
            await bot.send_photo(int(rider_group_id), photo_id, caption=caption)

        elif message.location:
            loc_lat = message.location.latitude
            loc_lng = message.location.longitude
            await bot.send_location(
                int(rider_group_id),
                latitude=loc_lat,
                longitude=loc_lng
            )
            await bot.send_message(
                int(rider_group_id),
                f"📍 <b>Customer location ({order.order_code})</b>"
            )

        # Record in audit log
        chat_msg = DeliveryChatMessage(
            order_id=order.id,
            sender_id=message.from_user.id,
            sender_role="customer",
            message_text=msg_text,
            photo_file_id=photo_id,
            location_lat=loc_lat,
            location_lng=loc_lng,
            telegram_message_id=message.message_id,
        )
        session.add(chat_msg)
        session.commit()


async def start_driver_live_location(bot, order: Order, driver_id: int):
    """
    Instruct driver to share live location for the delivery duration.

    The driver shares live location in the rider group → bot forwards to customer.
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


async def get_chat_history(order_id: int) -> list[dict]:
    """
    Get all recorded chat messages for an order.

    Returns:
        List of message dicts with sender_role, message_text, photo_file_id, timestamps
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
                "created_at": msg.created_at.isoformat() if msg.created_at else None,
            }
            for msg in messages
        ]
