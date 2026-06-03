"""Driver job-offer accept/decline callbacks (Card 26, Phase C).

These only *signal* the in-flight dispatch loop (in ``bot.dispatch.dispatcher``);
the actual order assignment is performed single-threaded inside that loop to
avoid two drivers racing onto the same order.
"""

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.dispatch.dispatcher import register_acceptance, register_decline
from bot.i18n import localize

logger = logging.getLogger(__name__)
router = Router()


def _parse(data: str, prefix: str) -> tuple[int, int] | None:
    """Parse ``{prefix}{order_id}_{driver_tg}`` → (order_id, driver_tg)."""
    try:
        order_part, driver_part = data.removeprefix(prefix).split("_", 1)
        return int(order_part), int(driver_part)
    except (ValueError, TypeError):
        return None


@router.callback_query(F.data.startswith("dispatch_accept_"))
async def accept_offer(call: CallbackQuery):
    parsed = _parse(call.data, "dispatch_accept_")
    if not parsed:
        await call.answer()
        return
    order_id, driver_tg = parsed
    if call.from_user.id != driver_tg:
        await call.answer()
        return

    if register_acceptance(order_id, driver_tg):
        try:
            await call.message.edit_text(localize("driver.offer.accept_ack"))
        except Exception:
            pass
        await call.answer(localize("driver.offer.accept_ack"))
    else:
        try:
            await call.message.edit_text(localize("driver.offer.taken"))
        except Exception:
            pass
        await call.answer(localize("driver.offer.taken"), show_alert=True)


@router.callback_query(F.data.startswith("dispatch_decline_"))
async def decline_offer(call: CallbackQuery):
    parsed = _parse(call.data, "dispatch_decline_")
    if not parsed:
        await call.answer()
        return
    order_id, driver_tg = parsed
    if call.from_user.id != driver_tg:
        await call.answer()
        return

    register_decline(order_id, driver_tg)
    try:
        await call.message.edit_text(localize("driver.offer.declined"))
    except Exception:
        pass
    await call.answer()
