"""Channel-agnostic platform contracts for multi-surface white-label.

Telegram is *one* messaging adapter. Public web catalog, media, leads, tickets,
and capability masks must not depend on Telegram DTOs or handlers.

Use:
  - ``platform.capabilities.resolve_capabilities`` / ``can`` / ``features_for``
  - ``platform.deep_links`` for TG → web funnel URL buttons (CARD-40 E2)
  - ``platform.media_ref`` for storage refs (local / tg / https / …)
  - ``platform.channels`` for channel ids and defaults
  - ``platform.messaging.get_messenger`` for outbound DMs / groups (CARD-29)
"""

from bot.platform.capabilities import (
    CAPABILITY_KEYS,
    SHARED_PARITY_CAPS,
    TG_OPS_CAPS,
    WEB_ONLY_CAPS,
    can,
    cap_enabled,
    features_for,
    resolve_capabilities,
)
from bot.platform.deep_links import funnel_url_button, storefront_url
from bot.platform.channels import CHANNELS, ChannelId
from bot.platform.identity import (
    PLATFORM_INSTAGRAM,
    PLATFORM_LINE,
    PLATFORM_TELEGRAM,
    backfill_telegram_identities,
    ensure_instagram_user,
    ensure_line_user,
    ensure_telegram_identity,
    link_identity,
    list_identities,
    resolve_user_id,
)
from bot.platform.messenger_router import notify_user
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
    "PLATFORM_INSTAGRAM",
    "PLATFORM_LINE",
    "PLATFORM_TELEGRAM",
    "SHARED_PARITY_CAPS",
    "TG_OPS_CAPS",
    "WEB_ONLY_CAPS",
    "ButtonSpec",
    "Messenger",
    "backfill_telegram_identities",
    "can",
    "cap_enabled",
    "ensure_instagram_user",
    "ensure_line_user",
    "ensure_telegram_identity",
    "features_for",
    "funnel_url_button",
    "get_messenger",
    "link_identity",
    "list_identities",
    "notify_user",
    "resolve_user_id",
    "set_messenger",
    "storefront_url",
    "resolve_capabilities",
    "normalize_media_ref",
    "parse_media_ref",
    "media_url_for_ref",
]
