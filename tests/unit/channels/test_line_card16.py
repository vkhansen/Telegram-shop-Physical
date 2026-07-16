"""CARD-16 LINE messaging channel — foundation + mask enforcement."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from bot.channels.line.adapter import LineAdapter
from bot.channels.line.config import LineConfig
from bot.channels.line.messenger import LineMessenger
from bot.channels.line.session import SessionStore
from bot.channels.line.signature import verify_line_signature
from bot.channels.line.webhook import register_line_routes
from bot.platform.capabilities import can, features_for
from bot.platform.identity import PLATFORM_LINE, ensure_line_user, resolve_user_id
from bot.platform.messenger_router import notify_user, preferred_customer_channel
from bot.platform.messaging import TransportRegistry
from bot.services.dto import ServiceResult


def _cfg(**kwargs) -> LineConfig:
    base = dict(
        enabled=True,
        channel_access_token="token",
        channel_secret="secret",
        webhook_path="/webhooks/line",
        default_brand_id=None,
        api_base="https://api.line.me",
    )
    base.update(kwargs)
    return LineConfig(**base)


async def _client_for(app: web.Application):
    server = TestServer(app)
    client = TestClient(server)
    await client.start_server()
    return client


def test_line_signature_accept_and_reject():
    body = b'{"events":[]}'
    secret = "chan-secret"
    dig = hmac.new(secret.encode(), body, hashlib.sha256).digest()
    sig = base64.b64encode(dig).decode()
    assert verify_line_signature(channel_secret=secret, body=body, header_value=sig)
    assert not verify_line_signature(channel_secret=secret, body=body, header_value="bad")
    assert not verify_line_signature(channel_secret=secret, body=body, header_value=None)
    assert verify_line_signature(channel_secret="", body=body, header_value=None)


def test_line_customer_mask_no_ops_or_live():
    assert can("line", "catalog", role="customer")
    assert can("line", "cart", role="customer")
    assert can("line", "checkout", role="customer")
    assert can("line", "order_status", role="customer")
    assert can("line", "tickets", role="customer")
    assert not can("line", "admin_console", role="customer")
    assert not can("line", "kitchen_ops", role="customer")
    assert not can("line", "location_live", role="customer")
    assert "admin_console" not in features_for("line", "admin")


@pytest.mark.asyncio
async def test_webhook_flag_off_no_routes():
    app = web.Application()
    ok = register_line_routes(app, config=_cfg(enabled=False))
    assert ok is False
    assert len(list(app.router.routes())) == 0


@pytest.mark.asyncio
async def test_webhook_signature_and_reply(db_with_roles, db_engine):
    posts: list = []

    async def poster(url, payload, headers):
        posts.append({"url": url, "payload": payload})
        return 200

    messenger = LineMessenger(
        channel_access_token="t",
        reply_url="https://api.line.me/v2/bot/message/reply",
        push_url="https://api.line.me/v2/bot/message/push",
        http_post=poster,
    )
    adapter = LineAdapter(config=_cfg(channel_secret="sec"), messenger=messenger, sessions=SessionStore())
    app = web.Application()
    assert register_line_routes(app, config=_cfg(channel_secret="sec"), adapter=adapter)
    client = await _client_for(app)
    try:
        # bad sig
        body = json.dumps({"events": []}).encode()
        bad = await client.post(
            "/webhooks/line",
            data=body,
            headers={"X-Line-Signature": "xx", "Content-Type": "application/json"},
        )
        assert bad.status == 403

        payload = {
            "events": [
                {
                    "type": "message",
                    "replyToken": "r1",
                    "source": {"type": "user", "userId": "Uline_test_1"},
                    "message": {"type": "text", "text": "hello"},
                }
            ]
        }
        body = json.dumps(payload).encode()
        dig = hmac.new(b"sec", body, hashlib.sha256).digest()
        sig = base64.b64encode(dig).decode()
        ok = await client.post(
            "/webhooks/line",
            data=body,
            headers={"X-Line-Signature": sig, "Content-Type": "application/json"},
        )
        assert ok.status == 200
        assert posts, "expected LINE outbound"
        # first message should use reply API
        assert "reply" in posts[0]["url"]
        text = posts[0]["payload"]["messages"][0]["text"]
        assert "Welcome" in text or "LINE" in text
    finally:
        await client.close()


def test_ensure_line_user(db_with_roles, db_engine):
    uid = ensure_line_user("U_unique_line_abc")
    assert uid > 1_000_000_000_000_000
    assert resolve_user_id(PLATFORM_LINE, "U_unique_line_abc") == uid
    assert ensure_line_user("U_unique_line_abc") == uid


@pytest.mark.asyncio
async def test_adapter_denies_admin(db_with_roles, db_engine):
    posts: list = []

    async def poster(url, payload, headers):
        posts.append(payload)
        return 200

    messenger = LineMessenger(
        channel_access_token="t",
        reply_url="https://api.line.me/v2/bot/message/reply",
        push_url="https://api.line.me/v2/bot/message/push",
        http_post=poster,
    )
    ad = LineAdapter(config=_cfg(), messenger=messenger, sessions=SessionStore())
    await ad.handle_event(
        {
            "type": "postback",
            "replyToken": "r2",
            "source": {"userId": "Uadmin_try"},
            "postback": {"data": "ADMIN", "displayText": "Admin"},
        }
    )
    assert posts
    msg = posts[0]["messages"][0]["text"]
    assert "Telegram" in msg


@pytest.mark.asyncio
async def test_adapter_support_ticket(db_with_roles, db_engine):
    posts: list = []

    async def poster(url, payload, headers):
        posts.append(payload)
        return 200

    messenger = LineMessenger(
        channel_access_token="t",
        reply_url="https://api.line.me/v2/bot/message/reply",
        push_url="https://api.line.me/v2/bot/message/push",
        http_post=poster,
    )
    store = SessionStore()
    ad = LineAdapter(config=_cfg(), messenger=messenger, sessions=store)
    uid = "Uticket_line_1"
    await ad.handle_event(
        {
            "type": "postback",
            "replyToken": "r3",
            "source": {"userId": uid},
            "postback": {"data": "LN_SUPPORT"},
        }
    )
    assert store.get(uid).state == "support_wait_body"
    with patch(
        "bot.channels.line.adapter.tickets_svc.create_ticket",
        return_value=ServiceResult.success(ticket_code="LNTEST01"),
    ):
        await ad.handle_event(
            {
                "type": "message",
                "replyToken": "r4",
                "source": {"userId": uid},
                "message": {"type": "text", "text": "Need help with order"},
            }
        )
    assert any(
        "LNTEST01" in (p.get("messages") or [{}])[0].get("text", "") for p in posts
    )


@pytest.mark.asyncio
async def test_notify_user_prefers_line(db_with_roles, db_engine):
    user_id = ensure_line_user("U_notify_line")
    ch, ext = preferred_customer_channel(user_id)
    assert ch == PLATFORM_LINE
    assert ext == "U_notify_line"

    posts: list = []

    async def poster(url, payload, headers):
        posts.append(payload)
        return 200

    line = LineMessenger(
        channel_access_token="t",
        reply_url="https://example/reply",
        push_url="https://example/push",
        http_post=poster,
    )
    reg = TransportRegistry()
    reg.register(line)
    tg = MagicMock()
    tg.send_text = AsyncMock(return_value=True)
    ok = await notify_user(user_id, "Order ready!", messenger=tg, registry=reg)
    assert ok is True
    assert posts
    assert posts[0]["to"] == "U_notify_line"
    tg.send_text.assert_not_called()
