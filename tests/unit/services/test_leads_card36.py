"""CARD-36 leads polish — validation, staff notify, preferred channel."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.platform.messaging import RecordingMessenger, set_messenger
from bot.services import leads_bookings


@pytest.fixture
def brand_slug(test_brand, db_engine):
    return test_brand.slug


def test_create_lead_requires_consent_and_contact(brand_slug, db_engine):
    with pytest.raises(ValueError, match="consent"):
        leads_bookings.create_lead(
            brand_slug=brand_slug,
            name="A",
            phone="0811111111",
            consent=False,
        )
    with pytest.raises(ValueError, match="phone_or_email"):
        leads_bookings.create_lead(
            brand_slug=brand_slug,
            name="A",
            consent=True,
        )
    with pytest.raises(ValueError, match="name"):
        leads_bookings.create_lead(
            brand_slug=brand_slug,
            name="  ",
            phone="081",
            consent=True,
        )


def test_create_lead_persists_channel_item_utm(brand_slug, db_engine):
    lead = leads_bookings.create_lead(
        brand_slug=brand_slug,
        name="Somchai",
        preferred_channel="line",
        channel_handle="@somchai",
        phone="0812345678",
        item_slug="green-tea",
        message="Wholesale?",
        source="ig_bio",
        utm={"utm_source": "instagram", "utm_campaign": "reel1", "junk": "x"},
        consent=True,
        age_confirmed=True,
    )
    assert lead["id"] > 0
    assert lead["status"] == "new"
    assert lead["preferred_channel"] == "line"
    assert lead["item_slug"] == "green-tea"
    assert lead["brand_slug"] == brand_slug
    assert "staff_message" in lead
    assert "New lead" in lead["staff_message"]
    assert "line" in lead["staff_message"].lower()
    assert "green-tea" in lead["staff_message"]


def test_create_booking_and_staff_message(brand_slug, db_engine):
    b = leads_bookings.create_booking(
        brand_slug=brand_slug,
        name="Mina",
        meeting_type="google_meet",
        email="mina@example.com",
        preferred_when="2026-08-01T14:00",
        notes="Demo",
        consent=True,
    )
    assert b["id"] > 0
    assert b["meeting_type"] == "google_meet"
    assert b["status"] == "requested"
    assert "booking" in b["staff_message"].lower()
    assert "google_meet" in b["staff_message"]


@pytest.mark.asyncio
async def test_notify_staff_uses_messenger(monkeypatch):
    rec = RecordingMessenger()
    set_messenger(rec)
    monkeypatch.setenv("OWNER_ID", "424242")
    monkeypatch.setattr(leads_bookings.EnvKeys, "OWNER_ID", "424242", raising=False)
    monkeypatch.setattr(leads_bookings.EnvKeys, "MAINTAINER_IDS", "", raising=False)
    monkeypatch.setattr(leads_bookings.EnvKeys, "SUPPORT_CHAT_ID", None, raising=False)

    # Reload staff ids from patched env via function
    with patch.object(leads_bookings, "staff_recipient_ids", return_value=[424242]):
        ok = await leads_bookings.notify_staff("📩 test lead")
    assert ok is True
    assert len(rec.texts) == 1
    assert rec.texts[0]["user_ref"] == 424242
    assert "test lead" in rec.texts[0]["text"]
    set_messenger(None)


@pytest.mark.asyncio
async def test_notify_staff_also_support_group(monkeypatch):
    rec = RecordingMessenger()
    set_messenger(rec)
    monkeypatch.setattr(
        "bot.services.leads_bookings.EnvKeys",
        type(
            "E",
            (),
            {
                "OWNER_ID": None,
                "MAINTAINER_IDS": "",
                "SUPPORT_CHAT_ID": "-1001",
            },
        ),
    )
    with patch.object(leads_bookings, "staff_recipient_ids", return_value=[]):
        ok = await leads_bookings.notify_staff("📅 booking")
    assert ok is True
    assert rec.groups
    assert rec.groups[0]["group_key"] == "-1001"
    set_messenger(None)


@pytest.mark.asyncio
async def test_create_lead_http_notifies(db_with_roles, test_brand, db_engine, monkeypatch):
    from aiohttp import web
    from aiohttp.test_utils import TestClient, TestServer

    from bot.web import auth_api

    rec = RecordingMessenger()
    set_messenger(rec)
    monkeypatch.setattr(leads_bookings, "staff_recipient_ids", lambda: [99])

    app = web.Application()
    auth_api.register_auth_and_ticket_routes(app)
    server = TestServer(app)
    client = TestClient(server)
    await client.start_server()
    try:
        res = await client.post(
            "/api/public/leads",
            json={
                "brand_slug": test_brand.slug,
                "name": "HTTP Lead",
                "phone": "0899999999",
                "channel": "whatsapp",
                "consent": True,
                "item_slug": "sku-1",
                "utm_source": "ig",
            },
        )
        assert res.status == 201, await res.text()
        data = await res.json()
        assert data["id"] > 0
        assert rec.texts, "staff should be notified"
        assert "HTTP Lead" in rec.texts[0]["text"] or "New lead" in rec.texts[0]["text"]
    finally:
        await client.close()
        set_messenger(None)


def test_parse_utm_from_mapping():
    assert leads_bookings.parse_utm_from_mapping({"utm": {"utm_source": "x"}}) == {
        "utm_source": "x"
    }
    assert leads_bookings.parse_utm_from_mapping({"utm_campaign": "c1"}) == {
        "utm_campaign": "c1"
    }
    assert leads_bookings.parse_utm_from_mapping({}) is None


def test_format_messages_stable():
    t = leads_bookings.format_lead_staff_message(
        lead_id=1,
        brand_slug="acme",
        brand_name="Acme",
        name="A",
        preferred_channel="phone",
        phone="1",
        email=None,
        channel_handle=None,
        item_slug=None,
        message="hi",
        source="web",
    )
    assert "Acme" in t and "#1" in t
