"""Public catalog read service for white-label sites (CARD-38).

Assembles brand / store / menu DTOs from relational data + web_profile.
Media URLs use Phase B media proxy (``/media/{token}``).
"""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo

from bot.database.main import Database
from bot.database.models.main import BranchInventory, Brand, Categories, Goods, Store
from bot.services.media_proxy import media_url_for
from bot.services.web_profile import normalize_commerce_mode


def slugify(text: str, *, max_len: int = 70) -> str:
    """ASCII-ish URL slug from display name."""
    if not text:
        return "item"
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return (text or "item")[:max_len]


def _now_hhmm(tz_name: str | None) -> str:
    """Current HH:MM in brand timezone; falls back to UTC if tzdata missing (e.g. Windows CI)."""
    from datetime import timezone as dt_timezone

    for key in (tz_name, "Asia/Bangkok", "UTC"):
        if not key:
            continue
        try:
            return datetime.now(ZoneInfo(key)).strftime("%H:%M")
        except Exception:
            continue
    return datetime.now(dt_timezone.utc).strftime("%H:%M")


def _in_time_window(now: str, start: str | None, end: str | None) -> bool:
    if not start or not end:
        return True
    # Same-day window (matches cart logic)
    return start <= now <= end


def _maps_url(lat: float | None, lng: float | None) -> str | None:
    if lat is None or lng is None:
        return None
    return f"https://www.google.com/maps?q={lat},{lng}"


def _file_ref(file_id: str | None, brand_id: int | None = None) -> str | None:
    """Public media URL via proxy (CARD-38 Phase B)."""
    return media_url_for(file_id, brand_id=brand_id)


def resolve_item_cta(
    *,
    commerce_mode: str,
    web_orderable: bool,
    inquiry_only: bool,
) -> str:
    """Return primary CTA key for storefront UI."""
    mode = normalize_commerce_mode(commerce_mode)
    if inquiry_only or mode == "portfolio":
        return "inquire"
    if mode == "hybrid" and not web_orderable:
        return "inquire"
    if not web_orderable:
        return "inquire"
    return "order"


def item_available(
    goods: Goods,
    *,
    now_hhmm: str,
    branch_inv: BranchInventory | None = None,
) -> tuple[bool, list[str]]:
    """Availability parity with bot (active, sold_out, daily limit, stock, time window)."""
    badges: list[str] = []
    if not goods.is_active:
        return False, ["inactive"]
    if goods.sold_out_today:
        return False, ["sold_out"]
    if goods.daily_limit is not None and goods.daily_sold_count >= goods.daily_limit:
        return False, ["daily_limit"]
    if not _in_time_window(now_hhmm, goods.available_from, goods.available_until):
        return False, ["outside_hours"]

    if goods.item_type == "product":
        if branch_inv is not None:
            avail = branch_inv.available_quantity
        else:
            avail = goods.available_quantity
        if avail <= 0:
            return False, ["out_of_stock"]
    # prepared: stock_quantity=0 means unlimited (project rule)

    if goods.prep_time_minutes:
        badges.append(f"prep:{goods.prep_time_minutes}m")
    return True, badges


def category_visible(cat: Categories, now_hhmm: str) -> bool:
    return _in_time_window(now_hhmm, cat.available_from, cat.available_until)


def _serialize_item(
    goods: Goods,
    *,
    commerce_mode: str,
    now_hhmm: str,
    brand_id: int | None = None,
    branch_inv: BranchInventory | None = None,
    include_description: bool = False,
) -> dict[str, Any] | None:
    if not getattr(goods, "web_listable", True):
        return None

    bid = brand_id if brand_id is not None else goods.brand_id
    available, badges = item_available(goods, now_hhmm=now_hhmm, branch_inv=branch_inv)
    cta = resolve_item_cta(
        commerce_mode=commerce_mode,
        web_orderable=bool(getattr(goods, "web_orderable", True)),
        inquiry_only=bool(getattr(goods, "inquiry_only", False)),
    )
    media_urls: list[str] = []
    if goods.image_file_id:
        ref = _file_ref(goods.image_file_id, bid)
        if ref:
            media_urls.append(ref)
    if goods.media and isinstance(goods.media, list):
        for m in goods.media:
            if isinstance(m, dict) and m.get("file_id"):
                ref = _file_ref(m["file_id"], bid)
                if ref and ref not in media_urls:
                    media_urls.append(ref)

    price: str | Decimal | None = goods.price

    dto: dict[str, Any] = {
        "slug": slugify(goods.name),
        "name": goods.name,
        "category": goods.category_name,
        "price": str(price) if price is not None else None,
        "image_url": media_urls[0] if media_urls else None,
        "media_urls": media_urls,
        "available": available,
        "badges": badges,
        "item_type": goods.item_type,
        "web_orderable": bool(getattr(goods, "web_orderable", True)),
        "inquiry_only": bool(getattr(goods, "inquiry_only", False)),
        "cta": cta,
        "prep_time_minutes": goods.prep_time_minutes,
        "allergens": goods.allergens,
    }
    if include_description:
        dto["description"] = goods.description
        dto["modifiers"] = goods.modifiers
        dto["calories"] = goods.calories
        dto["available_from"] = goods.available_from
        dto["available_until"] = goods.available_until
    return dto


def get_brand_by_slug(brand_slug: str) -> Brand | None:
    with Database().session() as s:
        brand = s.query(Brand).filter(Brand.slug == brand_slug, Brand.is_active.is_(True)).one_or_none()
        if brand:
            s.expunge(brand)
        return brand


def list_active_brands() -> list[dict[str, Any]]:
    with Database().session() as s:
        brands = s.query(Brand).filter(Brand.is_active.is_(True)).order_by(Brand.name).all()
        return [
            {
                "slug": b.slug,
                "name": b.name,
                "description": b.description,
                "logo_url": _file_ref(b.logo_file_id, b.id),
            }
            for b in brands
        ]


def get_brand_public(brand_slug: str) -> dict[str, Any] | None:
    """Brand home payload: identity + web_profile + store summaries."""
    with Database().session() as s:
        brand = s.query(Brand).filter(Brand.slug == brand_slug, Brand.is_active.is_(True)).one_or_none()
        if not brand:
            return None
        stores = (
            s.query(Store)
            .filter(Store.brand_id == brand.id, Store.is_active.is_(True))
            .order_by(Store.is_default.desc(), Store.name)
            .all()
        )
        mode = normalize_commerce_mode(brand.commerce_mode)
        web = brand.web_profile if isinstance(brand.web_profile, dict) else {}
        return {
            "slug": brand.slug,
            "name": brand.name,
            "description": brand.description,
            "logo_url": _file_ref(brand.logo_file_id, brand.id),
            "timezone": brand.timezone,
            "commerce_mode": mode,
            "age_gate_enabled": bool(brand.age_gate_enabled),
            "min_age": brand.min_age,
            "legal": {
                "legal_name": brand.legal_name,
                "dbd_number": brand.dbd_number,
            },
            "contact": {
                "support_email": brand.support_email,
                "support_phone": brand.support_phone,
            },
            "web": web,
            "stores": [
                {
                    "slug": st.slug or slugify(st.name),
                    "name": st.name,
                    "address": st.address,
                    "phone": st.phone,
                    "latitude": st.latitude,
                    "longitude": st.longitude,
                    "maps_url": _maps_url(st.latitude, st.longitude),
                    "is_default": bool(st.is_default),
                    "menu_image_url": _file_ref(st.menu_image_file_id, brand.id),
                }
                for st in stores
            ],
        }


def get_store_menu(brand_slug: str, store_slug: str) -> dict[str, Any] | None:
    """Branch page: contact columns + web_profile + categories/items with availability."""
    with Database().session() as s:
        brand = s.query(Brand).filter(Brand.slug == brand_slug, Brand.is_active.is_(True)).one_or_none()
        if not brand:
            return None
        matched = (
            s.query(Store)
            .filter(Store.brand_id == brand.id, Store.slug == store_slug, Store.is_active.is_(True))
            .one_or_none()
        )
        if matched is None:
            # Fallback for rows not yet backfilled: match slugify(name)
            candidates = (
                s.query(Store).filter(Store.brand_id == brand.id, Store.is_active.is_(True)).all()
            )
            for st in candidates:
                if slugify(st.name) == store_slug:
                    matched = st
                    break
        if not matched:
            return None

        now = _now_hhmm(brand.timezone)
        mode = normalize_commerce_mode(brand.commerce_mode)

        inv_rows = s.query(BranchInventory).filter(BranchInventory.store_id == matched.id).all()
        inv_map = {r.item_name: r for r in inv_rows}

        cats = (
            s.query(Categories)
            .filter((Categories.brand_id == brand.id) | (Categories.brand_id.is_(None)))
            .order_by(Categories.sort_order, Categories.name)
            .all()
        )
        goods_q = s.query(Goods).filter((Goods.brand_id == brand.id) | (Goods.brand_id.is_(None)))
        all_goods = goods_q.all()
        goods_by_cat: dict[str, list[Goods]] = {}
        for g in all_goods:
            goods_by_cat.setdefault(g.category_name, []).append(g)

        categories_out: list[dict[str, Any]] = []
        for cat in cats:
            if not category_visible(cat, now):
                continue
            items_out: list[dict[str, Any]] = []
            for g in goods_by_cat.get(cat.name, []):
                dto = _serialize_item(
                    g,
                    commerce_mode=mode,
                    now_hhmm=now,
                    brand_id=brand.id,
                    branch_inv=inv_map.get(g.name),
                )
                if dto:
                    items_out.append(dto)
            if not items_out:
                continue
            categories_out.append(
                {
                    "slug": slugify(cat.name),
                    "name": cat.name,
                    "sort_order": cat.sort_order,
                    "description": cat.description,
                    "image_url": _file_ref(cat.image_file_id, brand.id),
                    "items": items_out,
                }
            )

        store_web = matched.web_profile if isinstance(matched.web_profile, dict) else {}
        brand_web = brand.web_profile if isinstance(brand.web_profile, dict) else {}

        return {
            "brand": {
                "slug": brand.slug,
                "name": brand.name,
                "commerce_mode": mode,
                "age_gate_enabled": bool(brand.age_gate_enabled),
                "min_age": brand.min_age,
                "web": brand_web,
                "legal": {"legal_name": brand.legal_name, "dbd_number": brand.dbd_number},
            },
            "store": {
                "slug": matched.slug or slugify(matched.name),
                "name": matched.name,
                "address": matched.address,
                "phone": matched.phone,
                "latitude": matched.latitude,
                "longitude": matched.longitude,
                "maps_url": _maps_url(matched.latitude, matched.longitude),
                "menu_image_url": _file_ref(matched.menu_image_file_id, brand.id),
                "web": store_web,
            },
            "categories": categories_out,
        }


def get_store_item(brand_slug: str, store_slug: str, item_slug: str) -> dict[str, Any] | None:
    menu = get_store_menu(brand_slug, store_slug)
    if not menu:
        return None
    for cat in menu["categories"]:
        for it in cat["items"]:
            if it["slug"] == item_slug or slugify(it["name"]) == item_slug:
                # re-fetch full description
                with Database().session() as s:
                    brand = s.query(Brand).filter(Brand.slug == brand_slug).one_or_none()
                    goods = s.query(Goods).filter(Goods.name == it["name"]).one_or_none()
                    if not brand or not goods:
                        return {**it, "brand_slug": brand_slug, "store_slug": store_slug}
                    store = (
                        s.query(Store)
                        .filter(Store.brand_id == brand.id, Store.slug == store_slug)
                        .one_or_none()
                    )
                    inv = None
                    if store:
                        inv = (
                            s.query(BranchInventory)
                            .filter(
                                BranchInventory.store_id == store.id,
                                BranchInventory.item_name == goods.name,
                            )
                            .one_or_none()
                        )
                    now = _now_hhmm(brand.timezone)
                    mode = normalize_commerce_mode(brand.commerce_mode)
                    full = _serialize_item(
                        goods,
                        commerce_mode=mode,
                        now_hhmm=now,
                        brand_id=brand.id,
                        branch_inv=inv,
                        include_description=True,
                    )
                    if not full:
                        return None
                    full["brand_slug"] = brand_slug
                    full["store_slug"] = store_slug
                    return full
    return None
