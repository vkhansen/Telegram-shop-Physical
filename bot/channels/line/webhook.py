"""LINE Messaging API webhook (POST + signature)."""

from __future__ import annotations

import json
import logging
from typing import Any

from aiohttp import web

from bot.channels.line.adapter import LineAdapter
from bot.channels.line.config import LineConfig, load_line_config
from bot.channels.line.signature import verify_line_signature

logger = logging.getLogger(__name__)


def register_line_routes(
    app: web.Application,
    *,
    config: LineConfig | None = None,
    adapter: LineAdapter | None = None,
) -> bool:
    """
    Register POST webhook when channel is enabled.

    Returns True if routes were mounted. Flag-off → no routes (zero TG impact).
    """
    cfg = config or load_line_config()
    if not cfg.enabled:
        logger.info("LINE channel disabled (LINE_CHANNEL_ENABLED=false)")
        return False

    ad = adapter or LineAdapter(config=cfg)
    path = cfg.webhook_path if cfg.webhook_path.startswith("/") else f"/{cfg.webhook_path}"

    async def receive(request: web.Request) -> web.Response:
        body = await request.read()
        sig = request.headers.get("X-Line-Signature")
        if not verify_line_signature(
            channel_secret=cfg.channel_secret, body=body, header_value=sig
        ):
            logger.warning("LINE webhook bad signature")
            return web.json_response({"error": "invalid_signature"}, status=403)
        try:
            payload: dict[str, Any] = json.loads(body.decode("utf-8") or "{}")
        except Exception:
            return web.json_response({"error": "invalid_json"}, status=400)

        # destination = LINE bot/OA user id — used for multi-brand OA map
        destination = payload.get("destination")
        if isinstance(destination, str):
            ad.set_destination(destination)
        try:
            for event in payload.get("events") or []:
                if isinstance(event, dict):
                    await ad.handle_event(event, destination=destination if isinstance(destination, str) else None)
        except Exception:
            logger.exception("LINE webhook handler failed")
        # LINE expects 200 quickly
        return web.Response(text="OK", content_type="text/plain")

    async def health(request: web.Request) -> web.Response:
        """Optional GET for ops probes (LINE itself only POSTs)."""
        return web.json_response({"ok": True, "channel": "line", "enabled": True})

    app.router.add_post(path, receive)
    app.router.add_get(path, health)
    app["line_adapter"] = ad
    app["line_config"] = cfg
    logger.info("LINE webhook registered at %s", path)
    return True
