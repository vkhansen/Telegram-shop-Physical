"""BotInstance dataclass — wraps a single Bot + Dispatcher pair (Card 19)."""
from dataclasses import dataclass, field

from aiogram import Bot, Dispatcher


@dataclass
class BotInstance:
    """One active bot identity.

    bot     — aiogram Bot object (holds the Telegram token + HTTP session)
    dp      — aiogram Dispatcher (shared handler tree; BrandContextMiddleware layered on top)
    brand_id — DB Brand.id this bot represents
    config_id — DB BotConfig.id
    bot_username — @handle from Telegram, e.g. "BrandXBot"
    """
    bot: Bot
    dp: Dispatcher
    brand_id: int
    config_id: int
    bot_username: str = ""
