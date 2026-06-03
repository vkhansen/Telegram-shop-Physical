"""Per-store payment-target resolution + QR routing (Card 28).

The critical money path: an order must pay into — and have its slip verified
against — the right PromptPay account, resolved store → brand → global.
"""

from decimal import Decimal

import pytest

from bot.database.models.main import Brand, Store
from bot.payments.promptpay import generate_promptpay_payload, parse_promptpay_payload
from bot.payments.store_payment import get_store_menu_image, resolve_payment_target

STORE_ID = "0811111111"
BRAND_ID = "0822222222"
GLOBAL_ID = "0833333333"


def _brand(session, **kw):
    b = Brand(name=kw.pop("name", "Brand"), slug=kw.pop("slug", "brand"), **kw)
    session.add(b)
    session.commit()
    return b


def _store(session, brand_id, **kw):
    s = Store(name=kw.pop("name", "Branch"), brand_id=brand_id, **kw)
    session.add(s)
    session.commit()
    return s


@pytest.mark.database
def test_store_dynamic_id_wins(db_session):
    """A store with its own PromptPay id beats the brand and global settings."""
    b = _brand(db_session, promptpay_id=BRAND_ID, promptpay_name="Brand Acct")
    s = _store(db_session, b.id, promptpay_id=STORE_ID, promptpay_name="Branch Acct")

    t = resolve_payment_target(store_id=s.id, brand_id=b.id)
    assert t.source == "store"
    assert t.promptpay_id == STORE_ID
    assert t.promptpay_name == "Branch Acct"
    assert t.static_qr_file_id is None


@pytest.mark.database
def test_store_static_qr_only(db_session):
    """A store with only a static QR (no dynamic id) still resolves to the store."""
    b = _brand(db_session, promptpay_id=BRAND_ID, promptpay_name="Brand Acct")
    s = _store(db_session, b.id, payment_qr_file_id="static_qr_1", promptpay_name="Branch Acct")

    t = resolve_payment_target(store_id=s.id, brand_id=b.id)
    assert t.source == "store"
    assert t.promptpay_id == ""              # no dynamic id
    assert t.static_qr_file_id == "static_qr_1"
    assert t.promptpay_name == "Branch Acct"  # still used for slip verification


@pytest.mark.database
def test_brand_fallback(db_session):
    """A store with no payment config falls back to the brand's PromptPay."""
    b = _brand(db_session, promptpay_id=BRAND_ID, promptpay_name="Brand Acct")
    s = _store(db_session, b.id)  # no promptpay fields

    t = resolve_payment_target(store_id=s.id, brand_id=b.id)
    assert t.source == "brand"
    assert t.promptpay_id == BRAND_ID
    assert t.promptpay_name == "Brand Acct"


@pytest.mark.database
def test_global_fallback(db_session, monkeypatch):
    """No store/brand config → the global bot setting is used."""
    b = _brand(db_session)  # no promptpay
    s = _store(db_session, b.id)

    import bot.handlers.admin.settings_management as sm
    monkeypatch.setattr(sm, "get_promptpay_id", lambda: GLOBAL_ID)
    monkeypatch.setattr(sm, "get_promptpay_name", lambda: "Global Acct")

    t = resolve_payment_target(store_id=s.id, brand_id=b.id)
    assert t.source == "global"
    assert t.promptpay_id == GLOBAL_ID
    assert t.promptpay_name == "Global Acct"


@pytest.mark.database
def test_no_store_id_uses_brand(db_session):
    """An order with no store (menu-only brand) resolves at the brand level."""
    b = _brand(db_session, promptpay_id=BRAND_ID, promptpay_name="Brand Acct")
    t = resolve_payment_target(store_id=None, brand_id=b.id)
    assert t.source == "brand"
    assert t.promptpay_id == BRAND_ID


@pytest.mark.database
def test_get_store_menu_image(db_session):
    b = _brand(db_session)
    with_img = _store(db_session, b.id, name="A", menu_image_file_id="menu_board_1")
    without = _store(db_session, b.id, name="B")
    assert get_store_menu_image(with_img.id) == "menu_board_1"
    assert get_store_menu_image(without.id) is None
    assert get_store_menu_image(None) is None


@pytest.mark.database
def test_qr_encodes_resolved_store_id(db_session):
    """The generated QR payload encodes the *store's* PromptPay id, not the global one."""
    b = _brand(db_session, promptpay_id=BRAND_ID, promptpay_name="Brand Acct")
    s = _store(db_session, b.id, promptpay_id=STORE_ID, promptpay_name="Branch Acct")

    t = resolve_payment_target(store_id=s.id, brand_id=b.id)
    payload = generate_promptpay_payload(t.promptpay_id, Decimal("123.00"))
    parsed = parse_promptpay_payload(payload)
    # The branch's phone number is what the customer would pay into.
    assert parsed.promptpay_id == STORE_ID
