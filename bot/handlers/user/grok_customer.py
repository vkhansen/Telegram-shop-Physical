"""Grok AI Customer Shopping Assistant — Telegram handler (Card 22).

Entry points:
  - /ask command (any private chat)
  - callback_data == "ai_assistant_customer" (main menu button)
"""

import json
import logging
import time

from aiogram import F, Router
from aiogram.enums.chat_type import ChatType
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.ai.customer_executor import (
    execute_browse_menu,
    execute_check_coupon,
    execute_find_deals,
    execute_find_nearby_stores,
    execute_get_my_account,
    execute_get_order_status,
    execute_get_today_specials,
    execute_open_support_ticket,
    execute_start_app_live_chat,
    execute_start_store_live_chat,
)
from bot.ai.customer_schemas import CUSTOMER_TOOL_SCHEMA_MAP
from bot.ai.customer_tool_defs import CUSTOMER_TOOLS
from bot.ai.grok_client import call_grok
from bot.config.env import EnvKeys
from bot.handlers.user.ticket_handler import TicketStates, _get_maintainer_ids
from bot.keyboards.inline import back, simple_buttons
from bot.states.user_state import GrokCustomerStates

logger = logging.getLogger(__name__)
router = Router()

# Rate limit: 20 calls/hour per customer (configurable via env)
_GROK_CUSTOMER_RATE_LIMIT = EnvKeys.GROK_CUSTOMER_RATE_LIMIT
_GROK_RATE_WINDOW = 3600

_SYSTEM_PROMPT = """\
You are a friendly AI shopping assistant. You help customers find menu items, \
check available deals, look up their orders, and get support.

Rules:
- You can ONLY read catalog data and the current customer's own orders.
- You CANNOT modify prices, orders, or any menu items.
- Never reveal other customers' data.
- For support issues, always offer to open a ticket or start a live chat.
- Respond in the same language the customer writes in.
- Keep responses concise — Telegram messages are short.
- If the customer shares their location, use find_nearby_stores to help them.

Support routing:
- For app/bot/payment bugs → use start_app_live_chat (reaches platform developers)
- For order/food/delivery issues → use start_store_live_chat (reaches store staff)
- Either can be preceded by open_support_ticket to leave a written record first

Available tools: browse_menu, get_today_specials, find_deals, find_nearby_stores, \
check_coupon, get_order_status, get_my_account, open_support_ticket, \
start_app_live_chat, start_store_live_chat\
"""


def _check_rate_limit(state_data: dict) -> tuple[bool, int]:
    """Check per-customer Grok API call rate limit.

    Returns (allowed, seconds_until_reset).
    Updates grok_call_timestamps in-place inside state_data.
    """
    now = time.monotonic()
    timestamps: list[float] = state_data.get("grok_call_timestamps", [])
    timestamps = [t for t in timestamps if now - t < _GROK_RATE_WINDOW]
    if len(timestamps) >= _GROK_CUSTOMER_RATE_LIMIT:
        reset_in = int(_GROK_RATE_WINDOW - (now - timestamps[0]))
        state_data["grok_call_timestamps"] = timestamps
        return False, reset_in
    timestamps.append(now)
    state_data["grok_call_timestamps"] = timestamps
    return True, 0


def _trim_history(history: list[dict]) -> list[dict]:
    max_history = EnvKeys.GROK_MAX_HISTORY
    if len(history) <= max_history + 1:
        return history
    return [history[0]] + history[-(max_history):]


def _exit_keyboard():
    return simple_buttons([("❌ Exit AI Assistant", "exit_ai_customer")], per_row=1)


def _split_message(text: str, max_len: int = 4000) -> list[str]:
    if len(text) <= max_len:
        return [text]
    chunks = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break
        split_at = text.rfind("\n", 0, max_len)
        if split_at == -1:
            split_at = max_len
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip("\n")
    return chunks


# ── Entry points ──────────────────────────────────────────────────────────────

async def _start_customer_assistant(message: Message, state: FSMContext):
    """Shared setup for all entry points."""
    if not EnvKeys.GROK_API_KEY:
        await message.answer(
            "AI Assistant is not available right now. Please try again later."
        )
        return

    await state.set_state(GrokCustomerStates.chatting)
    await state.update_data(
        grok_history=[{"role": "system", "content": _SYSTEM_PROMPT}],
        grok_call_timestamps=[],
    )
    await message.answer(
        "Hi! I'm your AI shopping assistant. I can help you:\n"
        "- Find menu items by keyword, category, or price\n"
        "- Check what's available right now\n"
        "- Find deals and validate coupon codes\n"
        "- Look up your order status\n"
        "- Open a support ticket or start a live chat\n\n"
        "What can I help you with?",
        reply_markup=_exit_keyboard(),
    )


@router.message(Command("ask"), F.chat.type == ChatType.PRIVATE)
async def ask_command(message: Message, state: FSMContext):
    await state.clear()
    await _start_customer_assistant(message, state)


@router.callback_query(F.data == "ai_assistant_customer")
async def ai_assistant_button(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.clear()
    await _start_customer_assistant(call.message, state)


# ── Exit ──────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "exit_ai_customer")
async def exit_ai_customer(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("AI Assistant closed.", reply_markup=back("back_to_menu"))
    await call.answer()


@router.message(GrokCustomerStates.chatting, F.text == "/exit_ai")
async def exit_ai_command(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("AI Assistant closed.")


# ── Live chat relay ───────────────────────────────────────────────────────────

@router.message(GrokCustomerStates.app_live_chat, F.chat.type == ChatType.PRIVATE)
@router.message(GrokCustomerStates.store_live_chat, F.chat.type == ChatType.PRIVATE)
async def live_chat_relay(message: Message, state: FSMContext):
    """Relay customer messages to maintainers during live chat sessions."""
    data = await state.get_data()
    ticket_id = data.get("live_chat_ticket_id")
    ticket_code = data.get("live_chat_ticket_code")
    if not ticket_id:
        await state.clear()
        return

    if message.text == "/exit_ai":
        await state.clear()
        await message.answer("Live chat ended.")
        return

    user_id = message.from_user.id
    msg_text = message.text or message.caption or "(attachment)"
    photo_id = message.photo[-1].file_id if message.photo else None

    from bot.database import Database
    from bot.database.models.main import TicketMessage as TM
    with Database().session() as s:
        s.add(TM(
            ticket_id=ticket_id,
            sender_id=user_id,
            sender_role="user",
            message_text=msg_text,
        ))
        s.commit()

    relay = f"💬 [{ticket_code}] <b>User {user_id}:</b>\n{msg_text}"
    for mid in _get_maintainer_ids():
        try:
            if photo_id:
                await message.bot.send_photo(mid, photo_id, caption=relay)
            else:
                await message.bot.send_message(mid, relay)
        except Exception as e:
            logger.warning("Failed to relay to %s: %s", mid, e)

    support_chat = EnvKeys.SUPPORT_CHAT_ID
    if support_chat:
        try:
            if photo_id:
                await message.bot.send_photo(int(support_chat), photo_id, caption=relay)
            else:
                await message.bot.send_message(int(support_chat), relay)
        except Exception as e:
            logger.warning("Failed to relay to support chat: %s", e)

    await message.answer("✅ Message sent to support. They'll reply shortly.")


# ── Main chat loop ────────────────────────────────────────────────────────────

@router.message(GrokCustomerStates.chatting, F.chat.type == ChatType.PRIVATE)
async def handle_customer_message(message: Message, state: FSMContext):
    """Main conversation loop — every message goes through Grok."""
    data = await state.get_data()
    history: list[dict] = data.get("grok_history", [])

    # Rate limit check
    allowed, reset_in = _check_rate_limit(data)
    if not allowed:
        await state.update_data(grok_call_timestamps=data["grok_call_timestamps"])
        await message.answer(
            f"You've reached the AI request limit ({_GROK_CUSTOMER_RATE_LIMIT}/hour). "
            f"Please wait {reset_in // 60}m {reset_in % 60}s, or "
            f"open a support ticket if this is urgent.",
            reply_markup=_exit_keyboard(),
        )
        return

    # Extract user message text (handle location shares too)
    if message.location:
        user_text = (
            f"[Customer shared location: lat={message.location.latitude}, "
            f"lon={message.location.longitude}] Please use find_nearby_stores to help."
        )
    else:
        user_text = (message.text or message.caption or "").strip()
        if not user_text:
            await message.answer("Please send a text message.", reply_markup=_exit_keyboard())
            return

    history.append({"role": "user", "content": user_text})

    await message.bot.send_chat_action(message.chat.id, "typing")

    try:
        response = await call_grok(messages=history, tools=CUSTOMER_TOOLS)
    except Exception as e:
        logger.error("Grok API call failed: %s", e)
        await message.answer(
            "The AI service is temporarily unavailable. Please try again in a moment.",
            reply_markup=_exit_keyboard(),
        )
        return

    assistant_msg = response["choices"][0]["message"]
    history.append(assistant_msg)

    # Process tool calls
    if assistant_msg.get("tool_calls"):
        for tool_call in assistant_msg["tool_calls"]:
            result = await _process_tool_call(tool_call, message.from_user.id, message.bot, state)
            history.append({
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": json.dumps(result, default=str),
            })

            # Check if we entered live chat — stop the AI loop
            if result.get("_enter_live_chat"):
                history = _trim_history(history)
                await state.update_data(
                    grok_history=history,
                    grok_call_timestamps=data["grok_call_timestamps"],
                )
                return

        # Follow-up response from Grok after tool results
        try:
            await message.bot.send_chat_action(message.chat.id, "typing")
            followup = await call_grok(messages=history, tools=CUSTOMER_TOOLS)
            followup_msg = followup["choices"][0]["message"]
            history.append(followup_msg)

            depth = 0
            while followup_msg.get("tool_calls") and depth < 3:
                depth += 1
                for tc in followup_msg["tool_calls"]:
                    res = await _process_tool_call(tc, message.from_user.id, message.bot, state)
                    history.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": json.dumps(res, default=str),
                    })
                    if res.get("_enter_live_chat"):
                        history = _trim_history(history)
                        await state.update_data(
                            grok_history=history,
                            grok_call_timestamps=data["grok_call_timestamps"],
                        )
                        return
                await message.bot.send_chat_action(message.chat.id, "typing")
                followup = await call_grok(messages=history, tools=CUSTOMER_TOOLS)
                followup_msg = followup["choices"][0]["message"]
                history.append(followup_msg)

            reply_text = followup_msg.get("content") or "Done."
        except Exception as e:
            logger.error("Grok follow-up failed: %s", e)
            reply_text = "Action completed."
    else:
        reply_text = assistant_msg.get("content") or "I didn't quite understand. Could you rephrase?"

    history = _trim_history(history)
    await state.update_data(
        grok_history=history,
        grok_call_timestamps=data["grok_call_timestamps"],
    )

    for chunk in _split_message(reply_text):
        await message.answer(chunk, reply_markup=_exit_keyboard())


async def _process_tool_call(
    tool_call: dict,
    user_id: int,
    bot,
    state: FSMContext,
) -> dict:
    """Validate tool call against Pydantic schema and execute.

    Security: user_id always comes from Telegram auth (message.from_user.id),
    never from the AI payload.
    """
    func_name = tool_call["function"]["name"]

    try:
        args = json.loads(tool_call["function"]["arguments"])
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON in tool arguments: {e}"}

    schema_class = CUSTOMER_TOOL_SCHEMA_MAP.get(func_name)
    if not schema_class:
        return {"error": f"Unknown tool: {func_name}"}

    try:
        validated = schema_class.model_validate(args)
    except Exception as e:
        return {"error": "Validation failed", "details": str(e)}

    # Dispatch to executor
    if func_name == "browse_menu":
        return execute_browse_menu(validated)
    if func_name == "get_today_specials":
        return execute_get_today_specials(validated)
    if func_name == "find_deals":
        return execute_find_deals(validated)
    if func_name == "find_nearby_stores":
        return execute_find_nearby_stores(validated)
    if func_name == "check_coupon":
        return execute_check_coupon(validated)
    if func_name == "get_order_status":
        return execute_get_order_status(validated, user_id)
    if func_name == "get_my_account":
        return execute_get_my_account(user_id)
    if func_name == "open_support_ticket":
        return await execute_open_support_ticket(validated, user_id, bot)
    if func_name == "start_app_live_chat":
        result = await execute_start_app_live_chat(validated, user_id, bot)
        if result.get("success"):
            await _enter_live_chat(state, result, "app")
            result["_enter_live_chat"] = True
        return result
    if func_name == "start_store_live_chat":
        result = await execute_start_store_live_chat(validated, user_id, bot)
        if result.get("success"):
            await _enter_live_chat(state, result, "store")
            result["_enter_live_chat"] = True
        return result

    return {"error": f"Unhandled tool: {func_name}"}


async def _enter_live_chat(state: FSMContext, result: dict, chat_type: str) -> None:
    """Transition FSM into live chat state and send the UI to the user."""
    new_state = GrokCustomerStates.app_live_chat if chat_type == "app" else GrokCustomerStates.store_live_chat
    await state.set_state(new_state)
    await state.update_data(
        live_chat_ticket_id=result["ticket_id"],
        live_chat_ticket_code=result["ticket_code"],
    )
