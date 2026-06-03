"""Driver availability + live-location intake & live ETA (Card 26, Phases B & D).

A driver toggles online/offline and shares a Telegram live location while
online. Each pin move (an ``edited_message``) is appended to the location trail
and, if the driver has an order out for delivery, drives a live ETA push to that
customer.

The location handlers are gated by an approved-driver DB filter so that a
non-driver's private live-location edits fall through to the customer delivery
chat handlers in the user router.
"""

import logging

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.database.main import Database
from bot.database.methods import get_driver, record_driver_location, set_driver_online
from bot.database.models.main import Order
from bot.dispatch.eta import estimate_eta_minutes
from bot.dispatch.matching import haversine_km
from bot.i18n import localize

logger = logging.getLogger(__name__)
router = Router()

# order_id → last ETA (minutes) pushed, so we only message the customer on change.
_LAST_ETA: dict[int, int] = {}


def driver_status_text(driver: dict) -> str:
    if driver["status"] != "approved":
        return localize(f"driver.status.{driver['status']}")
    state_key = "driver.status.online" if driver["is_online"] else "driver.status.offline"
    return localize(state_key, active=driver["active_order_count"])


def driver_menu_keyboard(driver: dict) -> InlineKeyboardMarkup | None:
    if driver["status"] != "approved":
        return None
    if driver["is_online"]:
        btn = InlineKeyboardButton(text=localize("driver.menu.go_offline"),
                                   callback_data="driver_go_offline")
    else:
        btn = InlineKeyboardButton(text=localize("driver.menu.go_online"),
                                   callback_data="driver_go_online")
    return InlineKeyboardMarkup(inline_keyboard=[[btn]])


@router.callback_query(F.data == "driver_go_online")
async def go_online(call: CallbackQuery):
    if not set_driver_online(call.from_user.id, True):
        await call.answer(localize("driver.not_approved"), show_alert=True)
        return
    await call.message.edit_text(localize("driver.online.prompt_location"))
    await call.answer()


@router.callback_query(F.data == "driver_go_offline")
async def go_offline(call: CallbackQuery):
    if not set_driver_online(call.from_user.id, False):
        await call.answer(localize("driver.not_approved"), show_alert=True)
        return
    driver = get_driver(call.from_user.id)
    await call.message.edit_text(driver_status_text(driver), reply_markup=driver_menu_keyboard(driver))
    await call.answer(localize("driver.offline.done"))


async def _is_approved_driver(message: Message) -> bool:
    """Filter: True only for an approved driver, so non-drivers fall through."""
    if not message.from_user or message.from_user.is_bot:
        return False
    driver = get_driver(message.from_user.id)
    return bool(driver and driver["status"] == "approved")


@router.message(F.location, F.chat.type == ChatType.PRIVATE, _is_approved_driver)
async def driver_shares_location(message: Message):
    """Initial live/static location share from an approved driver."""
    record_driver_location(message.from_user.id,
                           message.location.latitude, message.location.longitude)
    await _maybe_push_eta(message.bot, message.from_user.id,
                          message.location.latitude, message.location.longitude)
    await message.answer(localize("driver.location.received"))


@router.edited_message(F.location, F.chat.type == ChatType.PRIVATE, _is_approved_driver)
async def driver_location_update(message: Message):
    """Live-location pin move from an approved driver (Telegram edited_message)."""
    record_driver_location(message.from_user.id,
                           message.location.latitude, message.location.longitude)
    await _maybe_push_eta(message.bot, message.from_user.id,
                          message.location.latitude, message.location.longitude)


async def _maybe_push_eta(bot, driver_tg: int, lat: float, lng: float) -> None:
    """If the driver has an order out for delivery, push a live ETA to the customer."""
    try:
        with Database().session() as s:
            order = (
                s.query(Order)
                .filter(Order.driver_id == driver_tg, Order.order_status == "out_for_delivery")
                .order_by(Order.created_at.desc())
                .first()
            )
            if not order or order.latitude is None or order.longitude is None:
                return
            order_id = order.id
            order_code = order.order_code
            buyer_id = order.buyer_id
            dest_lat, dest_lng = order.latitude, order.longitude

        eta = estimate_eta_minutes(haversine_km(lat, lng, dest_lat, dest_lng))
        if _LAST_ETA.get(order_id) == eta:
            return  # No change since last push — don't spam the customer.
        _LAST_ETA[order_id] = eta
        if buyer_id:
            await bot.send_message(
                buyer_id,
                localize("driver.customer.eta", order_code=order_code, minutes=eta),
            )
    except Exception:
        logger.warning("Failed to push ETA for driver %s", driver_tg)


def clear_eta_cache(order_id: int) -> None:
    """Drop the cached ETA once an order is delivered/cancelled."""
    _LAST_ETA.pop(order_id, None)
