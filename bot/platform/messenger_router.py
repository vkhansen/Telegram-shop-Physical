"""Multi-channel customer notify router (CARD-33).

Order status from Telegram ops must reach customers on their linked platform
(Instagram PSID, Telegram id, …). Groups (kitchen/rider) stay on Telegram.
"""

from __future__ import annotations

import logging
from typing import Any

from bot.platform.identity import (
    PLATFORM_INSTAGRAM,
    PLATFORM_LINE,
    PLATFORM_TELEGRAM,
    list_identities,
)
from bot.platform.messaging import (
    ButtonSpec,
    DeliveryTarget,
    Messenger,
    OutboundMessage,
    TransportRegistry,
    default_registry,
    get_messenger,
)

logger = logging.getLogger(__name__)

# Preference when multiple identities exist
_CUSTOMER_CHANNEL_ORDER = (
    PLATFORM_INSTAGRAM,
    PLATFORM_LINE,
    "whatsapp",
    PLATFORM_TELEGRAM,
    "web",
)


def preferred_customer_channel(user_id: int) -> tuple[str, str] | None:
    """
    Return ``(channel, external_id)`` for outbound customer DM.

    Prefers Instagram (and other messaging) over Telegram dual-write so pure-IG
    users receive status; falls back to Telegram when present.
    """
    ids = list_identities(user_id)
    if not ids:
        # Legacy: user_id is telegram_id
        return (PLATFORM_TELEGRAM, str(int(user_id)))
    by_plat = {r["platform"]: r["external_id"] for r in ids}
    for ch in _CUSTOMER_CHANNEL_ORDER:
        if ch in by_plat:
            return (ch, by_plat[ch])
    # any remaining
    first = ids[0]
    return (first["platform"], first["external_id"])


async def notify_user(
    user_id: int,
    text: str,
    *,
    buttons: ButtonSpec | None = None,
    messenger: Messenger | None = None,
    registry: TransportRegistry | None = None,
    prefer_channel: str | None = None,
) -> bool:
    """
    Send a customer DM on the best linked channel.

    *messenger* is used for Telegram (and as fallback).
    *registry* holds non-Telegram transports (e.g. InstagramMessenger).
    """
    reg = registry if registry is not None else default_registry
    m = messenger if messenger is not None else get_messenger()

    dest = preferred_customer_channel(int(user_id))
    if prefer_channel:
        ids = {r["platform"]: r["external_id"] for r in list_identities(int(user_id))}
        if prefer_channel in ids:
            dest = (prefer_channel, ids[prefer_channel])
    if not dest:
        return False
    channel, external_id = dest

    if channel == PLATFORM_TELEGRAM:
        try:
            return await m.send_text(int(external_id), text, buttons=buttons)
        except (TypeError, ValueError):
            return await m.send_text(external_id, text, buttons=buttons)

    transport = reg.get(channel)
    if transport is not None:
        ok = await transport.send(
            DeliveryTarget(channel=channel, external_id=external_id),
            OutboundMessage(text=text, metadata={"buttons": buttons}),
        )
        if ok:
            return True
        logger.warning("transport send failed channel=%s user_id=%s", channel, user_id)

    # Fallback: Telegram identity if different from preferred
    ids = {r["platform"]: r["external_id"] for r in list_identities(int(user_id))}
    if PLATFORM_TELEGRAM in ids and channel != PLATFORM_TELEGRAM:
        try:
            return await m.send_text(int(ids[PLATFORM_TELEGRAM]), text, buttons=buttons)
        except Exception:
            logger.exception("telegram fallback notify failed user_id=%s", user_id)
    return False


def register_customer_transport(transport: Any) -> None:
    """Register a MessageTransport on the process-wide registry."""
    default_registry.register(transport)
