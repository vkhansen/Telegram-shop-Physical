from datetime import datetime, timedelta

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.types import InlineKeyboardMarkup

from bot.database.models.main import Order
from bot.i18n import localize
from bot.config.env import EnvKeys
from bot.utils.currency import format_currency

import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shared Bot instance (lazy-initialized, reuses a single aiohttp session)
# ---------------------------------------------------------------------------
_shared_bot: Bot | None = None


def get_shared_bot() -> Bot:
    """
    Return a module-level Bot instance that reuses one aiohttp session
    instead of creating (and tearing down) a new one per notification.
    """
    global _shared_bot
    if _shared_bot is None:
        _shared_bot = Bot(
            token=EnvKeys.TOKEN,
            default=DefaultBotProperties(parse_mode="HTML"),
        )
    return _shared_bot


async def close_shared_bot() -> None:
    """Call on shutdown to cleanly close the shared session."""
    global _shared_bot
    if _shared_bot is not None:
        await _shared_bot.session.close()
        _shared_bot = None


# ---------------------------------------------------------------------------
# Core send helpers
# ---------------------------------------------------------------------------

async def send_order_notification(telegram_id: int, message_text: str) -> bool:
    """
    Send a notification message to user via Telegram.

    Args:
        telegram_id: Telegram user ID
        message_text: Message to send

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        bot = get_shared_bot()
        await bot.send_message(telegram_id, message_text)
        return True
    except Exception as e:
        logger.warning(f"Failed to send notification to {telegram_id}: {str(e)[:100]}")
        return False


async def _send_to_group(chat_id: str | int, message_text: str,
                         reply_markup: InlineKeyboardMarkup = None) -> int | None:
    """
    Send a message to a Telegram group and return the message_id.

    Returns:
        message_id on success, None on failure
    """
    if not chat_id:
        return None
    try:
        bot = get_shared_bot()
        msg = await bot.send_message(
            chat_id=int(chat_id),
            text=message_text,
            reply_markup=reply_markup,
        )
        return msg.message_id
    except Exception as e:
        logger.warning(f"Failed to send group message to {chat_id}: {str(e)[:100]}")
        return None


# ---------------------------------------------------------------------------
# Item formatting helper
# ---------------------------------------------------------------------------

def format_order_items(items: list) -> str:
    """
    Format order items for display.

    Args:
        items: List of OrderItem objects

    Returns:
        Formatted string with items list
    """
    if not items:
        return "N/A"

    items_list = [f"  • {item.item_name} x {item.quantity} - ${item.price * item.quantity}"
                  for item in items]
    return "\n".join(items_list)


# ---------------------------------------------------------------------------
# Order notification functions
# ---------------------------------------------------------------------------

async def notify_order_confirmed(order: Order, items: list, delivery_time: datetime) -> bool:
    """Send order confirmation notification to customer."""
    delivery_time_str = delivery_time.strftime("%Y-%m-%d %H:%M")
    items_formatted = format_order_items(items)

    message = localize("order.status.notify_order_confirmed",
                       order_code=order.order_code,
                       delivery_time=delivery_time_str,
                       items=items_formatted,
                       total=f"{order.total_price} {EnvKeys.PAY_CURRENCY}")

    return await send_order_notification(order.buyer_id, message)


async def notify_order_delivered(order: Order) -> bool:
    """Send order delivery confirmation to customer."""
    message = localize("order.status.notify_order_delivered",
                       order_code=order.order_code,
                       total=f"${order.total_price}")

    return await send_order_notification(order.buyer_id, message)


async def send_delivery_photo_to_customer(order: Order) -> bool:
    """
    Send delivery photo proof to customer (Card 4).

    Args:
        order: Order object with delivery_photo set (Telegram file_id)

    Returns:
        True if sent successfully, False otherwise
    """
    if not order.delivery_photo or not order.buyer_id:
        return False

    try:
        bot = get_shared_bot()
        caption = localize("delivery.photo.customer_notification",
                           order_code=order.order_code)
        await bot.send_photo(
            chat_id=order.buyer_id,
            photo=order.delivery_photo,
            caption=caption,
        )
        return True
    except Exception as e:
        logger.warning(f"Failed to send delivery photo to {order.buyer_id}: {str(e)[:100]}")
        return False


async def notify_order_modified(order: Order, changes_description: str) -> bool:
    """Send order modification notification to customer."""
    message = localize("order.status.notify_order_modified",
                       order_code=order.order_code,
                       changes=changes_description,
                       total=f"${order.total_price}")

    return await send_order_notification(order.buyer_id, message)


# ---------------------------------------------------------------------------
# Group notifications
# ---------------------------------------------------------------------------

async def notify_kitchen_group(bot: Bot, order: Order, items: list) -> int | None:
    """
    Send formatted order to kitchen group when status becomes 'confirmed'.

    Args:
        bot: Bot instance (unused, kept for interface consistency)
        order: Order object
        items: List of OrderItem objects

    Returns:
        message_id of the sent message, or None on failure
    """
    from bot.keyboards.inline import kitchen_order_keyboard

    items_formatted = format_order_items(items)
    total = format_currency(order.total_price)

    message = localize(
        "kitchen.order_received",
        order_id=order.id,
        order_code=order.order_code or "N/A",
        items=items_formatted,
        total=total,
        address=order.delivery_address or "N/A",
        phone=order.phone_number or "N/A",
    )

    keyboard = kitchen_order_keyboard(order.id)
    return await _send_to_group(EnvKeys.KITCHEN_GROUP_ID, message, reply_markup=keyboard)


async def notify_rider_group(bot: Bot, order: Order) -> int | None:
    """
    Notify rider group when status becomes 'ready'.

    Args:
        bot: Bot instance (unused, kept for interface consistency)
        order: Order object

    Returns:
        message_id of the sent message, or None on failure
    """
    from bot.keyboards.inline import rider_order_keyboard

    total = format_currency(order.total_price)

    message = localize(
        "rider.order_ready",
        order_id=order.id,
        order_code=order.order_code or "N/A",
        total=total,
        address=order.delivery_address or "N/A",
        phone=order.phone_number or "N/A",
    )

    keyboard = rider_order_keyboard(order.id)
    return await _send_to_group(EnvKeys.RIDER_GROUP_ID, message, reply_markup=keyboard)


async def notify_customer_status(bot: Bot, order: Order, new_status: str) -> bool:
    """
    Send status update to customer at each stage.

    Args:
        bot: Bot instance (unused, kept for interface consistency)
        order: Order object
        new_status: The new status string

    Returns:
        True if sent successfully
    """
    status_key_map = {
        "preparing": "order.status.preparing",
        "ready": "order.status.ready",
        "out_for_delivery": "order.status.out_for_delivery",
        "delivered": "order.status.delivered_notify",
    }

    key = status_key_map.get(new_status)
    if not key:
        return False

    message = localize(key, order_code=order.order_code or "N/A")
    return await send_order_notification(order.buyer_id, message)
