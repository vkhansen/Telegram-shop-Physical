"""Grok AI Admin Assistant — Telegram handler + conversation loop (Card 17).

Entry point: callback_data == "ai_assistant" from admin console.
"""

import json
import logging
import time

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.ai.data_parser import extract_content
from bot.ai.executor import execute_mutation, execute_query
from bot.ai.grok_client import call_grok
from bot.ai.image_gen import generate_and_save_item_image, get_items_missing_images
from bot.ai.prompts import build_system_prompt
from bot.ai.schemas import MUTATION_TOOLS, TOOL_SCHEMA_MAP
from bot.ai.tool_defs import ALL_TOOLS
from bot.config.env import EnvKeys
from bot.database import Database
from bot.database.models.main import Categories, Goods
from bot.filters import HasPermissionFilter
from bot.keyboards.inline import back
from bot.states.user_state import GrokAssistantStates

logger = logging.getLogger(__name__)
router = Router()


def _get_menu_context() -> tuple[list[dict], list[dict]]:
    """Load current categories and items for the system prompt."""
    with Database().session() as s:
        cats = s.query(Categories).order_by(Categories.sort_order).all()
        cat_list = [{"name": c.name} for c in cats]

        items = s.query(Goods).filter(Goods.is_active.is_(True)).order_by(Goods.name).all()
        item_list = [
            {
                "name": g.name,
                "price": str(g.price),
                "category_name": g.category_name,
                "stock_quantity": g.stock_quantity,
            }
            for g in items
        ]
    return cat_list, item_list


def _trim_history(history: list[dict]) -> list[dict]:
    """Keep system message + last GROK_MAX_HISTORY messages."""
    max_history = EnvKeys.GROK_MAX_HISTORY
    if len(history) <= max_history + 1:
        return history
    # Always keep system prompt (index 0)
    return [history[0]] + history[-(max_history):]


# Per-admin rate limit: 100 Grok API calls per 3600 seconds
_GROK_RATE_LIMIT = 100
_GROK_RATE_WINDOW = 3600


def _check_rate_limit(state_data: dict) -> tuple[bool, int]:
    """Check per-admin Grok API call rate limit.

    Returns (allowed, seconds_until_reset).
    Updates call_timestamps in-place.
    """
    now = time.monotonic()
    timestamps: list[float] = state_data.get("grok_call_timestamps", [])
    # Drop calls outside the rolling window
    timestamps = [t for t in timestamps if now - t < _GROK_RATE_WINDOW]
    if len(timestamps) >= _GROK_RATE_LIMIT:
        reset_in = int(_GROK_RATE_WINDOW - (now - timestamps[0]))
        state_data["grok_call_timestamps"] = timestamps
        return False, reset_in
    timestamps.append(now)
    state_data["grok_call_timestamps"] = timestamps
    return True, 0


def _exit_keyboard():
    return back("console", text="Exit AI Assistant")


# ── Entry Point ──────────────────────────────────────────────────────

@router.callback_query(
    F.data == "ai_assistant",
    HasPermissionFilter(permission=16),  # SHOP_MANAGE
)
async def start_assistant(callback: CallbackQuery, state: FSMContext):
    """Entry point from admin console."""
    if not EnvKeys.GROK_API_KEY:
        await callback.message.edit_text(
            "AI Assistant is not configured. Set GROK_API_KEY in .env.",
            reply_markup=back("console"),
        )
        await callback.answer()
        return

    categories, items = _get_menu_context()
    currency = EnvKeys.PAY_CURRENCY or "THB"
    system_prompt = build_system_prompt(categories, items, currency)

    await state.set_state(GrokAssistantStates.chatting)
    await state.update_data(
        grok_history=[{"role": "system", "content": system_prompt}],
        pending_action=None,
    )

    await callback.message.edit_text(
        "AI Assistant ready. You can:\n"
        "- Ask about orders, deliveries, or customers\n"
        "- Update menu items and prices\n"
        "- Send a CSV/file to import menu data\n"
        "- Ask anything about your shop data\n\n"
        "Type /exit_ai to leave.",
        reply_markup=_exit_keyboard(),
    )
    await callback.answer()


# ── Exit ─────────────────────────────────────────────────────────────

@router.message(GrokAssistantStates.chatting, F.text == "/exit_ai", HasPermissionFilter(permission=16))
@router.message(GrokAssistantStates.awaiting_confirmation, F.text == "/exit_ai", HasPermissionFilter(permission=16))
@router.message(GrokAssistantStates.awaiting_file, F.text == "/exit_ai", HasPermissionFilter(permission=16))
async def exit_assistant(message: Message, state: FSMContext):
    """Exit the AI assistant."""
    await state.clear()
    await message.answer("AI Assistant closed.", reply_markup=back("console"))


@router.callback_query(F.data == "exit_ai_assistant")
async def exit_assistant_cb(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("AI Assistant closed.", reply_markup=back("console"))
    await callback.answer()


# ── Main Chat Loop ───────────────────────────────────────────────────

@router.message(GrokAssistantStates.chatting, HasPermissionFilter(permission=16))
async def handle_chat_message(message: Message, state: FSMContext):
    """Main conversation loop — every message goes to Grok."""
    data = await state.get_data()
    history = data.get("grok_history", [])

    # Per-admin rate limit check (100 Grok API calls per hour)
    allowed, reset_in = _check_rate_limit(data)
    if not allowed:
        await state.update_data(grok_call_timestamps=data["grok_call_timestamps"])
        await message.answer(
            f"Rate limit reached (100 Grok calls/hour). "
            f"Please wait {reset_in // 60}m {reset_in % 60}s before trying again.",
            reply_markup=_exit_keyboard(),
        )
        return

    # Persist updated timestamps immediately
    await state.update_data(grok_call_timestamps=data["grok_call_timestamps"])

    # Extract content from message (text, CSV, photo, etc.)
    user_content = await extract_content(message)
    history.append({"role": "user", "content": user_content})

    # Capture photo file_id if admin attached a photo (for image updates)
    photo_file_id = None
    if message.photo:
        photo_file_id = message.photo[-1].file_id  # Largest resolution

    # Send typing indicator
    await message.bot.send_chat_action(message.chat.id, "typing")

    try:
        response = await call_grok(
            messages=history,
            tools=ALL_TOOLS,
        )
    except Exception as e:
        logger.error("Grok API call failed: %s", e)
        await message.answer(
            f"AI service error: {e}\nPlease try again.",
            reply_markup=_exit_keyboard(),
        )
        return

    assistant_msg = response["choices"][0]["message"]
    history.append(assistant_msg)

    # Process tool calls if present
    if assistant_msg.get("tool_calls"):
        for tool_call in assistant_msg["tool_calls"]:
            result = await _process_tool_call(
                tool_call, message.from_user.id, photo_file_id,
                bot=message.bot, chat_id=message.chat.id,
            )
            history.append({
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": json.dumps(result, default=str),
            })

        # Get Grok's follow-up response with tool results
        try:
            await message.bot.send_chat_action(message.chat.id, "typing")
            followup = await call_grok(messages=history, tools=ALL_TOOLS)
            followup_msg = followup["choices"][0]["message"]
            history.append(followup_msg)

            # Handle nested tool calls (Grok may chain actions)
            depth = 0
            while followup_msg.get("tool_calls") and depth < 3:
                depth += 1
                for tc in followup_msg["tool_calls"]:
                    res = await _process_tool_call(
                        tc, message.from_user.id, photo_file_id,
                        bot=message.bot, chat_id=message.chat.id,
                    )
                    history.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": json.dumps(res, default=str),
                    })
                await message.bot.send_chat_action(message.chat.id, "typing")
                followup = await call_grok(messages=history, tools=ALL_TOOLS)
                followup_msg = followup["choices"][0]["message"]
                history.append(followup_msg)

            reply_text = followup_msg.get("content") or "Done."
        except Exception as e:
            logger.error("Grok follow-up failed: %s", e)
            reply_text = f"Action executed but follow-up failed: {e}"
    else:
        reply_text = assistant_msg.get("content") or "I didn't understand. Could you rephrase?"

    # Trim history to prevent token overflow
    history = _trim_history(history)
    await state.update_data(grok_history=history)

    # Send response (split if too long for Telegram)
    for chunk in _split_message(reply_text):
        await message.answer(chunk, reply_markup=_exit_keyboard())


async def _process_tool_call(
    tool_call: dict,
    admin_id: int,
    photo_file_id: str | None = None,
    bot=None,
    chat_id: int | None = None,
) -> dict:
    """Validate tool call against Pydantic schema and execute."""
    func_name = tool_call["function"]["name"]

    try:
        args = json.loads(tool_call["function"]["arguments"])
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON in tool arguments: {e}"}

    # Inject photo_file_id for image update actions
    if func_name == "update_item_image" and photo_file_id:
        args["photo_file_id"] = photo_file_id

    schema_class = TOOL_SCHEMA_MAP.get(func_name)
    if not schema_class:
        return {"error": f"Unknown tool: {func_name}"}

    # Pydantic validation — the hard guardrail
    try:
        validated = schema_class.model_validate(args)
    except Exception as e:
        return {
            "error": "Validation failed",
            "details": str(e),
            "hint": "Ask the admin for the missing/invalid fields",
        }

    # Special handling: AI image generation needs bot + chat_id
    if func_name == "generate_item_images":
        return await _handle_generate_images(validated, admin_id, bot, chat_id)

    # Execute
    if func_name in MUTATION_TOOLS:
        return await execute_mutation(validated, admin_id)
    else:
        return await execute_query(validated)


async def _handle_generate_images(action, admin_id: int, bot, chat_id: int) -> dict:
    """Handle AI image generation — needs bot instance for Telegram upload."""
    if not action.confirm:
        return {"error": "Image generation requires confirm=True (costs API credits)"}
    if not bot or not chat_id:
        return {"error": "Image generation requires an active Telegram session"}

    # Determine which items to generate for
    if action.all_missing:
        items = get_items_missing_images()
    else:
        items = []
        with Database().session() as s:
            for name in action.item_names:
                goods = s.query(Goods).filter(Goods.name == name).first()
                if goods:
                    items.append({
                        "name": goods.name,
                        "description": goods.description,
                        "category_name": goods.category_name,
                    })
                else:
                    return {"error": f"Item '{name}' not found"}

    if not items:
        return {"success": True, "message": "No items need images", "generated": 0}

    # Generate images one by one, reporting progress
    generated = []
    failed = []
    for item in items:
        try:
            await bot.send_chat_action(chat_id, "upload_photo")
            result = await generate_and_save_item_image(
                bot=bot,
                chat_id=chat_id,
                item_name=item["name"],
                description=item["description"],
                category=item["category_name"],
            )
            if result.get("success"):
                generated.append(item["name"])
            else:
                failed.append({"item": item["name"], "error": result.get("error", "Unknown")})
        except Exception as e:
            failed.append({"item": item["name"], "error": str(e)})

    logger.info("AI admin %s generated %d images (%d failed)",
                admin_id, len(generated), len(failed))
    return {
        "success": True,
        "generated": len(generated),
        "generated_items": generated,
        "failed": len(failed),
        "failed_items": failed,
    }


def _split_message(text: str, max_len: int = 4000) -> list[str]:
    """Split long messages for Telegram's 4096 char limit."""
    if len(text) <= max_len:
        return [text]

    chunks = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break
        # Find a good split point
        split_at = text.rfind("\n", 0, max_len)
        if split_at == -1:
            split_at = max_len
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip("\n")
    return chunks
