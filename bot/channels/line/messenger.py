"""LINE Messaging API Messenger + MessageTransport (CARD-16 / CARD-29)."""

from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from bot.channels.line import renderer as R
from bot.platform.messaging import ButtonSpec, DeliveryTarget, OutboundMessage, UserRef

logger = logging.getLogger(__name__)

HttpPoster = Callable[[str, dict[str, Any], dict[str, str]], Awaitable[int]]


class LineMessenger:
    """Outbound LINE. *user_ref* is the LINE userId (U…)."""

    channel = "line"

    def __init__(
        self,
        *,
        channel_access_token: str,
        reply_url: str,
        push_url: str,
        http_post: HttpPoster | None = None,
    ) -> None:
        self._token = channel_access_token
        self._reply_url = reply_url
        self._push_url = push_url
        self._http_post = http_post
        self.sent: list[dict[str, Any]] = []
        # Last replyToken from inbound (optional one-shot reply)
        self._pending_reply_token: str | None = None

    def set_reply_token(self, token: str | None) -> None:
        self._pending_reply_token = (token or "").strip() or None

    def _auth_headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._token}",
        }

    def _message_body(self, text: str, buttons: ButtonSpec | None) -> dict[str, Any]:
        items = None
        if buttons and isinstance(buttons.native, dict):
            items = buttons.native.get("quickReply", {}).get("items") or buttons.native.get(
                "items"
            )
        elif buttons and isinstance(buttons.native, list):
            items = buttons.native
        return R.text_message(text, quick_items=items)

    async def _post(self, url: str, payload: dict[str, Any]) -> bool:
        if not self._token:
            logger.warning("LineMessenger: no channel access token")
            return False
        self.sent.append({"url": url, "payload": payload})
        headers = self._auth_headers()
        if self._http_post is not None:
            try:
                status = await self._http_post(url, payload, headers)
                return 200 <= int(status) < 300
            except Exception:
                logger.exception("LineMessenger http_post failed")
                return False
        try:
            import httpx

            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code >= 300:
                    logger.warning(
                        "LINE send failed status=%s body=%s",
                        resp.status_code,
                        resp.text[:300],
                    )
                return 200 <= resp.status_code < 300
        except Exception:
            logger.exception("LineMessenger send failed")
            return False

    async def send_text(
        self,
        user_ref: UserRef,
        text: str,
        *,
        buttons: ButtonSpec | None = None,
    ) -> bool:
        msg = self._message_body(text, buttons)
        # Prefer replyToken once if set (webhook response path)
        token = self._pending_reply_token
        if token:
            self._pending_reply_token = None
            return await self._post(
                self._reply_url,
                {"replyToken": token, "messages": [msg]},
            )
        return await self._post(
            self._push_url,
            {"to": str(user_ref), "messages": [msg]},
        )

    async def send_photo(
        self,
        user_ref: UserRef,
        photo: str,
        *,
        caption: str | None = None,
    ) -> bool:
        if photo.startswith("http://") or photo.startswith("https://"):
            msg: dict[str, Any] = {
                "type": "image",
                "originalContentUrl": photo,
                "previewImageUrl": photo,
            }
            token = self._pending_reply_token
            if token:
                self._pending_reply_token = None
                ok = await self._post(self._reply_url, {"replyToken": token, "messages": [msg]})
            else:
                ok = await self._post(self._push_url, {"to": str(user_ref), "messages": [msg]})
            if ok and caption:
                await self.send_text(user_ref, caption)
            return ok
        return await self.send_text(
            user_ref,
            (caption or "Image") + "\n(LINE needs a public HTTPS image URL.)",
        )

    async def send_group(
        self,
        group_key: str,
        text: str,
        *,
        buttons: ButtonSpec | None = None,
    ) -> str | None:
        logger.debug("LineMessenger.send_group ignored key=%s (ops stay on Telegram)", group_key)
        return None

    async def send(self, target: DeliveryTarget, message: OutboundMessage) -> bool:
        if target.channel != "line":
            return False
        return await self.send_text(target.external_id, message.text)
