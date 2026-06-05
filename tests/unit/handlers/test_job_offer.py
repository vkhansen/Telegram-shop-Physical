"""Dispatch offer/escalation tests (Card 26).

Drives the in-process dispatch loop (``bot.dispatch.dispatcher.auto_dispatch``)
with a fake bot, exercising decline-escalation and timeout→manual-fallback.
"""

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest

from bot.config import EnvKeys
from bot.database.main import Database
from bot.database.methods.driver import approve_driver, create_driver, record_driver_location, set_driver_online
from bot.database.models.main import Order, User
from bot.dispatch import dispatcher as disp

ORIGIN = (13.7563, 100.5018)


class FakeBot:
    """Records sent messages; flags offers so tests can await them."""

    def __init__(self):
        self.sent = []

    async def send_message(self, chat_id, text, reply_markup=None, **kw):
        self.sent.append({"chat_id": chat_id, "text": text, "markup": reply_markup})
        return SimpleNamespace(message_id=len(self.sent))

    def offered_drivers(self):
        out = []
        for m in self.sent:
            mk = m["markup"]
            rows = getattr(mk, "inline_keyboard", None)
            if rows and (rows[0][0].callback_data or "").startswith("dispatch_accept_"):
                out.append(m["chat_id"])
        return out


async def _wait_offers(bot, n, timeout=3.0):
    elapsed = 0.0
    while elapsed < timeout:
        if len(bot.offered_drivers()) >= n:
            return
        await asyncio.sleep(0.01)
        elapsed += 0.01
    raise AssertionError(f"expected {n} offers, saw {bot.offered_drivers()}")


def _seed_user(session, tg):
    session.add(User(telegram_id=tg, role_id=1, registration_date=datetime.now(UTC), referral_id=None))


def _seed_online_driver(session, tg, lat, lng):
    _seed_user(session, tg)
    session.commit()
    create_driver(tg, f"Driver {tg}")
    approve_driver(tg)
    set_driver_online(tg, True)
    record_driver_location(tg, lat, lng)


def _seed_ready_order(session, buyer_tg):
    _seed_user(session, buyer_tg)
    session.commit()
    order = Order(
        buyer_id=buyer_tg,
        total_price=Decimal("100.00"),
        payment_method="cash",
        delivery_address="123 Test Rd",
        phone_number="+66000000000",
        order_status="ready",
        order_code="DSP001",
        latitude=ORIGIN[0],
        longitude=ORIGIN[1],
    )
    session.add(order)
    session.commit()
    return order.id


def _order_driver_id(order_id):
    with Database().session() as s:
        return s.query(Order).filter(Order.id == order_id).one().driver_id


@pytest.mark.database
@pytest.mark.asyncio
async def test_decline_escalates(db_with_roles, monkeypatch):
    """Declining the first offer escalates to the next-nearest driver."""
    s = db_with_roles
    # d1 is nearer than d2 so it's offered first.
    _seed_online_driver(s, 201, 13.757, 100.502)
    _seed_online_driver(s, 202, 13.770, 100.515)
    order_id = _seed_ready_order(s, 9001)

    monkeypatch.setattr(EnvKeys, "AUTO_DISPATCH_OFFER_TIMEOUT", 30)
    monkeypatch.setattr(EnvKeys, "AUTO_DISPATCH_BATCH_SIZE", 1)
    monkeypatch.setattr(EnvKeys, "AUTO_DISPATCH_MAX_ROUNDS", 3)

    bot = FakeBot()
    task = asyncio.create_task(disp.auto_dispatch(bot, order_id))
    try:
        await _wait_offers(bot, 1)
        assert bot.offered_drivers() == [201]

        assert disp.register_decline(order_id, 201) is True
        await _wait_offers(bot, 2)
        assert bot.offered_drivers() == [201, 202]

        assert disp.register_acceptance(order_id, 202) is True
        await asyncio.wait_for(task, timeout=3)
    finally:
        if not task.done():
            task.cancel()

    assert _order_driver_id(order_id) == 202


@pytest.mark.database
@pytest.mark.asyncio
async def test_timeout_falls_back_to_manual(db_with_roles, monkeypatch):
    """When no driver responds, dispatch falls back to the rider-group notification."""
    s = db_with_roles
    _seed_online_driver(s, 301, 13.757, 100.502)
    order_id = _seed_ready_order(s, 9002)

    monkeypatch.setattr(EnvKeys, "AUTO_DISPATCH_OFFER_TIMEOUT", 0.05)
    monkeypatch.setattr(EnvKeys, "AUTO_DISPATCH_BATCH_SIZE", 1)
    monkeypatch.setattr(EnvKeys, "AUTO_DISPATCH_MAX_ROUNDS", 2)

    called = {}

    async def fake_rider_notification(bot, order, session):
        called["order_id"] = order.id

    import bot.handlers.admin.order_management as om

    monkeypatch.setattr(om, "_send_rider_notification", fake_rider_notification)

    bot = FakeBot()
    await asyncio.wait_for(disp.auto_dispatch(bot, order_id), timeout=3)

    assert called.get("order_id") == order_id
    assert _order_driver_id(order_id) is None


@pytest.mark.database
@pytest.mark.asyncio
async def test_no_gps_falls_back_immediately(db_with_roles, monkeypatch):
    """An order without customer GPS skips matching and goes straight to manual."""
    s = db_with_roles
    _seed_user(s, 9003)
    s.commit()
    order = Order(
        buyer_id=9003,
        total_price=Decimal("50.00"),
        payment_method="cash",
        delivery_address="No GPS",
        phone_number="+66000000001",
        order_status="ready",
        order_code="DSP003",
    )
    s.add(order)
    s.commit()
    order_id = order.id

    called = {}

    async def fake_rider_notification(bot, o, session):
        called["hit"] = True

    import bot.handlers.admin.order_management as om

    monkeypatch.setattr(om, "_send_rider_notification", fake_rider_notification)

    bot = FakeBot()
    await asyncio.wait_for(disp.auto_dispatch(bot, order_id), timeout=3)

    assert called.get("hit") is True
    assert bot.offered_drivers() == []
