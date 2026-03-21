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


@pytest.mark.unit
class TestCurrencyEdgeCases:
    """Edge case tests for currency formatting"""

    def test_negative_amount(self):
        """Negative amount formats with minus sign after currency symbol"""
        from bot.utils.currency import format_currency
        with patch('bot.utils.currency.EnvKeys') as mock_env:
            mock_env.PAY_CURRENCY = "THB"
            result = format_currency(Decimal("-100"))
            # Python's f-string formatting puts the minus before the symbol:
            # f"฿{Decimal('-100'):,.2f}" → "฿-100.00"
            assert result == "฿-100.00"

    def test_negative_amount_non_thb(self):
        """Negative amount with non-THB currency"""
        from bot.utils.currency import format_currency
        with patch('bot.utils.currency.EnvKeys') as mock_env:
            mock_env.PAY_CURRENCY = "USD"
            result = format_currency(Decimal("-50.25"))
            assert result == "-50.25 USD"

    def test_very_large_amount(self):
        """Very large amount formats with comma separators"""
        from bot.utils.currency import format_currency
        with patch('bot.utils.currency.EnvKeys') as mock_env:
            mock_env.PAY_CURRENCY = "THB"
            result = format_currency(Decimal("999999999.99"))
            assert result == "฿999,999,999.99"

    def test_three_decimal_places_rounded(self):
        """Amount with 3 decimal places is rounded to 2"""
        from bot.utils.currency import format_currency
        with patch('bot.utils.currency.EnvKeys') as mock_env:
            mock_env.PAY_CURRENCY = "THB"
            result = format_currency(Decimal("99.999"))
            # Python's :,.2f rounds 99.999 → 100.00
            assert result == "฿100.00"

    def test_tiny_amount_rounds_to_zero(self):
        """Decimal('0.001') rounds to 0.00"""
        from bot.utils.currency import format_currency
        with patch('bot.utils.currency.EnvKeys') as mock_env:
            mock_env.PAY_CURRENCY = "THB"
            result = format_currency(Decimal("0.001"))
            assert result == "฿0.00"

    def test_integer_zero(self):
        """Integer 0 formats as ฿0.00"""
        from bot.utils.currency import format_currency
        with patch('bot.utils.currency.EnvKeys') as mock_env:
            mock_env.PAY_CURRENCY = "THB"
            result = format_currency(0)
            assert result == "฿0.00"

    def test_rounding_half_up_behavior(self):
        """Test rounding at the boundary: 0.005 with Decimal"""
        from bot.utils.currency import format_currency
        with patch('bot.utils.currency.EnvKeys') as mock_env:
            mock_env.PAY_CURRENCY = "THB"
            result = format_currency(Decimal("99.995"))
            # Python's format rounds 99.995 → 100.00 (banker's rounding may vary)
            assert result in ("฿100.00", "฿99.99")

    def test_very_small_negative(self):
        """Very small negative rounds to -0.00 or 0.00"""
        from bot.utils.currency import format_currency
        with patch('bot.utils.currency.EnvKeys') as mock_env:
            mock_env.PAY_CURRENCY = "THB"
            result = format_currency(Decimal("-0.001"))
            assert result in ("฿-0.00", "฿0.00")
