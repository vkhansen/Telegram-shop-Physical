"""
Delivery zone pricing and time slot management (Card 10).

Simple distance-based zone pricing using Haversine formula.
"""
import os
from decimal import Decimal
from math import atan2, cos, radians, sin, sqrt

# Restaurant location (configurable via env)
RESTAURANT_LAT = float(os.getenv("RESTAURANT_LAT", "13.7563"))
RESTAURANT_LNG = float(os.getenv("RESTAURANT_LNG", "100.5018"))

# Default delivery zones (distance in km, fee in THB)
DEFAULT_DELIVERY_ZONES = [
    {"name": "Zone 1 - Central", "max_km": 3, "fee": Decimal("0")},
    {"name": "Zone 2 - Inner", "max_km": 7, "fee": Decimal("30")},
    {"name": "Zone 3 - Mid", "max_km": 12, "fee": Decimal("50")},
    {"name": "Zone 4 - Outer", "max_km": 20, "fee": Decimal("80")},
    {"name": "Zone 5 - Far", "max_km": 99, "fee": Decimal("120")},
]

# Default time slots
DEFAULT_TIME_SLOTS = [
    {"id": "lunch_early", "label": "11:00-12:00", "available": True},
    {"id": "lunch_peak", "label": "12:00-13:00", "available": True},
    {"id": "lunch_late", "label": "13:00-14:00", "available": True},
    {"id": "afternoon", "label": "14:00-17:00", "available": True},
    {"id": "dinner_early", "label": "17:00-18:30", "available": True},
    {"id": "dinner_peak", "label": "18:30-20:00", "available": True},
    {"id": "dinner_late", "label": "20:00-21:30", "available": True},
    {"id": "asap", "label": "ASAP", "available": True},
]


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two GPS coordinates using Haversine formula.

    Returns:
        Distance in kilometers
    """
    R = 6371  # Earth's radius in km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


def get_delivery_zone(lat: float, lon: float,
                      restaurant_lat: float | None = None,
                      restaurant_lon: float | None = None) -> dict | None:
    """
    Determine delivery zone based on distance from restaurant.

    Returns:
        Zone dict with name, max_km, fee — or None if no coordinates
    """
    if lat is None or lon is None:
        return None

    # MISC-02 fix: Use 'is None' check since 0.0 is a valid coordinate
    r_lat = RESTAURANT_LAT if restaurant_lat is None else restaurant_lat
    r_lon = RESTAURANT_LNG if restaurant_lon is None else restaurant_lon

    distance = calculate_distance(lat, lon, r_lat, r_lon)

    for zone in DEFAULT_DELIVERY_ZONES:
        if distance <= float(zone["max_km"]):
            return zone

    return DEFAULT_DELIVERY_ZONES[-1]


def get_available_time_slots() -> list[dict]:
    """Get list of currently available time slots."""
    return [slot for slot in DEFAULT_TIME_SLOTS if slot["available"]]
