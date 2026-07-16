"""Web ticket portal service (CARD-39) — reuses SupportTicket / TicketMessage."""

from __future__ import annotations

import random
import string
from datetime import UTC, datetime
from typing import Any

from bot.database.main import Database
from bot.database.models.main import Brand, SupportTicket, TicketMessage


def _code() -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=8))


def _resolve_brand_id(brand_slug: str | None) -> int | None:
    if not brand_slug:
        return None
    with Database().session() as s:
        b = s.query(Brand).filter(Brand.slug == brand_slug, Brand.is_active.is_(True)).one_or_none()
        return b.id if b else None


def list_tickets(user_id: int, brand_slug: str | None = None) -> list[dict[str, Any]]:
    brand_id = _resolve_brand_id(brand_slug)
    with Database().session() as s:
        q = s.query(SupportTicket).filter(SupportTicket.user_id == user_id)
        if brand_id is not None:
            q = q.filter((SupportTicket.brand_id == brand_id) | (SupportTicket.brand_id.is_(None)))
        rows = q.order_by(SupportTicket.updated_at.desc()).limit(100).all()
        return [
            {
                "ticket_code": t.ticket_code,
                "subject": t.subject,
                "status": t.status,
                "priority": t.priority,
                "brand_id": t.brand_id,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "updated_at": t.updated_at.isoformat() if t.updated_at else None,
            }
            for t in rows
        ]


def get_ticket(user_id: int, ticket_code: str) -> dict[str, Any] | None:
    with Database().session() as s:
        t = (
            s.query(SupportTicket)
            .filter(SupportTicket.ticket_code == ticket_code, SupportTicket.user_id == user_id)
            .one_or_none()
        )
        if not t:
            return None
        msgs = (
            s.query(TicketMessage)
            .filter(TicketMessage.ticket_id == t.id)
            .order_by(TicketMessage.created_at.asc())
            .all()
        )
        return {
            "ticket_code": t.ticket_code,
            "subject": t.subject,
            "status": t.status,
            "priority": t.priority,
            "brand_id": t.brand_id,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "messages": [
                {
                    "sender_role": m.sender_role,
                    "message_text": m.message_text,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in msgs
            ],
        }


def create_ticket(
    user_id: int,
    subject: str,
    message: str,
    priority: str = "normal",
    brand_slug: str | None = None,
) -> dict[str, Any]:
    subject = (subject or "").strip()[:200]
    message = (message or "").strip()
    if not subject or not message:
        raise ValueError("subject_and_message_required")
    brand_id = _resolve_brand_id(brand_slug)
    with Database().session() as s:
        for _ in range(10):
            code = _code()
            if s.query(SupportTicket).filter_by(ticket_code=code).first() is None:
                break
        ticket = SupportTicket(
            ticket_code=code,
            user_id=user_id,
            subject=subject,
            status="open",
            priority=priority if priority in ("low", "normal", "high", "urgent") else "normal",
            brand_id=brand_id,
        )
        s.add(ticket)
        s.flush()
        s.add(
            TicketMessage(
                ticket_id=ticket.id,
                sender_id=user_id,
                sender_role="user",
                message_text=message,
            )
        )
        s.commit()
        return {"ticket_code": code, "subject": subject, "status": "open", "brand_id": brand_id}


def reply_ticket(user_id: int, ticket_code: str, message: str) -> dict[str, Any] | None:
    message = (message or "").strip()
    if not message:
        raise ValueError("message_required")
    with Database().session() as s:
        t = (
            s.query(SupportTicket)
            .filter(SupportTicket.ticket_code == ticket_code, SupportTicket.user_id == user_id)
            .one_or_none()
        )
        if not t:
            return None
        if t.status in ("closed", "resolved"):
            t.status = "open"
        s.add(
            TicketMessage(
                ticket_id=t.id,
                sender_id=user_id,
                sender_role="user",
                message_text=message,
            )
        )
        t.updated_at = datetime.now(UTC)
        s.commit()
        return get_ticket(user_id, ticket_code)
