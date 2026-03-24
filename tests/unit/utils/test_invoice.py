"""Tests for invoice text generation."""
import pytest
from decimal import Decimal
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock


def _make_order(**overrides):
    """Build a mock Order with sensible defaults."""
    order = MagicMock()
    order.id = overrides.get("id", 1)
    order.order_code = overrides.get("order_code", "ABC123")
    order.created_at = overrides.get("created_at", datetime(2025, 6, 15, 14, 30, tzinfo=timezone.utc))
    order.payment_method = overrides.get("payment_method", "cash")
    order.store_id = overrides.get("store_id", None)
    order.delivery_fee = overrides.get("delivery_fee", None)
    order.coupon_discount = overrides.get("coupon_discount", None)
    order.coupon_code = overrides.get("coupon_code", None)
    order.bonus_applied = overrides.get("bonus_applied", None)
    order.total_price = overrides.get("total_price", Decimal("500.00"))
    order.delivery_address = overrides.get("delivery_address", "123 Main St")
    order.phone_number = overrides.get("phone_number", "0812345678")
    order.delivery_type = overrides.get("delivery_type", "door")
    return order


def _make_item(name="Widget", price=Decimal("100.00"), quantity=2):
    """Build a mock OrderItem."""
    item = MagicMock()
    item.item_name = name
    item.price = price
    item.quantity = quantity
    return item


def _patch_db(order, items, store=None):
    """Return a patch for Database().session() that serves mock order + items."""
    mock_session = MagicMock()

    from bot.database.models.main import Order, OrderItem

    def query_side_effect(model):
        q = MagicMock()
        if model is Order:
            q.filter_by.return_value.first.return_value = order
        elif model is OrderItem:
            q.filter_by.return_value.all.return_value = items
        else:
            # Store query
            q.filter_by.return_value.first.return_value = store
        return q

    mock_session.query.side_effect = query_side_effect
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=False)

    mock_db = MagicMock()
    mock_db.session.return_value = mock_session
    return patch("bot.utils.invoice.Database", return_value=mock_db)


@pytest.mark.unit
class TestGenerateInvoiceText:
    """Tests for generate_invoice_text()."""

    def test_order_not_found_returns_none(self):
        with _patch_db(order=None, items=[]):
            from bot.utils.invoice import generate_invoice_text
            result = generate_invoice_text(order_id=999)
        assert result is None

    def test_basic_invoice_contains_order_code(self):
        order = _make_order(order_code="XYZ789")
        items = [_make_item()]
        with _patch_db(order, items):
            from bot.utils.invoice import generate_invoice_text
            result = generate_invoice_text(order_id=1)
        assert "XYZ789" in result

    def test_basic_invoice_contains_date(self):
        order = _make_order()
        items = [_make_item()]
        with _patch_db(order, items):
            from bot.utils.invoice import generate_invoice_text
            result = generate_invoice_text(order_id=1)
        assert "2025-06-15 14:30" in result

    def test_payment_method_uppercased(self):
        order = _make_order(payment_method="promptpay")
        items = [_make_item()]
        with _patch_db(order, items):
            from bot.utils.invoice import generate_invoice_text
            result = generate_invoice_text(order_id=1)
        assert "PROMPTPAY" in result

    def test_items_listed_with_quantity_and_price(self):
        order = _make_order()
        items = [_make_item(name="Burger", price=Decimal("150.00"), quantity=3)]
        with _patch_db(order, items):
            from bot.utils.invoice import generate_invoice_text
            result = generate_invoice_text(order_id=1)
        assert "Burger" in result
        assert "3 x 150.00 = 450.00" in result

    def test_multiple_items(self):
        order = _make_order()
        items = [
            _make_item(name="Item A", price=Decimal("100.00"), quantity=1),
            _make_item(name="Item B", price=Decimal("50.00"), quantity=2),
        ]
        with _patch_db(order, items):
            from bot.utils.invoice import generate_invoice_text
            result = generate_invoice_text(order_id=1)
        assert "Item A" in result
        assert "Item B" in result
        assert "Subtotal: 200" in result

    def test_delivery_fee_shown_when_present(self):
        order = _make_order(delivery_fee=Decimal("30.00"))
        items = [_make_item()]
        with _patch_db(order, items):
            from bot.utils.invoice import generate_invoice_text
            result = generate_invoice_text(order_id=1)
        assert "Delivery Fee: 30.00" in result

    def test_delivery_fee_hidden_when_zero(self):
        order = _make_order(delivery_fee=Decimal("0"))
        items = [_make_item()]
        with _patch_db(order, items):
            from bot.utils.invoice import generate_invoice_text
            result = generate_invoice_text(order_id=1)
        assert "Delivery Fee" not in result

    def test_delivery_fee_hidden_when_none(self):
        order = _make_order(delivery_fee=None)
        items = [_make_item()]
        with _patch_db(order, items):
            from bot.utils.invoice import generate_invoice_text
            result = generate_invoice_text(order_id=1)
        assert "Delivery Fee" not in result

    def test_coupon_discount_shown(self):
        order = _make_order(coupon_discount=Decimal("50.00"), coupon_code="HALF")
        items = [_make_item()]
        with _patch_db(order, items):
            from bot.utils.invoice import generate_invoice_text
            result = generate_invoice_text(order_id=1)
        assert "Coupon (HALF): -50.00" in result

    def test_coupon_discount_hidden_when_zero(self):
        order = _make_order(coupon_discount=Decimal("0"), coupon_code="NOPE")
        items = [_make_item()]
        with _patch_db(order, items):
            from bot.utils.invoice import generate_invoice_text
            result = generate_invoice_text(order_id=1)
        assert "Coupon" not in result

    def test_bonus_applied_shown(self):
        order = _make_order(bonus_applied=Decimal("25.00"))
        items = [_make_item()]
        with _patch_db(order, items):
            from bot.utils.invoice import generate_invoice_text
            result = generate_invoice_text(order_id=1)
        assert "Bonus Applied: -25.00" in result

    def test_bonus_hidden_when_zero(self):
        order = _make_order(bonus_applied=Decimal("0"))
        items = [_make_item()]
        with _patch_db(order, items):
            from bot.utils.invoice import generate_invoice_text
            result = generate_invoice_text(order_id=1)
        assert "Bonus" not in result

    def test_total_price_shown(self):
        order = _make_order(total_price=Decimal("999.99"))
        items = [_make_item()]
        with _patch_db(order, items):
            from bot.utils.invoice import generate_invoice_text
            result = generate_invoice_text(order_id=1)
        assert "TOTAL: 999.99" in result

    def test_delivery_address_and_phone(self):
        order = _make_order(delivery_address="456 Elm Ave", phone_number="0999999999")
        items = [_make_item()]
        with _patch_db(order, items):
            from bot.utils.invoice import generate_invoice_text
            result = generate_invoice_text(order_id=1)
        assert "456 Elm Ave" in result
        assert "0999999999" in result

    def test_delivery_type_door_not_shown(self):
        """Door delivery is the default, so 'Type:' line should not appear."""
        order = _make_order(delivery_type="door")
        items = [_make_item()]
        with _patch_db(order, items):
            from bot.utils.invoice import generate_invoice_text
            result = generate_invoice_text(order_id=1)
        assert "Type:" not in result

    def test_delivery_type_pickup_shown(self):
        order = _make_order(delivery_type="pickup")
        items = [_make_item()]
        with _patch_db(order, items):
            from bot.utils.invoice import generate_invoice_text
            result = generate_invoice_text(order_id=1)
        assert "Type: pickup" in result

    def test_delivery_type_dead_drop_shown(self):
        order = _make_order(delivery_type="dead_drop")
        items = [_make_item()]
        with _patch_db(order, items):
            from bot.utils.invoice import generate_invoice_text
            result = generate_invoice_text(order_id=1)
        assert "Type: dead_drop" in result

    def test_store_shown_when_present(self):
        mock_store = MagicMock()
        mock_store.name = "Downtown Branch"
        order = _make_order(store_id=5)
        items = [_make_item()]
        with _patch_db(order, items, store=mock_store):
            from bot.utils.invoice import generate_invoice_text
            result = generate_invoice_text(order_id=1)
        assert "Store: Downtown Branch" in result

    def test_store_not_shown_when_no_store_id(self):
        order = _make_order(store_id=None)
        items = [_make_item()]
        with _patch_db(order, items):
            from bot.utils.invoice import generate_invoice_text
            result = generate_invoice_text(order_id=1)
        assert "Store:" not in result

    def test_receipt_header_and_footer(self):
        order = _make_order()
        items = [_make_item()]
        with _patch_db(order, items):
            from bot.utils.invoice import generate_invoice_text
            result = generate_invoice_text(order_id=1)
        assert "RECEIPT / INVOICE" in result
        assert "Thank you for your order!" in result

    def test_empty_items_list(self):
        """Invoice with no items should still generate without error."""
        order = _make_order()
        with _patch_db(order, items=[]):
            from bot.utils.invoice import generate_invoice_text
            result = generate_invoice_text(order_id=1)
        assert "Subtotal: 0" in result
        assert result is not None
