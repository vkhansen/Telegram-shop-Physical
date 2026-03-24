"""Tests for bot.utils.message_utils — send_or_edit and safe_edit_text."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.exceptions import TelegramBadRequest

from bot.utils.message_utils import send_or_edit, safe_edit_text


@pytest.mark.unit
class TestSendOrEdit:
    """Tests for the send_or_edit helper."""

    @pytest.mark.asyncio
    async def test_edit_true_calls_edit_text(self):
        msg = AsyncMock()
        await send_or_edit(msg, "hello", reply_markup="kb", edit=True)
        msg.edit_text.assert_awaited_once_with("hello", reply_markup="kb")
        msg.answer.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_edit_false_calls_answer(self):
        msg = AsyncMock()
        await send_or_edit(msg, "hello", reply_markup="kb", edit=False)
        msg.answer.assert_awaited_once_with("hello", reply_markup="kb")
        msg.edit_text.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_edit_default_is_false(self):
        msg = AsyncMock()
        await send_or_edit(msg, "text")
        msg.answer.assert_awaited_once()
        msg.edit_text.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_edit_true_no_edit_text_attr_falls_back_to_answer(self):
        msg = MagicMock(spec=[])  # no edit_text attribute
        msg.answer = AsyncMock()
        await send_or_edit(msg, "text", edit=True)
        msg.answer.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_kwargs_passed_through(self):
        msg = AsyncMock()
        await send_or_edit(msg, "text", edit=True, parse_mode="HTML")
        msg.edit_text.assert_awaited_once_with("text", reply_markup=None, parse_mode="HTML")


@pytest.mark.unit
class TestSafeEditText:
    """Tests for the safe_edit_text helper."""

    @pytest.mark.asyncio
    async def test_successful_edit_returns_true(self):
        msg = AsyncMock()
        result = await safe_edit_text(msg, "new text", reply_markup="kb")
        assert result is True
        msg.edit_text.assert_awaited_once_with("new text", reply_markup="kb")

    @pytest.mark.asyncio
    async def test_not_modified_returns_false(self):
        msg = AsyncMock()
        msg.edit_text.side_effect = TelegramBadRequest(
            method="editMessageText",
            message="Bad Request: message is not modified",
        )
        result = await safe_edit_text(msg, "same text")
        assert result is False

    @pytest.mark.asyncio
    async def test_other_bad_request_reraises(self):
        msg = AsyncMock()
        msg.edit_text.side_effect = TelegramBadRequest(
            method="editMessageText",
            message="Bad Request: message to edit not found",
        )
        with pytest.raises(TelegramBadRequest):
            await safe_edit_text(msg, "text")
