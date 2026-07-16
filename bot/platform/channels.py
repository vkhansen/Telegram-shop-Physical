"""Surface / channel identifiers (not product verticals).

Each brand can enable a subset of channels and mask capabilities per channel
via ``web_profile.channels``.
"""

from __future__ import annotations

from typing import Literal

ChannelId = Literal["web", "telegram", "line", "whatsapp", "instagram"]

CHANNELS: tuple[str, ...] = ("web", "telegram", "line", "whatsapp", "instagram")

# Default: web + telegram on for existing shops; others opt-in.
DEFAULT_CHANNEL_ENABLED: dict[str, bool] = {
    "web": True,
    "telegram": True,
    "line": False,
    "whatsapp": False,
    "instagram": False,
}


def normalize_channel(channel: str | None) -> str:
    c = (channel or "web").strip().lower()
    if c not in CHANNELS:
        return "web"
    return c
