"""
Tests for bot/utils/user_utils.py - get_telegram_username() function.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from bot.utils.user_utils import get_telegram_username


@pytest.mark.unit
class TestGetTelegramUsername:
    """Tests for get_telegram_username()"""

    @pytest.mark.asyncio
    async def test_returns_username_when_available(self):
        bot = AsyncMock()
        chat = MagicMock()
        chat.username = "testuser"
        bot.get_chat.return_value = chat

        result = await get_telegram_username(123456, bot)
        assert result == "testuser"
        bot.get_chat.assert_called_once_with(123456)

    @pytest.mark.asyncio
    async def test_returns_fallback_when_no_username(self):
        bot = AsyncMock()
        chat = MagicMock()
        chat.username = None
        bot.get_chat.return_value = chat

        result = await get_telegram_username(123456, bot)
        assert result == "user_123456"

    @pytest.mark.asyncio
    async def test_returns_fallback_on_exception(self):
        bot = AsyncMock()
        bot.get_chat.side_effect = Exception("API error")

        result = await get_telegram_username(123456, bot)
        assert result == "user_123456"

    @pytest.mark.asyncio
    async def test_returns_fallback_on_telegram_error(self):
        bot = AsyncMock()
        bot.get_chat.side_effect = RuntimeError("User not found")

        result = await get_telegram_username(999999, bot)
        assert result == "user_999999"

    @pytest.mark.asyncio
    async def test_fallback_format_uses_telegram_id(self):
        bot = AsyncMock()
        bot.get_chat.side_effect = Exception("fail")

        result = await get_telegram_username(42, bot)
        assert result == "user_42"

    @pytest.mark.asyncio
    async def test_returns_username_without_at_prefix(self):
        """Username returned by Telegram API should not have @ prefix"""
        bot = AsyncMock()
        chat = MagicMock()
        chat.username = "john_doe"  # Telegram API returns without @
        bot.get_chat.return_value = chat

        result = await get_telegram_username(123, bot)
        assert not result.startswith("@")
        assert result == "john_doe"

    @pytest.mark.asyncio
    async def test_empty_string_username_returns_fallback(self):
        """Empty string username is falsy, should return fallback"""
        bot = AsyncMock()
        chat = MagicMock()
        chat.username = ""
        bot.get_chat.return_value = chat

        result = await get_telegram_username(123, bot)
        # Empty string is falsy in Python, so it falls through to fallback
        assert result == "user_123"
