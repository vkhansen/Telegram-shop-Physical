"""End-to-end auto-dispatch flow (Card 26): ready → offer → accept → en route → delivered."""

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest

from bot.config import EnvKeys
from bot.database.main import Database
from bot.database.methods.driver import (
    adjust_active_orders,
    approve_driver,
    create_driver,
    get_driver,
    record_driver_location,
    set_driver_online,
)
from bot.database.models.main import Order, User
from bot.dispatch import dispatcher as disp
from bot.handlers.driver.availability import _maybe_push_eta, clear_eta_cache

ORIGIN = (13.7563, 100.5018)


class FakeBot:
    def __init__(self):
        self.sent = []

    async def send_message(self, chat_id, text, reply_markup=None, **kw):
        self.sent.append({"chat_id": chat_id, "text": text, "markup": reply_markup})
        return SimpleNamespace(message_id=len(self.sent))

    def offered_drivers(self):
        out = []
        for m in self.sent:
            rows = getattr(m["markup"], "inline_keyboard", None)
            if rows and (rows[0][0].callback_data or "").startswith("dispatch_accept_"):
                out.append(m["chat_id"])
        return out

    def texts_to(self, chat_id):
        return [m["text"] for m in self.sent if m["chat_id"] == chat_id]


async def _wait_offers(bot, n, timeout=3.0):
    elapsed = 0.0
    while elapsed < timeout:
        if len(bot.offered_drivers()) >= n:
            return
        await asyncio.sleep(0.01)
        elapsed += 0.01
    raise AssertionError(f"expected {n} offers, saw {bot.offered_drivers()}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ready_to_delivered_auto(db_with_roles, monkeypatch):
    s = db_with_roles
    driver_tg, buyer_tg = 401, 9101

    for tg in (driver_tg, buyer_tg):
        s.add(User(telegram_id=tg, role_id=1, registration_date=datetime.now(UTC), referral_id=None))
    s.commit()

    create_driver(driver_tg, "Speedy")
    approve_driver(driver_tg)
    set_driver_online(driver_tg, True)
    record_driver_location(driver_tg, 13.757, 100.502)

    order = Order(
        buyer_id=buyer_tg, total_price=Decimal("250.00"), payment_method="cash",
        delivery_address="55 Customer Lane", phone_number="+66999999999",
        order_status="ready", order_code="FLOW01",
        latitude=ORIGIN[0], longitude=ORIGIN[1],
    )
    s.add(order)
    s.commit()
    order_id = order.id
    clear_eta_cache(order_id)

    monkeypatch.setattr(EnvKeys, "AUTO_DISPATCH_OFFER_TIMEOUT", 30)
    monkeypatch.setattr(EnvKeys, "AUTO_DISPATCH_MAX_ROUNDS", 3)

    bot = FakeBot()

    # 1) ready → offer → accept
    task = asyncio.create_task(disp.auto_dispatch(bot, order_id))
    try:
        await _wait_offers(bot, 1)
        assert bot.offered_drivers() == [driver_tg]
        assert disp.register_acceptance(order_id, driver_tg) is True
        await asyncio.wait_for(task, timeout=3)
    finally:
        if not task.done():
            task.cancel()

    with Database().session() as sess:
        o = sess.query(Order).filter(Order.id == order_id).one()
        assert o.driver_id == driver_tg
        assert o.order_status == "ready"  # assigned but not yet picked up
    assert get_driver(driver_tg)["active_order_count"] == 1
    # Customer was told a driver is on the way.
    assert any("FLOW01" in t for t in bot.texts_to(buyer_tg))

    # 2) en route: driver picks up → out_for_delivery, then live location → ETA push
    with Database().session() as sess:
        sess.query(Order).filter(Order.id == order_id).update({Order.order_status: "out_for_delivery"})

    before = len(bot.texts_to(buyer_tg))
    await _maybe_push_eta(bot, driver_tg, 13.758, 100.503)
    after = bot.texts_to(buyer_tg)
    assert len(after) == before + 1
    assert "min" in after[-1].lower() or "นาที" in after[-1]

    # 3) delivered: capacity freed
    with Database().session() as sess:
        sess.query(Order).filter(Order.id == order_id).update(
            {Order.order_status: "delivered", Order.completed_at: datetime.now(UTC)}
        )
    adjust_active_orders(driver_tg, -1)
    clear_eta_cache(order_id)

    assert get_driver(driver_tg)["active_order_count"] == 0
