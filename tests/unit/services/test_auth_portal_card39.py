"""CARD-39 portal polish — OAuth redirect harden, auth config, ticket session."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from bot.services import tickets_web, web_auth
from bot.web import auth_api


def test_safe_next_path_allows_relative():
    assert web_auth.safe_next_path("/snus-demo/tickets") == "/snus-demo/tickets"
    assert web_auth.safe_next_path("/a/b?x=1") == "/a/b?x=1"
    assert web_auth.safe_next_path("/path#frag") == "/path"


def test_safe_next_path_rejects_open_redirects():
    default = "/safe"
    assert web_auth.safe_next_path("https://evil.example/phish", default=default) == default
    assert web_auth.safe_next_path("//evil.example", default=default) == default
    assert web_auth.safe_next_path("\\\\evil", default=default) == default
    assert web_auth.safe_next_path("../escape", default=default) == default
    assert web_auth.safe_next_path("/ok/../nope", default=default) == default
    assert web_auth.safe_next_path("", default=default) == default
    assert web_auth.safe_next_path(None, default=default) == default


def test_auth_public_config_flags(monkeypatch):
    monkeypatch.delenv("OAUTH_GOOGLE_CLIENT_ID", raising=False)
    monkeypatch.delenv("OAUTH_GOOGLE_CLIENT_SECRET", raising=False)
    monkeypatch.setenv("OAUTH_DEV_LOGIN", "true")
    cfg = web_auth.auth_public_config()
    assert cfg["google_enabled"] is False
    assert cfg["dev_login_enabled"] is True
    assert cfg["session_cookie"] == web_auth.SESSION_COOKIE


def test_create_and_list_tickets_web(db_with_roles, db_engine):
    user = web_auth.upsert_oauth_user(
        provider="dev",
        subject="dev:portal@example.com",
        email="portal@example.com",
        email_verified=True,
        display_name="Portal User",
    )
    uid = user["user_id"]
    created = tickets_web.create_ticket(uid, "Help please", "Something broke")
    assert created["ticket_code"]
    assert created["status"] == "open"
    listed = tickets_web.list_tickets(uid)
    assert any(t["ticket_code"] == created["ticket_code"] for t in listed)
    detail = tickets_web.get_ticket(uid, created["ticket_code"])
    assert detail is not None
    assert detail["subject"] == "Help please"
    assert len(detail["messages"]) >= 1


def test_create_ticket_validation():
    with pytest.raises(ValueError, match="subject_and_message"):
        tickets_web.create_ticket(1, "", "")


async def _client_for(app: web.Application) -> TestClient:
    server = TestServer(app)
    client = TestClient(server)
    await client.start_server()
    return client


@pytest.mark.asyncio
async def test_auth_config_endpoint():
    app = web.Application()
    auth_api.register_auth_and_ticket_routes(app)
    client = await _client_for(app)
    try:
        with patch.dict(os.environ, {"OAUTH_DEV_LOGIN": "1"}, clear=False):
            # clear google
            os.environ.pop("OAUTH_GOOGLE_CLIENT_ID", None)
            os.environ.pop("OAUTH_GOOGLE_CLIENT_SECRET", None)
            res = await client.get("/api/public/auth/config")
            assert res.status == 200
            data = await res.json()
            assert "google_enabled" in data
            assert data["google_enabled"] is False
            assert data.get("dev_login_enabled") is True
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_auth_config_google_enabled(monkeypatch):
    monkeypatch.setenv("OAUTH_GOOGLE_CLIENT_ID", "cid.apps.googleusercontent.com")
    monkeypatch.setenv("OAUTH_GOOGLE_CLIENT_SECRET", "secret")
    monkeypatch.delenv("OAUTH_DEV_LOGIN", raising=False)
    app = web.Application()
    auth_api.register_auth_and_ticket_routes(app)
    client = await _client_for(app)
    try:
        res = await client.get("/api/public/auth/config")
        assert res.status == 200
        data = await res.json()
        assert data["google_enabled"] is True
    finally:
        await client.close()


def test_google_redirect_uri_prefers_public_site(monkeypatch):
    monkeypatch.setenv("PUBLIC_SITE_URL", "https://shop.example.ts.net")
    monkeypatch.delenv("OAUTH_GOOGLE_REDIRECT_URI", raising=False)
    # Minimal fake request (only used if PUBLIC_SITE_URL missing)
    class _Req:
        url = type("U", (), {"with_path": lambda self, p: type("U2", (), {"with_query": lambda self, q: "http://x/api"})()})()

    uri = auth_api._google_redirect_uri(_Req())
    assert uri == "https://shop.example.ts.net/api/public/auth/google/callback"


def test_oauth_error_redirect_goes_to_login(monkeypatch):
    monkeypatch.setenv("PUBLIC_SITE_URL", "https://shop.example.ts.net")
    resp = auth_api._oauth_error_redirect(error="invalid_state", brand="snus-demo")
    assert resp.status == 302
    assert "snus-demo/login" in resp.headers["Location"]
    assert "error=invalid_state" in resp.headers["Location"]


@pytest.mark.asyncio
async def test_tickets_require_session():
    app = web.Application()
    auth_api.register_auth_and_ticket_routes(app)
    client = await _client_for(app)
    try:
        res = await client.get("/api/public/tickets")
        assert res.status == 401
        body = await res.json()
        assert body.get("error") == "unauthorized"
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_dev_login_and_tickets_flow(db_with_roles, db_engine, monkeypatch):
    monkeypatch.setenv("OAUTH_DEV_LOGIN", "true")
    app = web.Application()
    auth_api.register_auth_and_ticket_routes(app)
    client = await _client_for(app)
    try:
        login = await client.post(
            "/api/public/auth/dev-login",
            json={"email": "portal-e2e@example.com", "name": "E2E"},
        )
        assert login.status == 200
        me = await client.get("/api/public/auth/me")
        assert me.status == 200
        me_data = await me.json()
        assert me_data["authenticated"] is True

        create = await client.post(
            "/api/public/tickets",
            json={"subject": "Portal test", "message": "Hello from polish tests"},
        )
        assert create.status == 201
        ticket = await create.json()
        code = ticket["ticket_code"]

        listed = await client.get("/api/public/tickets")
        assert listed.status == 200
        tickets = (await listed.json())["tickets"]
        assert any(t["ticket_code"] == code for t in tickets)

        got = await client.get(f"/api/public/tickets/{code}")
        assert got.status == 200
        detail = await got.json()
        assert detail["subject"] == "Portal test"

        reply = await client.post(
            f"/api/public/tickets/{code}/messages",
            json={"message": "Follow-up"},
        )
        assert reply.status == 200
        thread = await reply.json()
        assert any(m.get("message_text") == "Follow-up" for m in thread.get("messages") or [])
    finally:
        await client.close()


def test_google_callback_uses_safe_next(monkeypatch):
    """Regression: open redirects must not win via oauth_next cookie."""
    assert web_auth.safe_next_path("https://evil.test", default="/brand/tickets") == "/brand/tickets"
