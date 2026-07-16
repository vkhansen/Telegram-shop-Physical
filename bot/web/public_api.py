"""Public catalog HTTP handlers (CARD-38 Phase A).

Mounted on the monitoring aiohttp app under ``/api/public/*`` without API key auth.
"""

from __future__ import annotations

import logging

from aiohttp import web

from bot.services import catalog_public as catalog

logger = logging.getLogger(__name__)


@web.middleware
async def cors_public_middleware(request: web.Request, handler):
    """Allow storefront origin to call public API with cookies (CARD-39)."""
    import os

    origin = request.headers.get("Origin", "")
    allowed = os.getenv("PUBLIC_SITE_URL", "http://127.0.0.1:4321").rstrip("/")
    # Also allow localhost variant
    allowed_origins = {allowed, allowed.replace("127.0.0.1", "localhost"), "http://localhost:4321", "http://127.0.0.1:4321"}

    if request.method == "OPTIONS" and (
        request.path.startswith("/api/public/") or request.path.startswith("/media/")
    ):
        resp = web.Response(status=204)
    else:
        resp = await handler(request)

    if origin in allowed_origins or (origin and os.getenv("PUBLIC_CORS_ALLOW_ALL", "").lower() in ("1", "true")):
        resp.headers["Access-Control-Allow-Origin"] = origin or allowed
        resp.headers["Access-Control-Allow-Credentials"] = "true"
        resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        resp.headers["Vary"] = "Origin"
    return resp


def register_public_catalog_routes(app: web.Application) -> None:
    """Register unauthenticated public catalog + media routes on *app*."""
    # CORS for storefront ↔ API (credentials)
    if cors_public_middleware not in app.middlewares:
        app.middlewares.append(cors_public_middleware)

    app.router.add_route("OPTIONS", "/api/public/{tail:.*}", lambda r: web.Response(status=204))
    app.router.add_get("/api/public/brands", list_brands)
    app.router.add_get("/api/public/brands/{brand_slug}", get_brand)
    app.router.add_get("/api/public/brands/{brand_slug}/stores", list_stores)
    app.router.add_get("/api/public/brands/{brand_slug}/stores/{store_slug}", get_store_menu)
    app.router.add_get(
        "/api/public/brands/{brand_slug}/stores/{store_slug}/items/{item_slug}",
        get_item,
    )
    app.router.add_get("/media/{token}", serve_media)
    # CARD-39: OAuth session + ticket portal API
    from bot.web.auth_api import register_auth_and_ticket_routes

    register_auth_and_ticket_routes(app)
    logger.info("Public catalog + media + auth/ticket routes registered")


async def list_brands(_request: web.Request) -> web.Response:
    try:
        data = catalog.list_active_brands()
        return web.json_response({"brands": data})
    except Exception:
        logger.exception("list_brands failed")
        return web.json_response({"error": "internal_error"}, status=500)


async def get_brand(request: web.Request) -> web.Response:
    brand_slug = request.match_info["brand_slug"]
    try:
        data = catalog.get_brand_public(brand_slug)
        if not data:
            return web.json_response({"error": "not_found"}, status=404)
        return web.json_response(data)
    except Exception:
        logger.exception("get_brand failed slug=%s", brand_slug)
        return web.json_response({"error": "internal_error"}, status=500)


async def list_stores(request: web.Request) -> web.Response:
    brand_slug = request.match_info["brand_slug"]
    try:
        data = catalog.get_brand_public(brand_slug)
        if not data:
            return web.json_response({"error": "not_found"}, status=404)
        return web.json_response({"brand_slug": brand_slug, "stores": data["stores"]})
    except Exception:
        logger.exception("list_stores failed slug=%s", brand_slug)
        return web.json_response({"error": "internal_error"}, status=500)


async def get_store_menu(request: web.Request) -> web.Response:
    brand_slug = request.match_info["brand_slug"]
    store_slug = request.match_info["store_slug"]
    try:
        data = catalog.get_store_menu(brand_slug, store_slug)
        if not data:
            return web.json_response({"error": "not_found"}, status=404)
        return web.json_response(data)
    except Exception:
        logger.exception("get_store_menu failed %s/%s", brand_slug, store_slug)
        return web.json_response({"error": "internal_error"}, status=500)


async def get_item(request: web.Request) -> web.Response:
    brand_slug = request.match_info["brand_slug"]
    store_slug = request.match_info["store_slug"]
    item_slug = request.match_info["item_slug"]
    try:
        data = catalog.get_store_item(brand_slug, store_slug, item_slug)
        if not data:
            return web.json_response({"error": "not_found"}, status=404)
        return web.json_response(data)
    except Exception:
        logger.exception("get_item failed %s/%s/%s", brand_slug, store_slug, item_slug)
        return web.json_response({"error": "internal_error"}, status=500)


async def serve_media(request: web.Request) -> web.Response:
    """CARD-38 Phase B — serve allowlisted catalog Telegram files from cache/Telegram."""
    from bot.services.media_proxy import get_media_bytes

    token = request.match_info["token"]
    # strip optional extension if clients append .jpg
    if "." in token and not token.startswith("."):
        # only strip short extensions
        base, ext = token.rsplit(".", 1)
        if len(ext) <= 4 and ext.isalpha():
            token = base
    try:
        result = await get_media_bytes(token)
        if not result:
            return web.Response(status=404, text="not found")
        data, ctype = result
        return web.Response(
            body=data,
            content_type=ctype,
            headers={"Cache-Control": "public, max-age=86400"},
        )
    except Exception:
        logger.exception("serve_media failed token=%s", token[:20])
        return web.Response(status=500, text="error")
