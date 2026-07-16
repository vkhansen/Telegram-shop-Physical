"""Web leads + meeting bookings (CARD-36)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from bot.database.main import Database
from bot.database.models.main import Booking, Brand, Lead, Store


def _brand_id(brand_slug: str) -> int | None:
    with Database().session() as s:
        b = s.query(Brand).filter(Brand.slug == brand_slug, Brand.is_active.is_(True)).one_or_none()
        return b.id if b else None


def _store_id(brand_id: int, store_slug: str | None) -> int | None:
    if not store_slug:
        return None
    with Database().session() as s:
        st = (
            s.query(Store)
            .filter(Store.brand_id == brand_id, Store.slug == store_slug, Store.is_active.is_(True))
            .one_or_none()
        )
        return st.id if st else None


def create_lead(
    *,
    brand_slug: str,
    name: str,
    preferred_channel: str = "phone",
    phone: str | None = None,
    email: str | None = None,
    store_slug: str | None = None,
    user_id: int | None = None,
    channel_handle: str | None = None,
    interest_type: str | None = None,
    item_slug: str | None = None,
    message: str | None = None,
    source: str = "web_site",
    utm: dict | None = None,
    age_confirmed: bool = False,
    consent: bool = False,
) -> dict[str, Any]:
    name = (name or "").strip()
    if not name:
        raise ValueError("name_required")
    if not phone and not email:
        raise ValueError("phone_or_email_required")
    if not consent:
        raise ValueError("consent_required")
    bid = _brand_id(brand_slug)
    if not bid:
        raise ValueError("brand_not_found")
    sid = _store_id(bid, store_slug)
    ch = (preferred_channel or "phone").lower()
    if ch not in ("line", "whatsapp", "phone", "email", "telegram"):
        ch = "phone"

    with Database().session() as s:
        lead = Lead(
            brand_id=bid,
            store_id=sid,
            user_id=user_id,
            name=name[:200],
            phone=(phone or None),
            email=(email or None),
            preferred_channel=ch,
            channel_handle=channel_handle,
            interest_type=interest_type,
            item_slug=item_slug,
            message=message,
            source=source,
            utm_json=utm,
            status="new",
            consent_at=datetime.now(UTC),
            age_confirmed=bool(age_confirmed),
        )
        s.add(lead)
        s.commit()
        return {
            "id": lead.id,
            "status": lead.status,
            "brand_id": bid,
            "preferred_channel": ch,
        }


def create_booking(
    *,
    brand_slug: str,
    name: str,
    meeting_type: str = "in_person",
    phone: str | None = None,
    email: str | None = None,
    store_slug: str | None = None,
    user_id: int | None = None,
    preferred_when: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    name = (name or "").strip()
    if not name:
        raise ValueError("name_required")
    if not phone and not email:
        raise ValueError("phone_or_email_required")
    bid = _brand_id(brand_slug)
    if not bid:
        raise ValueError("brand_not_found")
    sid = _store_id(bid, store_slug)
    mt = (meeting_type or "in_person").lower()
    if mt not in ("in_person", "google_meet", "phone_call"):
        mt = "in_person"
    slots = [preferred_when] if preferred_when else None

    with Database().session() as s:
        booking = Booking(
            brand_id=bid,
            store_id=sid,
            user_id=user_id,
            name=name[:200],
            phone=phone,
            email=email,
            meeting_type=mt,
            preferred_slots=slots,
            notes=notes,
            status="requested",
        )
        s.add(booking)
        s.commit()
        return {
            "id": booking.id,
            "status": booking.status,
            "meeting_type": mt,
            "brand_id": bid,
        }
