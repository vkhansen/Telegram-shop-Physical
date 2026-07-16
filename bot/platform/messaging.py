"""Messaging channel protocol — Telegram is an adapter, not the domain model.

CARD-29: domain/notify helpers depend on ``Messenger``, not aiogram Bot.
Future LINE / Instagram adapters implement the same protocol.

Also exposes a lower-level ``MessageTransport`` registry for multi-channel
routing (CARD-33 follow-up).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

# ---------------------------------------------------------------------------
# Low-level transport (channel registry)
# ---------------------------------------------------------------------------


@dataclass
class OutboundMessage:
    """Channel-agnostic outbound message."""

    text: str
    media_refs: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DeliveryTarget:
    """Where to send — identity is channel-scoped, not telegram_id-only."""

    channel: str  # web | telegram | line | …
    external_id: str
    brand_id: int | None = None
    locale: str | None = None


@runtime_checkable
class MessageTransport(Protocol):
    """Adapter interface for one messaging surface."""

    channel: str

    async def send(self, target: DeliveryTarget, message: OutboundMessage) -> bool:
        """Return True if accepted by the transport."""
        ...


class NullTransport:
    """No-op transport (tests / disabled channel)."""

    channel = "null"

    async def send(self, target: DeliveryTarget, message: OutboundMessage) -> bool:
        return False


class TransportRegistry:
    """Register channel transports; resolve by channel id."""

    def __init__(self) -> None:
        self._by_channel: dict[str, MessageTransport] = {}

    def register(self, transport: MessageTransport) -> None:
        self._by_channel[transport.channel] = transport

    def get(self, channel: str) -> MessageTransport | None:
        return self._by_channel.get(channel)

    async def send(self, target: DeliveryTarget, message: OutboundMessage) -> bool:
        t = self.get(target.channel)
        if not t:
            return False
        return await t.send(target, message)


# Process-wide registry (adapters register at bot startup)
default_registry = TransportRegistry()


# ---------------------------------------------------------------------------
# CARD-29 high-level Messenger port
# ---------------------------------------------------------------------------

UserRef = int | str
"""Customer destination: telegram_id today; opaque string for other channels later."""


@dataclass
class ButtonSpec:
    """Opaque button payload for adapters.

    *native* holds the channel-native markup (e.g. aiogram InlineKeyboardMarkup).
    Domain code should not construct Telegram types; adapters may set this when
    building keyboard helpers still live next to Telegram keyboards.
    """

    native: Any = None


@runtime_checkable
class Messenger(Protocol):
    """Outbound messaging port used by notify helpers and future multi-channel."""

    async def send_text(
        self,
        user_ref: UserRef,
        text: str,
        *,
        buttons: ButtonSpec | None = None,
    ) -> bool:
        """DM text to a user. Return True if accepted."""
        ...

    async def send_photo(
        self,
        user_ref: UserRef,
        photo: str,
        *,
        caption: str | None = None,
    ) -> bool:
        """DM photo. *photo* is a channel media id (Telegram file_id today)."""
        ...

    async def send_group(
        self,
        group_key: str,
        text: str,
        *,
        buttons: ButtonSpec | None = None,
    ) -> str | None:
        """
        Send to a named group (kitchen, rider) or raw chat id string.

        Returns platform message id as str, or None on failure.
        """
        ...


# Process-wide default messenger (lazy Telegram until overridden in tests)
_default_messenger: Messenger | None = None


def get_messenger() -> Messenger:
    """Return the process default Messenger (Telegram unless set_messenger)."""
    global _default_messenger
    if _default_messenger is None:
        from bot.platform.telegram_messenger import TelegramMessenger

        _default_messenger = TelegramMessenger()
    return _default_messenger


def set_messenger(messenger: Messenger | None) -> None:
    """Override default messenger (tests). Pass None to reset to lazy Telegram."""
    global _default_messenger
    _default_messenger = messenger


class RecordingMessenger:
    """In-memory Messenger for unit tests — records all outbound calls."""

    def __init__(self, *, succeed: bool = True) -> None:
        self.succeed = succeed
        self.texts: list[dict[str, Any]] = []
        self.photos: list[dict[str, Any]] = []
        self.groups: list[dict[str, Any]] = []
        self._group_seq = 0

    async def send_text(
        self,
        user_ref: UserRef,
        text: str,
        *,
        buttons: ButtonSpec | None = None,
    ) -> bool:
        self.texts.append({"user_ref": user_ref, "text": text, "buttons": buttons})
        return self.succeed

    async def send_photo(
        self,
        user_ref: UserRef,
        photo: str,
        *,
        caption: str | None = None,
    ) -> bool:
        self.photos.append({"user_ref": user_ref, "photo": photo, "caption": caption})
        return self.succeed

    async def send_group(
        self,
        group_key: str,
        text: str,
        *,
        buttons: ButtonSpec | None = None,
    ) -> str | None:
        self._group_seq += 1
        mid = str(self._group_seq)
        self.groups.append(
            {"group_key": group_key, "text": text, "buttons": buttons, "message_id": mid}
        )
        return mid if self.succeed else None
