"""Auth + ticket HTTP API for white-label storefront (CARD-39)."""

from __future__ import annotations

import logging
import os
import secrets
from urllib.parse import urlencode

from aiohttp import web

from bot.services import tickets_web, web_auth

logger = logging.getLogger(__name__)

COOKIE = web_auth.SESSION_COOKIE


def register_auth_and_ticket_routes(app: web.Application) -> None:
    app.router.add_get("/api/public/auth/me", auth_me)
    app.router.add_post("/api/public/auth/logout", auth_logout)
    app.router.add_post("/api/public/auth/dev-login", auth_dev_login)
    app.router.add_get("/api/public/auth/google/start", google_start)
    app.router.add_get("/api/public/auth/google/callback", google_callback)
    app.router.add_get("/api/public/tickets", tickets_list)
    app.router.add_post("/api/public/tickets", tickets_create)
    app.router.add_get("/api/public/tickets/{code}", tickets_get)
    app.router.add_post("/api/public/tickets/{code}/messages", tickets_reply)
    app.router.add_post("/api/public/leads", create_lead)
    app.router.add_post("/api/public/bookings", create_booking)
    logger.info("Auth + ticket + lead/booking API routes registered")


def _session_from_request(request: web.Request) -> dict | None:
    return web_auth.verify_session(request.cookies.get(COOKIE))


def _set_session_cookie(response: web.Response, token: str) -> None:
    secure = os.getenv("WEB_COOKIE_SECURE", "false").lower() in ("1", "true", "yes")
    response.set_cookie(
        COOKIE,
        token,
        max_age=web_auth.SESSION_MAX_AGE,
        httponly=True,
        samesite="Lax",
        secure=secure,
        path="/",
    )


def _clear_session_cookie(response: web.Response) -> None:
    response.del_cookie(COOKIE, path="/")


async def auth_me(request: web.Request) -> web.Response:
    sess = _session_from_request(request)
    if not sess:
        return web.json_response({"authenticated": False}, status=401)
    profile = web_auth.get_profile(int(sess["uid"]))
    return web.json_response({"authenticated": True, "session": sess, "profile": profile})


async def auth_logout(request: web.Request) -> web.Response:
    resp = web.json_response({"ok": True})
    _clear_session_cookie(resp)
    return resp


async def auth_dev_login(request: web.Request) -> web.Response:
    if not web_auth.dev_login_enabled():
        return web.json_response({"error": "dev_login_disabled"}, status=403)
    try:
        body = await request.json()
    except Exception:
        body = {}
    email = (body.get("email") or "dev@example.com").strip().lower()
    name = (body.get("name") or "Dev User").strip()
    subject = f"dev:{email}"
    user = web_auth.upsert_oauth_user(
        provider="dev",
        subject=subject,
        email=email,
        email_verified=True,
        display_name=name,
        username=email.split("@")[0],
    )
    token = web_auth.create_session_token(
        user_id=user["user_id"],
        email=user.get("email"),
        name=user.get("name"),
        avatar=user.get("avatar"),
    )
    resp = web.json_response({"ok": True, "user": user})
    _set_session_cookie(resp, token)
    return resp


async def google_start(request: web.Request) -> web.Response:
    if not web_auth.google_enabled():
        return web.json_response({"error": "google_oauth_not_configured"}, status=503)
    brand = request.query.get("brand", "")
    next_path = request.query.get("next", f"/{brand}/tickets" if brand else "/")
    redirect_uri = os.getenv("OAUTH_GOOGLE_REDIRECT_URI") or str(
        request.url.with_path("/api/public/auth/google/callback").with_query({})
    )
    state = secrets.token_urlsafe(24)
    # store state in short-lived cookie
    url = web_auth.google_authorize_url(redirect_uri=redirect_uri, state=state)
    resp = web.HTTPFound(url)
    resp.set_cookie("oauth_state", state, max_age=600, httponly=True, samesite="Lax", path="/")
    resp.set_cookie("oauth_next", next_path, max_age=600, httponly=True, samesite="Lax", path="/")
    resp.set_cookie("oauth_brand", brand, max_age=600, httponly=True, samesite="Lax", path="/")
    return resp


async def google_callback(request: web.Request) -> web.Response:
    if not web_auth.google_enabled():
        return web.json_response({"error": "google_oauth_not_configured"}, status=503)
    state = request.query.get("state", "")
    cookie_state = request.cookies.get("oauth_state", "")
    if not state or state != cookie_state:
        return web.json_response({"error": "invalid_state"}, status=400)
    code = request.query.get("code")
    if not code:
        return web.json_response({"error": "missing_code"}, status=400)
    redirect_uri = os.getenv("OAUTH_GOOGLE_REDIRECT_URI") or str(
        request.url.with_path("/api/public/auth/google/callback").with_query({})
    )
    info = await web_auth.google_exchange_code(code=code, redirect_uri=redirect_uri)
    if not info or not info.get("sub"):
        return web.json_response({"error": "oauth_failed"}, status=400)
    user = web_auth.upsert_oauth_user(
        provider="google",
        subject=str(info["sub"]),
        email=info.get("email"),
        email_verified=bool(info.get("email_verified")),
        display_name=info.get("name"),
        username=info.get("email", "").split("@")[0] if info.get("email") else None,
        avatar_url=info.get("picture"),
        raw_claims=info,
    )
    token = web_auth.create_session_token(
        user_id=user["user_id"],
        email=user.get("email"),
        name=user.get("name"),
        avatar=user.get("avatar"),
    )
    next_path = request.cookies.get("oauth_next") or "/tickets"
    # Prefer storefront origin for redirect
    storefront = os.getenv("PUBLIC_SITE_URL", "http://127.0.0.1:4321").rstrip("/")
    if next_path.startswith("http"):
        dest = next_path
    else:
        dest = storefront + (next_path if next_path.startswith("/") else f"/{next_path}")
    resp = web.HTTPFound(dest)
    _set_session_cookie(resp, token)
    resp.del_cookie("oauth_state", path="/")
    resp.del_cookie("oauth_next", path="/")
    resp.del_cookie("oauth_brand", path="/")
    return resp


async def tickets_list(request: web.Request) -> web.Response:
    sess = _session_from_request(request)
    if not sess:
        return web.json_response({"error": "unauthorized"}, status=401)
    brand = request.query.get("brand")
    return web.json_response({"tickets": tickets_web.list_tickets(int(sess["uid"]), brand_slug=brand)})


async def tickets_create(request: web.Request) -> web.Response:
    sess = _session_from_request(request)
    if not sess:
        return web.json_response({"error": "unauthorized"}, status=401)
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "invalid_json"}, status=400)
    try:
        ticket = tickets_web.create_ticket(
            int(sess["uid"]),
            subject=body.get("subject", ""),
            message=body.get("message", ""),
            priority=body.get("priority", "normal"),
            brand_slug=body.get("brand_slug") or body.get("brand"),
        )
        return web.json_response(ticket, status=201)
    except ValueError as e:
        return web.json_response({"error": str(e)}, status=400)


async def tickets_get(request: web.Request) -> web.Response:
    sess = _session_from_request(request)
    if not sess:
        return web.json_response({"error": "unauthorized"}, status=401)
    code = request.match_info["code"]
    data = tickets_web.get_ticket(int(sess["uid"]), code)
    if not data:
        return web.json_response({"error": "not_found"}, status=404)
    return web.json_response(data)


async def tickets_reply(request: web.Request) -> web.Response:
    sess = _session_from_request(request)
    if not sess:
        return web.json_response({"error": "unauthorized"}, status=401)
    code = request.match_info["code"]
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "invalid_json"}, status=400)
    try:
        data = tickets_web.reply_ticket(int(sess["uid"]), code, body.get("message", ""))
    except ValueError as e:
        return web.json_response({"error": str(e)}, status=400)
    if not data:
        return web.json_response({"error": "not_found"}, status=404)
    return web.json_response(data)


async def create_lead(request: web.Request) -> web.Response:
    """Public lead capture (CARD-36) — auth optional."""
    from bot.services import leads_bookings

    sess = _session_from_request(request)
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "invalid_json"}, status=400)
    try:
        lead = leads_bookings.create_lead(
            brand_slug=body.get("brand_slug") or body.get("brand") or "",
            name=body.get("name", ""),
            preferred_channel=body.get("preferred_channel") or body.get("channel") or "phone",
            phone=body.get("phone"),
            email=body.get("email"),
            store_slug=body.get("store_slug") or body.get("store"),
            user_id=int(sess["uid"]) if sess else None,
            channel_handle=body.get("channel_handle"),
            interest_type=body.get("interest_type"),
            item_slug=body.get("item_slug") or body.get("item"),
            message=body.get("message"),
            source=body.get("source") or "web_site",
            utm=body.get("utm"),
            age_confirmed=bool(body.get("age_confirmed")),
            consent=bool(body.get("consent")),
        )
        return web.json_response(lead, status=201)
    except ValueError as e:
        return web.json_response({"error": str(e)}, status=400)
    except Exception:
        logger.exception("create_lead failed")
        return web.json_response({"error": "internal_error"}, status=500)


async def create_booking(request: web.Request) -> web.Response:
    """Meeting booking request (CARD-36)."""
    from bot.services import leads_bookings

    sess = _session_from_request(request)
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "invalid_json"}, status=400)
    try:
        booking = leads_bookings.create_booking(
            brand_slug=body.get("brand_slug") or body.get("brand") or "",
            name=body.get("name", ""),
            meeting_type=body.get("meeting_type") or body.get("type") or "in_person",
            phone=body.get("phone") or body.get("contact"),
            email=body.get("email"),
            store_slug=body.get("store_slug") or body.get("store"),
            user_id=int(sess["uid"]) if sess else None,
            preferred_when=body.get("preferred_when") or body.get("when"),
            notes=body.get("notes"),
        )
        return web.json_response(booking, status=201)
    except ValueError as e:
        return web.json_response({"error": str(e)}, status=400)
    except Exception:
        logger.exception("create_booking failed")
        return web.json_response({"error": "internal_error"}, status=500)
