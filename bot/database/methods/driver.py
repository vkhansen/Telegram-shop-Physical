"""Driver persistence helpers for GPS dispatch (Card 26).

CRUD + availability queries for the ``drivers`` and ``driver_location_trail``
tables. Pure proximity ranking lives in :mod:`bot.dispatch.matching`; this module
only talks to the database and returns plain dicts (never ORM instances) so
callers never touch a detached object — matching the convention in ``read.py``.
"""

from datetime import UTC, datetime

from sqlalchemy import or_

from bot.config import EnvKeys
from bot.database.main import Database
from bot.database.models.main import Driver, DriverLocationTrail


def _to_dict(driver: Driver) -> dict:
    return {
        "id": driver.id,
        "telegram_id": driver.telegram_id,
        "brand_id": driver.brand_id,
        "name": driver.name,
        "phone": driver.phone,
        "vehicle_type": driver.vehicle_type,
        "service_zones": driver.service_zones,
        "status": driver.status,
        "is_online": driver.is_online,
        "is_available": driver.is_available,
        "active_order_count": driver.active_order_count,
        "rating": float(driver.rating) if driver.rating is not None else None,
        "last_latitude": driver.last_latitude,
        "last_longitude": driver.last_longitude,
        "last_location_at": driver.last_location_at,
    }


def create_driver(
    telegram_id: int,
    name: str,
    brand_id: int | None = None,
    phone: str | None = None,
    vehicle_type: str | None = None,
    service_zones: list | None = None,
    status: str = "pending",
) -> int:
    """Create a driver record (or return the existing one's id). Idempotent."""
    with Database().session() as s:
        existing = s.query(Driver).filter(Driver.telegram_id == telegram_id).one_or_none()
        if existing:
            return existing.id
        driver = Driver(
            telegram_id=telegram_id,
            name=name,
            brand_id=brand_id,
            phone=phone,
            vehicle_type=vehicle_type,
            service_zones=service_zones,
            status=status,
        )
        s.add(driver)
        s.flush()
        return driver.id


def get_driver(telegram_id: int) -> dict | None:
    """Return a driver dict by Telegram id, or None if not registered."""
    with Database().session() as s:
        driver = s.query(Driver).filter(Driver.telegram_id == telegram_id).one_or_none()
        return _to_dict(driver) if driver else None


def list_drivers(status: str | None = None, brand_id: int | None = None) -> list[dict]:
    """List drivers, optionally filtered by status and/or brand."""
    with Database().session() as s:
        q = s.query(Driver)
        if status:
            q = q.filter(Driver.status == status)
        if brand_id is not None:
            q = q.filter(Driver.brand_id == brand_id)
        return [_to_dict(d) for d in q.order_by(Driver.created_at).all()]


def approve_driver(telegram_id: int, approved_by: int | None = None) -> bool:
    """Promote a pending driver to approved. Returns False if no such driver."""
    with Database().session() as s:
        driver = s.query(Driver).filter(Driver.telegram_id == telegram_id).one_or_none()
        if not driver:
            return False
        driver.status = "approved"
        driver.approved_by = approved_by
        driver.approved_at = datetime.now(UTC)
        return True


def set_driver_status(telegram_id: int, status: str) -> bool:
    """Set a driver's approval status ('rejected', 'suspended', 'approved')."""
    with Database().session() as s:
        driver = s.query(Driver).filter(Driver.telegram_id == telegram_id).one_or_none()
        if not driver:
            return False
        driver.status = status
        # A driver who is no longer approved must not stay online/available.
        if status != "approved":
            driver.is_online = False
            driver.is_available = False
        return True


def set_driver_online(telegram_id: int, online: bool) -> bool:
    """Toggle a driver's online flag. Going offline also clears availability."""
    with Database().session() as s:
        driver = s.query(Driver).filter(Driver.telegram_id == telegram_id).one_or_none()
        if not driver or driver.status != "approved":
            return False
        driver.is_online = online
        driver.is_available = online
        return True


def set_driver_available(telegram_id: int, available: bool) -> bool:
    """Toggle whether an online driver can receive new offers."""
    with Database().session() as s:
        driver = s.query(Driver).filter(Driver.telegram_id == telegram_id).one_or_none()
        if not driver:
            return False
        driver.is_available = available
        return True


def record_driver_location(telegram_id: int, latitude: float, longitude: float) -> bool:
    """Append a location breadcrumb and update the driver's last-known position."""
    with Database().session() as s:
        driver = s.query(Driver).filter(Driver.telegram_id == telegram_id).one_or_none()
        if not driver:
            return False
        driver.last_latitude = latitude
        driver.last_longitude = longitude
        driver.last_location_at = datetime.now(UTC)
        s.add(DriverLocationTrail(driver_id=driver.id, latitude=latitude, longitude=longitude))
        return True


def adjust_active_orders(telegram_id: int, delta: int) -> None:
    """Increment/decrement a driver's active-order count (never below zero)."""
    with Database().session() as s:
        driver = s.query(Driver).filter(Driver.telegram_id == telegram_id).one_or_none()
        if not driver:
            return
        driver.active_order_count = max(0, (driver.active_order_count or 0) + delta)


def list_dispatchable_drivers(brand_id: int | None = None) -> list[dict]:
    """Return drivers eligible to receive an offer right now.

    Eligible = approved, online, available, under the active-order cap, and with
    a known position. Brand-scoped drivers match their own brand; drivers with a
    NULL brand are platform-wide and match any brand. Proximity ranking is the
    caller's job (:func:`bot.dispatch.matching.rank_drivers`).
    """
    max_active = EnvKeys.DRIVER_MAX_ACTIVE_ORDERS
    with Database().session() as s:
        q = s.query(Driver).filter(
            Driver.status == "approved",
            Driver.is_online.is_(True),
            Driver.is_available.is_(True),
            Driver.active_order_count < max_active,
            Driver.last_latitude.isnot(None),
            Driver.last_longitude.isnot(None),
        )
        if brand_id is not None:
            q = q.filter(or_(Driver.brand_id == brand_id, Driver.brand_id.is_(None)))
        return [_to_dict(d) for d in q.all()]
