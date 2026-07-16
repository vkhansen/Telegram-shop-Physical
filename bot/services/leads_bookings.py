"""Web leads + meeting bookings (CARD-36).

Single writer for Lead / Booking. Staff alerts go through Messenger (CARD-29).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from bot.config.env import EnvKeys
from bot.database.main import Database
from bot.database.models.main import Booking, Brand, Lead, Store

logger = logging.getLogger(__name__)

VALID_CHANNELS = frozenset({"line", "whatsapp", "phone", "email", "telegram"})
VALID_MEETING_TYPES = frozenset({"in_person", "google_meet", "phone_call"})


def _brand_row(brand_slug: str) -> dict[str, Any] | None:
    with Database().session() as s:
        b = s.query(Brand).filter(Brand.slug == brand_slug, Brand.is_active.is_(True)).one_or_none()
        if not b:
            return None
        return {"id": b.id, "slug": b.slug, "name": b.name}


def _brand_id(brand_slug: str) -> int | None:
    row = _brand_row(brand_slug)
    return int(row["id"]) if row else None


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


def _normalize_utm(utm: dict | None) -> dict[str, str] | None:
    if not utm or not isinstance(utm, dict):
        return None
    out: dict[str, str] = {}
    for k in ("utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "ref"):
        v = utm.get(k)
        if v is not None and str(v).strip():
            out[k] = str(v).strip()[:200]
    return out or None


def staff_recipient_ids() -> list[int]:
    """OWNER + MAINTAINER_IDS for lead/booking DMs."""
    ids: list[int] = []
    raw = EnvKeys.MAINTAINER_IDS or ""
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            ids.append(int(part))
    if EnvKeys.OWNER_ID:
        try:
            oid = int(EnvKeys.OWNER_ID)
            if oid not in ids:
                ids.append(oid)
        except (TypeError, ValueError):
            pass
    return ids


def format_lead_staff_message(
    *,
    lead_id: int,
    brand_slug: str,
    brand_name: str | None,
    name: str,
    preferred_channel: str,
    phone: str | None,
    email: str | None,
    channel_handle: str | None,
    item_slug: str | None,
    message: str | None,
    source: str,
) -> str:
    shop = brand_name or brand_slug
    lines = [
        f"📩 New lead #{lead_id}",
        f"Brand: {shop} ({brand_slug})",
        f"Name: {name}",
        f"Channel: {preferred_channel}",
    ]
    if channel_handle:
        lines.append(f"Handle: {channel_handle}")
    if phone:
        lines.append(f"Phone: {phone}")
    if email:
        lines.append(f"Email: {email}")
    if item_slug:
        lines.append(f"Item: {item_slug}")
    if message:
        lines.append(f"Message: {message[:400]}")
    lines.append(f"Source: {source}")
    return "\n".join(lines)


def format_booking_staff_message(
    *,
    booking_id: int,
    brand_slug: str,
    brand_name: str | None,
    name: str,
    meeting_type: str,
    phone: str | None,
    email: str | None,
    preferred_when: str | None,
    notes: str | None,
    store_slug: str | None,
) -> str:
    shop = brand_name or brand_slug
    lines = [
        f"📅 New booking #{booking_id}",
        f"Brand: {shop} ({brand_slug})",
        f"Name: {name}",
        f"Type: {meeting_type}",
    ]
    if store_slug:
        lines.append(f"Store: {store_slug}")
    if preferred_when:
        lines.append(f"When: {preferred_when}")
    if phone:
        lines.append(f"Phone: {phone}")
    if email:
        lines.append(f"Email: {email}")
    if notes:
        lines.append(f"Notes: {notes[:400]}")
    return "\n".join(lines)


async def notify_staff(text: str) -> bool:
    """
    DM OWNER/maintainers + optional SUPPORT_CHAT_ID group.

    Soft-fail: never raises to the request path. Returns True if any send accepted.
    """
    from bot.platform.messaging import get_messenger

    if not (text or "").strip():
        return False
    messenger = get_messenger()
    any_ok = False
    for uid in staff_recipient_ids():
        try:
            ok = await messenger.send_text(uid, text)
            any_ok = any_ok or bool(ok)
        except Exception as e:
            logger.warning("lead/booking staff DM failed user=%s: %s", uid, e)
    support = EnvKeys.SUPPORT_CHAT_ID
    if support:
        try:
            mid = await messenger.send_group(str(support), text)
            any_ok = any_ok or mid is not None
        except Exception as e:
            logger.warning("lead/booking support group failed: %s", e)
    return any_ok


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
    phone = (phone or "").strip() or None
    email = (email or "").strip() or None
    if not phone and not email:
        raise ValueError("phone_or_email_required")
    if not consent:
        raise ValueError("consent_required")
    brand = _brand_row(brand_slug)
    if not brand:
        raise ValueError("brand_not_found")
    bid = int(brand["id"])
    sid = _store_id(bid, store_slug)
    ch = (preferred_channel or "phone").lower().strip()
    if ch not in VALID_CHANNELS:
        ch = "phone"
    handle = (channel_handle or "").strip()[:128] or None
    item = (item_slug or "").strip()[:120] or None
    interest = (interest_type or "").strip()[:40] or None
    if item and not interest:
        interest = "product_inquiry"
    src = (source or "web_site").strip()[:40] or "web_site"
    utm_clean = _normalize_utm(utm)
    msg = (message or "").strip() or None

    with Database().session() as s:
        lead = Lead(
            brand_id=bid,
            store_id=sid,
            user_id=user_id,
            name=name[:200],
            phone=phone,
            email=email,
            preferred_channel=ch,
            channel_handle=handle,
            interest_type=interest,
            item_slug=item,
            message=msg,
            source=src,
            utm_json=utm_clean,
            status="new",
            consent_at=datetime.now(UTC),
            age_confirmed=bool(age_confirmed),
        )
        s.add(lead)
        s.commit()
        lead_id = int(lead.id)
        return {
            "id": lead_id,
            "status": lead.status,
            "brand_id": bid,
            "brand_slug": brand["slug"],
            "brand_name": brand["name"],
            "preferred_channel": ch,
            "item_slug": item,
            "staff_message": format_lead_staff_message(
                lead_id=lead_id,
                brand_slug=brand["slug"],
                brand_name=brand.get("name"),
                name=name[:200],
                preferred_channel=ch,
                phone=phone,
                email=email,
                channel_handle=handle,
                item_slug=item,
                message=msg,
                source=src,
            ),
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
    consent: bool = True,
) -> dict[str, Any]:
    name = (name or "").strip()
    if not name:
        raise ValueError("name_required")
    phone = (phone or "").strip() or None
    email = (email or "").strip() or None
    if not phone and not email:
        raise ValueError("phone_or_email_required")
    # Booking form always implies contact consent when checkbox present; default True for API compat
    if not consent:
        raise ValueError("consent_required")
    brand = _brand_row(brand_slug)
    if not brand:
        raise ValueError("brand_not_found")
    bid = int(brand["id"])
    sid = _store_id(bid, store_slug)
    mt = (meeting_type or "in_person").lower().strip()
    if mt not in VALID_MEETING_TYPES:
        mt = "in_person"
    when = (preferred_when or "").strip() or None
    slots = [when] if when else None
    note = (notes or "").strip() or None

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
            notes=note,
            status="requested",
        )
        s.add(booking)
        s.commit()
        booking_id = int(booking.id)
        return {
            "id": booking_id,
            "status": booking.status,
            "meeting_type": mt,
            "brand_id": bid,
            "brand_slug": brand["slug"],
            "brand_name": brand["name"],
            "staff_message": format_booking_staff_message(
                booking_id=booking_id,
                brand_slug=brand["slug"],
                brand_name=brand.get("name"),
                name=name[:200],
                meeting_type=mt,
                phone=phone,
                email=email,
                preferred_when=when,
                notes=note,
                store_slug=(store_slug or "").strip() or None,
            ),
        }


def parse_utm_from_mapping(data: dict[str, Any] | None) -> dict[str, str] | None:
    """Build utm dict from request body or query-like mapping."""
    if not data:
        return None
    if isinstance(data.get("utm"), dict):
        return _normalize_utm(data["utm"])
    flat = {
        k: data.get(k)
        for k in ("utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "ref")
        if data.get(k)
    }
    return _normalize_utm(flat) if flat else None
