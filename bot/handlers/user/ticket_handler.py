"""
User Support Ticket Handler (Telegram adapter).

CARD-40 Tier C: all ticket domain writes go through ``bot.services.tickets``.
Identity: Telegram ``from_user.id`` is the internal user_id (dual-write spine).
No OAuth / web auth adapter here — capability ``auth`` is web-only.
"""

import contextlib
import logging

from aiogram import F, Router
from aiogram.enums.chat_type import ChatType
from aiogram.filters import Command
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.config.env import EnvKeys
from bot.i18n import localize
from bot.keyboards.inline import back, simple_buttons
from bot.services import tickets as tickets_svc

router = Router()
logger = logging.getLogger(__name__)


class TicketStates(StatesGroup):
    waiting_subject = State()
    waiting_message = State()
    waiting_reply = State()
    waiting_screenshot = State()  # Optional screenshot attachment
    live_chatting = State()  # Active live chat with maintainer


def _get_maintainer_ids() -> list[int]:
    """Parse MAINTAINER_IDS from env (comma-separated), fallback to OWNER_ID."""
    raw = EnvKeys.MAINTAINER_IDS or ""
    ids = []
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            ids.append(int(part))
    if not ids and EnvKeys.OWNER_ID:
        with contextlib.suppress(ValueError, TypeError):
            ids.append(int(EnvKeys.OWNER_ID))
    return ids


async def _notify_maintainers(bot, text: str, photo_id: str | None = None):
    """Send notification to maintainers / support group (Telegram adapter I/O)."""
    from bot.platform.messaging import get_messenger

    messenger = get_messenger()
    for mid in _get_maintainer_ids():
        try:
            if photo_id:
                await messenger.send_photo(mid, photo_id, caption=text)
            else:
                await messenger.send_text(mid, text)
        except Exception as e:
            logger.warning("Failed to notify maintainer %s: %s", mid, e)
    support_chat = EnvKeys.SUPPORT_CHAT_ID
    if support_chat:
        try:
            # Group key: raw chat id string via Messenger port
            if photo_id:
                # send_photo is DM-shaped; fall back to bot for group photo if needed
                await bot.send_photo(int(support_chat), photo_id, caption=text)
            else:
                await messenger.send_group(str(support_chat), text)
        except Exception as e:
            logger.warning("Failed to notify support chat: %s", e)


# -- /support command ---------------------------------------------------------


@router.message(Command("support"))
async def support_command(message: Message, state: FSMContext):
    """Show support menu with bug report / feedback / live chat options."""
    await state.clear()
    await _show_support_menu(message, edit=False)


@router.callback_query(F.data == "support_menu")
async def support_menu_callback(call: CallbackQuery, state: FSMContext):
    """Show support menu from callback."""
    await state.clear()
    await _show_support_menu(call.message, edit=True)


async def _show_support_menu(message: Message, edit: bool = False):
    buttons = [
        (localize("support.btn.bug_report"), "support_bug_report"),
        (localize("support.btn.feedback"), "support_feedback"),
        (localize("support.btn.live_chat"), "support_live_chat"),
        (localize("support.btn.my_tickets"), "support_tickets"),
        (localize("btn.back"), "back_to_menu"),
    ]
    text = localize("support.menu_title")
    kb = simple_buttons(buttons, per_row=1)
    if edit:
        await message.edit_text(text, reply_markup=kb)
    else:
        await message.answer(text, reply_markup=kb)


# -- Bug report / feedback shortcuts ------------------------------------------


@router.callback_query(F.data == "support_bug_report")
async def start_bug_report(call: CallbackQuery, state: FSMContext):
    """Start bug report flow — high priority, prompts for screenshot."""
    await call.answer()
    await state.update_data(ticket_type="bug_report", ticket_priority="high", order_id=None)
    await state.set_state(TicketStates.waiting_subject)
    await call.message.edit_text(
        localize("support.bug.subject_prompt"),
        reply_markup=back("support_menu"),
    )


@router.callback_query(F.data == "support_feedback")
async def start_feedback(call: CallbackQuery, state: FSMContext):
    """Start feedback flow — normal priority."""
    await call.answer()
    await state.update_data(ticket_type="feedback", ticket_priority="low", order_id=None)
    await state.set_state(TicketStates.waiting_subject)
    await call.message.edit_text(
        localize("support.feedback.subject_prompt"),
        reply_markup=back("support_menu"),
    )


# -- Live chat ----------------------------------------------------------------


@router.callback_query(F.data == "support_live_chat")
async def start_live_chat(call: CallbackQuery, state: FSMContext):
    """Start a live chat session with maintainers."""
    maintainers = _get_maintainer_ids()
    if not maintainers:
        await call.answer(localize("support.no_maintainers"), show_alert=True)
        return

    await call.answer()
    user_id = call.from_user.id

    res = tickets_svc.create_ticket(
        user_id,
        "[LIVE_CHAT] Live support session",
        "Live chat session started",
        priority="high",
    )
    if not res.ok:
        await call.message.edit_text(
            localize("ticket.no_tickets"),
            reply_markup=back("support_menu"),
        )
        return

    ticket_id = res.data["id"]
    ticket_code = res.data["ticket_code"]

    await state.set_state(TicketStates.live_chatting)
    await state.update_data(live_chat_ticket_id=ticket_id, live_chat_ticket_code=ticket_code)

    await _notify_maintainers(
        call.bot,
        f"💬 <b>Live Chat Started</b>\n\nTicket: <b>{ticket_code}</b>\nUser: {user_id}\n\n"
        f"Reply via admin ticket panel or /support chat.",
    )

    await call.message.edit_text(
        localize("support.live_chat.started", ticket_code=ticket_code),
        reply_markup=simple_buttons(
            [
                (localize("support.btn.end_chat"), "support_end_live_chat"),
            ]
        ),
    )


@router.message(TicketStates.live_chatting, F.chat.type == ChatType.PRIVATE)
async def live_chat_message(message: Message, state: FSMContext):
    """Relay user message to maintainers during live chat."""
    data = await state.get_data()
    ticket_id = data.get("live_chat_ticket_id")
    ticket_code = data.get("live_chat_ticket_code")
    if not ticket_id:
        await state.clear()
        return

    user_id = message.from_user.id
    msg_text = message.text or message.caption or "(attachment)"
    photo_id = message.photo[-1].file_id if message.photo else None

    tickets_svc.append_message(user_id, msg_text, ticket_id=ticket_id)

    relay_text = f"💬 [{ticket_code}] <b>User {user_id}:</b>\n{msg_text}"
    await _notify_maintainers(message.bot, relay_text, photo_id)
    await message.answer(localize("support.live_chat.message_sent"))


@router.callback_query(F.data == "support_end_live_chat")
async def end_live_chat(call: CallbackQuery, state: FSMContext):
    """End the live chat session."""
    data = await state.get_data()
    ticket_id = data.get("live_chat_ticket_id")
    ticket_code = data.get("live_chat_ticket_code")

    if ticket_id:
        tickets_svc.append_message(
            call.from_user.id,
            "Live chat session ended by user",
            ticket_id=ticket_id,
        )
        await _notify_maintainers(call.bot, f"💬 [{ticket_code}] Live chat ended by user.")

    await state.clear()
    await call.message.edit_text(
        localize("support.live_chat.ended"),
        reply_markup=back("support_menu"),
    )


# -- Ticket list ---------------------------------------------------------------


@router.callback_query(F.data == "support_tickets")
async def support_tickets(call: CallbackQuery, state: FSMContext):
    """Show the user's tickets (open and resolved) with a create button."""
    await state.clear()
    user_id = call.from_user.id

    res = tickets_svc.list_tickets(user_id)
    tickets = res.data.get("tickets") if res.ok else []

    if not tickets:
        actions = [
            (localize("btn.create_ticket"), "create_ticket"),
            (localize("btn.back"), "back_to_menu"),
        ]
        await call.message.edit_text(
            localize("ticket.no_tickets"),
            reply_markup=simple_buttons(actions, per_row=1),
        )
        return

    buttons = []
    for ticket in tickets:
        status_icon = {"open": "🟢", "in_progress": "🔵", "resolved": "✅", "closed": "⚫"}.get(
            ticket.get("status"), ""
        )
        label = f"{status_icon} [{ticket['ticket_code']}] {ticket['subject']}"
        buttons.append((label, f"view_ticket_{ticket['id']}"))

    buttons.append((localize("btn.create_ticket"), "create_ticket"))
    buttons.append((localize("btn.back"), "back_to_menu"))

    await call.message.edit_text(
        localize("ticket.title"),
        reply_markup=simple_buttons(buttons, per_row=1),
    )


# -- Create ticket -------------------------------------------------------------


@router.callback_query(F.data == "create_ticket")
async def create_ticket(call: CallbackQuery, state: FSMContext):
    """Start ticket creation flow - ask for subject."""
    await state.set_state(TicketStates.waiting_subject)
    await state.update_data(order_id=None)
    await call.message.edit_text(
        localize("ticket.subject_prompt"),
        reply_markup=back("support_tickets"),
    )


@router.callback_query(F.data.startswith("create_ticket_for_order_"))
async def create_ticket_for_order(call: CallbackQuery, state: FSMContext):
    """Start ticket creation linked to a specific order."""
    order_id = int(call.data.replace("create_ticket_for_order_", ""))
    await state.set_state(TicketStates.waiting_subject)
    await state.update_data(order_id=order_id)
    await call.message.edit_text(
        localize("ticket.subject_prompt"),
        reply_markup=back("support_tickets"),
    )


@router.message(TicketStates.waiting_subject)
async def process_ticket_subject(message: Message, state: FSMContext):
    """Receive the ticket subject, ask for the initial message."""
    subject = message.text.strip()
    if not subject:
        await message.answer(localize("ticket.subject_prompt"))
        return

    await state.update_data(subject=subject)
    await state.set_state(TicketStates.waiting_message)
    await message.answer(
        localize("ticket.message_prompt"),
        reply_markup=back("support_tickets"),
    )


@router.message(TicketStates.waiting_message)
async def process_ticket_message(message: Message, state: FSMContext):
    """Receive the initial message, then ask for optional screenshot."""
    msg_text = (message.text or "").strip()
    if not msg_text:
        await message.answer(localize("ticket.message_prompt"))
        return

    await state.update_data(ticket_message_text=msg_text)

    data = await state.get_data()
    ticket_type = data.get("ticket_type", "general")

    # Bug reports prompt for screenshot; others skip
    if ticket_type == "bug_report":
        buttons = [
            (localize("support.btn.attach_screenshot"), "support_attach_screenshot"),
            (localize("support.btn.skip_screenshot"), "support_skip_screenshot"),
        ]
        await message.answer(
            localize("support.screenshot_prompt"),
            reply_markup=simple_buttons(buttons, per_row=1),
        )
        await state.set_state(TicketStates.waiting_screenshot)
    else:
        await _finalize_ticket(message, state)


@router.callback_query(F.data == "support_attach_screenshot", TicketStates.waiting_screenshot)
async def prompt_screenshot_upload(call: CallbackQuery, state: FSMContext):
    """Ask user to send a screenshot photo."""
    await call.answer()
    await call.message.edit_text(
        localize("support.screenshot_send"),
        reply_markup=back("support_menu"),
    )


@router.message(TicketStates.waiting_screenshot, F.photo)
async def receive_screenshot(message: Message, state: FSMContext):
    """Save screenshot and finalize ticket."""
    photo_id = message.photo[-1].file_id
    await state.update_data(ticket_screenshot=photo_id)
    await _finalize_ticket(message, state)


@router.callback_query(F.data == "support_skip_screenshot", TicketStates.waiting_screenshot)
async def skip_screenshot(call: CallbackQuery, state: FSMContext):
    """Skip screenshot and finalize ticket."""
    await call.answer()
    await _finalize_ticket(call.message, state, from_callback=True)


async def _finalize_ticket(message: Message, state: FSMContext, from_callback: bool = False):
    """Create the ticket via application service and notify maintainers."""
    data = await state.get_data()
    user_id = message.chat.id
    if not from_callback and message.from_user:
        user_id = message.from_user.id

    subject = data.get("subject", "No subject")
    msg_text = data.get("ticket_message_text", "")
    order_id = data.get("order_id")
    screenshot = data.get("ticket_screenshot")
    ticket_type = data.get("ticket_type", "general")
    priority = data.get("ticket_priority", "normal")

    # Prefix subject with type tag for bug reports / feedback
    if ticket_type in ("bug_report", "feedback"):
        subject = f"[{ticket_type.upper()}] {subject}"

    res = tickets_svc.create_ticket(
        user_id,
        subject,
        msg_text,
        priority=priority,
        order_id=order_id,
    )
    if not res.ok:
        await state.clear()
        err = localize("ticket.no_tickets")
        if from_callback:
            await message.edit_text(err, reply_markup=back("support_menu"))
        else:
            await message.answer(err, reply_markup=back("support_menu"))
        return

    ticket_code = res.data["ticket_code"]

    notification = (
        f"🎫 <b>New Ticket</b>\n\n"
        f"Code: <b>{ticket_code}</b>\n"
        f"Type: {ticket_type}\n"
        f"Priority: {priority}\n"
        f"From: {user_id}\n"
        f"Subject: {subject}\n\n"
        f"{msg_text}"
    )
    await _notify_maintainers(message.bot, notification, screenshot)

    await state.clear()
    confirm = localize("ticket.created", code=ticket_code)
    if from_callback:
        await message.edit_text(confirm, reply_markup=back("support_menu"))
    else:
        await message.answer(confirm, reply_markup=back("support_menu"))


# -- View ticket ---------------------------------------------------------------


@router.callback_query(F.data.startswith("view_ticket_"))
async def view_ticket(call: CallbackQuery, state: FSMContext):
    """View ticket details and message history."""
    ticket_id = int(call.data.replace("view_ticket_", ""))
    user_id = call.from_user.id

    res = tickets_svc.get_ticket(user_id, ticket_id=ticket_id)
    if not res.ok:
        await call.answer("Ticket not found", show_alert=True)
        return

    ticket = res.data["ticket"]
    created = (ticket.get("created_at") or "")[:16].replace("T", " ")

    text = (
        f"<b>{localize('ticket.view')}</b>\n\n"
        f"Code: <b>{ticket['ticket_code']}</b>\n"
        f"Subject: {ticket['subject']}\n"
        f"Status: {ticket['status']}\n"
        f"Created: {created}\n"
    )
    if ticket.get("order_id"):
        text += f"Order ID: {ticket['order_id']}\n"

    text += "\n--- Messages ---\n\n"
    for msg in ticket.get("messages") or []:
        role_label = "You" if msg.get("sender_role") == "user" else "Support"
        ts = (msg.get("created_at") or "")[:16].replace("T", " ")
        text += f"<b>[{role_label}]</b> {ts}\n{msg.get('message_text', '')}\n\n"

    buttons = []
    if ticket["status"] in ("open", "in_progress"):
        buttons.append((localize("ticket.reply_prompt"), f"reply_ticket_{ticket_id}"))
        buttons.append((localize("ticket.closed"), f"close_ticket_{ticket_id}"))
    buttons.append((localize("btn.my_tickets"), "support_tickets"))

    await call.message.edit_text(
        text,
        reply_markup=simple_buttons(buttons, per_row=1),
    )


# -- Reply to ticket -----------------------------------------------------------


@router.callback_query(F.data.startswith("reply_ticket_"))
async def reply_ticket(call: CallbackQuery, state: FSMContext):
    """Prompt user to enter a reply message."""
    ticket_id = int(call.data.replace("reply_ticket_", ""))
    await state.set_state(TicketStates.waiting_reply)
    await state.update_data(reply_ticket_id=ticket_id)
    await call.message.edit_text(
        localize("ticket.reply_prompt"),
        reply_markup=back(f"view_ticket_{ticket_id}"),
    )


@router.message(TicketStates.waiting_reply, F.text)
async def process_ticket_reply(message: Message, state: FSMContext):
    """Save the user's reply via tickets service."""
    msg_text = message.text.strip()
    if not msg_text:
        await message.answer(localize("ticket.reply_prompt"))
        return

    data = await state.get_data()
    ticket_id = data.get("reply_ticket_id")
    user_id = message.from_user.id

    res = tickets_svc.reply_ticket(user_id, msg_text, ticket_id=ticket_id)
    if not res.ok:
        await state.clear()
        await message.answer("Ticket not found", reply_markup=back("support_tickets"))
        return

    await state.clear()
    await message.answer(
        localize("ticket.reply_sent"),
        reply_markup=back(f"view_ticket_{ticket_id}"),
    )


# -- Close ticket --------------------------------------------------------------


@router.callback_query(F.data.startswith("close_ticket_"))
async def close_ticket(call: CallbackQuery, state: FSMContext):
    """User closes their own ticket."""
    ticket_id = int(call.data.replace("close_ticket_", ""))
    res = tickets_svc.close_ticket(call.from_user.id, ticket_id=ticket_id)
    if not res.ok:
        await call.answer("Ticket not found", show_alert=True)
        return

    await call.message.edit_text(
        localize("ticket.closed"),
        reply_markup=back("support_tickets"),
    )
