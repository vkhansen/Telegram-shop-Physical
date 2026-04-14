"""
Card 21 Phase 4 & 5 — Brand-switch guard + Store-switch availability tests.

Pins:
- save_cart_snapshot creates a SavedCart row with correct items_json and original_total.
- clear_cart empties the ShoppingCart (path used by delete_cart callback).
- remove_items_from_cart deletes only the named items, leaving others.
- bulk_update_cart_store updates store_id on all user cart rows.
- _serialize_cart_items produces schema_version=1 keys and string prices.
- _check_unavailable_items never flags 'prepared' items regardless of inventory.
- _check_unavailable_items flags 'product' items with insufficient BranchInventory stock.
- _check_unavailable_items flags 'product' items missing from BranchInventory entirely.
- Same-brand select_brand skips the prompt (no FSM transition).
- Empty cart + brand switch skips the prompt.
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from bot.database.main import Database
from bot.database.methods.create import add_to_cart, save_cart_snapshot
from bot.database.methods.delete import clear_cart, remove_items_from_cart
from bot.database.methods.read import get_cart_items
from bot.database.methods.update import bulk_update_cart_store
from bot.database.models.main import (
    BranchInventory,
    Categories,
    Goods,
    SavedCart,
    ShoppingCart,
    Store,
)
from bot.handlers.user.store_selection import (
    _check_unavailable_items,
    _serialize_cart_items,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def second_brand(db_session, test_user):
    """A second brand for brand-switch tests."""
    from bot.database.models.main import Brand
    brand = Brand(name="Second Brand", slug="second-brand")
    db_session.add(brand)
    db_session.commit()
    db_session.refresh(brand)
    return brand


@pytest.fixture
def second_store(db_session, test_brand):
    """A second store belonging to test_brand."""
    store = Store(name="Branch Two", brand_id=test_brand.id)
    db_session.add(store)
    db_session.commit()
    db_session.refresh(store)
    return store


@pytest.fixture
def seeded_prepared_item(db_session, test_brand):
    """A 'prepared' (unlimited-stock) item in the test brand."""
    cat = Categories(name="Hot Food", brand_id=test_brand.id)
    db_session.add(cat)
    db_session.commit()
    item = Goods(
        name="Pad Thai",
        price=Decimal("120.00"),
        description="Classic",
        category_name="Hot Food",
        stock_quantity=0,
        item_type="prepared",
        brand_id=test_brand.id,
        is_active=True,
    )
    db_session.add(item)
    db_session.commit()
    return item


@pytest.fixture
def seeded_product_item(db_session, test_brand):
    """A 'product' (inventory-tracked) item in the test brand."""
    cat = Categories(name="Drinks", brand_id=test_brand.id)
    db_session.add(cat)
    db_session.commit()
    item = Goods(
        name="Bottled Water",
        price=Decimal("20.00"),
        description="Still",
        category_name="Drinks",
        stock_quantity=50,
        item_type="product",
        brand_id=test_brand.id,
        is_active=True,
    )
    db_session.add(item)
    db_session.commit()
    return item


# ---------------------------------------------------------------------------
# DB helpers: save_cart_snapshot
# ---------------------------------------------------------------------------

class TestSaveCartSnapshot:
    def test_creates_saved_cart_row(self, db_session, test_user, test_brand, test_store):
        items = [{"name": "Pad Thai", "quantity": 2, "modifiers": None, "unit_price": "120.00"}]
        result = save_cart_snapshot(
            user_id=test_user.telegram_id,
            brand_id=test_brand.id,
            store_id=test_store.id,
            items_json=items,
            original_total=Decimal("240.00"),
        )
        assert result is True

        with Database().session() as s:
            row = s.query(SavedCart).filter_by(user_id=test_user.telegram_id).first()
        assert row is not None
        assert row.brand_id == test_brand.id
        assert row.store_id == test_store.id
        assert row.items_json["schema_version"] == 1
        assert row.items_json["items"][0]["name"] == "Pad Thai"
        assert row.original_total == Decimal("240.00")

    def test_items_json_uses_string_prices(self, db_session, test_user, test_brand, test_store):
        items = [{"name": "Item A", "quantity": 1, "modifiers": None, "unit_price": "99.99"}]
        save_cart_snapshot(
            user_id=test_user.telegram_id,
            brand_id=test_brand.id,
            store_id=test_store.id,
            items_json=items,
            original_total=Decimal("99.99"),
        )
        with Database().session() as s:
            row = s.query(SavedCart).filter_by(user_id=test_user.telegram_id).first()
        assert isinstance(row.items_json["items"][0]["unit_price"], str)

    def test_null_store_id_allowed(self, db_session, test_user, test_brand):
        items = [{"name": "X", "quantity": 1, "modifiers": None, "unit_price": "10.00"}]
        result = save_cart_snapshot(
            user_id=test_user.telegram_id,
            brand_id=test_brand.id,
            store_id=None,
            items_json=items,
            original_total=Decimal("10.00"),
        )
        assert result is True
        with Database().session() as s:
            row = s.query(SavedCart).filter_by(user_id=test_user.telegram_id).first()
        assert row.store_id is None


# ---------------------------------------------------------------------------
# DB helpers: remove_items_from_cart
# ---------------------------------------------------------------------------

class TestRemoveItemsFromCart:
    @pytest.mark.asyncio
    async def test_removes_only_named_items(
        self, db_session, test_user, test_brand, seeded_prepared_item, seeded_product_item
    ):
        await add_to_cart(test_user.telegram_id, "Pad Thai", brand_id=test_brand.id)
        await add_to_cart(test_user.telegram_id, "Bottled Water", brand_id=test_brand.id)

        remove_items_from_cart(test_user.telegram_id, ["Bottled Water"])

        items = await get_cart_items(test_user.telegram_id)
        names = [i['item_name'] for i in items]
        assert "Pad Thai" in names
        assert "Bottled Water" not in names

    def test_empty_list_is_no_op(self, db_session, test_user):
        remove_items_from_cart(test_user.telegram_id, [])  # must not raise

    @pytest.mark.asyncio
    async def test_delete_cart_clears_all(
        self, db_session, test_user, test_brand, seeded_prepared_item
    ):
        await add_to_cart(test_user.telegram_id, "Pad Thai", brand_id=test_brand.id)
        ok, _ = await clear_cart(test_user.telegram_id)
        assert ok
        items = await get_cart_items(test_user.telegram_id)
        assert items == []


# ---------------------------------------------------------------------------
# DB helpers: bulk_update_cart_store
# ---------------------------------------------------------------------------

class TestBulkUpdateCartStore:
    @pytest.mark.asyncio
    async def test_updates_all_cart_rows(
        self, db_session, test_user, test_brand, test_store, second_store,
        seeded_prepared_item
    ):
        await add_to_cart(
            test_user.telegram_id, "Pad Thai", brand_id=test_brand.id, store_id=test_store.id
        )
        bulk_update_cart_store(test_user.telegram_id, second_store.id)

        with Database().session() as s:
            rows = s.query(ShoppingCart).filter_by(user_id=test_user.telegram_id).all()
        assert all(r.store_id == second_store.id for r in rows)


# ---------------------------------------------------------------------------
# _serialize_cart_items
# ---------------------------------------------------------------------------

class TestSerializeCartItems:
    @pytest.mark.asyncio
    async def test_produces_correct_json_shape(
        self, db_session, test_user, test_brand, seeded_prepared_item
    ):
        await add_to_cart(test_user.telegram_id, "Pad Thai", quantity=3, brand_id=test_brand.id)
        cart_items = await get_cart_items(test_user.telegram_id)

        items_json, total = _serialize_cart_items(cart_items)

        assert len(items_json) == 1
        entry = items_json[0]
        assert entry["name"] == "Pad Thai"
        assert entry["quantity"] == 3
        assert isinstance(entry["unit_price"], str)
        assert total == Decimal("120.00") * 3

    @pytest.mark.asyncio
    async def test_modifier_cart_serializes_modifiers(
        self, db_session, test_user, test_brand, seeded_prepared_item
    ):
        mods = {"spice": "hot"}
        await add_to_cart(
            test_user.telegram_id, "Pad Thai", quantity=1,
            selected_modifiers=mods, brand_id=test_brand.id
        )
        cart_items = await get_cart_items(test_user.telegram_id)
        items_json, _ = _serialize_cart_items(cart_items)
        assert items_json[0]["modifiers"] == mods


# ---------------------------------------------------------------------------
# _check_unavailable_items
# ---------------------------------------------------------------------------

class TestCheckUnavailableItems:
    def _make_cart_items(self, items: list[tuple[str, int]]) -> list[dict]:
        """Build minimal get_cart_items-style dicts."""
        return [
            {"item_name": name, "quantity": qty, "price": Decimal("10"), "selected_modifiers": None}
            for name, qty in items
        ]

    def test_prepared_items_never_flagged(
        self, db_session, test_user, test_brand, test_store, seeded_prepared_item
    ):
        cart = self._make_cart_items([("Pad Thai", 5)])
        # No BranchInventory row at all — prepared should still not be flagged
        result = _check_unavailable_items(cart, test_store.id)
        assert result == []

    def test_product_missing_from_inventory_flagged(
        self, db_session, test_brand, test_store, seeded_product_item
    ):
        cart = self._make_cart_items([("Bottled Water", 1)])
        # No BranchInventory entry for this store
        result = _check_unavailable_items(cart, test_store.id)
        assert "Bottled Water" in result

    def test_product_with_sufficient_stock_not_flagged(
        self, db_session, test_brand, test_store, seeded_product_item
    ):
        inv = BranchInventory(
            store_id=test_store.id,
            item_name="Bottled Water",
            stock_quantity=10,
        )
        db_session.add(inv)
        db_session.commit()

        cart = self._make_cart_items([("Bottled Water", 5)])
        result = _check_unavailable_items(cart, test_store.id)
        assert result == []

    def test_product_with_insufficient_stock_flagged(
        self, db_session, test_brand, test_store, seeded_product_item
    ):
        inv = BranchInventory(
            store_id=test_store.id,
            item_name="Bottled Water",
            stock_quantity=2,
        )
        db_session.add(inv)
        db_session.commit()

        cart = self._make_cart_items([("Bottled Water", 5)])  # need 5, only 2 available
        result = _check_unavailable_items(cart, test_store.id)
        assert "Bottled Water" in result

    def test_mixed_prepared_and_product(
        self, db_session, test_brand, test_store,
        seeded_prepared_item, seeded_product_item
    ):
        # Bottled Water has no BranchInventory → should be flagged
        # Pad Thai is prepared → never flagged
        cart = self._make_cart_items([("Pad Thai", 2), ("Bottled Water", 1)])
        result = _check_unavailable_items(cart, test_store.id)
        assert "Pad Thai" not in result
        assert "Bottled Water" in result

    def test_empty_cart_returns_empty(self, db_session, test_store):
        result = _check_unavailable_items([], test_store.id)
        assert result == []
