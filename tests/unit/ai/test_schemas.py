"""Tests for Grok AI assistant Pydantic schemas (Card 17).

Validates that every action schema enforces its constraints correctly:
- Required fields reject missing values
- Field limits (min/max length, numeric bounds) are enforced
- Custom validators (price caps, identifier requirements) fire
- Valid inputs pass cleanly
"""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from bot.ai.schemas import (
    AdjustStockAction,
    BulkPriceUpdateAction,
    BulkPriceUpdateEntry,
    ColumnMappingGuess,
    CreateCategoryAction,
    CreateItemAction,
    DataMappingProposal,
    DeleteCategoryAction,
    DeleteItemAction,
    GetStatsAction,
    LookupUserAction,
    MenuImportAction,
    MenuImportRow,
    MUTATION_TOOLS,
    READ_TOOLS,
    SearchChatMessagesAction,
    SearchDeliveriesAction,
    SearchOrdersAction,
    TOOL_SCHEMA_MAP,
    UpdateItemAction,
    ViewInventoryAction,
)


# ── CreateItemAction ────────────────────────────────────────────────


class TestCreateItemAction:
    def test_valid_item(self):
        a = CreateItemAction(
            item_name="Pad Thai",
            description="Classic stir-fried noodles",
            price=Decimal("150.00"),
            category_name="Noodles",
            stock_quantity=50,
        )
        assert a.action == "create_item"
        assert a.item_name == "Pad Thai"
        assert a.price == Decimal("150.00")
        assert a.item_type == "prepared"

    def test_defaults(self):
        a = CreateItemAction(
            item_name="Soup",
            description="Hot soup",
            price=Decimal("80"),
            category_name="Soups",
        )
        assert a.stock_quantity == 0
        assert a.item_type == "prepared"

    def test_product_type(self):
        a = CreateItemAction(
            item_name="Water",
            description="Bottled water",
            price=Decimal("20"),
            category_name="Drinks",
            item_type="product",
        )
        assert a.item_type == "product"

    def test_rejects_empty_name(self):
        with pytest.raises(ValidationError, match="item_name"):
            CreateItemAction(
                item_name="",
                description="d",
                price=Decimal("10"),
                category_name="c",
            )

    def test_rejects_long_name(self):
        with pytest.raises(ValidationError):
            CreateItemAction(
                item_name="x" * 101,
                description="d",
                price=Decimal("10"),
                category_name="c",
            )

    def test_rejects_zero_price(self):
        with pytest.raises(ValidationError):
            CreateItemAction(
                item_name="Free Item",
                description="d",
                price=Decimal("0"),
                category_name="c",
            )

    def test_rejects_negative_price(self):
        with pytest.raises(ValidationError):
            CreateItemAction(
                item_name="Bad Item",
                description="d",
                price=Decimal("-10"),
                category_name="c",
            )

    def test_rejects_price_over_99999(self):
        with pytest.raises(ValidationError):
            CreateItemAction(
                item_name="Expensive",
                description="d",
                price=Decimal("100000"),
                category_name="c",
            )

    def test_price_over_10000_warns(self):
        """Custom validator rejects prices > 10,000."""
        with pytest.raises(ValidationError, match="10,000"):
            CreateItemAction(
                item_name="Pricey",
                description="d",
                price=Decimal("10001"),
                category_name="c",
            )

    def test_rejects_negative_stock(self):
        with pytest.raises(ValidationError):
            CreateItemAction(
                item_name="Item",
                description="d",
                price=Decimal("50"),
                category_name="c",
                stock_quantity=-1,
            )

    def test_rejects_invalid_item_type(self):
        with pytest.raises(ValidationError):
            CreateItemAction(
                item_name="Item",
                description="d",
                price=Decimal("50"),
                category_name="c",
                item_type="digital",
            )

    def test_rejects_missing_required_fields(self):
        with pytest.raises(ValidationError):
            CreateItemAction(item_name="Incomplete")


# ── UpdateItemAction ────────────────────────────────────────────────


class TestUpdateItemAction:
    def test_update_name_only(self):
        a = UpdateItemAction(item_name="Old Name", new_name="New Name")
        assert a.new_name == "New Name"
        assert a.new_price is None
        assert a.new_description is None

    def test_update_price_only(self):
        a = UpdateItemAction(item_name="Item", new_price=Decimal("200"))
        assert a.new_price == Decimal("200")

    def test_update_all_fields(self):
        a = UpdateItemAction(
            item_name="Item",
            new_name="Renamed",
            new_description="New desc",
            new_price=Decimal("300"),
            new_category="New Category",
        )
        assert a.new_name == "Renamed"
        assert a.new_description == "New desc"

    def test_rejects_price_over_10000(self):
        with pytest.raises(ValidationError, match="10,000"):
            UpdateItemAction(item_name="Item", new_price=Decimal("50000"))

    def test_accepts_price_at_10000(self):
        a = UpdateItemAction(item_name="Item", new_price=Decimal("10000"))
        assert a.new_price == Decimal("10000")

    def test_rejects_empty_new_name(self):
        with pytest.raises(ValidationError):
            UpdateItemAction(item_name="Item", new_name="")


# ── DeleteItemAction ────────────────────────────────────────────────


class TestDeleteItemAction:
    def test_valid_delete(self):
        a = DeleteItemAction(item_name="Pad Thai", confirm=True)
        assert a.confirm is True

    def test_confirm_false(self):
        a = DeleteItemAction(item_name="Pad Thai", confirm=False)
        assert a.confirm is False

    def test_rejects_missing_confirm(self):
        with pytest.raises(ValidationError):
            DeleteItemAction(item_name="Pad Thai")

    def test_rejects_missing_item_name(self):
        with pytest.raises(ValidationError):
            DeleteItemAction(confirm=True)


# ── BulkPriceUpdateAction ──────────────────────────────────────────


class TestBulkPriceUpdateAction:
    def test_valid_bulk_update(self):
        a = BulkPriceUpdateAction(updates=[
            {"item_name": "Pad Thai", "new_price": Decimal("150")},
            {"item_name": "Som Tam", "new_price": Decimal("80")},
        ])
        assert len(a.updates) == 2
        assert isinstance(a.updates[0], BulkPriceUpdateEntry)
        assert a.updates[0].item_name == "Pad Thai"
        assert a.updates[1].new_price == Decimal("80")

    def test_rejects_empty_updates(self):
        with pytest.raises(ValidationError):
            BulkPriceUpdateAction(updates=[])

    def test_rejects_too_many_updates(self):
        with pytest.raises(ValidationError):
            BulkPriceUpdateAction(
                updates=[{"item_name": f"Item {i}", "new_price": Decimal("10")} for i in range(51)]
            )

    def test_rejects_missing_item_name_in_entry(self):
        with pytest.raises(ValidationError):
            BulkPriceUpdateAction(updates=[{"new_price": Decimal("100")}])

    def test_rejects_missing_price_in_entry(self):
        with pytest.raises(ValidationError):
            BulkPriceUpdateAction(updates=[{"item_name": "Item"}])

    def test_rejects_negative_price_in_entry(self):
        with pytest.raises(ValidationError):
            BulkPriceUpdateAction(
                updates=[{"item_name": "Item", "new_price": Decimal("-5")}]
            )

    def test_rejects_price_over_10000_in_entry(self):
        with pytest.raises(ValidationError, match="10,000"):
            BulkPriceUpdateAction(
                updates=[{"item_name": "Item", "new_price": Decimal("15000")}]
            )


# ── CreateCategoryAction ───────────────────────────────────────────


class TestCreateCategoryAction:
    def test_valid(self):
        a = CreateCategoryAction(category_name="Desserts")
        assert a.sort_order == 0

    def test_with_sort_order(self):
        a = CreateCategoryAction(category_name="Drinks", sort_order=5)
        assert a.sort_order == 5

    def test_rejects_empty_name(self):
        with pytest.raises(ValidationError):
            CreateCategoryAction(category_name="")

    def test_rejects_negative_sort_order(self):
        with pytest.raises(ValidationError):
            CreateCategoryAction(category_name="X", sort_order=-1)


# ── DeleteCategoryAction ──────────────────────────────────────────


class TestDeleteCategoryAction:
    def test_valid(self):
        a = DeleteCategoryAction(category_name="Old Cat", confirm=True)
        assert a.confirm is True

    def test_rejects_missing_confirm(self):
        with pytest.raises(ValidationError):
            DeleteCategoryAction(category_name="Old Cat")


# ── AdjustStockAction ─────────────────────────────────────────────


class TestAdjustStockAction:
    def test_set_operation(self):
        a = AdjustStockAction(item_name="Item", operation="set", quantity=100)
        assert a.operation == "set"

    def test_add_operation(self):
        a = AdjustStockAction(item_name="Item", operation="add", quantity=10, comment="Restock")
        assert a.comment == "Restock"

    def test_remove_operation(self):
        a = AdjustStockAction(item_name="Item", operation="remove", quantity=5)
        assert a.operation == "remove"

    def test_rejects_invalid_operation(self):
        with pytest.raises(ValidationError):
            AdjustStockAction(item_name="Item", operation="multiply", quantity=2)

    def test_rejects_negative_quantity(self):
        with pytest.raises(ValidationError):
            AdjustStockAction(item_name="Item", operation="add", quantity=-1)

    def test_rejects_over_max_quantity(self):
        with pytest.raises(ValidationError):
            AdjustStockAction(item_name="Item", operation="set", quantity=100000)

    def test_comment_max_length(self):
        with pytest.raises(ValidationError):
            AdjustStockAction(
                item_name="Item", operation="add", quantity=1,
                comment="x" * 201,
            )


# ── SearchOrdersAction ────────────────────────────────────────────


class TestSearchOrdersAction:
    def test_defaults(self):
        a = SearchOrdersAction()
        assert a.limit == 20
        assert a.order_code is None

    def test_all_filters(self):
        a = SearchOrdersAction(
            order_code="ABC123",
            buyer_id=12345,
            status="delivered",
            payment_method="promptpay",
            delivery_type="door",
            date_from="2026-01-01",
            date_to="2026-01-31",
            limit=50,
        )
        assert a.status == "delivered"
        assert a.limit == 50

    def test_rejects_invalid_status(self):
        with pytest.raises(ValidationError):
            SearchOrdersAction(status="shipped")

    def test_rejects_invalid_payment_method(self):
        with pytest.raises(ValidationError):
            SearchOrdersAction(payment_method="paypal")

    def test_rejects_invalid_delivery_type(self):
        with pytest.raises(ValidationError):
            SearchOrdersAction(delivery_type="drone")

    def test_rejects_bad_date_format(self):
        with pytest.raises(ValidationError):
            SearchOrdersAction(date_from="01-01-2026")

    def test_rejects_limit_over_100(self):
        with pytest.raises(ValidationError):
            SearchOrdersAction(limit=101)

    def test_rejects_limit_zero(self):
        with pytest.raises(ValidationError):
            SearchOrdersAction(limit=0)


# ── SearchChatMessagesAction ──────────────────────────────────────


class TestSearchChatMessagesAction:
    def test_defaults(self):
        a = SearchChatMessagesAction()
        assert a.limit == 20

    def test_by_order_code(self):
        a = SearchChatMessagesAction(order_code="ABC123", keyword="photo")
        assert a.keyword == "photo"

    def test_filter_by_role(self):
        a = SearchChatMessagesAction(sender_role="driver")
        assert a.sender_role == "driver"

    def test_rejects_invalid_role(self):
        with pytest.raises(ValidationError):
            SearchChatMessagesAction(sender_role="admin")

    def test_has_photo_filter(self):
        a = SearchChatMessagesAction(has_photo=True)
        assert a.has_photo is True

    def test_has_location_filter(self):
        a = SearchChatMessagesAction(has_location=True)
        assert a.has_location is True

    def test_keyword_max_length(self):
        with pytest.raises(ValidationError):
            SearchChatMessagesAction(keyword="x" * 101)


# ── SearchDeliveriesAction ────────────────────────────────────────


class TestSearchDeliveriesAction:
    def test_defaults(self):
        a = SearchDeliveriesAction()
        assert a.limit == 20

    def test_all_filters(self):
        a = SearchDeliveriesAction(
            delivery_zone="zone_a",
            has_delivery_photo=True,
            has_gps=True,
            driver_id=99,
            delivery_type="dead_drop",
            date_from="2026-01-01",
            date_to="2026-01-31",
        )
        assert a.delivery_zone == "zone_a"
        assert a.delivery_type == "dead_drop"

    def test_rejects_invalid_delivery_type(self):
        with pytest.raises(ValidationError):
            SearchDeliveriesAction(delivery_type="mail")


# ── LookupUserAction ─────────────────────────────────────────────


class TestLookupUserAction:
    def test_by_telegram_id(self):
        a = LookupUserAction(telegram_id=12345)
        assert a.telegram_id == 12345
        assert a.include_orders is False

    def test_by_phone(self):
        a = LookupUserAction(phone_number="+66812345678")
        assert a.phone_number == "+66812345678"

    def test_with_includes(self):
        a = LookupUserAction(
            telegram_id=12345,
            include_orders=True,
            include_referrals=True,
        )
        assert a.include_orders is True
        assert a.include_referrals is True

    def test_rejects_no_identifier(self):
        """Must provide at least telegram_id or phone_number."""
        with pytest.raises(ValidationError, match="at least"):
            LookupUserAction()

    def test_rejects_phone_too_long(self):
        with pytest.raises(ValidationError):
            LookupUserAction(phone_number="x" * 51)


# ── GetStatsAction ───────────────────────────────────────────────


class TestGetStatsAction:
    def test_defaults(self):
        a = GetStatsAction()
        assert a.include_revenue is True
        assert a.include_top_items is False
        assert a.include_user_growth is False

    def test_with_date_range(self):
        a = GetStatsAction(
            date_from="2026-01-01",
            date_to="2026-03-22",
            include_top_items=True,
            include_user_growth=True,
        )
        assert a.date_from == "2026-01-01"

    def test_rejects_bad_date(self):
        with pytest.raises(ValidationError):
            GetStatsAction(date_from="Jan 1 2026")


# ── ViewInventoryAction ──────────────────────────────────────────


class TestViewInventoryAction:
    def test_defaults(self):
        a = ViewInventoryAction()
        assert a.only_low_stock is False
        assert a.low_stock_threshold == 5

    def test_low_stock_filter(self):
        a = ViewInventoryAction(only_low_stock=True, low_stock_threshold=10)
        assert a.low_stock_threshold == 10

    def test_category_filter(self):
        a = ViewInventoryAction(category_filter="Drinks")
        assert a.category_filter == "Drinks"


# ── MenuImportRow ────────────────────────────────────────────────


class TestMenuImportRow:
    def test_valid_row(self):
        r = MenuImportRow(
            item_name="Pad Thai",
            price=Decimal("150"),
            category_name="Noodles",
        )
        assert r.description == ""
        assert r.stock_quantity == 0
        assert r.item_type == "prepared"

    def test_full_row(self):
        r = MenuImportRow(
            item_name="Water",
            description="Bottled water 600ml",
            price=Decimal("20"),
            category_name="Drinks",
            stock_quantity=200,
            item_type="product",
        )
        assert r.stock_quantity == 200

    def test_rejects_zero_price(self):
        with pytest.raises(ValidationError):
            MenuImportRow(item_name="Free", price=Decimal("0"), category_name="c")


# ── MenuImportAction ────────────────────────────────────────────


class TestMenuImportAction:
    def test_valid_import(self):
        a = MenuImportAction(items=[
            {"item_name": "A", "price": Decimal("10"), "category_name": "c"},
            {"item_name": "B", "price": Decimal("20"), "category_name": "c"},
        ])
        assert len(a.items) == 2
        assert a.create_missing_categories is True
        assert a.skip_existing is True
        assert a.overwrite_existing is False

    def test_rejects_empty_items(self):
        with pytest.raises(ValidationError):
            MenuImportAction(items=[])

    def test_rejects_too_many_items(self):
        with pytest.raises(ValidationError):
            MenuImportAction(items=[
                {"item_name": f"Item {i}", "price": Decimal("10"), "category_name": "c"}
                for i in range(501)
            ])

    def test_validates_each_row(self):
        """Invalid row within import should fail validation."""
        with pytest.raises(ValidationError):
            MenuImportAction(items=[
                {"item_name": "Good", "price": Decimal("10"), "category_name": "c"},
                {"item_name": "", "price": Decimal("10"), "category_name": "c"},  # empty name
            ])


# ── DataMappingProposal ─────────────────────────────────────────


class TestDataMappingProposal:
    def test_valid_proposal(self):
        a = DataMappingProposal(mappings=[
            ColumnMappingGuess(
                source_column="name",
                target_field="item_name",
                confidence=0.95,
                sample_values=["Pad Thai", "Som Tam"],
            ),
            ColumnMappingGuess(
                source_column="cost",
                target_field="price",
                confidence=0.8,
            ),
        ])
        assert len(a.mappings) == 2
        assert a.unmapped_required == []
        assert a.warnings == []

    def test_with_unmapped_and_warnings(self):
        a = DataMappingProposal(
            mappings=[
                ColumnMappingGuess(
                    source_column="col1",
                    target_field="skip",
                    confidence=0.5,
                )
            ],
            unmapped_required=["item_name", "price"],
            warnings=["Column 'code' not recognized"],
        )
        assert len(a.unmapped_required) == 2

    def test_rejects_invalid_target_field(self):
        with pytest.raises(ValidationError):
            ColumnMappingGuess(
                source_column="col",
                target_field="nonexistent_field",
                confidence=0.5,
            )

    def test_rejects_confidence_out_of_range(self):
        with pytest.raises(ValidationError):
            ColumnMappingGuess(
                source_column="col",
                target_field="price",
                confidence=1.5,
            )


# ── Schema Registry ─────────────────────────────────────────────


class TestSchemaRegistry:
    def test_all_mutation_tools_in_map(self):
        for name in MUTATION_TOOLS:
            assert name in TOOL_SCHEMA_MAP, f"Mutation tool '{name}' missing from TOOL_SCHEMA_MAP"

    def test_all_read_tools_in_map(self):
        for name in READ_TOOLS:
            assert name in TOOL_SCHEMA_MAP, f"Read tool '{name}' missing from TOOL_SCHEMA_MAP"

    def test_no_overlap_between_read_and_mutation(self):
        overlap = READ_TOOLS & MUTATION_TOOLS
        assert not overlap, f"Tools in both READ and MUTATION: {overlap}"

    def test_map_covers_all_tools(self):
        all_tools = READ_TOOLS | MUTATION_TOOLS
        assert set(TOOL_SCHEMA_MAP.keys()) == all_tools

    def test_every_schema_has_action_literal(self):
        """Every schema in the map should have an action field that matches its key."""
        for key, cls in TOOL_SCHEMA_MAP.items():
            instance_fields = cls.model_fields
            assert "action" in instance_fields, f"{cls.__name__} missing 'action' field"
            # The default should match the registry key
            default = instance_fields["action"].default
            assert default == key, f"{cls.__name__}.action default '{default}' != registry key '{key}'"
