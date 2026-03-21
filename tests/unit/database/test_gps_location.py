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


@pytest.mark.unit
@pytest.mark.models
class TestGPSEdgeCases:
    """Edge case tests for GPS coordinate storage"""

    def test_zero_coordinates_gulf_of_guinea(self, db_with_roles, db_session):
        """Zero coordinates (0.0, 0.0) are valid — Gulf of Guinea"""
        user = User(telegram_id=910001, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        order = Order(
            buyer_id=910001,
            total_price=Decimal("50.00"),
            payment_method="cash",
            delivery_address="Gulf of Guinea",
            phone_number="0812345678",
            latitude=0.0,
            longitude=0.0,
            google_maps_link="https://www.google.com/maps?q=0.0,0.0"
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        assert order.latitude == pytest.approx(0.0)
        assert order.longitude == pytest.approx(0.0)

    def test_negative_coordinates_sydney(self, db_with_roles, db_session):
        """Negative latitude (Southern hemisphere) — Sydney, Australia"""
        user = User(telegram_id=910002, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        order = Order(
            buyer_id=910002,
            total_price=Decimal("75.00"),
            payment_method="cash",
            delivery_address="Sydney, Australia",
            phone_number="0812345678",
            latitude=-33.8688,
            longitude=151.2093,
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        assert order.latitude == pytest.approx(-33.8688, abs=0.0001)
        assert order.longitude == pytest.approx(151.2093, abs=0.0001)

    def test_extreme_latitude_north_pole(self, db_with_roles, db_session):
        """Extreme latitude boundary: North Pole (90.0)"""
        user = User(telegram_id=910003, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        order = Order(
            buyer_id=910003,
            total_price=Decimal("100.00"),
            payment_method="cash",
            delivery_address="North Pole",
            phone_number="0812345678",
            latitude=90.0,
            longitude=0.0,
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        assert order.latitude == pytest.approx(90.0)

    def test_extreme_latitude_south_pole(self, db_with_roles, db_session):
        """Extreme latitude boundary: South Pole (-90.0)"""
        user = User(telegram_id=910004, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        order = Order(
            buyer_id=910004,
            total_price=Decimal("100.00"),
            payment_method="cash",
            delivery_address="South Pole",
            phone_number="0812345678",
            latitude=-90.0,
            longitude=0.0,
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        assert order.latitude == pytest.approx(-90.0)

    def test_extreme_longitude_positive_180(self, db_with_roles, db_session):
        """Extreme longitude boundary: +180.0 (International Date Line)"""
        user = User(telegram_id=910005, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        order = Order(
            buyer_id=910005,
            total_price=Decimal("100.00"),
            payment_method="cash",
            delivery_address="Date Line East",
            phone_number="0812345678",
            latitude=0.0,
            longitude=180.0,
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        assert order.longitude == pytest.approx(180.0)

    def test_extreme_longitude_negative_180(self, db_with_roles, db_session):
        """Extreme longitude boundary: -180.0 (International Date Line)"""
        user = User(telegram_id=910006, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        order = Order(
            buyer_id=910006,
            total_price=Decimal("100.00"),
            payment_method="cash",
            delivery_address="Date Line West",
            phone_number="0812345678",
            latitude=0.0,
            longitude=-180.0,
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        assert order.longitude == pytest.approx(-180.0)

    def test_partial_coordinates_latitude_only(self, db_with_roles, db_session):
        """Latitude set but longitude is None — both stored independently"""
        user = User(telegram_id=910007, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        order = Order(
            buyer_id=910007,
            total_price=Decimal("100.00"),
            payment_method="cash",
            delivery_address="Partial coords",
            phone_number="0812345678",
            latitude=13.7563,
            longitude=None,
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        assert order.latitude == pytest.approx(13.7563, abs=0.0001)
        assert order.longitude is None

    def test_update_gps_from_none_to_coordinates(self, db_with_roles, db_session):
        """Update GPS: initially None, then update to coordinates"""
        user = User(telegram_id=910008, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        customer = CustomerInfo(
            telegram_id=910008,
            phone_number="0812345678",
            delivery_address="Initial no GPS"
        )
        db_session.add(customer)
        db_session.commit()

        assert customer.latitude is None
        assert customer.longitude is None

        # Update with GPS coordinates
        customer.latitude = 13.7563
        customer.longitude = 100.5018
        db_session.commit()
        db_session.refresh(customer)

        assert customer.latitude == pytest.approx(13.7563, abs=0.0001)
        assert customer.longitude == pytest.approx(100.5018, abs=0.0001)

    def test_order_with_gps_but_no_text_address(self, db_with_roles, db_session):
        """Order with GPS but delivery_address set to 'pickup' — still valid"""
        user = User(telegram_id=910009, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        order = Order(
            buyer_id=910009,
            total_price=Decimal("100.00"),
            payment_method="cash",
            delivery_address="pickup",
            phone_number="0812345678",
            latitude=13.7563,
            longitude=100.5018,
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        assert order.id is not None
        assert order.delivery_address == "pickup"
        assert order.latitude == pytest.approx(13.7563, abs=0.0001)
        assert order.longitude == pytest.approx(100.5018, abs=0.0001)
