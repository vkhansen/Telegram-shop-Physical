"""Proximity matching for driver dispatch (Card 26).

Generalises the Haversine ranking previously used only for store selection
(``bot/handlers/user/store_selection.py``) into reusable driver matching:
filter the dispatchable pool by zone + radius, then rank by distance with the
active-order count as a load-balancing tiebreaker.
"""

import math

from bot.config import EnvKeys
from bot.database.methods.driver import list_dispatchable_drivers


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in km between two GPS points."""
    R = 6371
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lng / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _serves_zone(driver: dict, zone: str | None) -> bool:
    """A driver with no declared service zones serves everywhere."""
    if not zone:
        return True
    zones = driver.get("service_zones")
    if not zones:
        return True
    return zone in zones


def rank_drivers(
    drivers: list[dict], lat: float, lng: float, zone: str | None = None, radius_km: float | None = None
) -> list[dict]:
    """Filter by zone + radius and rank nearest-first (load-balanced on ties).

    Each returned dict is the input driver dict plus a ``distance_km`` key.
    Pure function — no DB access — so it is trivially unit-testable.
    """
    if radius_km is None:
        radius_km = EnvKeys.AUTO_DISPATCH_RADIUS_KM

    ranked: list[dict] = []
    for d in drivers:
        if d.get("last_latitude") is None or d.get("last_longitude") is None:
            continue
        if not _serves_zone(d, zone):
            continue
        dist = haversine_km(lat, lng, d["last_latitude"], d["last_longitude"])
        if dist > radius_km:
            continue
        ranked.append({**d, "distance_km": dist})

    # Nearest first; break ties toward the least-loaded driver for fair spread.
    ranked.sort(key=lambda d: (round(d["distance_km"], 3), d.get("active_order_count", 0)))
    return ranked


def get_available_drivers(
    lat: float, lng: float, zone: str | None = None, brand_id: int | None = None, radius_km: float | None = None
) -> list[dict]:
    """Query the dispatchable pool and return it ranked nearest-first."""
    pool = list_dispatchable_drivers(brand_id=brand_id)
    return rank_drivers(pool, lat, lng, zone=zone, radius_km=radius_km)
