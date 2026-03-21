"""
Admin Ticket Management Handler.

Provides:
- List all open/in-progress tickets (sorted by priority then date)
- View ticket details and full message history
- Reply to tickets as admin
- Mark tickets as resolved
"""
from datetime import datetime, timezone

from aiogram import Router, F
from aiogram.filters.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.database import Database
from bot.database.models.main import SupportTicket, TicketMessage, Permission
from bot.filters import HasPermissionFilter
from bot.i18n import localize
from bot.keyboards.inline import back, simple_buttons

router = Router()

PRIORITY_ORDER = {"urgent": 0, "high": 1, "normal": 2, "low": 3}


class AdminTicketStates(StatesGroup):
    waiting_reply = State()


# -- Ticket list ---------------------------------------------------------------

@router.callback_query(F.data == "admin_tickets", HasPermissionFilter(permission=Permission.USERS_MANAGE))
async def admin_tickets(call: CallbackQuery, state: FSMContext):
    """Show all open/in-progress tickets sorted by priority then date."""
    await state.clear()

    with Database().session() as session:
        tickets = (
            session.query(SupportTicket)
            .filter(SupportTicket.status.in_(["open", "in_progress"]))
            .order_by(SupportTicket.created_at.asc())
            .all()
        )

    # Sort by priority (urgent first), then by creation date
    tickets.sort(key=lambda t: (PRIORITY_ORDER.get(t.priority, 99), t.created_at))

    if not tickets:
        await call.message.edit_text(
            localize("admin.ticket.title") + "\n\n" + localize("ticket.no_tickets"),
            reply_markup=back("console"),
        )
        return

    buttons = []
    for ticket in tickets:
        priority_icon = {"urgent": "🔴", "high": "🟠", "normal": "🟡", "low": "⚪"}.get(
            ticket.priority, ""
        )
        status_icon = {"open": "🟢", "in_progress": "🔵"}.get(ticket.status, "")
        label = f"{priority_icon}{status_icon} [{ticket.ticket_code}] {ticket.subject}"
        buttons.append((label, f"admin_view_ticket_{ticket.id}"))

    buttons.append((localize("btn.back"), "console"))

    await call.message.edit_text(
        localize("admin.ticket.list"),
        reply_markup=simple_buttons(buttons, per_row=1),
    )


# -- View ticket ---------------------------------------------------------------

@router.callback_query(
    F.data.startswith("admin_view_ticket_"),
    HasPermissionFilter(permission=Permission.USERS_MANAGE),
)
async def admin_view_ticket(call: CallbackQuery, state: FSMContext):
    """View ticket details and full message history."""
    ticket_id = int(call.data.replace("admin_view_ticket_", ""))

    with Database().session() as session:
        ticket = session.query(SupportTicket).filter_by(id=ticket_id).first()
        if not ticket:
            await call.answer("Ticket not found", show_alert=True)
            return

        messages = (
            session.query(TicketMessage)
            .filter_by(ticket_id=ticket.id)
            .order_by(TicketMessage.created_at.asc())
            .all()
        )

        text = (
            f"<b>{localize('admin.ticket.title')}</b>\n\n"
            f"Code: <b>{ticket.ticket_code}</b>\n"
            f"User ID: {ticket.user_id}\n"
            f"Subject: {ticket.subject}\n"
            f"Status: {ticket.status}\n"
            f"Priority: {ticket.priority}\n"
            f"Created: {ticket.created_at.strftime('%Y-%m-%d %H:%M')}\n"
        )
        if ticket.order_id:
            text += f"Order ID: {ticket.order_id}\n"
        if ticket.assigned_to:
            text += f"Assigned to: {ticket.assigned_to}\n"

        text += "\n--- Messages ---\n\n"
        for msg in messages:
            role_label = "User" if msg.sender_role == "user" else "Admin"
            text += (
                f"<b>[{role_label}]</b> {msg.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                f"{msg.message_text}\n\n"
            )

    buttons = []
    if ticket.status in ("open", "in_progress"):
        buttons.append((localize("admin.ticket.reply_prompt"), f"admin_reply_ticket_{ticket_id}"))
        buttons.append((localize("admin.ticket.resolved"), f"admin_resolve_ticket_{ticket_id}"))
    buttons.append((localize("btn.back"), "admin_tickets"))

    await call.message.edit_text(
        text,
        reply_markup=simple_buttons(buttons, per_row=1),
    )


# -- Reply to ticket -----------------------------------------------------------

@router.callback_query(
    F.data.startswith("admin_reply_ticket_"),
    HasPermissionFilter(permission=Permission.USERS_MANAGE),
)
async def admin_reply_ticket(call: CallbackQuery, state: FSMContext):
    """Prompt admin to enter a reply message."""
    ticket_id = int(call.data.replace("admin_reply_ticket_", ""))
    await state.set_state(AdminTicketStates.waiting_reply)
    await state.update_data(reply_ticket_id=ticket_id)
    await call.message.edit_text(
        localize("admin.ticket.reply_prompt"),
        reply_markup=back(f"admin_view_ticket_{ticket_id}"),
    )


@router.message(AdminTicketStates.waiting_reply)
async def process_admin_reply(message: Message, state: FSMContext):
    """Save the admin's reply to the ticket."""
    msg_text = message.text.strip()
    if not msg_text:
        await message.answer(localize("admin.ticket.reply_prompt"))
        return

    data = await state.get_data()
    ticket_id = data.get("reply_ticket_id")
    admin_id = message.from_user.id

    with Database().session() as session:
        ticket = session.query(SupportTicket).filter_by(id=ticket_id).first()
        if not ticket:
            await state.clear()
            await message.answer("Ticket not found", reply_markup=back("admin_tickets"))
            return

        ticket_message = TicketMessage(
            ticket_id=ticket.id,
            sender_id=admin_id,
            sender_role="admin",
            message_text=msg_text,
            created_at=datetime.now(timezone.utc),
        )
        session.add(ticket_message)

        # Mark as in-progress if it was open
        if ticket.status == "open":
            ticket.status = "in_progress"
        ticket.assigned_to = admin_id
        ticket.updated_at = datetime.now(timezone.utc)
        session.commit()

        # Notify the user about the admin reply
        try:
            await message.bot.send_message(
                ticket.user_id,
                localize("ticket.view") + f"\n\n"
                f"[{ticket.ticket_code}] {ticket.subject}\n\n"
                f"<b>New reply from support:</b>\n{msg_text}",
            )
        except Exception:
            pass

    await state.clear()
    await message.answer(
        localize("admin.ticket.reply_prompt") + " - Sent",
        reply_markup=back(f"admin_view_ticket_{ticket_id}"),
    )


# -- Resolve ticket ------------------------------------------------------------

@router.callback_query(
    F.data.startswith("admin_resolve_ticket_"),
    HasPermissionFilter(permission=Permission.USERS_MANAGE),
)
async def admin_resolve_ticket(call: CallbackQuery, state: FSMContext):
    """Mark a ticket as resolved."""
    ticket_id = int(call.data.replace("admin_resolve_ticket_", ""))

    with Database().session() as session:
        ticket = session.query(SupportTicket).filter_by(id=ticket_id).first()
        if not ticket:
            await call.answer("Ticket not found", show_alert=True)
            return

        ticket.status = "resolved"
        ticket.updated_at = datetime.now(timezone.utc)
        ticket.resolved_at = datetime.now(timezone.utc)
        session.commit()

        # Notify the user
        try:
            await call.bot.send_message(
                ticket.user_id,
                localize("admin.ticket.resolved") + f"\n\n"
                f"[{ticket.ticket_code}] {ticket.subject}",
            )
        except Exception:
            pass

    await call.message.edit_text(
        localize("admin.ticket.resolved"),
        reply_markup=back("admin_tickets"),
    )
