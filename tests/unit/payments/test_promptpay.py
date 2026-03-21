"""Tests for PromptPay QR generation (Card 1)"""
import pytest
from decimal import Decimal

from bot.payments.promptpay import generate_promptpay_payload, _crc16


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
