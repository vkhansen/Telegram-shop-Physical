"""Instagram Messenger + MessageTransport (CARD-33 / CARD-29 port)."""

from __future__ import annotations

import base64
import logging
from typing import Any, Callable, Awaitable

from bot.platform.messaging import (
    ButtonSpec,
    DeliveryTarget,
    OutboundMessage,
    UserRef,
)

logger = logging.getLogger(__name__)

# Optional injectable HTTP poster: async (url, json, headers) -> status_code
HttpPoster = Callable[[str, dict[str, Any], dict[str, str]], Awaitable[int]]


class InstagramMessenger:
    """Outbound IG Messaging API. *user_ref* is the Instagram PSID (str)."""

    channel = "instagram"

    def __init__(
        self,
        *,
        page_access_token: str,
        graph_messages_url: str,
        http_post: HttpPoster | None = None,
    ) -> None:
        self._token = page_access_token
        self._url = graph_messages_url
        self._http_post = http_post
        self.sent: list[dict[str, Any]] = []  # test visibility when using default mock

    async def _post(self, payload: dict[str, Any]) -> bool:
        if not self._token:
            logger.warning("InstagramMessenger: no page access token")
            return False
        url = f"{self._url}?access_token={self._token}"
        headers = {"Content-Type": "application/json"}
        self.sent.append(payload)
        if self._http_post is not None:
            try:
                status = await self._http_post(url, payload, headers)
                return 200 <= int(status) < 300
            except Exception:
                logger.exception("InstagramMessenger http_post failed")
                return False
        # Lazy real HTTP when no injector (production)
        try:
            import httpx

            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code >= 300:
                    logger.warning(
                        "IG send failed status=%s body=%s",
                        resp.status_code,
                        resp.text[:300],
                    )
                return 200 <= resp.status_code < 300
        except Exception:
            logger.exception("InstagramMessenger send failed")
            return False

    def _recipient(self, user_ref: UserRef) -> dict[str, str]:
        return {"id": str(user_ref)}

    async def send_text(
        self,
        user_ref: UserRef,
        text: str,
        *,
        buttons: ButtonSpec | None = None,
    ) -> bool:
        message: dict[str, Any] = {"text": (text or "")[:1000]}
        # Optional quick replies in ButtonSpec.native
        if buttons and isinstance(buttons.native, dict):
            qrs = buttons.native.get("quick_replies")
            if qrs:
                message["quick_replies"] = qrs
        elif buttons and isinstance(buttons.native, list):
            message["quick_replies"] = buttons.native
        return await self._post(
            {
                "recipient": self._recipient(user_ref),
                "messaging_type": "RESPONSE",
                "message": message,
            }
        )

    async def send_photo(
        self,
        user_ref: UserRef,
        photo: str,
        *,
        caption: str | None = None,
    ) -> bool:
        """*photo* is a public HTTPS URL, or ``data:image/png;base64,...`` (text fallback)."""
        if photo.startswith("http://") or photo.startswith("https://"):
            ok = await self._post(
                {
                    "recipient": self._recipient(user_ref),
                    "messaging_type": "RESPONSE",
                    "message": {
                        "attachment": {
                            "type": "image",
                            "payload": {"url": photo, "is_reusable": False},
                        }
                    },
                }
            )
            if ok and caption:
                await self.send_text(user_ref, caption)
            return ok
        # Cannot host raw bytes on Graph without URL — send caption + note
        note = caption or "Payment QR"
        if photo.startswith("data:"):
            return await self.send_text(
                user_ref,
                f"{note}\n(QR image must be hosted at a public URL for Instagram.)",
            )
        return await self.send_text(user_ref, f"{note}\n{photo}"[:1000])

    async def send_group(
        self,
        group_key: str,
        text: str,
        *,
        buttons: ButtonSpec | None = None,
    ) -> str | None:
        # Instagram has no kitchen/rider groups — ops stay on Telegram
        logger.debug("InstagramMessenger.send_group ignored key=%s", group_key)
        return None

    async def send(self, target: DeliveryTarget, message: OutboundMessage) -> bool:
        """MessageTransport interface."""
        if target.channel != "instagram":
            return False
        return await self.send_text(target.external_id, message.text)

    @staticmethod
    def qr_data_uri(qr_bytes: bytes) -> str:
        b64 = base64.b64encode(qr_bytes).decode("ascii")
        return f"data:image/png;base64,{b64}"
