"""
Card 21 — Persistent Cart Stub regression tests.

Pins:
- add_to_cart sets expires_at on new rows AND bulk-resets it across the
  whole user cart on every subsequent add.
- get_cart_items performs lazy expiry: if any row is past TTL, the entire
  cart is cleared and an empty list is returned.
- build_cart_stub returns "" when the cart is empty / expired, and returns
  a formatted banner when the cart has items.
- inject_cart_stub is a no-op for an empty stub, and prepends with a
  separator otherwise.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from bot.config import EnvKeys
from bot.database.main import Database
from bot.database.methods.create import add_to_cart
from bot.database.methods.read import get_cart_items
from bot.database.models.main import Brand, Categories, Goods, ShoppingCart, Store
from bot.utils.cart_stub import (
    _as_aware_utc,
    build_cart_stub,
    flash_cart_added,
    format_cart_stub,
    format_flash_stub,
    get_cart_stub_data,
    inject_cart_stub,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def seeded_item(db_session, test_user, test_brand):
    cat = Categories(name="Drinks", brand_id=test_brand.id)
    db_session.add(cat)
    db_session.commit()

    item = Goods(
        name="Iced Tea",
        price=Decimal("45.00"),
        description="Refreshing",
        category_name="Drinks",
        stock_quantity=0,  # prepared → unlimited
        item_type="prepared",
        brand_id=test_brand.id,
        is_active=True,
    )
    db_session.add(item)
    db_session.commit()
    return item


# ---------------------------------------------------------------------------
# Phase 6: add_to_cart sets/resets expires_at
# ---------------------------------------------------------------------------

class TestAddToCartSetsExpiresAt:
    @pytest.mark.asyncio
    async def test_new_cart_row_has_expires_at(self, db_session, test_user, seeded_item):
        before = datetime.now(timezone.utc)
        success, _ = await add_to_cart(test_user.telegram_id, "Iced Tea", quantity=1)
        after = datetime.now(timezone.utc)
        assert success

        db_session.expire_all()
        row = db_session.query(ShoppingCart).filter_by(user_id=test_user.telegram_id).one()
        assert row.expires_at is not None
        ttl = timedelta(minutes=EnvKeys.CART_TTL_MINUTES)
        # SQLite drops tzinfo on round-trip — normalize to UTC for comparison
        row_exp = _as_aware_utc(row.expires_at)
        assert before + ttl - timedelta(seconds=5) <= row_exp <= after + ttl + timedelta(seconds=5)

    @pytest.mark.asyncio
    async def test_second_add_resets_expiry_across_whole_cart(
        self, db_session, test_user, test_brand
    ):
        # Seed two items in the same brand
        db_session.add(Categories(name="C", brand_id=test_brand.id))
        db_session.commit()
        for name in ("A", "B"):
            db_session.add(Goods(
                name=name, price=Decimal("10"), description="d",
                category_name="C", stock_quantity=0,
                item_type="prepared", brand_id=test_brand.id,
            ))
        db_session.commit()

        # First add: A
        await add_to_cart(test_user.telegram_id, "A", quantity=1)

        # Forcibly age A's expires_at into the past to simulate time passing
        stale = datetime.now(timezone.utc) - timedelta(hours=10)
        with Database().session() as s:
            s.query(ShoppingCart).filter_by(user_id=test_user.telegram_id).update(
                {ShoppingCart.expires_at: stale}, synchronize_session=False,
            )
            s.commit()

        # Second add: B. This should reset expiry on BOTH A and B.
        before = datetime.now(timezone.utc)
        await add_to_cart(test_user.telegram_id, "B", quantity=1)

        with Database().session() as s:
            rows = s.query(ShoppingCart).filter_by(user_id=test_user.telegram_id).all()
            assert len(rows) == 2
            for r in rows:
                r_exp = _as_aware_utc(r.expires_at)
                assert r_exp > before, (
                    f"expected expires_at to be reset past {before}, got {r_exp}"
                )

    @pytest.mark.asyncio
    async def test_quantity_update_also_refreshes_expiry(
        self, db_session, test_user, seeded_item
    ):
        await add_to_cart(test_user.telegram_id, "Iced Tea", quantity=1)

        # Age
        stale = datetime.now(timezone.utc) - timedelta(hours=10)
        with Database().session() as s:
            s.query(ShoppingCart).filter_by(user_id=test_user.telegram_id).update(
                {ShoppingCart.expires_at: stale}, synchronize_session=False,
            )
            s.commit()

        before = datetime.now(timezone.utc)
        await add_to_cart(test_user.telegram_id, "Iced Tea", quantity=2)  # qty update path

        with Database().session() as s:
            row = s.query(ShoppingCart).filter_by(user_id=test_user.telegram_id).one()
            assert row.quantity == 3  # 1 + 2
            assert _as_aware_utc(row.expires_at) > before


# ---------------------------------------------------------------------------
# Phase 6: get_cart_items lazy-expires stale carts
# ---------------------------------------------------------------------------

class TestGetCartItemsLazyExpiry:
    @pytest.mark.asyncio
    async def test_returns_items_when_fresh(self, db_session, test_user, seeded_item):
        await add_to_cart(test_user.telegram_id, "Iced Tea", quantity=2)
        items = await get_cart_items(test_user.telegram_id)
        assert len(items) == 1
        assert items[0]["item_name"] == "Iced Tea"
        assert items[0]["quantity"] == 2

    @pytest.mark.asyncio
    async def test_expired_cart_cleared_and_returns_empty(
        self, db_session, test_user, seeded_item
    ):
        await add_to_cart(test_user.telegram_id, "Iced Tea", quantity=1)

        # Age all rows past their TTL
        stale = datetime.now(timezone.utc) - timedelta(hours=10)
        with Database().session() as s:
            s.query(ShoppingCart).filter_by(user_id=test_user.telegram_id).update(
                {ShoppingCart.expires_at: stale}, synchronize_session=False,
            )
            s.commit()

        items = await get_cart_items(test_user.telegram_id)
        assert items == []

        # Side effect: rows should be deleted
        with Database().session() as s:
            remaining = s.query(ShoppingCart).filter_by(user_id=test_user.telegram_id).count()
            assert remaining == 0

    @pytest.mark.asyncio
    async def test_null_expires_at_never_expires(self, db_session, test_user, seeded_item):
        # Pre-card-21 rows may have NULL expires_at; they must never be expired
        row = ShoppingCart(
            user_id=test_user.telegram_id,
            item_name="Iced Tea",
            quantity=1,
        )
        row.expires_at = None  # explicit
        db_session.add(row)
        db_session.commit()

        items = await get_cart_items(test_user.telegram_id)
        assert len(items) == 1


# ---------------------------------------------------------------------------
# Phase 2: build_cart_stub integration
# ---------------------------------------------------------------------------

class TestBuildCartStub:
    def test_empty_cart_returns_empty_string(self, db_with_roles, test_user):
        assert build_cart_stub(test_user.telegram_id) == ""

    def test_empty_cart_get_stub_data_returns_none(self, db_with_roles, test_user):
        assert get_cart_stub_data(test_user.telegram_id) is None

    @pytest.mark.asyncio
    async def test_populated_cart_returns_banner_with_total(
        self, db_session, test_user, seeded_item
    ):
        await add_to_cart(test_user.telegram_id, "Iced Tea", quantity=2)
        stub = build_cart_stub(test_user.telegram_id)
        # Should contain cart emoji + currency + total
        assert "\U0001f6d2" in stub  # 🛒
        assert EnvKeys.PAY_CURRENCY in stub
        assert "90" in stub  # 45 * 2

    @pytest.mark.asyncio
    async def test_get_stub_data_returns_totals_and_counts(
        self, db_session, test_user, seeded_item
    ):
        await add_to_cart(test_user.telegram_id, "Iced Tea", quantity=3)
        data = get_cart_stub_data(test_user.telegram_id)
        assert data is not None
        assert data["item_count"] == 1
        assert data["total"] == Decimal("135.00")  # 45 * 3

    @pytest.mark.asyncio
    async def test_expired_cart_returns_empty_banner(
        self, db_session, test_user, seeded_item
    ):
        await add_to_cart(test_user.telegram_id, "Iced Tea", quantity=1)

        # Force expiry
        stale = datetime.now(timezone.utc) - timedelta(hours=10)
        with Database().session() as s:
            s.query(ShoppingCart).filter_by(user_id=test_user.telegram_id).update(
                {ShoppingCart.expires_at: stale}, synchronize_session=False,
            )
            s.commit()

        assert build_cart_stub(test_user.telegram_id) == ""

        # get_cart_stub_data's own lazy expiry should have cleared the cart
        with Database().session() as s:
            remaining = s.query(ShoppingCart).filter_by(user_id=test_user.telegram_id).count()
            assert remaining == 0

    def test_build_stub_with_brand_and_store(self, db_session, test_user, test_brand):
        # Seed category/item/store then manually add a cart row with brand+store
        db_session.add(Categories(name="C", brand_id=test_brand.id))
        db_session.commit()
        db_session.add(Goods(
            name="X", price=Decimal("50"), description="d",
            category_name="C", stock_quantity=0,
            item_type="prepared", brand_id=test_brand.id,
        ))
        store = Store(
            name="Silom Branch", brand_id=test_brand.id,
            address="1 Silom", latitude=13.7, longitude=100.5,
            phone="+66", is_default=True,
        )
        db_session.add(store)
        db_session.commit()

        cart = ShoppingCart(
            user_id=test_user.telegram_id,
            item_name="X",
            quantity=1,
            brand_id=test_brand.id,
            store_id=store.id,
        )
        cart.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        db_session.add(cart)
        db_session.commit()

        stub = build_cart_stub(test_user.telegram_id)
        assert test_brand.name in stub
        assert "Silom Branch" in stub


# ---------------------------------------------------------------------------
# Phase 2: inject_cart_stub / format helpers (pure functions)
# ---------------------------------------------------------------------------

class TestStubFormatters:
    def test_inject_empty_stub_is_noop(self):
        assert inject_cart_stub("Menu text", "") == "Menu text"

    def test_inject_nonempty_stub_prepends_with_separator(self):
        result = inject_cart_stub("Menu text", "🛒 X · ฿10")
        assert result.startswith("🛒 X · ฿10\n")
        assert "Menu text" in result
        # There's a horizontal separator between stub and body
        assert "\u2500" in result or "─" in result

    def test_format_cart_stub_all_fields(self):
        result = format_cart_stub("SomChai", "Silom", Decimal("450"))
        assert "SomChai" in result
        assert "Silom" in result
        assert "450" in result
        assert result.startswith("\U0001f6d2")  # 🛒

    def test_format_cart_stub_brand_only(self):
        result = format_cart_stub("SomChai", "", Decimal("50"))
        assert "SomChai" in result
        assert "50" in result

    def test_format_cart_stub_total_only(self):
        result = format_cart_stub("", "", Decimal("99"))
        assert "99" in result

    def test_format_flash_stub(self):
        result = format_flash_stub("Pad Thai", 2, Decimal("180"))
        assert "Pad Thai" in result
        assert "x2" in result
        assert "180" in result
        assert "\u2728" in result  # sparkles


# ---------------------------------------------------------------------------
# Phase 3: flash_cart_added two-step animation
# ---------------------------------------------------------------------------

class TestFlashCartAdded:
    @pytest.mark.asyncio
    async def test_two_step_edit_flash_then_settle(self, monkeypatch):
        edits: list[tuple[str, object]] = []

        async def fake_edit(msg, text, reply_markup=None, **kw):
            edits.append((text, reply_markup))

        async def fake_sleep(seconds):
            edits.append(("__sleep__", seconds))

        monkeypatch.setattr("bot.utils.message_utils.safe_edit_text", fake_edit)
        monkeypatch.setattr("bot.utils.cart_stub.asyncio.sleep", fake_sleep)

        settle_markup = object()
        await flash_cart_added(
            message=object(),
            item_name="Pad Thai",
            quantity=1,
            item_total=Decimal("90"),
            settle_text="🛒 Shop · ฿90\n────\nMenu",
            settle_markup=settle_markup,
            user_id=42,
        )

        assert len(edits) == 3
        flash_text, flash_markup = edits[0]
        assert "Pad Thai" in flash_text
        assert "x1" in flash_text
        assert "90" in flash_text
        assert flash_markup is settle_markup
        assert edits[1] == ("__sleep__", EnvKeys.CART_FLASH_SECONDS)
        assert edits[2] == ("🛒 Shop · ฿90\n────\nMenu", settle_markup)

    @pytest.mark.asyncio
    async def test_settle_skipped_when_edit_raises(self, monkeypatch):
        calls = {"n": 0}

        async def fake_edit(msg, text, reply_markup=None, **kw):
            calls["n"] += 1
            if calls["n"] == 2:
                raise RuntimeError("message was changed by concurrent tap")

        async def fake_sleep(seconds):
            pass

        monkeypatch.setattr("bot.utils.message_utils.safe_edit_text", fake_edit)
        monkeypatch.setattr("bot.utils.cart_stub.asyncio.sleep", fake_sleep)

        # Should not raise — helper swallows settle-time exceptions
        await flash_cart_added(
            message=object(),
            item_name="X",
            quantity=1,
            item_total=Decimal("10"),
            settle_text="settled",
            settle_markup=None,
            user_id=1,
        )
        assert calls["n"] == 2  # flash edit succeeded, settle edit raised

    @pytest.mark.asyncio
    async def test_flash_edit_raising_also_swallowed(self, monkeypatch):
        async def fake_edit(msg, text, reply_markup=None, **kw):
            raise RuntimeError("cannot edit")

        async def fake_sleep(seconds):
            pass

        monkeypatch.setattr("bot.utils.message_utils.safe_edit_text", fake_edit)
        monkeypatch.setattr("bot.utils.cart_stub.asyncio.sleep", fake_sleep)

        # First edit already fails — helper must not propagate
        await flash_cart_added(
            message=object(),
            item_name="X",
            quantity=1,
            item_total=Decimal("10"),
            settle_text="settled",
            settle_markup=None,
            user_id=1,
        )
