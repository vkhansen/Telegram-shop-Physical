"""CARD-16 LINE messaging channel — foundation + Flex/QR/Redis/multi-OA polish."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from bot.channels.line import renderer as R
from bot.channels.line.adapter import LineAdapter
from bot.channels.line.config import LineConfig, parse_oa_brand_map
from bot.channels.line.messenger import LineMessenger
from bot.channels.line.qr_host import read_qr_png, store_qr_png
from bot.channels.line.session import LineSession, RedisSessionStore, SessionStore
from bot.channels.line.signature import verify_line_signature
from bot.channels.line.webhook import register_line_routes
from bot.platform.capabilities import can, features_for
from bot.platform.identity import PLATFORM_LINE, ensure_line_user, resolve_user_id
from bot.platform.messenger_router import notify_user, preferred_customer_channel
from bot.platform.messaging import TransportRegistry
from bot.services.dto import ServiceResult
from bot.web.public_api import register_public_catalog_routes


def _cfg(**kwargs) -> LineConfig:
    base = dict(
        enabled=True,
        channel_access_token="token",
        channel_secret="secret",
        webhook_path="/webhooks/line",
        default_brand_id=None,
        api_base="https://api.line.me",
        oa_brand_map={},
        session_backend="memory",
        use_flex=True,
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
        msg0 = posts[0]["payload"]["messages"][0]
        # Flex welcome (CARD-16 polish) or text fallback
        if msg0.get("type") == "flex":
            assert "Welcome" in (msg0.get("altText") or "") or "shop" in (
                msg0.get("altText") or ""
            ).lower()
        else:
            text = msg0.get("text") or ""
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


def test_parse_oa_brand_map_csv_and_json():
    assert parse_oa_brand_map("Uaaa:1,Ubbb:2") == {"Uaaa": 1, "Ubbb": 2}
    assert parse_oa_brand_map('{"Uaaa": 3}') == {"Uaaa": 3}
    assert parse_oa_brand_map("") == {}
    assert parse_oa_brand_map("bad") == {}


def test_brand_id_for_destination():
    cfg = _cfg(default_brand_id=9, oa_brand_map={"Uoa1": 42})
    assert cfg.brand_id_for_destination("Uoa1") == 42
    assert cfg.brand_id_for_destination("unknown") == 9
    assert cfg.brand_id_for_destination(None) == 9


def test_qr_host_store_and_read(tmp_path, monkeypatch):
    monkeypatch.setenv("LINE_QR_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("PUBLIC_MEDIA_BASE_URL", "https://cdn.example")
    # re-import path constants pick env via functions
    from bot.channels.line import qr_host as qh

    monkeypatch.setattr(qh, "_CACHE_DIR", tmp_path)
    monkeypatch.setattr(qh, "_META", {})
    url = qh.store_qr_png("ORD1", b"\x89PNG\r\nfake")
    assert url and url.startswith("https://cdn.example/media/line-qr/")
    token = url.rsplit("/", 1)[-1].replace(".png", "")
    assert qh.read_qr_png(token) == b"\x89PNG\r\nfake"
    assert qh.read_qr_png("../evil") is None


def test_flex_menu_and_payment_shapes():
    menu = R.menu_flex("Demo", ["• Item — 10"])
    assert menu["type"] == "flex"
    assert menu["contents"]["type"] == "bubble"
    pay = R.payment_qr_flex(
        order_code="X1",
        amount="100",
        promptpay_id="0812345678",
        qr_image_url="https://cdn.example/q.png",
    )
    assert pay["contents"]["hero"]["url"].startswith("https://")


def test_session_store_save_roundtrip():
    store = SessionStore()
    s = store.get("U1")
    s.state = "checkout_phone"
    s.data["phone"] = "0811111111"
    store.save("U1", s)
    s2 = store.get("U1")
    assert s2.state == "checkout_phone"
    assert s2.data["phone"] == "0811111111"


def test_redis_session_store_with_fake_redis():
    class FakeRedis:
        def __init__(self):
            self.data = {}

        def get(self, k):
            return self.data.get(k)

        def setex(self, k, ttl, v):
            self.data[k] = v if isinstance(v, (bytes, str)) else str(v)

        def delete(self, *keys):
            for k in keys:
                self.data.pop(k, None)

        def scan_iter(self, match=None):
            return list(self.data.keys())

    store = RedisSessionStore(FakeRedis(), ttl_seconds=60)
    s = store.get("Uredis")
    s.state = "support_wait_body"
    store.save("Uredis", s)
    s2 = store.get("Uredis")
    assert s2.state == "support_wait_body"
    store.clear("Uredis")
    assert store.get("Uredis").state == "idle"


@pytest.mark.asyncio
async def test_messenger_send_flex():
    posts: list = []

    async def poster(url, payload, headers):
        posts.append(payload)
        return 200

    m = LineMessenger(
        channel_access_token="t",
        reply_url="https://api.line.me/v2/bot/message/reply",
        push_url="https://api.line.me/v2/bot/message/push",
        http_post=poster,
    )
    m.set_reply_token("rt-flex")
    ok = await m.send_flex("U1", R.welcome_flex("Shop"))
    assert ok is True
    assert posts[0]["replyToken"] == "rt-flex"
    assert posts[0]["messages"][0]["type"] == "flex"


@pytest.mark.asyncio
async def test_line_qr_media_route(tmp_path, monkeypatch):
    monkeypatch.setattr("bot.channels.line.qr_host._CACHE_DIR", tmp_path)
    monkeypatch.setattr("bot.channels.line.qr_host._META", {})
    from bot.channels.line import qr_host as qh

    url = qh.store_qr_png("Z9", b"png-bytes-here")
    token = url.rsplit("/", 1)[-1].replace(".png", "")
    app = web.Application()
    register_public_catalog_routes(app)
    client = await _client_for(app)
    try:
        resp = await client.get(f"/media/line-qr/{token}.png")
        assert resp.status == 200
        assert await resp.read() == b"png-bytes-here"
        assert resp.headers.get("Content-Type", "").startswith("image/png")
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_adapter_promptpay_sends_qr_image(db_with_roles, db_engine, tmp_path, monkeypatch):
    monkeypatch.setattr("bot.channels.line.qr_host._CACHE_DIR", tmp_path)
    monkeypatch.setattr("bot.channels.line.qr_host._META", {})
    monkeypatch.setenv("PUBLIC_MEDIA_BASE_URL", "https://cdn.example")

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
    ad = LineAdapter(config=_cfg(use_flex=True), messenger=messenger, sessions=store)
    uid = "Upay_line_1"
    # prime checkout state
    sess = store.get(uid)
    sess.state = "checkout_pay"
    sess.data["phone"] = "0812345678"
    sess.data["address"] = "123 Test Rd Bangkok"
    store.save(uid, sess)

    cart_data = {
        "empty": False,
        "items": [{"item_name": "Tea", "quantity": 1, "price": "50", "total": "50"}],
        "total": "50",
        "total_decimal": Decimal("50"),
    }
    order_res = ServiceResult.success(
        order_code="LNORD01",
        payment_method="promptpay",
        final_amount="50",
    )
    qr_res = ServiceResult.success(
        order_code="LNORD01",
        amount="50",
        promptpay_id="0812345678",
        qr_bytes=b"\x89PNG\r\nfakeqr",
        has_dynamic_qr=True,
    )
    with (
        patch("bot.channels.line.adapter.cart_svc.list_items", new=AsyncMock(return_value=ServiceResult.success(**cart_data))),
        patch("bot.channels.line.adapter.checkout_svc.ensure_delivery_profile", return_value=ServiceResult.success()),
        patch("bot.channels.line.adapter.checkout_svc.start_promptpay_order", return_value=order_res),
        patch("bot.channels.line.adapter.checkout_svc.build_promptpay_qr_payload", return_value=qr_res),
    ):
        await ad.handle_event(
            {
                "type": "postback",
                "replyToken": "rpay",
                "source": {"userId": uid},
                "postback": {"data": "LN_PAY_PROMPTPAY"},
            }
        )
    # Expect at least one image message in outbound
    types = []
    for p in posts:
        for m in p.get("messages") or []:
            types.append(m.get("type"))
    assert "image" in types or "flex" in types

