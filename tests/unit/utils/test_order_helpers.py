"""Tests for order helper utilities"""
import pytest
from unittest.mock import patch


@pytest.mark.unit
class TestBuildGoogleMapsLink:
    """Tests for build_google_maps_link()"""

    def test_both_coords_provided(self):
        """Both coordinates provided returns correct URL"""
        from bot.utils.order_helpers import build_google_maps_link
        result = build_google_maps_link(13.7563, 100.5018)
        assert result == "https://www.google.com/maps?q=13.7563,100.5018"

    def test_latitude_none(self):
        """Latitude is None returns None"""
        from bot.utils.order_helpers import build_google_maps_link
        result = build_google_maps_link(None, 100.5018)
        assert result is None

    def test_longitude_none(self):
        """Longitude is None returns None"""
        from bot.utils.order_helpers import build_google_maps_link
        result = build_google_maps_link(13.7563, None)
        assert result is None

    def test_both_none(self):
        """Both coordinates None returns None"""
        from bot.utils.order_helpers import build_google_maps_link
        result = build_google_maps_link(None, None)
        assert result is None

    def test_zero_coordinates(self):
        """Zero coordinates (0.0, 0.0) return a valid URL"""
        from bot.utils.order_helpers import build_google_maps_link
        result = build_google_maps_link(0.0, 0.0)
        assert result == "https://www.google.com/maps?q=0.0,0.0"

    def test_negative_coordinates(self):
        """Negative coordinates return a valid URL"""
        from bot.utils.order_helpers import build_google_maps_link
        result = build_google_maps_link(-33.8688, -151.2093)
        assert result == "https://www.google.com/maps?q=-33.8688,-151.2093"

    def test_very_precise_coordinates(self):
        """Very precise coordinates are formatted correctly"""
        from bot.utils.order_helpers import build_google_maps_link
        result = build_google_maps_link(13.756331, 100.501765)
        assert result == "https://www.google.com/maps?q=13.756331,100.501765"

    def test_integer_coordinates(self):
        """Integer coordinates produce a valid URL"""
        from bot.utils.order_helpers import build_google_maps_link
        result = build_google_maps_link(13, 100)
        assert result == "https://www.google.com/maps?q=13,100"


@pytest.mark.unit
class TestFormatItemsSummary:
    """Tests for format_items_summary()"""

    def test_normal_cart_items(self):
        """Normal cart items produce formatted strings with currency"""
        from bot.utils.order_helpers import format_items_summary
        cart_items = [
            {'item_name': 'Widget', 'quantity': 2, 'total': 500},
            {'item_name': 'Gadget', 'quantity': 1, 'total': 300},
        ]
        with patch('bot.utils.order_helpers.EnvKeys') as mock_env:
            mock_env.PAY_CURRENCY = "THB"
            result = format_items_summary(cart_items)

        assert len(result) == 2
        assert result[0] == "Widget x2 = 500 THB"
        assert result[1] == "Gadget x1 = 300 THB"

    def test_empty_list(self):
        """Empty cart returns empty list"""
        from bot.utils.order_helpers import format_items_summary
        with patch('bot.utils.order_helpers.EnvKeys') as mock_env:
            mock_env.PAY_CURRENCY = "THB"
            result = format_items_summary([])

        assert result == []

    def test_single_item(self):
        """Single item returns single formatted string"""
        from bot.utils.order_helpers import format_items_summary
        cart_items = [
            {'item_name': 'Phone Case', 'quantity': 1, 'total': 150},
        ]
        with patch('bot.utils.order_helpers.EnvKeys') as mock_env:
            mock_env.PAY_CURRENCY = "USD"
            result = format_items_summary(cart_items)

        assert len(result) == 1
        assert result[0] == "Phone Case x1 = 150 USD"

    def test_item_with_quantity_greater_than_one(self):
        """Item with quantity > 1 formats correctly"""
        from bot.utils.order_helpers import format_items_summary
        cart_items = [
            {'item_name': 'Sticker Pack', 'quantity': 5, 'total': 250},
        ]
        with patch('bot.utils.order_helpers.EnvKeys') as mock_env:
            mock_env.PAY_CURRENCY = "THB"
            result = format_items_summary(cart_items)

        assert result[0] == "Sticker Pack x5 = 250 THB"

    def test_uses_pay_currency_from_env(self):
        """Items use PAY_CURRENCY from EnvKeys"""
        from bot.utils.order_helpers import format_items_summary
        cart_items = [
            {'item_name': 'Item', 'quantity': 1, 'total': 100},
        ]
        with patch('bot.utils.order_helpers.EnvKeys') as mock_env:
            mock_env.PAY_CURRENCY = "BTC"
            result = format_items_summary(cart_items)

        assert "BTC" in result[0]
        assert "THB" not in result[0]

    def test_decimal_total(self):
        """Items with decimal totals format correctly"""
        from bot.utils.order_helpers import format_items_summary
        cart_items = [
            {'item_name': 'Charm', 'quantity': 3, 'total': 149.99},
        ]
        with patch('bot.utils.order_helpers.EnvKeys') as mock_env:
            mock_env.PAY_CURRENCY = "THB"
            result = format_items_summary(cart_items)

        assert result[0] == "Charm x3 = 149.99 THB"


@pytest.mark.unit
class TestExtractDeliveryFields:
    """Tests for extract_delivery_fields()."""

    def test_defaults_when_empty_dict(self):
        from bot.utils.order_helpers import extract_delivery_fields
        result = extract_delivery_fields({})
        assert result["delivery_type"] == "door"
        assert result["drop_instructions"] is None
        assert result["drop_latitude"] is None
        assert result["drop_longitude"] is None
        assert result["drop_media"] is None

    def test_uses_provided_delivery_type(self):
        from bot.utils.order_helpers import extract_delivery_fields
        result = extract_delivery_fields({"delivery_type": "dead_drop"})
        assert result["delivery_type"] == "dead_drop"

    def test_pickup_type(self):
        from bot.utils.order_helpers import extract_delivery_fields
        result = extract_delivery_fields({"delivery_type": "pickup"})
        assert result["delivery_type"] == "pickup"

    def test_drop_fields_populated(self):
        from bot.utils.order_helpers import extract_delivery_fields
        data = {
            "delivery_type": "dead_drop",
            "drop_instructions": "Behind the bench",
            "drop_latitude": 13.75,
            "drop_longitude": 100.50,
            "drop_media": ["file_id_1"],
        }
        result = extract_delivery_fields(data)
        assert result["drop_instructions"] == "Behind the bench"
        assert result["drop_latitude"] == 13.75
        assert result["drop_longitude"] == 100.50
        assert result["drop_media"] == ["file_id_1"]

    def test_extra_keys_ignored(self):
        from bot.utils.order_helpers import extract_delivery_fields
        result = extract_delivery_fields({"delivery_type": "door", "unrelated": "value"})
        assert "unrelated" not in result


@pytest.mark.unit
class TestCreateOrderFromCustomer:
    """Tests for create_order_from_customer()."""

    def _make_customer_info(self, lat=None, lon=None):
        from unittest.mock import MagicMock
        ci = MagicMock()
        ci.delivery_address = "123 Test St"
        ci.phone_number = "+66812345678"
        ci.delivery_note = "Leave at door"
        ci.latitude = lat
        ci.longitude = lon
        return ci

    def test_creates_order_with_correct_fields(self, db_session, test_user):
        from decimal import Decimal
        from bot.utils.order_helpers import create_order_from_customer

        ci = self._make_customer_info()
        order = create_order_from_customer(
            session=db_session,
            user_id=test_user.telegram_id,
            customer_info=ci,
            payment_method="cash",
            total_amount=Decimal("250.00"),
        )

        assert order.buyer_id == test_user.telegram_id
        assert order.total_price == Decimal("250.00")
        assert order.payment_method == "cash"
        assert order.order_status == "pending"

    def test_order_code_is_six_uppercase(self, db_session, test_user):
        from decimal import Decimal
        from bot.utils.order_helpers import create_order_from_customer

        ci = self._make_customer_info()
        order = create_order_from_customer(
            session=db_session,
            user_id=test_user.telegram_id,
            customer_info=ci,
            payment_method="cash",
            total_amount=Decimal("100"),
        )
        assert len(order.order_code) == 6
        assert order.order_code.isupper()

    def test_google_maps_link_generated_with_coords(self, db_session, test_user):
        from decimal import Decimal
        from bot.utils.order_helpers import create_order_from_customer

        ci = self._make_customer_info(lat=13.75, lon=100.50)
        order = create_order_from_customer(
            session=db_session,
            user_id=test_user.telegram_id,
            customer_info=ci,
            payment_method="cash",
            total_amount=Decimal("100"),
        )
        assert order.google_maps_link is not None
        assert "13.75" in order.google_maps_link

    def test_no_coords_gives_no_maps_link(self, db_session, test_user):
        from decimal import Decimal
        from bot.utils.order_helpers import create_order_from_customer

        ci = self._make_customer_info(lat=None, lon=None)
        order = create_order_from_customer(
            session=db_session,
            user_id=test_user.telegram_id,
            customer_info=ci,
            payment_method="cash",
            total_amount=Decimal("100"),
        )
        assert order.google_maps_link is None

    def test_bonus_applied(self, db_session, test_user):
        from decimal import Decimal
        from bot.utils.order_helpers import create_order_from_customer

        ci = self._make_customer_info()
        order = create_order_from_customer(
            session=db_session,
            user_id=test_user.telegram_id,
            customer_info=ci,
            payment_method="cash",
            total_amount=Decimal("200"),
            bonus_applied=Decimal("50"),
        )
        assert order.bonus_applied == Decimal("50")

    def test_delivery_type_stored(self, db_session, test_user):
        from decimal import Decimal
        from bot.utils.order_helpers import create_order_from_customer

        ci = self._make_customer_info()
        order = create_order_from_customer(
            session=db_session,
            user_id=test_user.telegram_id,
            customer_info=ci,
            payment_method="cash",
            total_amount=Decimal("100"),
            delivery_type="dead_drop",
            drop_instructions="under the bridge",
        )
        assert order.delivery_type == "dead_drop"
        assert order.drop_instructions == "under the bridge"


@pytest.mark.unit
class TestCreateOrderItems:
    """Tests for create_order_items()."""

    def _cart(self):
        return [
            {'item_name': 'Widget', 'quantity': 2, 'price': '50.00', 'total': '100.00',
             'selected_modifiers': None},
            {'item_name': 'Gadget', 'quantity': 1, 'price': '75.00', 'total': '75.00',
             'selected_modifiers': {'size': 'large'}},
        ]

    def test_returns_correct_summary_count(self, db_session, test_order):
        from bot.utils.order_helpers import create_order_items
        with patch('bot.utils.order_helpers.EnvKeys') as mock_env:
            mock_env.PAY_CURRENCY = "THB"
            summary, to_reserve = create_order_items(
                db_session, test_order.id, self._cart()
            )
        assert len(summary) == 2

    def test_summary_strings_contain_item_name(self, db_session, test_order):
        from bot.utils.order_helpers import create_order_items
        with patch('bot.utils.order_helpers.EnvKeys') as mock_env:
            mock_env.PAY_CURRENCY = "THB"
            summary, _ = create_order_items(db_session, test_order.id, self._cart())
        assert any("Widget" in s for s in summary)
        assert any("Gadget" in s for s in summary)

    def test_reserve_list_has_name_and_qty(self, db_session, test_order):
        from bot.utils.order_helpers import create_order_items
        with patch('bot.utils.order_helpers.EnvKeys') as mock_env:
            mock_env.PAY_CURRENCY = "THB"
            _, to_reserve = create_order_items(db_session, test_order.id, self._cart())
        assert {'item_name': 'Widget', 'quantity': 2} in to_reserve
        assert {'item_name': 'Gadget', 'quantity': 1} in to_reserve

    def test_empty_cart_returns_empty_lists(self, db_session, test_order):
        from bot.utils.order_helpers import create_order_items
        summary, to_reserve = create_order_items(db_session, test_order.id, [])
        assert summary == []
        assert to_reserve == []
