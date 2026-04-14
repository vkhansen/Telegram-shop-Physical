"""BrandContextMiddleware — injects brand_id into every aiogram handler (Card 19).

Each Bot instance in BotPool has its own BrandContextMiddleware(brand_id=X).
Handlers receive brand_id via data["brand_id"].

In single-bot mode (MULTI_BOT_ENABLED=false), the middleware is also registered
with brand_id=1 so that all handlers have a consistent data["brand_id"] key.
"""
from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


class BrandContextMiddleware(BaseMiddleware):
    """Injects ``brand_id`` (and ``brand_context`` stub) into every handler data dict."""

    def __init__(self, brand_id: int):
        self._brand_id = brand_id
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        data["brand_id"] = self._brand_id
        return await handler(event, data)
