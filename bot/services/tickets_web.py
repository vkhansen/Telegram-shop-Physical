"""Web ticket portal facade (CARD-39) — delegates to shared tickets service.

CARD-40 Tier C: single writer is ``bot.services.tickets``. This module keeps
the plain-dict / raise-ValueError shape used by ``auth_api`` HTTP handlers.
"""

from __future__ import annotations

from typing import Any

from bot.services import tickets as tickets_svc


def list_tickets(user_id: int, brand_slug: str | None = None) -> list[dict[str, Any]]:
    res = tickets_svc.list_tickets(user_id, brand_slug=brand_slug)
    if not res.ok:
        return []
    return list(res.data.get("tickets") or [])


def get_ticket(user_id: int, ticket_code: str) -> dict[str, Any] | None:
    res = tickets_svc.get_ticket(user_id, ticket_code=ticket_code)
    if not res.ok:
        return None
    return res.data.get("ticket")


def create_ticket(
    user_id: int,
    subject: str,
    message: str,
    priority: str = "normal",
    brand_slug: str | None = None,
) -> dict[str, Any]:
    res = tickets_svc.create_ticket(
        user_id,
        subject,
        message,
        priority=priority,
        brand_slug=brand_slug,
    )
    if not res.ok:
        # Preserve legacy HTTP error contract
        if res.error_key == "ticket.subject_and_message_required":
            raise ValueError("subject_and_message_required")
        raise ValueError(res.error_key or "ticket_create_failed")
    return {
        "ticket_code": res.data["ticket_code"],
        "subject": res.data["subject"],
        "status": res.data["status"],
        "brand_id": res.data.get("brand_id"),
        "id": res.data.get("id"),
    }


def reply_ticket(user_id: int, ticket_code: str, message: str) -> dict[str, Any] | None:
    res = tickets_svc.reply_ticket(user_id, message, ticket_code=ticket_code)
    if not res.ok:
        if res.error_key == "ticket.message_required":
            raise ValueError("message_required")
        if res.error_key == "ticket.not_found":
            return None
        raise ValueError(res.error_key or "ticket_reply_failed")
    ticket = res.data.get("ticket")
    if ticket:
        return ticket
    # Fallback if reply only returned ids
    return get_ticket(user_id, ticket_code)
