"""Customer-facing catalog / deals / store lookup (CARD-40 Tier D).

Channel-agnostic read helpers used by Grok tools (and reusable by web chatbox).
Not brand-slug scoped like ``catalog_public`` — global menu search for assistants.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from bot.database.main import Database
from bot.database.models.main import Coupon, Goods, Store
from bot.services.dto import ServiceResult


def _bangkok_now() -> datetime:
    tz = timezone(timedelta(hours=7))
    return datetime.now(tz)


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def browse_menu(
    *,
    keyword: str | None = None,
    category: str | None = None,
    max_price: Decimal | float | None = None,
    min_price: Decimal | float | None = None,
    in_stock_only: bool = True,
    limit: int = 10,
) -> ServiceResult:
    """Search active goods by keyword / category / price."""
    limit = max(1, min(int(limit), 20))
    with Database().session() as s:
        q = s.query(Goods).filter(Goods.is_active.is_(True))
        if in_stock_only:
            q = q.filter(Goods.sold_out_today.is_(False))
        if keyword:
            kw = f"%{keyword}%"
            q = q.filter(
                (Goods.name.ilike(kw)) | (Goods.description.ilike(kw)) | (Goods.allergens.ilike(kw))
            )
        if category:
            q = q.filter(Goods.category_name.ilike(f"%{category}%"))
        if max_price is not None:
            q = q.filter(Goods.price <= max_price)
        if min_price is not None:
            q = q.filter(Goods.price >= min_price)
        items = q.order_by(Goods.price).limit(limit).all()
        payload = [
            {
                "name": g.name,
                "price": str(g.price),
                "category": g.category_name,
                "description": g.description[:200] if g.description else None,
                "allergens": g.allergens,
                "prep_time_minutes": g.prep_time_minutes,
                "calories": g.calories,
                "available": g.is_currently_available,
            }
            for g in items
        ]
        return ServiceResult.success(items=payload, count=len(payload))


def today_specials(*, category: str | None = None) -> ServiceResult:
    """Items whose availability window is active in Bangkok time."""
    now = _bangkok_now()
    current_time = now.strftime("%H:%M")
    with Database().session() as s:
        q = s.query(Goods).filter(
            Goods.is_active.is_(True),
            Goods.sold_out_today.is_(False),
            Goods.available_from.isnot(None),
            Goods.available_until.isnot(None),
        )
        if category:
            q = q.filter(Goods.category_name.ilike(f"%{category}%"))
        all_items = q.all()
        active = [g for g in all_items if g.available_from <= current_time <= g.available_until]
        payload = [
            {
                "name": g.name,
                "price": str(g.price),
                "category": g.category_name,
                "available_from": g.available_from,
                "available_until": g.available_until,
            }
            for g in active
        ]
        return ServiceResult.success(
            current_time_bangkok=current_time,
            items=payload,
            count=len(payload),
        )


def find_deals(*, min_order_max: Decimal | float | None = None) -> ServiceResult:
    """Active public coupons."""
    now = datetime.now(UTC)
    with Database().session() as s:
        q = s.query(Coupon).filter(
            Coupon.is_active.is_(True),
            (Coupon.valid_until.is_(None)) | (Coupon.valid_until >= now),
            (Coupon.valid_from.is_(None)) | (Coupon.valid_from <= now),
            (Coupon.max_uses.is_(None)) | (Coupon.current_uses < Coupon.max_uses),
        )
        if min_order_max is not None:
            q = q.filter((Coupon.min_order.is_(None)) | (Coupon.min_order <= min_order_max))
        coupons = q.order_by(Coupon.discount_value.desc()).all()
        deals = [
            {
                "code": c.code,
                "discount_type": c.discount_type,
                "discount_value": str(c.discount_value),
                "min_order": str(c.min_order) if c.min_order else None,
                "max_discount": str(c.max_discount) if c.max_discount else None,
                "valid_until": c.valid_until.isoformat() if c.valid_until else None,
            }
            for c in coupons
        ]
        return ServiceResult.success(deals=deals, count=len(deals))


def find_nearby_stores(
    latitude: float,
    longitude: float,
    *,
    max_distance_km: float = 10.0,
) -> ServiceResult:
    """Active stores with lat/lon within radius, sorted by distance."""
    with Database().session() as s:
        stores = (
            s.query(Store)
            .filter(
                Store.is_active.is_(True),
                Store.latitude.isnot(None),
                Store.longitude.isnot(None),
            )
            .all()
        )

    results: list[dict[str, Any]] = []
    for store in stores:
        dist = _haversine_km(latitude, longitude, float(store.latitude), float(store.longitude))
        if dist <= max_distance_km:
            results.append(
                {
                    "name": store.name,
                    "address": store.address,
                    "distance_km": round(dist, 2),
                    "phone": store.phone,
                }
            )
    results.sort(key=lambda x: x["distance_km"])
    return ServiceResult.success(stores=results, count=len(results))


def check_coupon(
    code: str,
    *,
    order_total: Decimal | float | None = None,
) -> ServiceResult:
    """Validate a coupon and optionally compute discount for *order_total*."""
    now = datetime.now(UTC)
    with Database().session() as s:
        coupon = s.query(Coupon).filter(Coupon.code == code.upper()).first()

    if not coupon:
        return ServiceResult.success(valid=False, reason="Coupon code not found")
    if not coupon.is_active:
        return ServiceResult.success(valid=False, reason="Coupon is inactive")
    if coupon.valid_from and coupon.valid_from > now:
        return ServiceResult.success(valid=False, reason="Coupon is not yet active")
    if coupon.valid_until and coupon.valid_until < now:
        return ServiceResult.success(valid=False, reason="Coupon has expired")
    if coupon.max_uses and coupon.current_uses >= coupon.max_uses:
        return ServiceResult.success(valid=False, reason="Coupon has reached its usage limit")

    result: dict[str, Any] = {
        "valid": True,
        "code": coupon.code,
        "discount_type": coupon.discount_type,
        "discount_value": str(coupon.discount_value),
        "min_order": str(coupon.min_order) if coupon.min_order else None,
        "max_discount": str(coupon.max_discount) if coupon.max_discount else None,
        "valid_until": coupon.valid_until.isoformat() if coupon.valid_until else None,
    }

    if order_total is not None and float(order_total) > 0:
        total = Decimal(str(order_total))
        if coupon.min_order and total < coupon.min_order:
            result["applicable"] = False
            result["reason"] = f"Order minimum is {coupon.min_order}"
        else:
            if coupon.discount_type == "percent":
                raw = total * coupon.discount_value / 100
                discount = min(raw, coupon.max_discount) if coupon.max_discount else raw
            else:
                discount = coupon.discount_value
            result["applicable"] = True
            result["effective_discount"] = str(round(discount, 2))
            result["final_total"] = str(round(total - discount, 2))

    return ServiceResult.success(**result)
