"""Telegram adapter for the CARD-29 Messenger port.

Owns the shared Bot session. Domain/notify code must call ``get_messenger()``,
not construct Bot instances for outbound DMs.
"""

from __future__ import annotations

import logging
from typing import Any

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties

from bot.config.env import EnvKeys
from bot.platform.messaging import ButtonSpec, UserRef

logger = logging.getLogger(__name__)

_shared_bot: Bot | None = None

# Named groups used by kitchen/rider notify helpers
GROUP_KEY_ENV: dict[str, str] = {
    "kitchen": "KITCHEN_GROUP_ID",
    "rider": "RIDER_GROUP_ID",
}


def get_shared_bot() -> Bot:
    """
    Return a process-level Bot that reuses one aiohttp session.

    Prefer ``get_messenger()`` for new code. Kept public for inventory alerts
    and shutdown hooks that still need a raw Bot.
    """
    global _shared_bot
    if _shared_bot is None:
        _shared_bot = Bot(
            token=EnvKeys.TOKEN,
            default=DefaultBotProperties(parse_mode="HTML"),
        )
    return _shared_bot


async def close_shared_bot() -> None:
    """Call on shutdown to cleanly close the shared session."""
    global _shared_bot
    if _shared_bot is not None:
        await _shared_bot.session.close()
        _shared_bot = None


def _resolve_group_chat_id(group_key: str) -> int | None:
    """Map kitchen/rider keys (or raw numeric id) to a Telegram chat id."""
    key = (group_key or "").strip()
    if not key:
        return None
    env_attr = GROUP_KEY_ENV.get(key.lower())
    if env_attr:
        raw = getattr(EnvKeys, env_attr, None) or ""
        if not raw:
            return None
        try:
            return int(raw)
        except (TypeError, ValueError):
            logger.warning("Invalid %s value: %r", env_attr, raw)
            return None
    try:
        return int(key)
    except (TypeError, ValueError):
        return None


def _native_markup(buttons: ButtonSpec | None) -> Any:
    if buttons is None:
        return None
    return buttons.native


class TelegramMessenger:
    """Messenger implementation backed by aiogram Bot API."""

    channel = "telegram"

    def __init__(self, bot: Bot | None = None) -> None:
        self._bot = bot

    def _bot_or_shared(self) -> Bot:
        return self._bot if self._bot is not None else get_shared_bot()

    async def send_text(
        self,
        user_ref: UserRef,
        text: str,
        *,
        buttons: ButtonSpec | None = None,
    ) -> bool:
        try:
            await self._bot_or_shared().send_message(
                chat_id=int(user_ref),
                text=text,
                reply_markup=_native_markup(buttons),
            )
            return True
        except Exception as e:
            logger.warning("Telegram send_text failed user=%s: %s", user_ref, str(e)[:100])
            return False

    async def send_photo(
        self,
        user_ref: UserRef,
        photo: str,
        *,
        caption: str | None = None,
    ) -> bool:
        try:
            await self._bot_or_shared().send_photo(
                chat_id=int(user_ref),
                photo=photo,
                caption=caption,
            )
            return True
        except Exception as e:
            logger.warning("Telegram send_photo failed user=%s: %s", user_ref, str(e)[:100])
            return False

    async def send_group(
        self,
        group_key: str,
        text: str,
        *,
        buttons: ButtonSpec | None = None,
    ) -> str | None:
        chat_id = _resolve_group_chat_id(group_key)
        if chat_id is None:
            return None
        try:
            msg = await self._bot_or_shared().send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=_native_markup(buttons),
            )
            return str(msg.message_id)
        except Exception as e:
            logger.warning(
                "Telegram send_group failed group=%s: %s", group_key, str(e)[:100]
            )
            return None
