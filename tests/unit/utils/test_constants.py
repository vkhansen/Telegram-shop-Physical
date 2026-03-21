"""Tests for application-wide constants"""
import pytest

from bot.utils.constants import (
    PAYMENT_BITCOIN,
    PAYMENT_CASH,
    PAYMENT_PROMPTPAY,
    DELIVERY_DOOR,
    DELIVERY_DEAD_DROP,
    DELIVERY_PICKUP,
)


@pytest.mark.unit
class TestPaymentConstants:
    """Tests for payment method constants"""

    def test_payment_bitcoin_value(self):
        """PAYMENT_BITCOIN matches the string used in order_handler.py"""
        assert PAYMENT_BITCOIN == "bitcoin"

    def test_payment_cash_value(self):
        """PAYMENT_CASH matches the string used in order_handler.py"""
        assert PAYMENT_CASH == "cash"

    def test_payment_promptpay_value(self):
        """PAYMENT_PROMPTPAY matches the string used in order_handler.py"""
        assert PAYMENT_PROMPTPAY == "promptpay"

    def test_payment_constants_are_strings(self):
        """All payment constants are non-empty strings"""
        for const in (PAYMENT_BITCOIN, PAYMENT_CASH, PAYMENT_PROMPTPAY):
            assert isinstance(const, str)
            assert len(const) > 0

    def test_payment_constants_are_not_none(self):
        """No payment constant is None"""
        assert PAYMENT_BITCOIN is not None
        assert PAYMENT_CASH is not None
        assert PAYMENT_PROMPTPAY is not None

    def test_payment_constants_are_unique(self):
        """All payment constants have distinct values"""
        values = [PAYMENT_BITCOIN, PAYMENT_CASH, PAYMENT_PROMPTPAY]
        assert len(values) == len(set(values))


@pytest.mark.unit
class TestDeliveryConstants:
    """Tests for delivery type constants"""

    def test_delivery_door_value(self):
        """DELIVERY_DOOR matches the string used in order_handler.py"""
        assert DELIVERY_DOOR == "door"

    def test_delivery_dead_drop_value(self):
        """DELIVERY_DEAD_DROP matches the string used in order_handler.py"""
        assert DELIVERY_DEAD_DROP == "dead_drop"

    def test_delivery_pickup_value(self):
        """DELIVERY_PICKUP matches the string used in order_handler.py"""
        assert DELIVERY_PICKUP == "pickup"

    def test_delivery_constants_are_strings(self):
        """All delivery constants are non-empty strings"""
        for const in (DELIVERY_DOOR, DELIVERY_DEAD_DROP, DELIVERY_PICKUP):
            assert isinstance(const, str)
            assert len(const) > 0

    def test_delivery_constants_are_not_none(self):
        """No delivery constant is None"""
        assert DELIVERY_DOOR is not None
        assert DELIVERY_DEAD_DROP is not None
        assert DELIVERY_PICKUP is not None

    def test_delivery_constants_are_unique(self):
        """All delivery constants have distinct values"""
        values = [DELIVERY_DOOR, DELIVERY_DEAD_DROP, DELIVERY_PICKUP]
        assert len(values) == len(set(values))
