"""Tests for Grok AI action executor (Card 17).

Tests that validated Pydantic actions execute correctly against the database.
Uses the SQLite test database from conftest.py.
"""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from bot.ai.executor import execute_mutation, execute_query
from bot.ai.schemas import (
    AdjustStockAction,
    BulkPriceUpdateAction,
    CreateCategoryAction,
    CreateItemAction,
    DeleteCategoryAction,
    DeleteItemAction,
    GetStatsAction,
    LookupUserAction,
    SearchChatMessagesAction,
    SearchDeliveriesAction,
    SearchOrdersAction,
    UpdateItemAction,
    ViewInventoryAction,
)
from bot.database.models.main import (
    Categories,
    DeliveryChatMessage,
    Goods,
    Order,
    OrderItem,
    User,
)


# ── Query Executor Tests ────────────────────────────────────────────


class TestSearchOrders:
    @pytest.mark.asyncio
    async def test_search_all_orders(self, test_order):
        action = SearchOrdersAction()
        result = await execute_query(action)
        assert "orders" in result
        assert result["count"] >= 1

    @pytest.mark.asyncio
    async def test_search_by_order_code(self, test_order):
        action = SearchOrdersAction(order_code="TEST01")
        result = await execute_query(action)
        assert result["count"] == 1
        assert result["orders"][0]["order_code"] == "TEST01"

    @pytest.mark.asyncio
    async def test_search_by_status(self, test_order):
        action = SearchOrdersAction(status="pending")
        result = await execute_query(action)
        assert result["count"] >= 1
        assert all(o["status"] == "pending" for o in result["orders"])

    @pytest.mark.asyncio
    async def test_search_nonexistent_returns_empty(self, test_order):
        action = SearchOrdersAction(order_code="XXXXXX")
        result = await execute_query(action)
        assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_search_by_payment_method(self, test_order):
        action = SearchOrdersAction(payment_method="cash")
        result = await execute_query(action)
        assert result["count"] >= 1

    @pytest.mark.asyncio
    async def test_search_with_limit(self, test_order):
        action = SearchOrdersAction(limit=1)
        result = await execute_query(action)
        assert len(result["orders"]) <= 1

    @pytest.mark.asyncio
    async def test_order_includes_items(self, test_order):
        action = SearchOrdersAction(order_code="TEST01")
        result = await execute_query(action)
        order = result["orders"][0]
        assert "items" in order
        assert len(order["items"]) >= 1
        assert order["items"][0]["name"] == "Test Product"


class TestSearchChat:
    @pytest.mark.asyncio
    async def test_empty_chat_returns_empty(self, test_order):
        action = SearchChatMessagesAction()
        result = await execute_query(action)
        assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_search_by_order_code(self, db_session, test_order):
        msg = DeliveryChatMessage(
            order_id=test_order.id,
            sender_id=99,
            sender_role="driver",
            message_text="Delivered!",
        )
        db_session.add(msg)
        db_session.commit()

        action = SearchChatMessagesAction(order_code="TEST01")
        result = await execute_query(action)
        assert result["count"] == 1
        assert result["messages"][0]["text"] == "Delivered!"

    @pytest.mark.asyncio
    async def test_search_by_keyword(self, db_session, test_order):
        msg = DeliveryChatMessage(
            order_id=test_order.id,
            sender_id=99,
            sender_role="customer",
            message_text="Where is my food?",
        )
        db_session.add(msg)
        db_session.commit()

        action = SearchChatMessagesAction(keyword="food")
        result = await execute_query(action)
        assert result["count"] >= 1


class TestSearchDeliveries:
    @pytest.mark.asyncio
    async def test_filters_to_delivery_statuses(self, db_session, test_user):
        """Only returns orders with delivery-related statuses."""
        # Create a delivered order
        order = Order(
            buyer_id=test_user.telegram_id,
            total_price=Decimal("100"),
            payment_method="cash",
            delivery_address="123 St",
            phone_number="+66",
            order_status="delivered",
            delivery_type="door",
        )
        db_session.add(order)
        db_session.commit()

        action = SearchDeliveriesAction()
        result = await execute_query(action)
        assert result["count"] >= 1
        assert all(d["status"] in ("out_for_delivery", "delivered") for d in result["deliveries"])


class TestViewInventory:
    @pytest.mark.asyncio
    async def test_view_all(self, test_goods):
        action = ViewInventoryAction()
        result = await execute_query(action)
        assert result["count"] >= 1
        item = result["inventory"][0]
        assert "name" in item
        assert "stock" in item
        assert "available" in item

    @pytest.mark.asyncio
    async def test_filter_by_category(self, test_goods):
        action = ViewInventoryAction(category_filter="Test Category")
        result = await execute_query(action)
        assert result["count"] >= 1

    @pytest.mark.asyncio
    async def test_filter_nonexistent_category(self, test_goods):
        action = ViewInventoryAction(category_filter="Nonexistent")
        result = await execute_query(action)
        assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_low_stock_filter(self, test_goods, test_goods_low_stock):
        action = ViewInventoryAction(only_low_stock=True, low_stock_threshold=10)
        result = await execute_query(action)
        # Low stock product has 5 units, should show; test_goods has 100, should not
        names = [i["name"] for i in result["inventory"]]
        assert "Low Stock Product" in names


class TestGetStats:
    @pytest.mark.asyncio
    async def test_basic_stats(self, test_goods, test_user):
        action = GetStatsAction()
        result = await execute_query(action)
        assert "total_users" in result
        assert "total_items" in result
        assert "total_categories" in result
        assert "today_revenue" in result

    @pytest.mark.asyncio
    async def test_stats_with_growth(self, test_user):
        action = GetStatsAction(include_user_growth=True)
        result = await execute_query(action)
        assert "today_new_users" in result

    @pytest.mark.asyncio
    async def test_stats_with_top_items(self, test_order):
        action = GetStatsAction(include_top_items=True)
        result = await execute_query(action)
        assert "top_items" in result


class TestLookupUser:
    @pytest.mark.asyncio
    async def test_by_telegram_id(self, test_user):
        action = LookupUserAction(telegram_id=test_user.telegram_id)
        result = await execute_query(action)
        assert "user" in result
        assert result["user"]["telegram_id"] == test_user.telegram_id

    @pytest.mark.asyncio
    async def test_user_not_found(self):
        action = LookupUserAction(telegram_id=999999999)
        result = await execute_query(action)
        assert "error" in result

    @pytest.mark.asyncio
    async def test_by_phone(self, test_customer_info):
        action = LookupUserAction(phone_number="+1234567890")
        result = await execute_query(action)
        assert "user" in result

    @pytest.mark.asyncio
    async def test_with_referrals(self, test_user):
        action = LookupUserAction(
            telegram_id=test_user.telegram_id,
            include_referrals=True,
        )
        result = await execute_query(action)
        assert "referral_count" in result["user"]

    @pytest.mark.asyncio
    async def test_with_orders(self, test_user, test_order):
        """include_orders=True populates the orders list with the user's orders."""
        action = LookupUserAction(
            telegram_id=test_user.telegram_id,
            include_orders=True,
        )
        result = await execute_query(action)
        assert "user" in result
        assert "orders" in result["user"]
        orders = result["user"]["orders"]
        assert len(orders) >= 1
        order = orders[0]
        assert "order_code" in order
        assert "status" in order
        assert "total_price" in order
        assert "payment_method" in order
        assert "created_at" in order

    @pytest.mark.asyncio
    async def test_without_orders_key_absent(self, test_user):
        """When include_orders is not set, the orders key is absent from the result."""
        action = LookupUserAction(telegram_id=test_user.telegram_id)
        result = await execute_query(action)
        assert "user" in result
        assert "orders" not in result["user"]


# ── Mutation Executor Tests ─────────────────────────────────────────


class TestCreateItem:
    @pytest.mark.asyncio
    async def test_create_item(self, test_category):
        action = CreateItemAction(
            item_name="New Dish",
            description="A new dish",
            price=Decimal("120"),
            category_name=test_category.name,
            stock_quantity=0,
        )
        result = await execute_mutation(action, admin_id=1)
        assert result["success"] is True
        assert result["created"] == "New Dish"

    @pytest.mark.asyncio
    async def test_create_item_with_stock(self, test_user, test_category):
        """Uses test_user so admin_id FK resolves in inventory_log."""
        action = CreateItemAction(
            item_name="Stocked Item",
            description="Has stock",
            price=Decimal("50"),
            category_name=test_category.name,
            stock_quantity=25,
        )
        result = await execute_mutation(action, admin_id=test_user.telegram_id)
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_create_duplicate_item(self, test_goods):
        action = CreateItemAction(
            item_name=test_goods.name,  # Already exists
            description="Duplicate",
            price=Decimal("100"),
            category_name=test_goods.category_name,
        )
        result = await execute_mutation(action, admin_id=1)
        assert "error" in result
        assert "already exists" in result["error"]


class TestUpdateItem:
    @pytest.mark.asyncio
    async def test_update_price(self, test_goods):
        action = UpdateItemAction(
            item_name=test_goods.name,
            new_price=Decimal("199.99"),
        )
        result = await execute_mutation(action, admin_id=1)
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_update_nonexistent(self):
        action = UpdateItemAction(
            item_name="Does Not Exist",
            new_price=Decimal("50"),
        )
        result = await execute_mutation(action, admin_id=1)
        assert "error" in result
        assert "not found" in result["error"]


class TestDeleteItem:
    @pytest.mark.asyncio
    async def test_delete_item(self, test_goods):
        action = DeleteItemAction(item_name=test_goods.name, confirm=True)
        result = await execute_mutation(action, admin_id=1)
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_delete_without_confirm(self, test_goods):
        action = DeleteItemAction(item_name=test_goods.name, confirm=False)
        result = await execute_mutation(action, admin_id=1)
        assert "error" in result

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self):
        action = DeleteItemAction(item_name="Ghost Item", confirm=True)
        result = await execute_mutation(action, admin_id=1)
        assert "error" in result


class TestBulkPriceUpdate:
    @pytest.mark.asyncio
    async def test_bulk_update(self, multiple_products):
        action = BulkPriceUpdateAction(updates=[
            {"item_name": "Product 1", "new_price": Decimal("99")},
            {"item_name": "Product 2", "new_price": Decimal("199")},
        ])
        result = await execute_mutation(action, admin_id=1)
        assert result["success"] is True
        assert len(result["updated"]) == 2

    @pytest.mark.asyncio
    async def test_bulk_update_nonexistent_item(self, test_goods):
        action = BulkPriceUpdateAction(updates=[
            {"item_name": "Ghost", "new_price": Decimal("100")},
        ])
        result = await execute_mutation(action, admin_id=1)
        assert len(result["errors"]) == 1


class TestAdjustStock:
    @pytest.mark.asyncio
    async def test_set_stock(self, test_user, test_goods):
        action = AdjustStockAction(
            item_name=test_goods.name,
            operation="set",
            quantity=200,
        )
        result = await execute_mutation(action, admin_id=test_user.telegram_id)
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_add_stock(self, test_user, test_goods):
        action = AdjustStockAction(
            item_name=test_goods.name,
            operation="add",
            quantity=50,
        )
        result = await execute_mutation(action, admin_id=test_user.telegram_id)
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_remove_stock(self, test_user, test_goods):
        action = AdjustStockAction(
            item_name=test_goods.name,
            operation="remove",
            quantity=10,
        )
        result = await execute_mutation(action, admin_id=test_user.telegram_id)
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_remove_too_much_stock(self, test_user, test_goods):
        action = AdjustStockAction(
            item_name=test_goods.name,
            operation="remove",
            quantity=99999,
        )
        result = await execute_mutation(action, admin_id=test_user.telegram_id)
        assert "error" in result

    @pytest.mark.asyncio
    async def test_adjust_nonexistent(self):
        action = AdjustStockAction(
            item_name="Ghost",
            operation="add",
            quantity=10,
        )
        result = await execute_mutation(action, admin_id=1)
        assert "error" in result


class TestCreateCategory:
    @pytest.mark.asyncio
    async def test_create(self):
        action = CreateCategoryAction(category_name="New Cat")
        result = await execute_mutation(action, admin_id=1)
        assert result["success"] is True
        assert result["created"] == "New Cat"

    @pytest.mark.asyncio
    async def test_create_duplicate(self, test_category):
        action = CreateCategoryAction(category_name=test_category.name)
        result = await execute_mutation(action, admin_id=1)
        assert "error" in result
        assert "already exists" in result["error"]


class TestDeleteCategory:
    @pytest.mark.asyncio
    async def test_delete(self, db_session):
        cat = Categories(name="Temp Cat")
        db_session.add(cat)
        db_session.commit()

        action = DeleteCategoryAction(category_name="Temp Cat", confirm=True)
        result = await execute_mutation(action, admin_id=1)
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_delete_without_confirm(self, test_category):
        action = DeleteCategoryAction(category_name=test_category.name, confirm=False)
        result = await execute_mutation(action, admin_id=1)
        assert "error" in result

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self):
        action = DeleteCategoryAction(category_name="Nope", confirm=True)
        result = await execute_mutation(action, admin_id=1)
        assert "error" in result


class TestImportMenu:
    @pytest.mark.asyncio
    async def test_import_new_items(self, test_user, test_category):
        from bot.ai.schemas import MenuImportAction
        action = MenuImportAction(items=[
            {"item_name": "Import A", "price": Decimal("100"),
             "category_name": test_category.name, "description": "Imported"},
            {"item_name": "Import B", "price": Decimal("200"),
             "category_name": test_category.name, "description": "Imported"},
        ])
        result = await execute_mutation(action, admin_id=test_user.telegram_id)
        assert result["success"] is True
        assert result["created"] == 2
        assert result["skipped"] == 0

    @pytest.mark.asyncio
    async def test_import_skip_existing(self, test_goods):
        from bot.ai.schemas import MenuImportAction
        action = MenuImportAction(items=[
            {"item_name": test_goods.name, "price": Decimal("50"),
             "category_name": test_goods.category_name, "description": "dup"},
        ], skip_existing=True)
        result = await execute_mutation(action, admin_id=1)
        assert result["skipped"] == 1
        assert result["created"] == 0

    @pytest.mark.asyncio
    async def test_import_creates_missing_categories(self, test_user):
        from bot.ai.schemas import MenuImportAction
        action = MenuImportAction(
            items=[
                {"item_name": "Brand New",  "price": Decimal("50"),
                 "category_name": "AutoCreated", "description": "d"},
            ],
            create_missing_categories=True,
        )
        result = await execute_mutation(action, admin_id=test_user.telegram_id)
        assert result["success"] is True
        assert result["created"] == 1


class TestUnknownAction:
    @pytest.mark.asyncio
    async def test_unknown_query(self):
        from pydantic import BaseModel
        class FakeAction(BaseModel):
            action: str = "nonexistent"
        result = await execute_query(FakeAction())
        assert "error" in result

    @pytest.mark.asyncio
    async def test_unknown_mutation(self):
        from pydantic import BaseModel
        class FakeAction(BaseModel):
            action: str = "nonexistent"
        result = await execute_mutation(FakeAction(), admin_id=1)
        assert "error" in result
