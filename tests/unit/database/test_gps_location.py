"""Tests for GPS location fields on Order and CustomerInfo (Card 2)"""
import pytest
from datetime import datetime, timezone
from decimal import Decimal

from bot.database.models.main import Order, CustomerInfo, User


@pytest.mark.unit
@pytest.mark.models
class TestGPSLocationFields:
    """Test GPS location model fields"""

    def test_order_gps_fields_nullable(self, db_with_roles, db_session):
        """GPS fields on Order should be nullable (optional)"""
        user = User(telegram_id=900001, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        order = Order(
            buyer_id=900001,
            total_price=Decimal("100.00"),
            payment_method="cash",
            delivery_address="123 Test St",
            phone_number="0812345678",
            order_status="pending"
        )
        db_session.add(order)
        db_session.commit()

        assert order.latitude is None
        assert order.longitude is None
        assert order.google_maps_link is None

    def test_order_gps_fields_stored(self, db_with_roles, db_session):
        """GPS coordinates and maps link persist on Order"""
        user = User(telegram_id=900002, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        order = Order(
            buyer_id=900002,
            total_price=Decimal("250.00"),
            payment_method="cash",
            delivery_address="456 Soi Sukhumvit",
            phone_number="0898765432",
            order_status="pending",
            latitude=13.7563,
            longitude=100.5018,
            google_maps_link="https://www.google.com/maps?q=13.7563,100.5018"
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        assert order.latitude == pytest.approx(13.7563, abs=0.0001)
        assert order.longitude == pytest.approx(100.5018, abs=0.0001)
        assert order.google_maps_link == "https://www.google.com/maps?q=13.7563,100.5018"

    def test_customer_info_gps_fields(self, db_with_roles, db_session):
        """CustomerInfo stores lat/lng for reuse across orders"""
        user = User(telegram_id=900003, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        customer = CustomerInfo(
            telegram_id=900003,
            phone_number="0812345678",
            delivery_address="789 Bangkok"
        )
        customer.latitude = 13.7400
        customer.longitude = 100.5200
        db_session.add(customer)
        db_session.commit()
        db_session.refresh(customer)

        assert customer.latitude == pytest.approx(13.7400, abs=0.0001)
        assert customer.longitude == pytest.approx(100.5200, abs=0.0001)

    def test_customer_info_gps_nullable(self, db_with_roles, db_session):
        """CustomerInfo GPS fields default to None"""
        user = User(telegram_id=900004, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        customer = CustomerInfo(
            telegram_id=900004,
            phone_number="0812345678",
            delivery_address="Test address"
        )
        db_session.add(customer)
        db_session.commit()

        assert customer.latitude is None
        assert customer.longitude is None

    def test_order_without_location_still_valid(self, db_with_roles, db_session):
        """Order with text address only (no GPS) should be fully valid"""
        user = User(telegram_id=900005, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        order = Order(
            buyer_id=900005,
            total_price=Decimal("150.00"),
            payment_method="cash",
            delivery_address="Text-only address, no GPS",
            phone_number="0898765432",
            order_status="pending"
        )
        db_session.add(order)
        db_session.commit()

        assert order.id is not None
        assert order.latitude is None
        assert order.delivery_address == "Text-only address, no GPS"

    def test_google_maps_link_format(self, db_with_roles, db_session):
        """Google Maps link should be generated correctly from coordinates"""
        lat, lng = 13.7563, 100.5018
        maps_link = f"https://www.google.com/maps?q={lat},{lng}"

        user = User(telegram_id=900006, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        order = Order(
            buyer_id=900006,
            total_price=Decimal("100.00"),
            payment_method="cash",
            delivery_address="Test",
            phone_number="0812345678",
            google_maps_link=maps_link
        )
        db_session.add(order)
        db_session.commit()

        assert "google.com/maps" in order.google_maps_link
        assert "13.7563" in order.google_maps_link
        assert "100.5018" in order.google_maps_link
