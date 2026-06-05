"""Driver proximity matching tests (Card 26)."""

from datetime import UTC, datetime

import pytest

from bot.config import EnvKeys
from bot.database.methods.driver import (
    adjust_active_orders,
    approve_driver,
    create_driver,
    record_driver_location,
    set_driver_online,
)
from bot.database.models.main import User
from bot.dispatch.matching import get_available_drivers, haversine_km, rank_drivers

# A reference origin (Bangkok) and a handful of nearby/far points.
ORIGIN = (13.7563, 100.5018)


def _driver(tg, lat, lng, active=0, zones=None):
    return {
        "telegram_id": tg,
        "last_latitude": lat,
        "last_longitude": lng,
        "active_order_count": active,
        "service_zones": zones,
    }


@pytest.mark.unit
def test_nearest_available_ranked():
    """The closest driver ranks first; distance_km is attached and ordered."""
    near = _driver(1, 13.757, 100.502)  # ~tens of metres away
    mid = _driver(2, 13.78, 100.52)  # a couple of km
    far = _driver(3, 13.85, 100.60)  # ~13 km
    ranked = rank_drivers([far, mid, near], *ORIGIN, radius_km=50)

    assert [d["telegram_id"] for d in ranked] == [1, 2, 3]
    assert ranked[0]["distance_km"] < ranked[1]["distance_km"] < ranked[2]["distance_km"]


@pytest.mark.unit
def test_radius_excludes_distant_drivers():
    near = _driver(1, 13.757, 100.502)
    far = _driver(2, 18.0, 99.0)  # hundreds of km away
    ranked = rank_drivers([near, far], *ORIGIN, radius_km=8)
    assert [d["telegram_id"] for d in ranked] == [1]


@pytest.mark.unit
def test_zone_filter():
    """Drivers declaring zones only match their zone; undeclared serve anywhere."""
    zoned = _driver(1, 13.757, 100.502, zones=["north"])
    anywhere = _driver(2, 13.758, 100.503, zones=None)
    ranked = rank_drivers([zoned, anywhere], *ORIGIN, zone="south", radius_km=50)
    assert [d["telegram_id"] for d in ranked] == [2]


@pytest.mark.unit
def test_distance_tiebreak_prefers_least_loaded():
    """Co-located drivers are ordered by fewest active orders (load balancing)."""
    busy = _driver(1, 13.757, 100.502, active=2)
    idle = _driver(2, 13.757, 100.502, active=0)
    ranked = rank_drivers([busy, idle], *ORIGIN, radius_km=50)
    assert [d["telegram_id"] for d in ranked] == [2, 1]


@pytest.mark.unit
def test_haversine_known_distance():
    # ~1 deg latitude ≈ 111 km.
    assert 110 < haversine_km(13.0, 100.0, 14.0, 100.0) < 112


def _make_user(session, tg):
    session.add(User(telegram_id=tg, role_id=1, registration_date=datetime.now(UTC), referral_id=None))


@pytest.mark.database
def test_excludes_offline_and_busy(db_with_roles):
    """The dispatchable query drops offline, at-capacity, and unapproved drivers."""
    s = db_with_roles
    for tg in (100, 101, 102, 103):
        _make_user(s, tg)
    s.commit()

    # 100: approved, online, located → eligible
    create_driver(100, "Online Near")
    approve_driver(100)
    set_driver_online(100, True)
    record_driver_location(100, *ORIGIN)

    # 101: approved + located but never went online → excluded
    create_driver(101, "Offline")
    approve_driver(101)
    record_driver_location(101, *ORIGIN)

    # 102: approved + online but at capacity → excluded
    create_driver(102, "Busy")
    approve_driver(102)
    set_driver_online(102, True)
    record_driver_location(102, *ORIGIN)
    for _ in range(EnvKeys.DRIVER_MAX_ACTIVE_ORDERS):
        adjust_active_orders(102, 1)

    # 103: pending (never approved) → can't go online → excluded
    create_driver(103, "Pending")
    set_driver_online(103, True)  # no-op: not approved

    ranked = get_available_drivers(*ORIGIN)
    assert [d["telegram_id"] for d in ranked] == [100]
