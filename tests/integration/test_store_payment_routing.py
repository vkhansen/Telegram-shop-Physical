"""End-to-end per-store payment routing (Card 28).

The critical path: a customer pays the QR for an order placed in a specific
store, uploads the slip, and the slip is auto-verified **against that store's
PromptPay account** (store → brand → global). Drives the real
``process_receipt_photo`` handler with fakes, capturing the receiver name the
slip verifier is asked to match.
"""

import io
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest

from bot.database.main import Database
from bot.database.models.main import Brand, Order, Store, User
from bot.handlers.user.order_handler import process_receipt_photo
from bot.payments.slip_verify import SlipProvider, SlipVerifyResult, VerifyStatus


# ── Fakes ────────────────────────────────────────────────────────────────────
class FakeState:
    def __init__(self, data):
        self._d = dict(data)

    async def get_data(self):
        return dict(self._d)

    async def update_data(self, **kw):
        self._d.update(kw)

    async def set_state(self, *a, **k):
        pass

    async def clear(self):
        self._d.clear()


class FakeBot:
    def __init__(self):
        self.sent = []

    async def get_file(self, file_id):
        return SimpleNamespace(file_path="path/to/file")

    async def download_file(self, path):
        return io.BytesIO(b"fake-slip-bytes")

    async def send_photo(self, *a, **k):
        self.sent.append(("photo", a, k))

    async def send_message(self, *a, **k):
        self.sent.append(("message", a, k))


class FakeMessage:
    def __init__(self, bot, file_id, user_id=555):
        self.bot = bot
        self.photo = [SimpleNamespace(file_id=file_id)]
        self.from_user = SimpleNamespace(id=user_id)
        self.answers = []

    async def answer(self, *a, **k):
        self.answers.append((a, k))

    async def answer_photo(self, *a, **k):
        self.answers.append(("photo", a, k))


def _seed_order(session, *, store_promptpay=None, store_name_acct=None,
                brand_promptpay=None, brand_name_acct=None):
    """Create user + brand + store + a pending PromptPay order; return order id."""
    session.add(User(telegram_id=555, role_id=1, registration_date=datetime.now(UTC), referral_id=None))
    brand = Brand(name="Acme", slug="acme", promptpay_id=brand_promptpay, promptpay_name=brand_name_acct)
    session.add(brand)
    session.commit()
    store = Store(name="Downtown", brand_id=brand.id,
                  promptpay_id=store_promptpay, promptpay_name=store_name_acct)
    session.add(store)
    session.commit()
    order = Order(
        buyer_id=555, total_price=Decimal("250.00"), payment_method="promptpay",
        delivery_address="1 Test Rd", phone_number="+66000000000",
        order_status="pending", order_code="PAY028",
        brand_id=brand.id, store_id=store.id,
    )
    session.add(order)
    session.commit()
    return order.id


def _verified_result(receiver_name):
    return SlipVerifyResult(
        status=VerifyStatus.VERIFIED,
        provider=SlipProvider.SLIPOK,
        transaction_id="TXN-028",
        amount=Decimal("250.00"),
        sender_name="Customer Payer",
        receiver_name=receiver_name,
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_slip_verified_against_store_account(db_with_roles, monkeypatch):
    """A store with its own PromptPay → the slip is verified against the store name."""
    order_id = _seed_order(
        db_with_roles,
        store_promptpay="0811111111", store_name_acct="Downtown Branch Co",
        brand_promptpay="0822222222", brand_name_acct="Acme HQ",
    )

    captured = {}

    async def fake_verify_slip(*, slip_image, expected_amount, expected_receiver):
        captured["receiver"] = expected_receiver
        captured["amount"] = expected_amount
        return _verified_result("Downtown Branch Co")

    import bot.payments.slip_verify as sv
    monkeypatch.setattr(sv, "verify_slip", fake_verify_slip)
    monkeypatch.setattr("bot.config.EnvKeys.SLIP_AUTO_VERIFY", "1")

    bot = FakeBot()
    msg = FakeMessage(bot, "slip_photo_1")
    state = FakeState({"promptpay_order_id": order_id})

    await process_receipt_photo(msg, state)

    # Verified against the STORE's account, not the brand/global one.
    assert captured["receiver"] == "Downtown Branch Co"
    assert captured["amount"] == Decimal("250.00")

    with Database().session() as s:
        o = s.query(Order).filter(Order.id == order_id).one()
        assert o.order_status == "confirmed"
        assert o.slip_receiver_name == "Downtown Branch Co"
        assert o.slip_transaction_id == "TXN-028"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_slip_verified_against_brand_when_store_unset(db_with_roles, monkeypatch):
    """A store with no PromptPay → slip verified against the brand account."""
    order_id = _seed_order(
        db_with_roles,
        store_promptpay=None, store_name_acct=None,
        brand_promptpay="0822222222", brand_name_acct="Acme HQ",
    )

    captured = {}

    async def fake_verify_slip(*, slip_image, expected_amount, expected_receiver):
        captured["receiver"] = expected_receiver
        return _verified_result("Acme HQ")

    import bot.payments.slip_verify as sv
    monkeypatch.setattr(sv, "verify_slip", fake_verify_slip)
    monkeypatch.setattr("bot.config.EnvKeys.SLIP_AUTO_VERIFY", "1")

    bot = FakeBot()
    msg = FakeMessage(bot, "slip_photo_2")
    state = FakeState({"promptpay_order_id": order_id})

    await process_receipt_photo(msg, state)

    assert captured["receiver"] == "Acme HQ"
    with Database().session() as s:
        assert s.query(Order).filter(Order.id == order_id).one().order_status == "confirmed"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_slip_verified_against_global_when_no_store_or_brand(db_with_roles, monkeypatch):
    """No store/brand account → slip verified against the global setting."""
    order_id = _seed_order(db_with_roles)  # neither store nor brand promptpay

    import bot.handlers.admin.settings_management as sm
    monkeypatch.setattr(sm, "get_promptpay_id", lambda: "0833333333")
    monkeypatch.setattr(sm, "get_promptpay_name", lambda: "Global Account")

    captured = {}

    async def fake_verify_slip(*, slip_image, expected_amount, expected_receiver):
        captured["receiver"] = expected_receiver
        return _verified_result("Global Account")

    import bot.payments.slip_verify as sv
    monkeypatch.setattr(sv, "verify_slip", fake_verify_slip)
    monkeypatch.setattr("bot.config.EnvKeys.SLIP_AUTO_VERIFY", "1")

    bot = FakeBot()
    msg = FakeMessage(bot, "slip_photo_3")
    state = FakeState({"promptpay_order_id": order_id})

    await process_receipt_photo(msg, state)

    assert captured["receiver"] == "Global Account"
