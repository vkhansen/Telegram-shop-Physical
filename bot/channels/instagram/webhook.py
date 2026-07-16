"""Meta Instagram webhook routes (verify + receive)."""

from __future__ import annotations

import logging
from typing import Any

from aiohttp import web

from bot.channels.instagram.adapter import InstagramAdapter
from bot.channels.instagram.config import InstagramConfig, load_instagram_config
from bot.channels.instagram.signature import verify_hub_signature_256

logger = logging.getLogger(__name__)


def register_instagram_routes(
    app: web.Application,
    *,
    config: InstagramConfig | None = None,
    adapter: InstagramAdapter | None = None,
) -> bool:
    """
    Register GET/POST webhook when channel is enabled.

    Returns True if routes were mounted. Flag-off → no routes (zero TG impact).
    """
    cfg = config or load_instagram_config()
    if not cfg.enabled:
        logger.info("Instagram channel disabled (INSTAGRAM_CHANNEL_ENABLED=false)")
        return False

    ad = adapter or InstagramAdapter(config=cfg)
    path = cfg.webhook_path if cfg.webhook_path.startswith("/") else f"/{cfg.webhook_path}"

    async def verify(request: web.Request) -> web.Response:
        # Meta subscription verification
        mode = request.query.get("hub.mode")
        token = request.query.get("hub.verify_token")
        challenge = request.query.get("hub.challenge")
        if mode == "subscribe" and token and token == cfg.verify_token and challenge:
            return web.Response(text=str(challenge), content_type="text/plain")
        return web.Response(text="Forbidden", status=403)

    async def receive(request: web.Request) -> web.Response:
        body = await request.read()
        sig = request.headers.get("X-Hub-Signature-256") or request.headers.get("X-Hub-Signature")
        if not verify_hub_signature_256(app_secret=cfg.app_secret, body=body, header_value=sig):
            logger.warning("Instagram webhook bad signature")
            return web.json_response({"error": "invalid_signature"}, status=403)
        try:
            import json

            payload: dict[str, Any] = json.loads(body.decode("utf-8") or "{}")
        except Exception:
            return web.json_response({"error": "invalid_json"}, status=400)

        # Acknowledge quickly; process entries
        try:
            await _dispatch_payload(ad, payload)
        except Exception:
            logger.exception("Instagram webhook handler failed")
        return web.json_response({"ok": True})

    app.router.add_get(path, verify)
    app.router.add_post(path, receive)
    app["instagram_adapter"] = ad
    app["instagram_config"] = cfg
    logger.info("Instagram webhook registered at %s", path)
    return True


async def _dispatch_payload(adapter: InstagramAdapter, payload: dict[str, Any]) -> None:
    if payload.get("object") not in ("instagram", "page", None):
        # Still try messaging arrays for flexibility in tests
        pass
    for entry in payload.get("entry") or []:
        for event in entry.get("messaging") or []:
            if isinstance(event, dict):
                await adapter.handle_messaging_event(event)
