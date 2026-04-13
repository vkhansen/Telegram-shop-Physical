"""Tests for Grok AI admin assistant handler (Card 17).

Tests handler functions, pure utilities, and tool call processing.
All external I/O (Grok API, DB, Telegram) is mocked.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.handlers.admin.grok_assistant import (
    _handle_generate_images,
    _process_tool_call,
    _split_message,
    _trim_history,
    exit_assistant,
    exit_assistant_cb,
    handle_chat_message,
    start_assistant,
)
from bot.states.user_state import GrokAssistantStates


# ── Helpers ──────────────────────────────────────────────────────────


def _grok_response(content="Hello!", tool_calls=None):
    msg = {"role": "assistant", "content": content}
    if tool_calls:
        msg["tool_calls"] = tool_calls
    return {"choices": [{"message": msg}]}


def _tool_call(name, args_dict, call_id="tc_001"):
    return {
        "id": call_id,
        "function": {
            "name": name,
            "arguments": json.dumps(args_dict),
        },
    }


# ── _trim_history ─────────────────────────────────────────────────────


class TestTrimHistory:
    def _make_history(self, n_extra: int) -> list[dict]:
        """system message + n_extra user messages."""
        history = [{"role": "system", "content": "sys"}]
        for i in range(n_extra):
            history.append({"role": "user", "content": f"msg {i}"})
        return history

    def test_short_history_unchanged(self):
        history = self._make_history(10)
        assert _trim_history(history) == history

    def test_exactly_max_plus_one_not_trimmed(self):
        # MAX_HISTORY=50 → 51 messages total (system + 50 user) must NOT trim
        history = self._make_history(50)
        assert len(history) == 51
        result = _trim_history(history)
        assert result == history

    def test_exactly_max_plus_two_is_trimmed(self):
        # 52 messages → trimmed to system + 50 last
        history = self._make_history(51)
        assert len(history) == 52
        result = _trim_history(history)
        assert len(result) == 51
        assert result[0] == history[0]  # system preserved
        assert result[-1] == history[-1]  # last message preserved
        assert history[1] not in result  # second oldest dropped

    def test_very_long_history_keeps_system_and_last_50(self):
        history = self._make_history(100)
        result = _trim_history(history)
        assert len(result) == 51
        assert result[0]["role"] == "system"
        assert result[1:] == history[-50:]

    def test_empty_history_returned_unchanged(self):
        assert _trim_history([]) == []

    def test_system_only_unchanged(self):
        h = [{"role": "system", "content": "x"}]
        assert _trim_history(h) == h


# ── _split_message ────────────────────────────────────────────────────


class TestSplitMessage:
    def test_short_text_single_chunk(self):
        result = _split_message("hello world")
        assert result == ["hello world"]

    def test_exactly_max_len_single_chunk(self):
        text = "a" * 4000
        result = _split_message(text)
        assert result == [text]

    def test_long_text_splits_at_newline(self):
        chunk1 = "line1\n" * 800  # ~4800 chars
        result = _split_message(chunk1)
        assert len(result) > 1
        for chunk in result:
            assert len(chunk) <= 4000

    def test_no_newlines_splits_at_max_len(self):
        text = "x" * 8001
        result = _split_message(text, max_len=4000)
        assert len(result) == 3
        assert len(result[0]) == 4000
        assert len(result[1]) == 4000
        assert len(result[2]) == 1

    def test_custom_max_len(self):
        result = _split_message("abcdef", max_len=3)
        assert result == ["abc", "def"]

    def test_leading_newlines_stripped_between_chunks(self):
        # text that splits on a newline should not have leading newlines in next chunk
        text = ("a" * 3999) + "\n" + "b"
        result = _split_message(text)
        assert len(result) == 2
        assert result[1] == "b"

    def test_multiline_large_message(self):
        lines = ["word " * 100 for _ in range(50)]
        text = "\n".join(lines)
        result = _split_message(text)
        for chunk in result:
            assert len(chunk) <= 4000


# ── _process_tool_call ────────────────────────────────────────────────


class TestProcessToolCall:
    @pytest.mark.asyncio
    async def test_invalid_json_returns_error(self):
        tc = {"id": "tc1", "function": {"name": "search_orders", "arguments": "not valid json{"}}
        result = await _process_tool_call(tc, admin_id=1)
        assert "error" in result
        assert "JSON" in result["error"]

    @pytest.mark.asyncio
    async def test_unknown_tool_returns_error(self):
        tc = _tool_call("nonexistent_tool", {})
        result = await _process_tool_call(tc, admin_id=1)
        assert "error" in result
        assert "Unknown tool" in result["error"]

    @pytest.mark.asyncio
    async def test_validation_failure_returns_error_with_hint(self):
        # lookup_user requires telegram_id or phone_number; empty dict fails
        tc = _tool_call("lookup_user", {})
        result = await _process_tool_call(tc, admin_id=1)
        assert "error" in result
        assert "hint" in result

    @pytest.mark.asyncio
    async def test_valid_query_calls_execute_query(self):
        tc = _tool_call("search_orders", {})
        with patch("bot.handlers.admin.grok_assistant.execute_query", new_callable=AsyncMock) as mock_eq:
            mock_eq.return_value = {"orders": [], "count": 0}
            result = await _process_tool_call(tc, admin_id=1)
        mock_eq.assert_called_once()
        assert result == {"orders": [], "count": 0}

    @pytest.mark.asyncio
    async def test_valid_mutation_calls_execute_mutation(self):
        tc = _tool_call("create_item", {
            "item_name": "Test Item",
            "description": "A test",
            "price": "99.00",
            "category_name": "Food",
        })
        with patch("bot.handlers.admin.grok_assistant.execute_mutation", new_callable=AsyncMock) as mock_em:
            mock_em.return_value = {"success": True}
            result = await _process_tool_call(tc, admin_id=42)
        mock_em.assert_called_once()
        _, call_kwargs = mock_em.call_args
        # admin_id is second positional arg
        assert result == {"success": True}

    @pytest.mark.asyncio
    async def test_update_item_image_injects_photo_file_id(self):
        tc = _tool_call("update_item_image", {"item_name": "Burger"})
        with patch("bot.handlers.admin.grok_assistant.execute_mutation", new_callable=AsyncMock) as mock_em:
            mock_em.return_value = {"success": True}
            await _process_tool_call(tc, admin_id=1, photo_file_id="FILE123")
        validated_action = mock_em.call_args[0][0]
        assert validated_action.photo_file_id == "FILE123"

    @pytest.mark.asyncio
    async def test_update_item_image_no_photo_uses_none(self):
        tc = _tool_call("update_item_image", {"item_name": "Burger"})
        with patch("bot.handlers.admin.grok_assistant.execute_mutation", new_callable=AsyncMock) as mock_em:
            mock_em.return_value = {"success": True}
            await _process_tool_call(tc, admin_id=1, photo_file_id=None)
        validated_action = mock_em.call_args[0][0]
        assert validated_action.photo_file_id is None

    @pytest.mark.asyncio
    async def test_generate_item_images_delegates_to_handler(self):
        tc = _tool_call("generate_item_images", {"confirm": True, "all_missing": True})
        with patch(
            "bot.handlers.admin.grok_assistant._handle_generate_images",
            new_callable=AsyncMock,
        ) as mock_hgi:
            mock_hgi.return_value = {"success": True, "generated": 2}
            bot_mock = AsyncMock()
            result = await _process_tool_call(tc, admin_id=1, bot=bot_mock, chat_id=100)
        mock_hgi.assert_called_once()
        assert result == {"success": True, "generated": 2}

    @pytest.mark.asyncio
    async def test_view_inventory_is_query_not_mutation(self):
        tc = _tool_call("view_inventory", {})
        with patch("bot.handlers.admin.grok_assistant.execute_query", new_callable=AsyncMock) as mock_eq:
            mock_eq.return_value = {"items": []}
            result = await _process_tool_call(tc, admin_id=1)
        mock_eq.assert_called_once()
        assert result == {"items": []}


# ── start_assistant ───────────────────────────────────────────────────


class TestStartAssistant:
    @pytest.mark.asyncio
    async def test_no_api_key_sends_not_configured(self):
        callback = AsyncMock()
        callback.message = AsyncMock()
        state = AsyncMock()

        with patch("bot.handlers.admin.grok_assistant.EnvKeys") as mock_env:
            mock_env.GROK_API_KEY = None
            await start_assistant(callback, state)

        callback.message.edit_text.assert_called_once()
        text = callback.message.edit_text.call_args[0][0]
        assert "not configured" in text.lower() or "GROK_API_KEY" in text
        callback.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_empty_api_key_sends_not_configured(self):
        callback = AsyncMock()
        callback.message = AsyncMock()
        state = AsyncMock()

        with patch("bot.handlers.admin.grok_assistant.EnvKeys") as mock_env:
            mock_env.GROK_API_KEY = ""
            await start_assistant(callback, state)

        callback.message.edit_text.assert_called_once()
        callback.answer.assert_called_once()
        # state should not be changed
        state.set_state.assert_not_called()

    @pytest.mark.asyncio
    async def test_valid_api_key_sets_chatting_state(self):
        callback = AsyncMock()
        callback.message = AsyncMock()
        state = AsyncMock()

        with (
            patch("bot.handlers.admin.grok_assistant.EnvKeys") as mock_env,
            patch("bot.handlers.admin.grok_assistant._get_menu_context", return_value=([], [])),
            patch("bot.handlers.admin.grok_assistant.build_system_prompt", return_value="sys prompt"),
        ):
            mock_env.GROK_API_KEY = "sk-test"
            mock_env.PAY_CURRENCY = "THB"
            await start_assistant(callback, state)

        state.set_state.assert_called_once_with(GrokAssistantStates.chatting)
        callback.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_system_prompt_stored_in_history(self):
        callback = AsyncMock()
        callback.message = AsyncMock()
        state = AsyncMock()

        with (
            patch("bot.handlers.admin.grok_assistant.EnvKeys") as mock_env,
            patch("bot.handlers.admin.grok_assistant._get_menu_context", return_value=([], [])),
            patch("bot.handlers.admin.grok_assistant.build_system_prompt", return_value="MY SYSTEM PROMPT"),
        ):
            mock_env.GROK_API_KEY = "sk-test"
            mock_env.PAY_CURRENCY = "THB"
            await start_assistant(callback, state)

        update_call = state.update_data.call_args
        history = update_call[1]["grok_history"]
        assert history[0]["role"] == "system"
        assert history[0]["content"] == "MY SYSTEM PROMPT"

    @pytest.mark.asyncio
    async def test_pending_action_initialised_to_none(self):
        callback = AsyncMock()
        callback.message = AsyncMock()
        state = AsyncMock()

        with (
            patch("bot.handlers.admin.grok_assistant.EnvKeys") as mock_env,
            patch("bot.handlers.admin.grok_assistant._get_menu_context", return_value=([], [])),
            patch("bot.handlers.admin.grok_assistant.build_system_prompt", return_value="sys"),
        ):
            mock_env.GROK_API_KEY = "sk-test"
            mock_env.PAY_CURRENCY = "USD"
            await start_assistant(callback, state)

        update_call = state.update_data.call_args
        assert update_call[1]["pending_action"] is None

    @pytest.mark.asyncio
    async def test_welcome_message_sent(self):
        callback = AsyncMock()
        callback.message = AsyncMock()
        state = AsyncMock()

        with (
            patch("bot.handlers.admin.grok_assistant.EnvKeys") as mock_env,
            patch("bot.handlers.admin.grok_assistant._get_menu_context", return_value=([], [])),
            patch("bot.handlers.admin.grok_assistant.build_system_prompt", return_value="sys"),
        ):
            mock_env.GROK_API_KEY = "sk-test"
            mock_env.PAY_CURRENCY = "THB"
            await start_assistant(callback, state)

        callback.message.edit_text.assert_called_once()
        text = callback.message.edit_text.call_args[0][0]
        assert "AI Assistant ready" in text


# ── exit_assistant ────────────────────────────────────────────────────


class TestExitAssistant:
    @pytest.mark.asyncio
    async def test_clears_state(self):
        message = AsyncMock()
        state = AsyncMock()
        await exit_assistant(message, state)
        state.clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_sends_closed_message(self):
        message = AsyncMock()
        state = AsyncMock()
        await exit_assistant(message, state)
        message.answer.assert_called_once()
        text = message.answer.call_args[0][0]
        assert "closed" in text.lower()


# ── exit_assistant_cb ─────────────────────────────────────────────────


class TestExitAssistantCb:
    @pytest.mark.asyncio
    async def test_clears_state(self):
        callback = AsyncMock()
        callback.message = AsyncMock()
        state = AsyncMock()
        await exit_assistant_cb(callback, state)
        state.clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_edits_message_to_closed(self):
        callback = AsyncMock()
        callback.message = AsyncMock()
        state = AsyncMock()
        await exit_assistant_cb(callback, state)
        callback.message.edit_text.assert_called_once()
        text = callback.message.edit_text.call_args[0][0]
        assert "closed" in text.lower()

    @pytest.mark.asyncio
    async def test_calls_callback_answer(self):
        callback = AsyncMock()
        callback.message = AsyncMock()
        state = AsyncMock()
        await exit_assistant_cb(callback, state)
        callback.answer.assert_called_once()


# ── handle_chat_message ───────────────────────────────────────────────


class TestHandleChatMessage:
    def _make_message(self, text="hello", has_photo=False):
        message = AsyncMock()
        message.text = text
        message.photo = None
        message.from_user = MagicMock()
        message.from_user.id = 99
        message.chat = MagicMock()
        message.chat.id = 100
        message.bot = AsyncMock()
        if has_photo:
            photo = MagicMock()
            photo.file_id = "photo_abc"
            message.photo = [photo]
        return message

    def _make_state(self, history=None):
        state = AsyncMock()
        state.get_data = AsyncMock(return_value={
            "grok_history": history or [{"role": "system", "content": "sys"}],
        })
        return state

    @pytest.mark.asyncio
    async def test_plain_text_response_sent_to_user(self):
        message = self._make_message("Hi Grok")
        state = self._make_state()

        with (
            patch("bot.handlers.admin.grok_assistant.extract_content", new_callable=AsyncMock, return_value="Hi Grok"),
            patch("bot.handlers.admin.grok_assistant.call_grok", new_callable=AsyncMock, return_value=_grok_response("Hey there!")),
        ):
            await handle_chat_message(message, state)

        message.answer.assert_called()
        all_text = " ".join(call[0][0] for call in message.answer.call_args_list)
        assert "Hey there!" in all_text

    @pytest.mark.asyncio
    async def test_api_error_sends_error_message(self):
        message = self._make_message()
        state = self._make_state()

        with (
            patch("bot.handlers.admin.grok_assistant.extract_content", new_callable=AsyncMock, return_value="test"),
            patch("bot.handlers.admin.grok_assistant.call_grok", new_callable=AsyncMock, side_effect=RuntimeError("timeout")),
        ):
            await handle_chat_message(message, state)

        message.answer.assert_called_once()
        text = message.answer.call_args[0][0]
        assert "error" in text.lower() or "timeout" in text

    @pytest.mark.asyncio
    async def test_api_error_returns_early_no_state_update(self):
        message = self._make_message()
        state = self._make_state()

        with (
            patch("bot.handlers.admin.grok_assistant.extract_content", new_callable=AsyncMock, return_value="x"),
            patch("bot.handlers.admin.grok_assistant.call_grok", new_callable=AsyncMock, side_effect=Exception("boom")),
        ):
            await handle_chat_message(message, state)

        state.update_data.assert_not_called()

    @pytest.mark.asyncio
    async def test_empty_content_uses_fallback_text(self):
        message = self._make_message()
        state = self._make_state()

        with (
            patch("bot.handlers.admin.grok_assistant.extract_content", new_callable=AsyncMock, return_value="q"),
            patch("bot.handlers.admin.grok_assistant.call_grok", new_callable=AsyncMock, return_value=_grok_response(content=None)),
        ):
            await handle_chat_message(message, state)

        all_text = " ".join(call[0][0] for call in message.answer.call_args_list)
        assert "didn't understand" in all_text or "rephrase" in all_text.lower()

    @pytest.mark.asyncio
    async def test_tool_call_processed_and_followup_sent(self):
        message = self._make_message()
        state = self._make_state()

        tc = _tool_call("search_orders", {})
        first_response = _grok_response(content=None, tool_calls=[tc])
        followup_response = _grok_response("Here are the orders.")

        call_grok_responses = [first_response, followup_response]

        with (
            patch("bot.handlers.admin.grok_assistant.extract_content", new_callable=AsyncMock, return_value="show orders"),
            patch("bot.handlers.admin.grok_assistant.call_grok", new_callable=AsyncMock, side_effect=call_grok_responses),
            patch("bot.handlers.admin.grok_assistant.execute_query", new_callable=AsyncMock, return_value={"orders": [], "count": 0}),
        ):
            await handle_chat_message(message, state)

        all_text = " ".join(call[0][0] for call in message.answer.call_args_list)
        assert "Here are the orders." in all_text

    @pytest.mark.asyncio
    async def test_history_saved_after_response(self):
        message = self._make_message("Hello")
        state = self._make_state()

        with (
            patch("bot.handlers.admin.grok_assistant.extract_content", new_callable=AsyncMock, return_value="Hello"),
            patch("bot.handlers.admin.grok_assistant.call_grok", new_callable=AsyncMock, return_value=_grok_response("Hi!")),
        ):
            await handle_chat_message(message, state)

        state.update_data.assert_called_once()
        saved_history = state.update_data.call_args[1]["grok_history"]
        assert any(m["role"] == "user" for m in saved_history)
        assert any(m["role"] == "assistant" for m in saved_history)

    @pytest.mark.asyncio
    async def test_photo_message_captures_file_id(self):
        message = self._make_message(has_photo=True)
        state = self._make_state()

        tc = _tool_call("update_item_image", {"item_name": "Burger"})
        first_response = _grok_response(content=None, tool_calls=[tc])
        followup_response = _grok_response("Image updated.")

        with (
            patch("bot.handlers.admin.grok_assistant.extract_content", new_callable=AsyncMock, return_value="[photo]"),
            patch("bot.handlers.admin.grok_assistant.call_grok", new_callable=AsyncMock, side_effect=[first_response, followup_response]),
            patch("bot.handlers.admin.grok_assistant.execute_mutation", new_callable=AsyncMock, return_value={"success": True}) as mock_mut,
        ):
            await handle_chat_message(message, state)

        mock_mut.assert_called_once()
        validated_action = mock_mut.call_args[0][0]
        assert validated_action.photo_file_id == "photo_abc"

    @pytest.mark.asyncio
    async def test_followup_api_error_sends_partial_message(self):
        message = self._make_message()
        state = self._make_state()

        tc = _tool_call("search_orders", {})
        first_response = _grok_response(content=None, tool_calls=[tc])

        with (
            patch("bot.handlers.admin.grok_assistant.extract_content", new_callable=AsyncMock, return_value="x"),
            patch("bot.handlers.admin.grok_assistant.call_grok", new_callable=AsyncMock, side_effect=[first_response, Exception("followup fail")]),
            patch("bot.handlers.admin.grok_assistant.execute_query", new_callable=AsyncMock, return_value={"orders": []}),
        ):
            await handle_chat_message(message, state)

        all_text = " ".join(call[0][0] for call in message.answer.call_args_list)
        assert "follow-up failed" in all_text or "followup fail" in all_text

    @pytest.mark.asyncio
    async def test_nested_tool_calls_depth_loop(self):
        message = self._make_message()
        state = self._make_state()

        tc = _tool_call("search_orders", {})
        # Every call returns another tool_call until depth=3, then plain text
        tool_response = _grok_response(content=None, tool_calls=[tc])
        final_response = _grok_response("All done.")

        # first call_grok (initial) + 1 tool call follow-up chain of 3 + final = 5 calls
        responses = [tool_response, tool_response, tool_response, tool_response, final_response]

        with (
            patch("bot.handlers.admin.grok_assistant.extract_content", new_callable=AsyncMock, return_value="q"),
            patch("bot.handlers.admin.grok_assistant.call_grok", new_callable=AsyncMock, side_effect=responses),
            patch("bot.handlers.admin.grok_assistant.execute_query", new_callable=AsyncMock, return_value={"orders": []}),
        ):
            await handle_chat_message(message, state)

        # Should not loop forever — must terminate
        all_text = " ".join(call[0][0] for call in message.answer.call_args_list)
        assert all_text  # some reply was sent

    @pytest.mark.asyncio
    async def test_typing_action_sent(self):
        message = self._make_message()
        state = self._make_state()

        with (
            patch("bot.handlers.admin.grok_assistant.extract_content", new_callable=AsyncMock, return_value="hi"),
            patch("bot.handlers.admin.grok_assistant.call_grok", new_callable=AsyncMock, return_value=_grok_response("hey")),
        ):
            await handle_chat_message(message, state)

        message.bot.send_chat_action.assert_called()


# ── _handle_generate_images ───────────────────────────────────────────


class TestHandleGenerateImages:
    def _make_action(self, confirm=True, all_missing=True, item_names=None):
        from bot.ai.schemas import GenerateItemImagesAction
        return GenerateItemImagesAction(
            confirm=confirm,
            all_missing=all_missing,
            item_names=item_names or [],
        )

    @pytest.mark.asyncio
    async def test_confirm_false_returns_error(self):
        action = self._make_action(confirm=False, all_missing=True)
        result = await _handle_generate_images(action, admin_id=1, bot=AsyncMock(), chat_id=100)
        assert "error" in result
        assert "confirm" in result["error"].lower() or "True" in result["error"]

    @pytest.mark.asyncio
    async def test_bot_none_returns_error(self):
        action = self._make_action(confirm=True, all_missing=True)
        result = await _handle_generate_images(action, admin_id=1, bot=None, chat_id=100)
        assert "error" in result

    @pytest.mark.asyncio
    async def test_chat_id_none_returns_error(self):
        action = self._make_action(confirm=True, all_missing=True)
        result = await _handle_generate_images(action, admin_id=1, bot=AsyncMock(), chat_id=None)
        assert "error" in result

    @pytest.mark.asyncio
    async def test_all_missing_empty_list_returns_no_items_needed(self):
        action = self._make_action(confirm=True, all_missing=True)
        bot_mock = AsyncMock()

        with patch("bot.handlers.admin.grok_assistant.get_items_missing_images", return_value=[]):
            result = await _handle_generate_images(action, admin_id=1, bot=bot_mock, chat_id=100)

        assert result["success"] is True
        assert result["generated"] == 0

    @pytest.mark.asyncio
    async def test_all_missing_generates_all(self):
        action = self._make_action(confirm=True, all_missing=True)
        bot_mock = AsyncMock()
        items = [
            {"name": "A", "description": "desc A", "category_name": "Cat"},
            {"name": "B", "description": "desc B", "category_name": "Cat"},
        ]

        with (
            patch("bot.handlers.admin.grok_assistant.get_items_missing_images", return_value=items),
            patch(
                "bot.handlers.admin.grok_assistant.generate_and_save_item_image",
                new_callable=AsyncMock,
                return_value={"success": True},
            ),
        ):
            result = await _handle_generate_images(action, admin_id=1, bot=bot_mock, chat_id=100)

        assert result["success"] is True
        assert result["generated"] == 2
        assert result["failed"] == 0

    @pytest.mark.asyncio
    async def test_failed_item_counted_in_failed(self):
        action = self._make_action(confirm=True, all_missing=True)
        bot_mock = AsyncMock()
        items = [{"name": "X", "description": "d", "category_name": "C"}]

        with (
            patch("bot.handlers.admin.grok_assistant.get_items_missing_images", return_value=items),
            patch(
                "bot.handlers.admin.grok_assistant.generate_and_save_item_image",
                new_callable=AsyncMock,
                return_value={"success": False, "error": "API limit"},
            ),
        ):
            result = await _handle_generate_images(action, admin_id=1, bot=bot_mock, chat_id=100)

        assert result["generated"] == 0
        assert result["failed"] == 1
        assert result["failed_items"][0]["item"] == "X"

    @pytest.mark.asyncio
    async def test_exception_during_generation_counted_as_failed(self):
        action = self._make_action(confirm=True, all_missing=True)
        bot_mock = AsyncMock()
        items = [{"name": "Y", "description": "d", "category_name": "C"}]

        with (
            patch("bot.handlers.admin.grok_assistant.get_items_missing_images", return_value=items),
            patch(
                "bot.handlers.admin.grok_assistant.generate_and_save_item_image",
                new_callable=AsyncMock,
                side_effect=RuntimeError("crash"),
            ),
        ):
            result = await _handle_generate_images(action, admin_id=1, bot=bot_mock, chat_id=100)

        assert result["failed"] == 1
        assert "crash" in result["failed_items"][0]["error"]

    @pytest.mark.asyncio
    async def test_specific_item_names_found_in_db(self):
        action = self._make_action(confirm=True, all_missing=False, item_names=["Pad Thai"])
        bot_mock = AsyncMock()

        mock_goods = MagicMock()
        mock_goods.name = "Pad Thai"
        mock_goods.description = "Noodles"
        mock_goods.category_name = "Mains"

        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session.query.return_value.filter.return_value.first.return_value = mock_goods

        with (
            patch("bot.handlers.admin.grok_assistant.Database") as mock_db,
            patch(
                "bot.handlers.admin.grok_assistant.generate_and_save_item_image",
                new_callable=AsyncMock,
                return_value={"success": True},
            ),
        ):
            mock_db.return_value.session.return_value = mock_session
            result = await _handle_generate_images(action, admin_id=1, bot=bot_mock, chat_id=100)

        assert result["generated"] == 1
        assert "Pad Thai" in result["generated_items"]

    @pytest.mark.asyncio
    async def test_specific_item_name_not_found_returns_error(self):
        action = self._make_action(confirm=True, all_missing=False, item_names=["Ghost Item"])
        bot_mock = AsyncMock()

        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session.query.return_value.filter.return_value.first.return_value = None

        with patch("bot.handlers.admin.grok_assistant.Database") as mock_db:
            mock_db.return_value.session.return_value = mock_session
            result = await _handle_generate_images(action, admin_id=1, bot=bot_mock, chat_id=100)

        assert "error" in result
        assert "Ghost Item" in result["error"]
