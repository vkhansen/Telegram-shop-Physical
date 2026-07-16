"""CARD-33 Instagram messaging channel — foundation + mask enforcement."""

from __future__ import annotations

import hashlib
import hmac
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from bot.channels.instagram.adapter import InstagramAdapter
from bot.channels.instagram.config import InstagramConfig
from bot.channels.instagram.messenger import InstagramMessenger
from bot.channels.instagram.session import SessionStore
from bot.channels.instagram.signature import verify_hub_signature_256
from bot.channels.instagram.webhook import register_instagram_routes
from bot.platform.capabilities import can, features_for
from bot.platform.identity import PLATFORM_INSTAGRAM, ensure_instagram_user, list_identities, resolve_user_id
from bot.platform.messenger_router import notify_user, preferred_customer_channel
from bot.platform.messaging import TransportRegistry
from bot.services.dto import ServiceResult


async def _client_for(app: web.Application):
    server = TestServer(app)
    client = TestClient(server)
    await client.start_server()
    return client


def _cfg(**kwargs) -> InstagramConfig:
    base = dict(
        enabled=True,
        page_access_token="token",
        app_secret="secret",
        verify_token="verify-me",
        webhook_path="/webhooks/instagram",
        default_brand_id=None,
        graph_api_version="v21.0",
        public_media_base_url="",
    )
    base.update(kwargs)
    return InstagramConfig(**base)


# ---------------------------------------------------------------------------
# Signature
# ---------------------------------------------------------------------------


def test_signature_accept_and_reject():
    body = b'{"object":"instagram"}'
    secret = "app-secret"
    dig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_hub_signature_256(app_secret=secret, body=body, header_value=f"sha256={dig}")
    assert not verify_hub_signature_256(app_secret=secret, body=body, header_value="sha256=deadbeef")
    assert not verify_hub_signature_256(app_secret=secret, body=body, header_value=None)
    # Empty secret → skip (dev)
    assert verify_hub_signature_256(app_secret="", body=body, header_value=None)


# ---------------------------------------------------------------------------
# Caps / mask
# ---------------------------------------------------------------------------


def test_instagram_customer_mask_no_ops_or_live():
    assert can("instagram", "catalog", role="customer")
    assert can("instagram", "cart", role="customer")
    assert can("instagram", "checkout", role="customer")
    assert can("instagram", "order_status", role="customer")
    assert can("instagram", "tickets", role="customer")
    assert not can("instagram", "admin_console", role="customer")
    assert not can("instagram", "kitchen_ops", role="customer")
    assert not can("instagram", "driver_dispatch", role="customer")
    assert not can("instagram", "location_live", role="customer")
    assert not can("instagram", "delivery_chat", role="customer")
    assert "admin_console" not in features_for("instagram", "admin")


# ---------------------------------------------------------------------------
# Webhook routes
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_webhook_flag_off_no_routes():
    app = web.Application()
    ok = register_instagram_routes(app, config=_cfg(enabled=False))
    assert ok is False
    assert len(app.router.routes()) == 0


@pytest.mark.asyncio
async def test_webhook_verify_and_signature():
    http_posts: list = []

    async def poster(url, payload, headers):
        http_posts.append(payload)
        return 200

    messenger = InstagramMessenger(
        page_access_token="t",
        graph_messages_url="https://graph.facebook.com/v21.0/me/messages",
        http_post=poster,
    )
    adapter = InstagramAdapter(config=_cfg(app_secret="sec"), messenger=messenger, sessions=SessionStore())
    app = web.Application()
    assert register_instagram_routes(app, config=_cfg(app_secret="sec"), adapter=adapter)

    client = await _client_for(app)
    try:
        resp = await client.get(
            "/webhooks/instagram",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "verify-me",
                "hub.challenge": "12345",
            },
        )
        assert resp.status == 200
        assert await resp.text() == "12345"

        body = json.dumps(
            {
                "object": "instagram",
                "entry": [
                    {
                        "messaging": [
                            {
                                "sender": {"id": "psid-1"},
                                "message": {"text": "hello"},
                            }
                        ]
                    }
                ],
            }
        ).encode()
        bad = await client.post(
            "/webhooks/instagram",
            data=body,
            headers={"X-Hub-Signature-256": "sha256=00", "Content-Type": "application/json"},
        )
        assert bad.status == 403
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_webhook_accepts_valid_signature_and_replies(db_with_roles, db_engine):
    posts: list = []

    async def poster(url, payload, headers):
        posts.append(payload)
        return 200

    messenger = InstagramMessenger(
        page_access_token="t",
        graph_messages_url="https://graph.facebook.com/v21.0/me/messages",
        http_post=poster,
    )
    store = SessionStore()
    adapter = InstagramAdapter(config=_cfg(app_secret="sec"), messenger=messenger, sessions=store)
    app = web.Application()
    register_instagram_routes(app, config=_cfg(app_secret="sec"), adapter=adapter)
    client = await _client_for(app)
    try:
        payload = {
            "object": "instagram",
            "entry": [
                {
                    "messaging": [
                        {
                            "sender": {"id": "ig_psid_test_1"},
                            "message": {"text": "hello"},
                        }
                    ]
                }
            ],
        }
        body = json.dumps(payload).encode()
        dig = hmac.new(b"sec", body, hashlib.sha256).hexdigest()
        resp = await client.post(
            "/webhooks/instagram",
            data=body,
            headers={"X-Hub-Signature-256": f"sha256={dig}", "Content-Type": "application/json"},
        )
        assert resp.status == 200
        assert posts, "expected outbound IG reply"
        text = posts[0]["message"]["text"]
        assert "Welcome" in text or "Instagram" in text
    finally:
        await client.close()


# ---------------------------------------------------------------------------
# Identity
# ---------------------------------------------------------------------------


def test_ensure_instagram_user_and_resolve(db_with_roles, db_engine):
    uid = ensure_instagram_user("psid_unique_abc")
    assert uid > 1_000_000_000_000_000
    assert resolve_user_id(PLATFORM_INSTAGRAM, "psid_unique_abc") == uid
    assert ensure_instagram_user("psid_unique_abc") == uid  # idempotent
    ids = list_identities(uid)
    assert any(r["platform"] == PLATFORM_INSTAGRAM for r in ids)


# ---------------------------------------------------------------------------
# Adapter: ops denial, tickets, caps
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_adapter_denies_admin_payload(db_with_roles, db_engine):
    posts: list = []

    async def poster(url, payload, headers):
        posts.append(payload)
        return 200

    messenger = InstagramMessenger(
        page_access_token="t",
        graph_messages_url="https://example/msg",
        http_post=poster,
    )
    ad = InstagramAdapter(config=_cfg(), messenger=messenger, sessions=SessionStore())
    await ad.handle_messaging_event(
        {
            "sender": {"id": "psid_admin_try"},
            "postback": {"payload": "ADMIN", "title": "Admin"},
        }
    )
    assert posts
    assert "Telegram" in posts[0]["message"]["text"]
    assert "Admin" in posts[0]["message"]["text"] or "admin" in posts[0]["message"]["text"].lower()


@pytest.mark.asyncio
async def test_adapter_support_ticket_uses_service(db_with_roles, db_engine):
    posts: list = []

    async def poster(url, payload, headers):
        posts.append(payload)
        return 200

    messenger = InstagramMessenger(
        page_access_token="t",
        graph_messages_url="https://example/msg",
        http_post=poster,
    )
    store = SessionStore()
    ad = InstagramAdapter(config=_cfg(), messenger=messenger, sessions=store)
    psid = "psid_ticket_1"
    await ad.handle_messaging_event(
        {"sender": {"id": psid}, "message": {"quick_reply": {"payload": "IG_SUPPORT"}, "text": "Support"}}
    )
    assert store.get(psid).state == "support_wait_body"
    with patch(
        "bot.channels.instagram.adapter.tickets_svc.create_ticket",
        return_value=ServiceResult.success(ticket_code="IGTEST01"),
    ) as mock_create:
        await ad.handle_messaging_event(
            {"sender": {"id": psid}, "message": {"text": "My order never arrived"}}
        )
        mock_create.assert_called_once()
        args = mock_create.call_args
        assert "My order never arrived" in args[0] or "My order never arrived" in str(args)
    assert any("IGTEST01" in (p.get("message") or {}).get("text", "") for p in posts)


# ---------------------------------------------------------------------------
# Messenger router
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_notify_user_prefers_instagram(db_with_roles, db_engine):
    uid = ensure_instagram_user("psid_notify_1")
    ch, ext = preferred_customer_channel(uid)
    assert ch == PLATFORM_INSTAGRAM
    assert ext == "psid_notify_1"

    posts: list = []

    async def poster(url, payload, headers):
        posts.append(payload)
        return 200

    ig = InstagramMessenger(
        page_access_token="t",
        graph_messages_url="https://example/msg",
        http_post=poster,
    )
    reg = TransportRegistry()
    reg.register(ig)
    tg = MagicMock()
    tg.send_text = AsyncMock(return_value=True)

    ok = await notify_user(uid, "Order ready!", messenger=tg, registry=reg)
    assert ok is True
    assert posts
    assert posts[0]["recipient"]["id"] == "psid_notify_1"
    tg.send_text.assert_not_called()


@pytest.mark.asyncio
async def test_notify_user_telegram_fallback(db_with_roles, test_user, db_engine):
    """User with only telegram identity uses Telegram messenger."""
    from bot.platform.identity import ensure_telegram_identity

    ensure_telegram_identity(test_user.telegram_id)
    tg = MagicMock()
    tg.send_text = AsyncMock(return_value=True)
    reg = TransportRegistry()
    ok = await notify_user(test_user.telegram_id, "hi", messenger=tg, registry=reg)
    assert ok is True
    tg.send_text.assert_awaited()
