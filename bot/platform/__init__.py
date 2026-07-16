"""Channel-agnostic platform contracts for multi-surface white-label.

Telegram is *one* messaging adapter. Public web catalog, media, leads, tickets,
and capability masks must not depend on Telegram DTOs or handlers.

Use:
  - ``platform.capabilities.resolve_capabilities`` / ``can`` / ``features_for``
  - ``platform.media_ref`` for storage refs (local / tg / https / …)
  - ``platform.channels`` for channel ids and defaults
  - ``platform.messaging.get_messenger`` for outbound DMs / groups (CARD-29)
"""

from bot.platform.capabilities import (
    CAPABILITY_KEYS,
    can,
    cap_enabled,
    features_for,
    resolve_capabilities,
)
from bot.platform.channels import CHANNELS, ChannelId
from bot.platform.identity import (
    PLATFORM_TELEGRAM,
    backfill_telegram_identities,
    ensure_telegram_identity,
    link_identity,
    resolve_user_id,
)
from bot.platform.media_ref import media_url_for_ref, normalize_media_ref, parse_media_ref
from bot.platform.messaging import (
    ButtonSpec,
    Messenger,
    get_messenger,
    set_messenger,
)

__all__ = [
    "CAPABILITY_KEYS",
    "CHANNELS",
    "ChannelId",
    "PLATFORM_TELEGRAM",
    "ButtonSpec",
    "Messenger",
    "backfill_telegram_identities",
    "can",
    "cap_enabled",
    "ensure_telegram_identity",
    "features_for",
    "get_messenger",
    "link_identity",
    "resolve_user_id",
    "set_messenger",
    "resolve_capabilities",
    "normalize_media_ref",
    "parse_media_ref",
    "media_url_for_ref",
]
