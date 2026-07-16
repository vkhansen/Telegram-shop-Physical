"""Instagram Messaging adapter (CARD-33).

Masked customer channel on the same service bus as Telegram/web.
Enable with ``INSTAGRAM_CHANNEL_ENABLED=true``; flag-off has zero effect on TG.
"""

from bot.channels.instagram.config import InstagramConfig, load_instagram_config
from bot.channels.instagram.webhook import register_instagram_routes

__all__ = [
    "InstagramConfig",
    "load_instagram_config",
    "register_instagram_routes",
]
