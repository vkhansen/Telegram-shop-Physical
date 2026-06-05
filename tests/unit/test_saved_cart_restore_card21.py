"""
Card 21 Phase 4 completion — Saved-cart restore-from-Profile tests.

Pins:
- get_saved_carts returns brand/store names, item_count, and total.
- restore_saved_cart recreates ShoppingCart rows and consumes the snapshot.
- restore replaces any pre-existing active cart (brand-switch semantics).
- restore skips items that are no longer orderable and reports them.
- restore preserves selected modifiers.
- restore of a missing snapshot returns not_found.
- delete_saved_cart removes the row (and returns False when absent).
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from bot.database.methods.create import add_to_cart, restore_saved_cart, save_cart_snapshot
from bot.database.methods.delete import delete_saved_cart
from bot.database.methods.read import get_cart_items, get_saved_carts
from bot.database.models.main import Categories, Goods

# ---------------------------------------------------------------------------
# Fixtures (local copies — mirror test_brand_switch_card21.py)
# ---------------------------------------------------------------------------


@pytest.fixture
def seeded_prepared_item(db_session, test_brand):
    """A 'prepared' (unlimited-stock) item in the test brand."""
    db_session.add(Categories(name="Hot Food", brand_id=test_brand.id))
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
    db_session.add(Categories(name="Drinks", brand_id=test_brand.id))
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


def _save(test_user, test_brand, test_store, items, total):
    return save_cart_snapshot(
        user_id=test_user.telegram_id,
        brand_id=test_brand.id,
        store_id=test_store.id,
        items_json=items,
        original_total=Decimal(total),
    )


# ---------------------------------------------------------------------------
# get_saved_carts
# ---------------------------------------------------------------------------


class TestGetSavedCarts:
    def test_empty_when_none(self, db_session, test_user):
        assert get_saved_carts(test_user.telegram_id) == []

    def test_returns_names_count_and_total(self, db_session, test_user, test_brand, test_store, seeded_prepared_item):
        _save(
            test_user,
            test_brand,
            test_store,
            [{"name": "Pad Thai", "quantity": 3, "modifiers": None, "unit_price": "120.00"}],
            "360.00",
        )
        carts = get_saved_carts(test_user.telegram_id)
        assert len(carts) == 1
        c = carts[0]
        assert c["brand_name"] == test_brand.name
        assert c["store_name"] == test_store.name
        assert c["item_count"] == 3
        assert c["total"] == Decimal("360.00")


# ---------------------------------------------------------------------------
# restore_saved_cart
# ---------------------------------------------------------------------------


class TestRestoreSavedCart:
    async def test_recreates_cart_and_consumes_snapshot(
        self, db_session, test_user, test_brand, test_store, seeded_prepared_item
    ):
        _save(
            test_user,
            test_brand,
            test_store,
            [{"name": "Pad Thai", "quantity": 2, "modifiers": None, "unit_price": "120.00"}],
            "240.00",
        )
        sc_id = get_saved_carts(test_user.telegram_id)[0]["id"]

        result = await restore_saved_cart(test_user.telegram_id, sc_id)

        assert result["ok"] is True
        assert result["restored"] == 1
        assert result["skipped"] == []
        assert result["brand_id"] == test_brand.id
        items = await get_cart_items(test_user.telegram_id)
        assert any(i["item_name"] == "Pad Thai" and i["quantity"] == 2 for i in items)
        # snapshot consumed
        assert get_saved_carts(test_user.telegram_id) == []

    async def test_replaces_existing_active_cart(
        self, db_session, test_user, test_brand, test_store, seeded_prepared_item, seeded_product_item
    ):
        await add_to_cart(test_user.telegram_id, "Bottled Water", 1, brand_id=test_brand.id, store_id=test_store.id)
        _save(
            test_user,
            test_brand,
            test_store,
            [{"name": "Pad Thai", "quantity": 1, "modifiers": None, "unit_price": "120.00"}],
            "120.00",
        )
        sc_id = get_saved_carts(test_user.telegram_id)[0]["id"]

        await restore_saved_cart(test_user.telegram_id, sc_id)

        items = await get_cart_items(test_user.telegram_id)
        assert {i["item_name"] for i in items} == {"Pad Thai"}  # water replaced

    async def test_skips_unavailable_items(self, db_session, test_user, test_brand, test_store, seeded_prepared_item):
        _save(
            test_user,
            test_brand,
            test_store,
            [
                {"name": "Pad Thai", "quantity": 1, "modifiers": None, "unit_price": "120.00"},
                {"name": "Ghost Item", "quantity": 1, "modifiers": None, "unit_price": "50.00"},
            ],
            "170.00",
        )
        sc_id = get_saved_carts(test_user.telegram_id)[0]["id"]

        result = await restore_saved_cart(test_user.telegram_id, sc_id)

        assert result["restored"] == 1
        assert result["skipped"] == ["Ghost Item"]
        items = await get_cart_items(test_user.telegram_id)
        assert {i["item_name"] for i in items} == {"Pad Thai"}

    async def test_preserves_modifiers(self, db_session, test_user, test_brand, test_store, seeded_prepared_item):
        mods = {"spice_level": "thai_hot"}
        _save(
            test_user,
            test_brand,
            test_store,
            [{"name": "Pad Thai", "quantity": 1, "modifiers": mods, "unit_price": "120.00"}],
            "120.00",
        )
        sc_id = get_saved_carts(test_user.telegram_id)[0]["id"]

        await restore_saved_cart(test_user.telegram_id, sc_id)

        items = await get_cart_items(test_user.telegram_id)
        pad_thai = next(i for i in items if i["item_name"] == "Pad Thai")
        assert pad_thai["selected_modifiers"] == mods

    async def test_missing_snapshot_returns_not_found(self, db_session, test_user):
        result = await restore_saved_cart(test_user.telegram_id, 999999)
        assert result["ok"] is False
        assert result["not_found"] is True
        assert result["restored"] == 0


# ---------------------------------------------------------------------------
# delete_saved_cart
# ---------------------------------------------------------------------------


class TestDeleteSavedCart:
    def test_removes_row_then_false_when_absent(
        self, db_session, test_user, test_brand, test_store, seeded_prepared_item
    ):
        _save(
            test_user,
            test_brand,
            test_store,
            [{"name": "Pad Thai", "quantity": 1, "modifiers": None, "unit_price": "120.00"}],
            "120.00",
        )
        sc_id = get_saved_carts(test_user.telegram_id)[0]["id"]

        assert delete_saved_cart(test_user.telegram_id, sc_id) is True
        assert get_saved_carts(test_user.telegram_id) == []
        assert delete_saved_cart(test_user.telegram_id, sc_id) is False
