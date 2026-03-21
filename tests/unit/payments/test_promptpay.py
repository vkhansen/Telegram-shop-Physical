"""Tests for PromptPay QR generation and parsing (Card 1)"""
import pytest
from decimal import Decimal

from bot.payments.promptpay import (
    generate_promptpay_payload,
    _crc16,
    parse_emvco_tlv,
    parse_promptpay_payload,
)


@pytest.mark.unit
class TestPromptPayPayload:
    """Test PromptPay EMVCo payload generation"""

    def test_generate_payload_phone_number(self):
        """Payload generated for phone number ID"""
        payload = generate_promptpay_payload("0812345678", Decimal("100.00"))
        assert payload  # Non-empty
        assert "0066812345678" in payload  # Phone converted to international format
        assert "100" in payload  # Amount included
        assert len(payload) > 50  # Reasonable length

    def test_generate_payload_national_id(self):
        """Payload generated for 13-digit national ID"""
        payload = generate_promptpay_payload("1234567890123", Decimal("250.50"))
        assert payload
        assert "1234567890123" in payload
        assert "250.50" in payload

    def test_payload_contains_thb_currency(self):
        """Payload should contain THB currency code (764)"""
        payload = generate_promptpay_payload("0812345678", Decimal("100"))
        assert "764" in payload

    def test_payload_contains_country_code(self):
        """Payload should contain Thailand country code (TH)"""
        payload = generate_promptpay_payload("0812345678", Decimal("100"))
        assert "TH" in payload

    def test_payload_ends_with_crc(self):
        """Payload should end with 4-char CRC hex"""
        payload = generate_promptpay_payload("0812345678", Decimal("100"))
        # Last 4 chars should be hex CRC
        crc_part = payload[-4:]
        assert all(c in "0123456789ABCDEF" for c in crc_part)

    def test_zero_amount_raises(self):
        """Zero amount should raise ValueError"""
        with pytest.raises(ValueError, match="greater than 0"):
            generate_promptpay_payload("0812345678", Decimal("0"))

    def test_negative_amount_raises(self):
        """Negative amount should raise ValueError"""
        with pytest.raises(ValueError, match="greater than 0"):
            generate_promptpay_payload("0812345678", Decimal("-50"))

    def test_empty_id_raises(self):
        """Empty PromptPay ID should raise ValueError"""
        with pytest.raises(ValueError, match="required"):
            generate_promptpay_payload("", Decimal("100"))

    def test_invalid_id_length_raises(self):
        """Invalid ID length should raise ValueError"""
        with pytest.raises(ValueError, match="Invalid PromptPay ID"):
            generate_promptpay_payload("12345", Decimal("100"))

    def test_phone_with_dashes(self):
        """Phone number with dashes should work"""
        payload = generate_promptpay_payload("081-234-5678", Decimal("100"))
        assert "0066812345678" in payload

    def test_different_amounts_different_payloads(self):
        """Different amounts should produce different payloads"""
        p1 = generate_promptpay_payload("0812345678", Decimal("100"))
        p2 = generate_promptpay_payload("0812345678", Decimal("200"))
        assert p1 != p2

    def test_crc16_known_value(self):
        """CRC-16 should produce consistent results"""
        result = _crc16("test")
        assert isinstance(result, int)
        assert 0 <= result <= 0xFFFF
        # Same input always gives same output
        assert _crc16("test") == _crc16("test")


@pytest.mark.unit
class TestPromptPayQRGeneration:
    """Test QR code image generation"""

    def test_generate_qr_image(self):
        """Should generate valid PNG bytes"""
        try:
            from bot.payments.promptpay import generate_promptpay_qr
            qr_bytes = generate_promptpay_qr("0812345678", Decimal("450.00"))
            assert isinstance(qr_bytes, bytes)
            assert len(qr_bytes) > 100  # Non-trivial image
            # PNG magic bytes
            assert qr_bytes[:4] == b'\x89PNG'
        except ImportError:
            pytest.skip("qrcode library not installed")

    def test_generate_qr_invalid_amount(self):
        """QR generation with invalid amount should raise"""
        try:
            from bot.payments.promptpay import generate_promptpay_qr
            with pytest.raises(ValueError):
                generate_promptpay_qr("0812345678", Decimal("0"))
        except ImportError:
            pytest.skip("qrcode library not installed")


@pytest.mark.unit
@pytest.mark.models
class TestPromptPayOrderFields:
    """Test PromptPay-related Order model fields"""

    def test_order_payment_receipt_fields_nullable(self, db_with_roles, db_session):
        """Payment receipt fields should default to None"""
        from bot.database.models.main import Order, User
        from datetime import datetime, timezone

        user = User(telegram_id=700001, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        order = Order(
            buyer_id=700001,
            total_price=Decimal("100.00"),
            payment_method="promptpay",
            delivery_address="Test",
            phone_number="0812345678"
        )
        db_session.add(order)
        db_session.commit()

        assert order.payment_receipt_photo is None
        assert order.payment_verified_by is None
        assert order.payment_verified_at is None

    def test_order_promptpay_payment_method(self, db_with_roles, db_session):
        """Order with promptpay payment method persists"""
        from bot.database.models.main import Order, User
        from datetime import datetime, timezone

        user = User(telegram_id=700002, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        order = Order(
            buyer_id=700002,
            total_price=Decimal("450.00"),
            payment_method="promptpay",
            delivery_address="Bangkok",
            phone_number="0898765432"
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        assert order.payment_method == "promptpay"

    def test_save_receipt_photo(self, db_with_roles, db_session):
        """Can save receipt photo file_id to order"""
        from bot.database.models.main import Order, User
        from datetime import datetime, timezone

        user = User(telegram_id=700003, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        order = Order(
            buyer_id=700003,
            total_price=Decimal("300.00"),
            payment_method="promptpay",
            delivery_address="Test",
            phone_number="0812345678"
        )
        db_session.add(order)
        db_session.commit()

        order.payment_receipt_photo = "AgACAgIAAxk_receipt_file_id"
        db_session.commit()
        db_session.refresh(order)

        assert order.payment_receipt_photo == "AgACAgIAAxk_receipt_file_id"

    def test_verify_payment(self, db_with_roles, db_session):
        """Can mark payment as verified with admin ID and timestamp"""
        from bot.database.models.main import Order, User
        from datetime import datetime, timezone

        user = User(telegram_id=700004, registration_date=datetime.now(timezone.utc))
        admin = User(telegram_id=700005, registration_date=datetime.now(timezone.utc), role_id=2)
        db_session.add_all([user, admin])
        db_session.commit()

        order = Order(
            buyer_id=700004,
            total_price=Decimal("500.00"),
            payment_method="promptpay",
            delivery_address="Test",
            phone_number="0812345678",
            order_status="reserved"
        )
        db_session.add(order)
        db_session.commit()

        # Simulate admin verification
        now = datetime.now(timezone.utc)
        order.payment_receipt_photo = "AgACAgIAAxk_receipt"
        order.payment_verified_by = 700005
        order.payment_verified_at = now
        order.order_status = "confirmed"
        db_session.commit()
        db_session.refresh(order)

        assert order.payment_verified_by == 700005
        assert order.payment_verified_at is not None
        assert order.order_status == "confirmed"


@pytest.mark.unit
class TestPromptPayPayloadEdgeCases:
    """Edge-case tests for PromptPay payload generation."""

    def test_very_small_amount(self):
        """Smallest practical amount (0.01 THB) should generate valid payload."""
        payload = generate_promptpay_payload("0812345678", Decimal("0.01"))
        assert payload
        assert "0.01" in payload

    def test_very_large_amount(self):
        """Large amount (999999.99 THB) should generate valid payload."""
        payload = generate_promptpay_payload("0812345678", Decimal("999999.99"))
        assert payload
        assert "999999.99" in payload

    def test_amount_with_extra_decimals(self):
        """Amount with 3+ decimal places should still produce a payload."""
        payload = generate_promptpay_payload("0812345678", Decimal("100.555"))
        assert payload
        assert "100.555" in payload

    def test_phone_with_spaces(self):
        """Phone number with spaces should be cleaned and accepted."""
        payload = generate_promptpay_payload("081 234 5678", Decimal("100"))
        assert "0066812345678" in payload

    def test_phone_already_international_format_wrong_length(self):
        """Phone in international format without leading 0 (11 digits) should raise."""
        with pytest.raises(ValueError, match="Invalid PromptPay ID"):
            generate_promptpay_payload("66812345678", Decimal("100"))

    def test_id_with_12_digits_raises(self):
        """12-digit ID (neither 10 nor 13) should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid PromptPay ID"):
            generate_promptpay_payload("123456789012", Decimal("100"))

    def test_none_promptpay_id_raises(self):
        """None as promptpay_id should raise an error."""
        with pytest.raises((ValueError, TypeError, AttributeError)):
            generate_promptpay_payload(None, Decimal("100"))

    def test_crc16_empty_string(self):
        """CRC16 of empty string should return the initial value (0xFFFF)."""
        result = _crc16("")
        assert isinstance(result, int)
        assert result == 0xFFFF  # No bytes processed, initial CRC unchanged

    def test_crc16_long_string(self):
        """CRC16 of a 100+ character string should return valid 16-bit value."""
        long_input = "A" * 150
        result = _crc16(long_input)
        assert isinstance(result, int)
        assert 0 <= result <= 0xFFFF

    def test_two_identical_payloads_deterministic(self):
        """Same inputs must produce identical payloads (deterministic)."""
        p1 = generate_promptpay_payload("0812345678", Decimal("250.00"))
        p2 = generate_promptpay_payload("0812345678", Decimal("250.00"))
        assert p1 == p2


@pytest.mark.unit
class TestEMVCoTLVParser:
    """Test EMVCo TLV payload parsing."""

    def test_parse_simple_tlv(self):
        """Parse a simple TLV string."""
        # tag=00, length=02, value="01"
        result = parse_emvco_tlv("000201")
        assert result["00"] == "01"

    def test_parse_multiple_tags(self):
        """Parse multiple TLV fields."""
        # 00:02:"01" + 01:02:"11" + 58:02:"TH"
        result = parse_emvco_tlv("00020101021158025448")
        assert result["00"] == "01"
        assert result["01"] == "11"

    def test_parse_empty_string(self):
        result = parse_emvco_tlv("")
        assert result == {}

    def test_parse_truncated_data(self):
        """Gracefully handle truncated payload."""
        # tag=00, length=05, but only 2 chars of value
        result = parse_emvco_tlv("000501")
        assert result == {}


@pytest.mark.unit
class TestPromptPayPayloadParsing:
    """Test round-trip: generate → parse PromptPay payloads."""

    def test_roundtrip_phone_number(self):
        """Generate payload with phone, parse it back, get same phone."""
        payload = generate_promptpay_payload("0812345678", Decimal("450.00"))
        info = parse_promptpay_payload(payload)

        assert info.promptpay_id == "0812345678"
        assert info.id_type == "phone"
        assert info.amount == Decimal("450.00")
        assert info.country_code == "TH"
        assert info.currency_code == "764"

    def test_roundtrip_national_id(self):
        """Generate payload with national ID, parse it back."""
        payload = generate_promptpay_payload("1234567890123", Decimal("100"))
        info = parse_promptpay_payload(payload)

        assert info.promptpay_id == "1234567890123"
        assert info.id_type == "national_id"
        assert info.amount == Decimal("100")

    def test_roundtrip_various_amounts(self):
        """Different amounts should round-trip correctly."""
        for amount_str in ("1", "50.50", "9999.99", "0.01"):
            amount = Decimal(amount_str)
            payload = generate_promptpay_payload("0898765432", amount)
            info = parse_promptpay_payload(payload)
            assert info.amount == amount

    def test_parse_invalid_short_payload(self):
        with pytest.raises(ValueError, match="too short"):
            parse_promptpay_payload("0002")

    def test_parse_no_merchant_info(self):
        """Payload without tag 29 should raise."""
        # Valid TLV but no tag 29/30
        with pytest.raises(ValueError, match="merchant"):
            parse_promptpay_payload("000201010211530376458025448" + "6304" + "0000")

    def test_parse_empty_payload(self):
        with pytest.raises(ValueError):
            parse_promptpay_payload("")

    def test_parse_none_payload(self):
        with pytest.raises(ValueError):
            parse_promptpay_payload(None)
