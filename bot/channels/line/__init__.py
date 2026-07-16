"""LINE Messaging adapter (CARD-16).

Masked customer channel on the same service bus as Telegram / Instagram / web.
Enable with ``LINE_CHANNEL_ENABLED=true``; flag-off has zero effect on TG.
"""

from bot.channels.line.config import LineConfig, load_line_config
from bot.channels.line.webhook import register_line_routes

__all__ = [
    "LineConfig",
    "load_line_config",
    "register_line_routes",
]
