"""Support tickets application service (CARD-40 Tier C / CARD-32).

Single writer for SupportTicket / TicketMessage. Adapters (Telegram handlers,
web auth API, future Grok tools) call here — not domain ORM directly.

Identity rule: *user_id* is the internal users.telegram_id (resolved at the
adapter edge via TG dual-write or web OAuth session — never invent OAuth in bot).
"""

from __future__ import annotations

import random
import string
from datetime import UTC, datetime
from typing import Any

from bot.database.main import Database
from bot.database.models.main import Brand, SupportTicket, TicketMessage
from bot.services.dto import ServiceResult

VALID_PRIORITIES = frozenset({"low", "normal", "high", "urgent"})
VALID_STATUSES = frozenset({"open", "in_progress", "resolved", "closed"})
CLOSED_STATUSES = frozenset({"closed", "resolved"})


def _code() -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=8))


def _resolve_brand_id(brand_slug: str | None, brand_id: int | None = None) -> int | None:
    if brand_id is not None:
        return int(brand_id)
    if not brand_slug:
        return None
    with Database().session() as s:
        b = s.query(Brand).filter(Brand.slug == brand_slug, Brand.is_active.is_(True)).one_or_none()
        return b.id if b else None


def _ticket_summary(t: SupportTicket) -> dict[str, Any]:
    return {
        "id": t.id,
        "ticket_code": t.ticket_code,
        "subject": t.subject,
        "status": t.status,
        "priority": t.priority,
        "brand_id": t.brand_id,
        "order_id": t.order_id,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
    }


def _ticket_detail(t: SupportTicket, msgs: list[TicketMessage]) -> dict[str, Any]:
    data = _ticket_summary(t)
    data["messages"] = [
        {
            "sender_role": m.sender_role,
            "message_text": m.message_text,
            "sender_id": m.sender_id,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in msgs
    ]
    return data


def _find_ticket(
    s,
    user_id: int,
    *,
    ticket_id: int | None = None,
    ticket_code: str | None = None,
) -> SupportTicket | None:
    q = s.query(SupportTicket).filter(SupportTicket.user_id == user_id)
    if ticket_id is not None:
        q = q.filter(SupportTicket.id == int(ticket_id))
    elif ticket_code:
        q = q.filter(SupportTicket.ticket_code == str(ticket_code).strip())
    else:
        return None
    return q.one_or_none()


def list_tickets(
    user_id: int,
    *,
    brand_slug: str | None = None,
    brand_id: int | None = None,
    limit: int = 100,
) -> ServiceResult:
    """List tickets for *user_id* (optional brand filter)."""
    bid = _resolve_brand_id(brand_slug, brand_id)
    with Database().session() as s:
        q = s.query(SupportTicket).filter(SupportTicket.user_id == user_id)
        if bid is not None:
            q = q.filter((SupportTicket.brand_id == bid) | (SupportTicket.brand_id.is_(None)))
        rows = q.order_by(SupportTicket.updated_at.desc()).limit(max(1, min(limit, 200))).all()
        tickets = [_ticket_summary(t) for t in rows]
        return ServiceResult.success(tickets=tickets, count=len(tickets))


def get_ticket(
    user_id: int,
    *,
    ticket_id: int | None = None,
    ticket_code: str | None = None,
) -> ServiceResult:
    """Ticket detail + messages. Lookup by id or code."""
    if ticket_id is None and not ticket_code:
        return ServiceResult.fail("ticket.query.missing_id")
    with Database().session() as s:
        t = _find_ticket(s, user_id, ticket_id=ticket_id, ticket_code=ticket_code)
        if not t:
            return ServiceResult.fail("ticket.not_found")
        msgs = (
            s.query(TicketMessage)
            .filter(TicketMessage.ticket_id == t.id)
            .order_by(TicketMessage.created_at.asc())
            .all()
        )
        return ServiceResult.success(ticket=_ticket_detail(t, msgs))


def create_ticket(
    user_id: int,
    subject: str,
    message: str,
    *,
    priority: str = "normal",
    brand_slug: str | None = None,
    brand_id: int | None = None,
    order_id: int | None = None,
) -> ServiceResult:
    """Open a ticket and store the first user message. Single writer."""
    subject = (subject or "").strip()[:200]
    message = (message or "").strip()
    if not subject or not message:
        return ServiceResult.fail("ticket.subject_and_message_required")
    pri = priority if priority in VALID_PRIORITIES else "normal"
    bid = _resolve_brand_id(brand_slug, brand_id)

    with Database().session() as s:
        code = None
        for _ in range(10):
            candidate = _code()
            if s.query(SupportTicket).filter_by(ticket_code=candidate).first() is None:
                code = candidate
                break
        if not code:
            return ServiceResult.fail("ticket.code_generation_failed")

        ticket = SupportTicket(
            ticket_code=code,
            user_id=int(user_id),
            subject=subject,
            status="open",
            priority=pri,
            brand_id=bid,
            order_id=order_id,
        )
        s.add(ticket)
        s.flush()
        s.add(
            TicketMessage(
                ticket_id=ticket.id,
                sender_id=int(user_id),
                sender_role="user",
                message_text=message,
            )
        )
        s.commit()
        return ServiceResult.success(
            id=ticket.id,
            ticket_code=code,
            subject=subject,
            status="open",
            priority=pri,
            brand_id=bid,
            order_id=order_id,
        )


def reply_ticket(
    user_id: int,
    message: str,
    *,
    ticket_id: int | None = None,
    ticket_code: str | None = None,
    reopen: bool = True,
) -> ServiceResult:
    """Append a user message; optionally reopen closed/resolved tickets."""
    message = (message or "").strip()
    if not message:
        return ServiceResult.fail("ticket.message_required")
    if ticket_id is None and not ticket_code:
        return ServiceResult.fail("ticket.query.missing_id")

    with Database().session() as s:
        t = _find_ticket(s, user_id, ticket_id=ticket_id, ticket_code=ticket_code)
        if not t:
            return ServiceResult.fail("ticket.not_found")
        if reopen and t.status in CLOSED_STATUSES:
            t.status = "open"
        s.add(
            TicketMessage(
                ticket_id=t.id,
                sender_id=int(user_id),
                sender_role="user",
                message_text=message,
            )
        )
        t.updated_at = datetime.now(UTC)
        code = t.ticket_code
        tid = t.id
        s.commit()

    detail = get_ticket(user_id, ticket_id=tid, ticket_code=code)
    if not detail.ok:
        return ServiceResult.success(id=tid, ticket_code=code, status="open")
    return ServiceResult.success(ticket=detail.data["ticket"])


def close_ticket(
    user_id: int,
    *,
    ticket_id: int | None = None,
    ticket_code: str | None = None,
    status: str = "closed",
) -> ServiceResult:
    """Customer closes (or resolves) their own ticket."""
    if status not in ("closed", "resolved"):
        status = "closed"
    if ticket_id is None and not ticket_code:
        return ServiceResult.fail("ticket.query.missing_id")

    with Database().session() as s:
        t = _find_ticket(s, user_id, ticket_id=ticket_id, ticket_code=ticket_code)
        if not t:
            return ServiceResult.fail("ticket.not_found")
        t.status = status
        now = datetime.now(UTC)
        t.updated_at = now
        t.resolved_at = now
        code = t.ticket_code
        tid = t.id
        s.commit()
        return ServiceResult.success(id=tid, ticket_code=code, status=status)


def append_message(
    user_id: int,
    message: str,
    *,
    ticket_id: int | None = None,
    ticket_code: str | None = None,
    sender_role: str = "user",
) -> ServiceResult:
    """Append a message without reopening rules (live chat / system notes)."""
    message = (message or "").strip()
    if not message:
        return ServiceResult.fail("ticket.message_required")
    if ticket_id is None and not ticket_code:
        return ServiceResult.fail("ticket.query.missing_id")
    role = sender_role if sender_role in ("user", "admin") else "user"

    with Database().session() as s:
        t = _find_ticket(s, user_id, ticket_id=ticket_id, ticket_code=ticket_code)
        if not t:
            return ServiceResult.fail("ticket.not_found")
        s.add(
            TicketMessage(
                ticket_id=t.id,
                sender_id=int(user_id),
                sender_role=role,
                message_text=message,
            )
        )
        t.updated_at = datetime.now(UTC)
        tid = t.id
        code = t.ticket_code
        s.commit()
        return ServiceResult.success(id=tid, ticket_code=code)
