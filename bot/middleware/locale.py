from typing import Dict, Any, Callable, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, CallbackQuery, Message

from bot.i18n import set_request_locale, get_user_locale


class LocaleMiddleware(BaseMiddleware):
    """Sets the per-request locale from the user's saved DB preference."""

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        user = None
        if isinstance(event, (Message, CallbackQuery)):
            user = event.from_user

        if user:
            saved_locale = get_user_locale(user.id)
            if saved_locale:
                set_request_locale(saved_locale)

        try:
            return await handler(event, data)
        finally:
            # Reset so it doesn't leak to another request in the same context
            set_request_locale(None)
