"""
Tests for bot/utils/delivery_types.py - needs_delivery_photo() function.
"""
import pytest
from unittest.mock import MagicMock

from bot.utils.delivery_types import needs_delivery_photo


@pytest.mark.unit
class TestNeedsDeliveryPhoto:
    """Tests for needs_delivery_photo() helper"""

    def _make_order(self, delivery_type="door", delivery_photo=None):
        """Create a mock order with the specified fields"""
        order = MagicMock()
        order.delivery_type = delivery_type
        order.delivery_photo = delivery_photo
        return order

    def test_dead_drop_without_photo_needs_photo(self):
        order = self._make_order(delivery_type="dead_drop", delivery_photo=None)
        assert needs_delivery_photo(order) is True

    def test_dead_drop_with_photo_does_not_need_photo(self):
        order = self._make_order(delivery_type="dead_drop", delivery_photo="file_id_123")
        assert needs_delivery_photo(order) is False

    def test_door_delivery_does_not_need_photo(self):
        order = self._make_order(delivery_type="door", delivery_photo=None)
        assert needs_delivery_photo(order) is False

    def test_door_delivery_with_photo_does_not_need_photo(self):
        order = self._make_order(delivery_type="door", delivery_photo="file_id_123")
        assert needs_delivery_photo(order) is False

    def test_pickup_does_not_need_photo(self):
        order = self._make_order(delivery_type="pickup", delivery_photo=None)
        assert needs_delivery_photo(order) is False

    def test_pickup_with_photo_does_not_need_photo(self):
        order = self._make_order(delivery_type="pickup", delivery_photo="file_id_123")
        assert needs_delivery_photo(order) is False

    def test_dead_drop_empty_string_photo_needs_photo(self):
        """Empty string for delivery_photo is falsy, so it should still need photo"""
        order = self._make_order(delivery_type="dead_drop", delivery_photo="")
        assert needs_delivery_photo(order) is True

    def test_unknown_delivery_type_does_not_need_photo(self):
        """Unknown delivery types should not require photo"""
        order = self._make_order(delivery_type="unknown_type", delivery_photo=None)
        assert needs_delivery_photo(order) is False
