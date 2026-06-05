"""Unit tests for bot.database.integrity — valid graphs pass, broken configs are caught."""

import datetime as dt

import pytest

from bot.database.integrity import Severity, check_integrity, summarize
from bot.database.models.main import (
    BotConfig,
    BranchInventory,
    Brand,
    Categories,
    Goods,
    Store,
)

pytestmark = pytest.mark.database


def _now():
    return dt.datetime.now(dt.UTC)


def build_valid_brand(session, slug="acme", with_item=True):
    """A minimal fully-valid brand: active brand + default store + bot config +
    category + one priced item in it."""
    brand = Brand(name=f"Brand {slug}", slug=slug)
    session.add(brand)
    session.flush()
    session.add(Store(name="Main", brand_id=brand.id, is_default=True))
    session.add(BotConfig(brand_id=brand.id, bot_token=f"TOKEN:{slug}"))
    cat = Categories(name=f"{slug}:Mains", brand_id=brand.id)
    session.add(cat)
    session.flush()
    if with_item:
        session.add(
            Goods(
                name=f"{slug}:Pad Thai",
                brand_id=brand.id,
                category_name=cat.name,
                price=120,
                description="Tasty",
                item_type="prepared",
            )
        )
    session.flush()
    return brand, cat


def errors(session):
    return [v for v in check_integrity(session) if v.severity is Severity.ERROR]


def checks_fired(session):
    return {v.check for v in check_integrity(session)}


def test_valid_brand_has_no_violations(db_session):
    build_valid_brand(db_session)
    assert check_integrity(db_session) == []


def test_item_referencing_missing_category_is_caught(db_session):
    brand, _ = build_valid_brand(db_session)
    # Bypass the FK at the ORM layer to simulate a dangling reference in data.
    db_session.add(
        Goods(name=f"{brand.slug}:Ghost", brand_id=brand.id, category_name="does-not-exist", price=50, description="x")
    )
    # FK may block flush on SQLite; if it does, that's fine — but if data lands, we catch it.
    try:
        db_session.flush()
    except Exception:
        db_session.rollback()
        pytest.skip("DB enforced the FK at write time (also acceptable)")
    assert "item_category_missing" in checks_fired(db_session)


def test_cross_brand_item_is_caught(db_session):
    _brand_a, _cat_a = build_valid_brand(db_session, slug="aaa")
    brand_b, _ = build_valid_brand(db_session, slug="bbb")
    # Item lives in brand_a's category but claims brand_b — no FK catches this.
    item = db_session.query(Goods).filter_by(name="aaa:Pad Thai").first()
    item.brand_id = brand_b.id
    db_session.flush()
    assert "item_category_cross_brand" in checks_fired(db_session)


def test_unbranded_category_is_warned(db_session):
    _, cat = build_valid_brand(db_session)
    cat.brand_id = None
    db_session.flush()
    assert "unbranded" in checks_fired(db_session)


def test_zero_price_item_is_error(db_session):
    build_valid_brand(db_session)
    item = db_session.query(Goods).first()
    item.price = 0
    db_session.flush()
    assert "item_bad_price" in {v.check for v in errors(db_session)}


def test_empty_description_is_error(db_session):
    build_valid_brand(db_session)
    item = db_session.query(Goods).first()
    item.description = "   "
    db_session.flush()
    assert "item_missing_description" in checks_fired(db_session)


def test_bad_item_type_is_error(db_session):
    build_valid_brand(db_session)
    item = db_session.query(Goods).first()
    item.item_type = "widget"
    db_session.flush()
    assert "item_bad_type" in checks_fired(db_session)


def test_multiple_default_stores_is_error(db_session):
    brand, _ = build_valid_brand(db_session)
    db_session.add(Store(name="Second", brand_id=brand.id, is_default=True))
    db_session.flush()
    assert "brand_multiple_default_stores" in {v.check for v in errors(db_session)}


def test_invalid_modifier_schema_is_caught(db_session):
    build_valid_brand(db_session)
    item = db_session.query(Goods).first()
    item.modifiers = {"spice": {"label": "Spice", "type": "triple", "options": []}}
    db_session.flush()
    fired = checks_fired(db_session)
    assert "modifier_bad_type" in fired
    assert "modifier_no_options" in fired


def test_oversold_branch_inventory_is_warning(db_session):
    brand, cat = build_valid_brand(db_session)
    item = Goods(
        name=f"{brand.slug}:Water",
        brand_id=brand.id,
        category_name=cat.name,
        price=15,
        description="Bottled",
        item_type="product",
        stock_quantity=10,
    )
    db_session.add(item)
    store = db_session.query(Store).filter_by(brand_id=brand.id).first()
    db_session.add(BranchInventory(store_id=store.id, item_name=item.name, stock_quantity=2, reserved_quantity=9))
    db_session.flush()
    fired = checks_fired(db_session)
    assert "branch_inv_oversold" in fired


def test_summarize_counts(db_session):
    build_valid_brand(db_session)
    item = db_session.query(Goods).first()
    item.price = 0  # 1 error
    item.brand_id = None  # triggers unbranded warning + cross-brand error
    db_session.flush()
    s = summarize(check_integrity(db_session))
    assert s["errors"] >= 1
    assert s["total"] == s["errors"] + s["warnings"]
