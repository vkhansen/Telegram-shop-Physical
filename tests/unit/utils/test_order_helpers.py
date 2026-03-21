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
