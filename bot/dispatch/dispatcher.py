"""Auto-dispatch orchestration for ready orders (Card 26).

When an order becomes ``ready`` and ``AUTO_DISPATCH_ENABLED`` is on, we offer it
to the nearest available driver(s), wait for an accept, and escalate on
decline/timeout. After ``AUTO_DISPATCH_MAX_ROUNDS`` rounds with no taker we fall
back to the manual rider-group notification — so the feature is always safe to
turn off and the legacy flow keeps working.

Offer state lives in-process (``_SESSIONS``) keyed by order id; the accept/
decline callbacks in ``bot/handlers/driver/job_offer.py`` signal the waiting
dispatch loop through it.
"""

import asyncio
import contextlib
import logging

from bot.config import EnvKeys
from bot.database.main import Database
from bot.database.methods.driver import adjust_active_orders
from bot.database.models.main import Order
from bot.dispatch.matching import get_available_drivers
from bot.i18n import localize
from bot.utils.background import track_task

logger = logging.getLogger(__name__)


class DispatchSession:
    """Tracks one order's in-flight offer round."""

    def __init__(self, order_id: int):
        self.order_id = order_id
        self.offered: set[int] = set()  # every driver ever offered this order
        self.declined: set[int] = set()  # drivers who declined/timed out
        self.current_batch: set[int] = set()  # drivers awaiting a reply this round
        self.event = asyncio.Event()
        self.accepted_by: int | None = None
        self.finished = False


_SESSIONS: dict[int, DispatchSession] = {}


def get_session(order_id: int) -> DispatchSession | None:
    return _SESSIONS.get(order_id)


def register_acceptance(order_id: int, driver_tg: int) -> bool:
    """Record the first driver to accept. Returns False if too late / already taken."""
    session = _SESSIONS.get(order_id)
    if not session or session.finished or session.accepted_by is not None:
        return False
    if driver_tg not in session.offered or driver_tg in session.declined:
        return False
    session.accepted_by = driver_tg
    session.event.set()
    return True


def register_decline(order_id: int, driver_tg: int) -> bool:
    """Record a decline. If the whole current batch has now declined, advance early."""
    session = _SESSIONS.get(order_id)
    if not session or session.finished:
        return False
    session.declined.add(driver_tg)
    if session.current_batch and session.current_batch <= session.declined:
        session.event.set()
    return True


def _order_snapshot(order_id: int) -> dict | None:
    """Read the dispatch-relevant fields of an order into a plain dict."""
    with Database().session() as s:
        o = s.query(Order).filter(Order.id == order_id).one_or_none()
        if not o:
            return None
        return {
            "id": o.id,
            "order_code": o.order_code,
            "order_status": o.order_status,
            "driver_id": o.driver_id,
            "latitude": o.latitude,
            "longitude": o.longitude,
            "delivery_zone": o.delivery_zone,
            "brand_id": o.brand_id,
            "delivery_address": o.delivery_address,
            "google_maps_link": o.google_maps_link,
            "total_price": o.total_price,
            "payment_method": o.payment_method,
            "delivery_type": o.delivery_type,
            "delivery_note": o.delivery_note,
        }


def _offer_text(order: dict) -> str:
    return localize(
        "driver.offer.title",
        order_code=order["order_code"],
        address=order["delivery_address"],
        total=order["total_price"],
        payment=order["payment_method"],
        type=order["delivery_type"],
    )


def _offer_keyboard(order_id: int, driver_tg: int):
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=localize("driver.offer.accept_btn"),
                    callback_data=f"dispatch_accept_{order_id}_{driver_tg}",
                ),
                InlineKeyboardButton(
                    text=localize("driver.offer.decline_btn"),
                    callback_data=f"dispatch_decline_{order_id}_{driver_tg}",
                ),
            ]
        ]
    )


def _driver_action_keyboard(order_id: int):
    """The pickup/delivered buttons the assigned driver uses to drive the order."""
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=localize("rider.btn.picked_up"), callback_data=f"rider_picked_{order_id}")],
            [InlineKeyboardButton(text=localize("rider.btn.delivered"), callback_data=f"rider_delivered_{order_id}")],
        ]
    )


async def _assign(bot, order: dict, driver_tg: int) -> bool:
    """Atomically claim the order for the accepting driver. Returns success."""
    with Database().session() as s:
        o = s.query(Order).filter(Order.id == order["id"]).with_for_update().one_or_none()
        if not o or o.order_status != "ready" or o.driver_id is not None:
            return False
        o.driver_id = driver_tg
    adjust_active_orders(driver_tg, +1)
    logger.info("Order %s auto-assigned to driver %s", order["order_code"], driver_tg)

    # Tell the winning driver they've got it, with the action buttons.
    try:
        await bot.send_message(
            driver_tg,
            localize("driver.offer.accepted", order_code=order["order_code"], address=order["delivery_address"]),
            reply_markup=_driver_action_keyboard(order["id"]),
        )
        if order.get("google_maps_link"):
            await bot.send_message(driver_tg, order["google_maps_link"])
    except Exception:
        logger.warning("Failed to send assignment confirmation to driver %s", driver_tg)

    # Notify the customer that a rider is on the way.
    await _notify_customer_assigned(bot, order)
    return True


async def _notify_customer_assigned(bot, order: dict) -> None:
    try:
        with Database().session() as s:
            o = s.query(Order).filter(Order.id == order["id"]).one_or_none()
            buyer_id = o.buyer_id if o else None
        if buyer_id:
            await bot.send_message(
                buyer_id,
                localize("driver.customer.assigned", order_code=order["order_code"]),
            )
    except Exception:
        logger.warning("Failed to notify customer for order %s", order["order_code"])


async def _expire_offer(bot, driver_tg: int, order: dict) -> None:
    """Tell a driver an offer they didn't take is gone (best-effort)."""
    with contextlib.suppress(Exception):
        await bot.send_message(
            driver_tg,
            localize("driver.offer.expired", order_code=order["order_code"]),
        )


async def _manual_fallback(bot, order_id: int) -> None:
    """No driver took it — hand off to the manual rider-group notification."""
    logger.info("Auto-dispatch exhausted for order %s; falling back to rider group", order_id)
    try:
        from bot.handlers.admin.order_management import _send_rider_notification

        with Database().session() as s:
            o = s.query(Order).filter(Order.id == order_id).one_or_none()
            if o and o.order_status == "ready" and o.driver_id is None:
                await _send_rider_notification(bot, o, s)
    except Exception:
        logger.exception("Manual rider-group fallback failed for order %s", order_id)


async def auto_dispatch(bot, order_id: int) -> None:
    """Offer the order to nearby drivers, escalating until accepted or exhausted."""
    order = _order_snapshot(order_id)
    if not order or order["order_status"] != "ready":
        return
    if order["latitude"] is None or order["longitude"] is None:
        # No customer GPS to match against — manual flow only.
        await _manual_fallback(bot, order_id)
        return

    session = DispatchSession(order_id)
    _SESSIONS[order_id] = session
    timeout = EnvKeys.AUTO_DISPATCH_OFFER_TIMEOUT
    batch_size = max(1, EnvKeys.AUTO_DISPATCH_BATCH_SIZE)

    try:
        for _round in range(EnvKeys.AUTO_DISPATCH_MAX_ROUNDS):
            # Re-query each round so freshly-online drivers can be matched.
            ranked = get_available_drivers(
                order["latitude"],
                order["longitude"],
                zone=order["delivery_zone"],
                brand_id=order["brand_id"],
            )
            candidates = [
                d
                for d in ranked
                if d["telegram_id"] not in session.offered and d["telegram_id"] not in session.declined
            ]
            if not candidates:
                break

            batch = candidates[:batch_size]
            session.current_batch = {d["telegram_id"] for d in batch}
            session.offered |= session.current_batch
            session.event.clear()

            for d in batch:
                try:
                    await bot.send_message(
                        d["telegram_id"],
                        _offer_text(order),
                        reply_markup=_offer_keyboard(order_id, d["telegram_id"]),
                    )
                except Exception:
                    logger.warning("Failed to send offer to driver %s", d["telegram_id"])
                    session.declined.add(d["telegram_id"])

            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(session.event.wait(), timeout=timeout)

            if session.accepted_by is not None:
                if await _assign(bot, order, session.accepted_by):
                    session.finished = True
                    # Let the other (now-stale) offers in this batch know.
                    for tg in session.current_batch - {session.accepted_by}:
                        await _expire_offer(bot, tg, order)
                    return
                # Assignment lost a race (cancelled/taken); reopen for next round.
                session.declined.add(session.accepted_by)
                session.accepted_by = None

        # Rounds exhausted with no successful assignment.
        await _manual_fallback(bot, order_id)
    finally:
        session.finished = True
        _SESSIONS.pop(order_id, None)


def start_auto_dispatch(bot, order_id: int) -> None:
    """Fire-and-forget the dispatch loop so the caller (a button handler) returns fast."""
    track_task(asyncio.create_task(auto_dispatch(bot, order_id)))


async def on_order_ready(bot, order_id: int, session=None) -> None:
    """Entry point when an order reaches ``ready``.

    Routes to auto-dispatch when enabled, otherwise the legacy rider-group
    notification. ``session`` (if provided) is the live ORM session of the
    caller, used for the immediate manual path so per-branch group lookup works.
    """
    if EnvKeys.AUTO_DISPATCH_ENABLED:
        start_auto_dispatch(bot, order_id)
        return
    from bot.handlers.admin.order_management import _send_rider_notification

    if session is not None:
        o = session.query(Order).filter(Order.id == order_id).one_or_none()
        if o:
            await _send_rider_notification(bot, o, session)
    else:
        with Database().session() as s:
            o = s.query(Order).filter(Order.id == order_id).one_or_none()
            if o:
                await _send_rider_notification(bot, o, s)
