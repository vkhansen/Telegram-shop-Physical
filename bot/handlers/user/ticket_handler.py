"""
User Support Ticket Handler.

Provides:
- View user's support tickets
- Create new tickets (optionally linked to an order)
- View ticket details and message history
- Reply to existing tickets
- Close own tickets
"""
import random
import string
from datetime import datetime, timezone

from aiogram import Router, F
from aiogram.filters.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.database import Database
from bot.database.models.main import SupportTicket, TicketMessage, Order
from bot.i18n import localize
from bot.keyboards.inline import back, simple_buttons

router = Router()


class TicketStates(StatesGroup):
    waiting_subject = State()
    waiting_message = State()
    waiting_reply = State()


def _generate_ticket_code() -> str:
    """Generate a unique 8-character ticket code."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


# -- Ticket list ---------------------------------------------------------------

@router.callback_query(F.data == "support_tickets")
async def support_tickets(call: CallbackQuery, state: FSMContext):
    """Show the user's tickets (open and resolved) with a create button."""
    await state.clear()
    user_id = call.from_user.id

    with Database().session() as session:
        tickets = (
            session.query(SupportTicket)
            .filter_by(user_id=user_id)
            .order_by(SupportTicket.created_at.desc())
            .all()
        )

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
            ticket.status, ""
        )
        label = f"{status_icon} [{ticket.ticket_code}] {ticket.subject}"
        buttons.append((label, f"view_ticket_{ticket.id}"))

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
    """Receive the initial message and create the ticket."""
    msg_text = message.text.strip()
    if not msg_text:
        await message.answer(localize("ticket.message_prompt"))
        return

    data = await state.get_data()
    subject = data["subject"]
    order_id = data.get("order_id")
    user_id = message.from_user.id
    ticket_code = _generate_ticket_code()

    with Database().session() as session:
        ticket = SupportTicket(
            ticket_code=ticket_code,
            user_id=user_id,
            subject=subject,
            status="open",
            priority="normal",
            order_id=order_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(ticket)
        session.flush()

        ticket_message = TicketMessage(
            ticket_id=ticket.id,
            sender_id=user_id,
            sender_role="user",
            message_text=msg_text,
            created_at=datetime.now(timezone.utc),
        )
        session.add(ticket_message)
        session.commit()

    await state.clear()
    await message.answer(
        localize("ticket.created", ticket_code=ticket_code),
        reply_markup=back("support_tickets"),
    )


# -- View ticket ---------------------------------------------------------------

@router.callback_query(F.data.startswith("view_ticket_"))
async def view_ticket(call: CallbackQuery, state: FSMContext):
    """View ticket details and message history."""
    ticket_id = int(call.data.replace("view_ticket_", ""))

    with Database().session() as session:
        ticket = session.query(SupportTicket).filter_by(id=ticket_id).first()
        if not ticket or ticket.user_id != call.from_user.id:
            await call.answer("Ticket not found", show_alert=True)
            return

        messages = (
            session.query(TicketMessage)
            .filter_by(ticket_id=ticket.id)
            .order_by(TicketMessage.created_at.asc())
            .all()
        )

        text = (
            f"<b>{localize('ticket.view')}</b>\n\n"
            f"Code: <b>{ticket.ticket_code}</b>\n"
            f"Subject: {ticket.subject}\n"
            f"Status: {ticket.status}\n"
            f"Created: {ticket.created_at.strftime('%Y-%m-%d %H:%M')}\n"
        )
        if ticket.order_id:
            text += f"Order ID: {ticket.order_id}\n"

        text += "\n--- Messages ---\n\n"
        for msg in messages:
            role_label = "You" if msg.sender_role == "user" else "Support"
            text += (
                f"<b>[{role_label}]</b> {msg.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                f"{msg.message_text}\n\n"
            )

    buttons = []
    if ticket.status in ("open", "in_progress"):
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


@router.message(TicketStates.waiting_reply)
async def process_ticket_reply(message: Message, state: FSMContext):
    """Save the user's reply to the ticket."""
    msg_text = message.text.strip()
    if not msg_text:
        await message.answer(localize("ticket.reply_prompt"))
        return

    data = await state.get_data()
    ticket_id = data.get("reply_ticket_id")
    user_id = message.from_user.id

    with Database().session() as session:
        ticket = session.query(SupportTicket).filter_by(id=ticket_id).first()
        if not ticket or ticket.user_id != user_id:
            await state.clear()
            await message.answer("Ticket not found", reply_markup=back("support_tickets"))
            return

        ticket_message = TicketMessage(
            ticket_id=ticket.id,
            sender_id=user_id,
            sender_role="user",
            message_text=msg_text,
            created_at=datetime.now(timezone.utc),
        )
        session.add(ticket_message)
        ticket.updated_at = datetime.now(timezone.utc)
        session.commit()

    await state.clear()
    await message.answer(
        localize("ticket.reply_prompt") + "\n\n" + localize("ticket.created", ticket_code=""),
        reply_markup=back(f"view_ticket_{ticket_id}"),
    )


# -- Close ticket --------------------------------------------------------------

@router.callback_query(F.data.startswith("close_ticket_"))
async def close_ticket(call: CallbackQuery, state: FSMContext):
    """User closes their own ticket."""
    ticket_id = int(call.data.replace("close_ticket_", ""))

    with Database().session() as session:
        ticket = session.query(SupportTicket).filter_by(id=ticket_id).first()
        if not ticket or ticket.user_id != call.from_user.id:
            await call.answer("Ticket not found", show_alert=True)
            return

        ticket.status = "closed"
        ticket.updated_at = datetime.now(timezone.utc)
        ticket.resolved_at = datetime.now(timezone.utc)
        session.commit()

    await call.message.edit_text(
        localize("ticket.closed"),
        reply_markup=back("support_tickets"),
    )
