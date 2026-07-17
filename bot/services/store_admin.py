"""Admin store operations as application services (Telegram/web-agnostic).

Handlers and harnesses call these instead of duplicating ORM snippets.
Covers list / view / edit / toggle / set-default for multi-branch brands.
"""

from __future__ import annotations

from typing import Any

from bot.database.main import Database
from bot.database.models.main import Brand, Store
from bot.services.catalog_public import slugify


def _store_dto(store: Store) -> dict[str, Any]:
    return {
        "id": int(store.id),
        "brand_id": store.brand_id,
        "name": store.name,
        "slug": store.slug,
        "address": store.address,
        "phone": store.phone,
        "latitude": store.latitude,
        "longitude": store.longitude,
        "is_active": bool(store.is_active),
        "is_default": bool(store.is_default),
        "promptpay_id": store.promptpay_id,
        "promptpay_name": store.promptpay_name,
        "has_menu_image": bool(store.menu_image_file_id),
        "has_static_qr": bool(store.payment_qr_file_id),
        "web_profile": store.web_profile if isinstance(store.web_profile, dict) else {},
    }


def list_stores(*, brand_slug: str | None = None, brand_id: int | None = None) -> list[dict[str, Any]]:
    """List stores for a brand (or all stores if neither filter is set)."""
    with Database().session() as s:
        q = s.query(Store)
        if brand_id is not None:
            q = q.filter(Store.brand_id == brand_id)
        elif brand_slug:
            brand = s.query(Brand).filter_by(slug=brand_slug).one_or_none()
            if not brand:
                return []
            q = q.filter(Store.brand_id == brand.id)
        rows = q.order_by(Store.is_default.desc(), Store.name).all()
        return [_store_dto(r) for r in rows]


def get_store(store_id: int) -> dict[str, Any] | None:
    with Database().session() as s:
        store = s.query(Store).filter_by(id=store_id).one_or_none()
        return _store_dto(store) if store else None


def get_store_by_slug(brand_slug: str, store_slug: str) -> dict[str, Any] | None:
    with Database().session() as s:
        brand = s.query(Brand).filter_by(slug=brand_slug).one_or_none()
        if not brand:
            return None
        store = (
            s.query(Store)
            .filter_by(brand_id=brand.id, slug=store_slug)
            .one_or_none()
        )
        return _store_dto(store) if store else None


def create_store(
    *,
    brand_slug: str,
    name: str,
    address: str | None = None,
    phone: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    slug: str | None = None,
    is_default: bool = False,
    web_profile: dict | None = None,
) -> dict[str, Any]:
    name = (name or "").strip()
    if not name:
        raise ValueError("name_required")
    if len(name) > 200:
        raise ValueError("name_too_long")

    with Database().session() as s:
        brand = s.query(Brand).filter_by(slug=brand_slug).one_or_none()
        if not brand:
            raise ValueError("brand_not_found")
        existing = s.query(Store).filter_by(brand_id=brand.id, name=name).one_or_none()
        if existing:
            raise ValueError("name_exists")
        store_slug = (slug or slugify(name)).strip()[:80] or slugify(name)
        if s.query(Store).filter_by(brand_id=brand.id, slug=store_slug).one_or_none():
            raise ValueError("slug_exists")
        if is_default:
            s.query(Store).filter(Store.brand_id == brand.id, Store.is_default.is_(True)).update(
                {"is_default": False}
            )
        store = Store(
            name=name,
            slug=store_slug,
            brand_id=brand.id,
            address=(address or "").strip() or None,
            phone=(phone or "").strip() or None,
            latitude=latitude,
            longitude=longitude,
            is_default=is_default,
            is_active=True,
            web_profile=web_profile or {"schema_version": 1},
        )
        s.add(store)
        s.commit()
        return _store_dto(store)


def update_store(
    store_id: int,
    *,
    name: str | None = None,
    address: str | None = ...,  # type: ignore[assignment]
    phone: str | None = ...,  # type: ignore[assignment]
    latitude: float | None = ...,  # type: ignore[assignment]
    longitude: float | None = ...,  # type: ignore[assignment]
    slug: str | None = None,
    web_profile: dict | None = None,
    promptpay_id: str | None = ...,  # type: ignore[assignment]
    promptpay_name: str | None = ...,  # type: ignore[assignment]
) -> dict[str, Any]:
    """Patch store fields. Pass ``None`` explicitly to clear optional strings/coords.

    Omitted kwargs (default sentinel ``...``) leave the column unchanged.
    """
    with Database().session() as s:
        store = s.query(Store).filter_by(id=store_id).one_or_none()
        if not store:
            raise ValueError("store_not_found")
        if name is not None:
            name = name.strip()
            if not name:
                raise ValueError("name_required")
            clash = (
                s.query(Store)
                .filter(Store.brand_id == store.brand_id, Store.name == name, Store.id != store_id)
                .one_or_none()
            )
            if clash:
                raise ValueError("name_exists")
            store.name = name
        if address is not ...:
            store.address = (address or "").strip() or None if address is not None else None
        if phone is not ...:
            store.phone = (phone or "").strip() or None if phone is not None else None
        if latitude is not ...:
            store.latitude = latitude
        if longitude is not ...:
            store.longitude = longitude
        if slug is not None:
            new_slug = slug.strip()[:80]
            if not new_slug:
                raise ValueError("slug_required")
            clash = (
                s.query(Store)
                .filter(Store.brand_id == store.brand_id, Store.slug == new_slug, Store.id != store_id)
                .one_or_none()
            )
            if clash:
                raise ValueError("slug_exists")
            store.slug = new_slug
        if web_profile is not None:
            store.web_profile = web_profile
        if promptpay_id is not ...:
            store.promptpay_id = (promptpay_id or "").strip() or None if promptpay_id is not None else None
        if promptpay_name is not ...:
            store.promptpay_name = (
                (promptpay_name or "").strip() or None if promptpay_name is not None else None
            )
        s.commit()
        return _store_dto(store)


def toggle_store(store_id: int, *, is_active: bool | None = None) -> dict[str, Any]:
    """Flip active flag, or set explicitly when ``is_active`` is provided."""
    with Database().session() as s:
        store = s.query(Store).filter_by(id=store_id).one_or_none()
        if not store:
            raise ValueError("store_not_found")
        store.is_active = (not store.is_active) if is_active is None else bool(is_active)
        s.commit()
        return _store_dto(store)


def set_default_store(store_id: int) -> dict[str, Any]:
    with Database().session() as s:
        store = s.query(Store).filter_by(id=store_id).one_or_none()
        if not store:
            raise ValueError("store_not_found")
        s.query(Store).filter(Store.brand_id == store.brand_id, Store.is_default.is_(True)).update(
            {"is_default": False}
        )
        store.is_default = True
        store.is_active = True
        s.commit()
        return _store_dto(store)
