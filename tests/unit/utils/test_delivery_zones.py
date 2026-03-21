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


@pytest.mark.unit
class TestHaversineEdgeCases:
    """Edge-case tests for Haversine distance calculation."""

    def test_negative_coordinates_southern_hemisphere(self):
        """Negative latitude (southern hemisphere) should work correctly."""
        # Sydney: -33.8688, 151.2093  Melbourne: -37.8136, 144.9631
        d = calculate_distance(-33.8688, 151.2093, -37.8136, 144.9631)
        assert 700 < d < 900  # ~714 km straight line

    def test_negative_coordinates_western_hemisphere(self):
        """Negative longitude (western hemisphere) should work correctly."""
        # New York: 40.7128, -74.0060  Los Angeles: 34.0522, -118.2437
        d = calculate_distance(40.7128, -74.0060, 34.0522, -118.2437)
        assert 3900 < d < 4000  # ~3944 km

    def test_large_distance_equator_to_pole(self):
        """Distance from equator (0,0) to near north pole (90,0)."""
        d = calculate_distance(0, 0, 90, 0)
        # Quarter of Earth circumference ≈ 10018 km
        assert 10000 < d < 10050

    def test_very_close_points(self):
        """Two points < 0.1 km apart should return small positive distance."""
        # Shift by ~0.0005 degrees ≈ ~55 meters
        d = calculate_distance(13.7563, 100.5018, 13.7568, 100.5018)
        assert 0 < d < 0.1

    def test_same_latitude_different_longitude(self):
        """Points on same latitude but different longitude."""
        d = calculate_distance(13.7563, 100.0, 13.7563, 101.0)
        assert d > 0
        # 1 degree of longitude at lat ~13.76 ≈ ~108 km
        assert 100 < d < 115

    def test_same_longitude_different_latitude(self):
        """Points on same longitude but different latitude."""
        d = calculate_distance(13.0, 100.5018, 14.0, 100.5018)
        assert d > 0
        # 1 degree of latitude ≈ 111 km
        assert 110 < d < 112


@pytest.mark.unit
class TestZoneBoundaryConditions:
    """Edge-case tests for delivery zone boundary logic."""

    def test_distance_exactly_at_zone1_boundary(self):
        """Distance just under 3.0 km should be Zone 1 (max_km=3, uses <=)."""
        rest_lat, rest_lon = 10.0, 100.0
        # 1 degree latitude = ~111.195 km; use 2.99 km to stay within boundary
        lat_offset = 2.99 / 111.195
        zone = get_delivery_zone(rest_lat + lat_offset, rest_lon, rest_lat, rest_lon)
        d = calculate_distance(rest_lat + lat_offset, rest_lon, rest_lat, rest_lon)
        assert d < 3.0
        assert "Zone 1" in zone["name"]

    def test_distance_just_over_zone1_boundary(self):
        """Distance just over 3.0 km should be Zone 2."""
        rest_lat, rest_lon = 10.0, 100.0
        lat_offset = 3.02 / 111.195
        zone = get_delivery_zone(rest_lat + lat_offset, rest_lon, rest_lat, rest_lon)
        d = calculate_distance(rest_lat + lat_offset, rest_lon, rest_lat, rest_lon)
        assert d > 3.0
        assert "Zone 2" in zone["name"]

    def test_distance_exactly_at_zone2_boundary_7km(self):
        """Distance just under 7.0 km should be Zone 2."""
        rest_lat, rest_lon = 10.0, 100.0
        lat_offset = 6.99 / 111.195
        zone = get_delivery_zone(rest_lat + lat_offset, rest_lon, rest_lat, rest_lon)
        d = calculate_distance(rest_lat + lat_offset, rest_lon, rest_lat, rest_lon)
        assert d < 7.0
        assert "Zone 2" in zone["name"]

    def test_distance_exactly_at_zone3_boundary_12km(self):
        """Distance just under 12.0 km should be Zone 3."""
        rest_lat, rest_lon = 10.0, 100.0
        lat_offset = 11.99 / 111.195
        zone = get_delivery_zone(rest_lat + lat_offset, rest_lon, rest_lat, rest_lon)
        d = calculate_distance(rest_lat + lat_offset, rest_lon, rest_lat, rest_lon)
        assert d < 12.0
        assert "Zone 3" in zone["name"]

    def test_distance_exactly_at_zone4_boundary_20km(self):
        """Distance just under 20.0 km should be Zone 4."""
        rest_lat, rest_lon = 10.0, 100.0
        lat_offset = 19.99 / 111.195
        zone = get_delivery_zone(rest_lat + lat_offset, rest_lon, rest_lat, rest_lon)
        d = calculate_distance(rest_lat + lat_offset, rest_lon, rest_lat, rest_lon)
        assert d < 20.0
        assert "Zone 4" in zone["name"]

    def test_distance_zero_at_restaurant(self):
        """Distance = 0 (same coords as restaurant) → Zone 1."""
        zone = get_delivery_zone(13.7563, 100.5018, 13.7563, 100.5018)
        assert zone is not None
        assert "Zone 1" in zone["name"]
        assert zone["fee"] == Decimal("0")

    def test_very_large_distance_still_zone5(self):
        """Distance > 99 km should still return Zone 5 (last zone fallback)."""
        # ~500 km away — exceeds all zone max_km, fallback returns last zone
        zone = get_delivery_zone(18.0, 100.5018, 13.7563, 100.5018)
        d = calculate_distance(18.0, 100.5018, 13.7563, 100.5018)
        assert d > 99
        assert zone is not None
        assert zone["fee"] == Decimal("120")

    def test_custom_restaurant_coordinates_override(self):
        """Custom restaurant lat/lon should be used instead of defaults."""
        # Customer at (10.0, 100.0), restaurant at (10.0, 100.0) → Zone 1
        zone = get_delivery_zone(10.0, 100.0, restaurant_lat=10.0, restaurant_lon=100.0)
        assert zone is not None
        assert "Zone 1" in zone["name"]

    def test_partial_coordinates_lat_only_returns_none(self):
        """Providing lat but None lon should return None."""
        zone = get_delivery_zone(13.7563, None)
        assert zone is None

    def test_partial_coordinates_lon_only_returns_none(self):
        """Providing lon but None lat should return None."""
        zone = get_delivery_zone(None, 100.5018)
        assert zone is None


@pytest.mark.unit
class TestTimeSlotEdgeCases:
    """Edge-case tests for time slot management."""

    def test_slot_availability_filtering(self):
        """Setting a slot to unavailable should exclude it from results."""
        original = DEFAULT_TIME_SLOTS[0]["available"]
        try:
            DEFAULT_TIME_SLOTS[0]["available"] = False
            available = get_available_time_slots()
            assert len(available) == 7
            assert DEFAULT_TIME_SLOTS[0] not in available
        finally:
            DEFAULT_TIME_SLOTS[0]["available"] = original

    def test_slot_ids_are_unique(self):
        """All slot IDs must be unique."""
        ids = [slot["id"] for slot in DEFAULT_TIME_SLOTS]
        assert len(ids) == len(set(ids))

    def test_all_slots_have_label_and_id(self):
        """Every slot dict must have both 'label' and 'id' keys."""
        for slot in DEFAULT_TIME_SLOTS:
            assert "label" in slot, f"Slot missing 'label': {slot}"
            assert "id" in slot, f"Slot missing 'id': {slot}"
            assert isinstance(slot["label"], str)
            assert isinstance(slot["id"], str)
            assert len(slot["label"]) > 0
            assert len(slot["id"]) > 0
