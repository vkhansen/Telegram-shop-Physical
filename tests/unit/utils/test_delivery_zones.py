"""Tests for delivery zone pricing and time slots (Card 10)"""
import pytest
from decimal import Decimal

from bot.config.delivery_zones import (
    calculate_distance, get_delivery_zone, get_available_time_slots,
    DEFAULT_TIME_SLOTS
)


@pytest.mark.unit
class TestHaversineDistance:
    """Test distance calculation"""

    def test_same_point_zero_distance(self):
        """Same coordinates should give 0 distance"""
        d = calculate_distance(13.7563, 100.5018, 13.7563, 100.5018)
        assert d == pytest.approx(0.0, abs=0.001)

    def test_known_distance_bangkok(self):
        """Known distance: Siam to Asok ~3km"""
        # Siam: 13.7462, 100.5347  Asok: 13.7373, 100.5601
        d = calculate_distance(13.7462, 100.5347, 13.7373, 100.5601)
        assert 2.0 < d < 4.0  # Roughly 2.9km

    def test_long_distance(self):
        """Bangkok to Chiang Mai ~600km"""
        d = calculate_distance(13.7563, 100.5018, 18.7883, 98.9853)
        assert 550 < d < 700


@pytest.mark.unit
class TestGetDeliveryZone:
    """Test zone detection"""

    def test_zone_central(self):
        """1km from restaurant → Zone 1, fee=0"""
        # Very close to default restaurant location
        zone = get_delivery_zone(13.757, 100.502, 13.7563, 100.5018)
        assert zone is not None
        assert zone["fee"] == Decimal("0")
        assert "Zone 1" in zone["name"]

    def test_zone_inner(self):
        """~5km from restaurant → Zone 2"""
        # Roughly 5km away
        zone = get_delivery_zone(13.72, 100.55, 13.7563, 100.5018)
        assert zone is not None
        assert zone["fee"] == Decimal("30")

    def test_zone_far(self):
        """25km+ from restaurant → Zone 5"""
        zone = get_delivery_zone(13.95, 100.7, 13.7563, 100.5018)
        assert zone is not None
        assert zone["fee"] == Decimal("120")

    def test_zone_no_gps(self):
        """No GPS coordinates → None"""
        assert get_delivery_zone(None, None) is None
        assert get_delivery_zone(None, 100.5) is None
        assert get_delivery_zone(13.7, None) is None


@pytest.mark.unit
class TestTimeSlots:
    """Test time slot management"""

    def test_default_slots_count(self):
        """All 8 default time slots present"""
        assert len(DEFAULT_TIME_SLOTS) == 8

    def test_all_slots_available(self):
        """All default slots are available"""
        available = get_available_time_slots()
        assert len(available) == 8

    def test_asap_slot_exists(self):
        """ASAP slot should be available"""
        slots = get_available_time_slots()
        asap = [s for s in slots if s["id"] == "asap"]
        assert len(asap) == 1
        assert asap[0]["label"] == "ASAP"


@pytest.mark.unit
@pytest.mark.models
class TestDeliveryZoneOrderFields:
    """Test delivery zone/time slot Order model fields"""

    def test_order_zone_and_fee_fields(self, db_with_roles, db_session):
        """Order stores zone, fee, and time slot"""
        from bot.database.models.main import Order, User
        from datetime import datetime, timezone

        user = User(telegram_id=300001, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        order = Order(
            buyer_id=300001, total_price=Decimal("200.00"),
            payment_method="cash", delivery_address="Test",
            phone_number="0812345678"
        )
        order.delivery_zone = "Zone 2 - Inner"
        order.delivery_fee = Decimal("30.00")
        order.preferred_time_slot = "dinner_peak"
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        assert order.delivery_zone == "Zone 2 - Inner"
        assert order.delivery_fee == Decimal("30.00")
        assert order.preferred_time_slot == "dinner_peak"

    def test_order_zone_fields_nullable(self, db_with_roles, db_session):
        """Zone fields default to None"""
        from bot.database.models.main import Order, User
        from datetime import datetime, timezone

        user = User(telegram_id=300002, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        order = Order(
            buyer_id=300002, total_price=Decimal("100.00"),
            payment_method="cash", delivery_address="Test",
            phone_number="0812345678"
        )
        db_session.add(order)
        db_session.commit()

        assert order.delivery_zone is None
        assert order.preferred_time_slot is None
