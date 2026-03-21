"""Tests for currency formatting (Card 6)"""
import pytest
from decimal import Decimal
from unittest.mock import patch


@pytest.mark.unit
class TestCurrencyFormatting:
    """Test THB currency formatting"""

    def test_format_thb_basic(self):
        """Basic THB formatting with comma separators"""
        from bot.utils.currency import format_currency
        with patch('bot.utils.currency.EnvKeys') as mock_env:
            mock_env.PAY_CURRENCY = "THB"
            result = format_currency(Decimal("1234.5"))
            assert result == "฿1,234.50"

    def test_format_thb_zero(self):
        """Zero amount formatted correctly"""
        from bot.utils.currency import format_currency
        with patch('bot.utils.currency.EnvKeys') as mock_env:
            mock_env.PAY_CURRENCY = "THB"
            result = format_currency(Decimal("0"))
            assert result == "฿0.00"

    def test_format_thb_large(self):
        """Large amount with multiple comma separators"""
        from bot.utils.currency import format_currency
        with patch('bot.utils.currency.EnvKeys') as mock_env:
            mock_env.PAY_CURRENCY = "THB"
            result = format_currency(Decimal("1000000"))
            assert result == "฿1,000,000.00"

    def test_format_thb_decimal_rounding(self):
        """Always shows exactly two decimal places"""
        from bot.utils.currency import format_currency
        with patch('bot.utils.currency.EnvKeys') as mock_env:
            mock_env.PAY_CURRENCY = "THB"
            assert format_currency(Decimal("99")) == "฿99.00"
            assert format_currency(Decimal("99.1")) == "฿99.10"
            assert format_currency(Decimal("99.99")) == "฿99.99"

    def test_format_thb_small_amount(self):
        """Small amount under 1 baht"""
        from bot.utils.currency import format_currency
        with patch('bot.utils.currency.EnvKeys') as mock_env:
            mock_env.PAY_CURRENCY = "THB"
            result = format_currency(Decimal("0.50"))
            assert result == "฿0.50"

    def test_format_non_thb_currency(self):
        """Non-THB currencies use suffix format"""
        from bot.utils.currency import format_currency
        with patch('bot.utils.currency.EnvKeys') as mock_env:
            mock_env.PAY_CURRENCY = "USD"
            result = format_currency(Decimal("1234.50"))
            assert result == "1,234.50 USD"

    def test_format_accepts_string_input(self):
        """Should handle string-convertible amounts"""
        from bot.utils.currency import format_currency
        with patch('bot.utils.currency.EnvKeys') as mock_env:
            mock_env.PAY_CURRENCY = "THB"
            result = format_currency("450.00")
            assert result == "฿450.00"

    def test_format_accepts_int_input(self):
        """Should handle integer amounts"""
        from bot.utils.currency import format_currency
        with patch('bot.utils.currency.EnvKeys') as mock_env:
            mock_env.PAY_CURRENCY = "THB"
            result = format_currency(450)
            assert result == "฿450.00"
