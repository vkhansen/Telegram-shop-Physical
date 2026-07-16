"""Customer Grok assistant executor (Card 22 + CARD-40 Tier D).

Security invariant: every query that touches user-owned data is filtered by
``user_id`` sourced from adapter auth (Telegram ``from_user.id`` today), never
from the AI tool call payload itself.

CARD-40 D: tools call application services (tickets, order_query, customer_catalog)
and notify via Messenger — not a parallel domain stack.
"""

from __future__ import annotations

import contextlib
import logging

from bot.ai.customer_schemas import (
    BrowseMenuAction,
    CheckCouponAction,
    FindDealsAction,
    FindNearbyStoresAction,
    GetOrderStatusAction,
    GetTodaySpecialsAction,
    OpenSupportTicketAction,
    StartAppLiveChatAction,
    StartStoreLiveChatAction,
)
from bot.config.env import EnvKeys
from bot.database import Database
from bot.database.models.main import CustomerInfo, User
from bot.services import customer_catalog as catalog_svc
from bot.services import order_query as order_query_svc
from bot.services import tickets as tickets_svc

logger = logging.getLogger(__name__)


def _get_maintainer_ids() -> list[int]:
    raw = EnvKeys.MAINTAINER_IDS or ""
    ids: list[int] = []
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            ids.append(int(part))
    if not ids and EnvKeys.OWNER_ID:
        with contextlib.suppress(ValueError, TypeError):
            ids.append(int(EnvKeys.OWNER_ID))
    return ids


async def _notify_ids(ids: list[int], text: str) -> None:
    """D4: maintainer / support pings via Messenger port (not raw bot API)."""
    from bot.platform.messaging import get_messenger

    messenger = get_messenger()
    for uid in ids:
        try:
            await messenger.send_text(uid, text)
        except Exception as e:
            logger.warning("Failed to notify %s: %s", uid, e)
    support_chat = EnvKeys.SUPPORT_CHAT_ID
    if support_chat:
        try:
            await messenger.send_group(str(support_chat), text)
        except Exception as e:
            logger.warning("Failed to notify support chat: %s", e)


def _resolve_own_order_id(user_id: int, order_code: str | None) -> int | None:
    if not order_code:
        return None
    res = order_query_svc.get_order(user_id, order_code=order_code.upper())
    if not res.ok:
        return None
    return res.data["order"].get("id")


# ── Catalog tools ─────────────────────────────────────────────────────────────


def execute_browse_menu(action: BrowseMenuAction) -> dict:
    res = catalog_svc.browse_menu(
        keyword=action.keyword,
        category=action.category,
        max_price=action.max_price,
        min_price=action.min_price,
        in_stock_only=action.in_stock_only,
        limit=action.limit,
    )
    return res.data if res.ok else {"error": res.error_key, "detail": res.error_detail}


def execute_get_today_specials(action: GetTodaySpecialsAction) -> dict:
    res = catalog_svc.today_specials(category=action.category)
    return res.data if res.ok else {"error": res.error_key, "detail": res.error_detail}


def execute_find_deals(action: FindDealsAction) -> dict:
    res = catalog_svc.find_deals(min_order_max=action.min_order_max)
    return res.data if res.ok else {"error": res.error_key, "detail": res.error_detail}


def execute_find_nearby_stores(action: FindNearbyStoresAction) -> dict:
    res = catalog_svc.find_nearby_stores(
        action.latitude,
        action.longitude,
        max_distance_km=action.max_distance_km,
    )
    return res.data if res.ok else {"error": res.error_key, "detail": res.error_detail}


def execute_check_coupon(action: CheckCouponAction) -> dict:
    res = catalog_svc.check_coupon(action.code, order_total=action.order_total)
    return res.data if res.ok else {"error": res.error_key, "detail": res.error_detail}


# ── Own-account tools ─────────────────────────────────────────────────────────


def execute_get_order_status(action: GetOrderStatusAction, user_id: int) -> dict:
    if action.order_code:
        res = order_query_svc.get_order(user_id, order_code=action.order_code.upper())
        if not res.ok:
            return {"orders": [], "message": "No orders found"}
        o = res.data["order"]
        return {
            "orders": [
                {
                    "order_code": o.get("order_code"),
                    "status": o.get("order_status"),
                    "total_price": o.get("total_price"),
                    "payment_method": o.get("payment_method"),
                    "delivery_type": o.get("delivery_type"),
                    "created_at": o.get("created_at"),
                    "delivery_time": o.get("delivery_time"),
                }
            ]
        }

    res = order_query_svc.list_orders(user_id, limit=action.limit)
    if not res.ok:
        return {"error": res.error_key, "detail": res.error_detail}
    orders = res.data.get("orders") or []
    if not orders:
        return {"orders": [], "message": "No orders found"}
    return {
        "orders": [
            {
                "order_code": o.get("order_code"),
                "status": o.get("order_status"),
                "total_price": o.get("total_price"),
                "payment_method": o.get("payment_method"),
                "delivery_type": o.get("delivery_type"),
                "created_at": o.get("created_at"),
                "delivery_time": o.get("delivery_time"),
            }
            for o in orders
        ]
    }


def execute_get_my_account(user_id: int) -> dict:
    """Account summary (no dedicated service yet — read-only user profile)."""
    with Database().session() as s:
        user = s.query(User).filter(User.telegram_id == user_id).first()
        info = s.query(CustomerInfo).filter(CustomerInfo.telegram_id == user_id).first()
        if not user:
            return {"error": "User not found"}
        referral_count = s.query(User).filter(User.referral_id == user_id).count()

    return {
        "telegram_id": user_id,
        "registered_at": user.registration_date.isoformat() if user.registration_date else None,
        "bonus_balance": str(info.bonus_balance) if info else "0",
        "total_spent": str(info.total_spendings) if info else "0",
        "completed_orders": info.completed_orders_count if info else 0,
        "referral_count": referral_count,
    }


# ── Support tools (tickets service single writer) ─────────────────────────────


async def execute_open_support_ticket(action: OpenSupportTicketAction, user_id: int, bot=None) -> dict:
    del bot  # notifications use Messenger; bot kept for call-site compatibility
    order_id = _resolve_own_order_id(user_id, action.order_code)
    res = tickets_svc.create_ticket(
        user_id,
        action.subject,
        action.description,
        priority=action.priority,
        order_id=order_id,
    )
    if not res.ok:
        return {"success": False, "error": res.error_key, "detail": res.error_detail}

    ticket_code = res.data["ticket_code"]
    maintainers = _get_maintainer_ids()
    notify_text = (
        f"🎫 <b>New Support Ticket</b>\n\n"
        f"Code: <b>{ticket_code}</b>\n"
        f"User: {user_id}\n"
        f"Subject: {action.subject}\n"
        f"Priority: {action.priority}\n"
        f"Via: AI Assistant"
    )
    await _notify_ids(maintainers, notify_text)
    return {"success": True, "ticket_code": ticket_code, "ticket_id": res.data.get("id")}


async def execute_start_app_live_chat(action: StartAppLiveChatAction, user_id: int, bot=None) -> dict:
    del bot
    maintainers = _get_maintainer_ids()
    if not maintainers:
        return {"success": False, "error": "No maintainers configured"}

    res = tickets_svc.create_ticket(
        user_id,
        f"[APP_LIVE_CHAT] {action.reason[:150]}",
        f"App live chat started. Reason: {action.reason}",
        priority="high",
    )
    if not res.ok:
        return {"success": False, "error": res.error_key, "detail": res.error_detail}

    ticket_code = res.data["ticket_code"]
    ticket_id = res.data["id"]
    notify_text = (
        f"💬 <b>App Live Chat Request</b>\n\n"
        f"Ticket: <b>{ticket_code}</b>\n"
        f"User: {user_id}\n"
        f"Reason: {action.reason}\n\n"
        f"Respond via admin ticket panel."
    )
    await _notify_ids(maintainers, notify_text)
    return {
        "success": True,
        "ticket_code": ticket_code,
        "ticket_id": ticket_id,
        "relay_target": "maintainers",
    }


async def execute_start_store_live_chat(action: StartStoreLiveChatAction, user_id: int, bot=None) -> dict:
    del bot
    order_id = _resolve_own_order_id(user_id, action.order_code)
    res = tickets_svc.create_ticket(
        user_id,
        f"[STORE_LIVE_CHAT] {action.reason[:150]}",
        f"Store live chat started. Reason: {action.reason}",
        priority="high",
        order_id=order_id,
    )
    if not res.ok:
        return {"success": False, "error": res.error_key, "detail": res.error_detail}

    ticket_code = res.data["ticket_code"]
    ticket_id = res.data["id"]
    maintainers = _get_maintainer_ids()
    notify_text = (
        f"🏪 <b>Store Live Chat Request</b>\n\n"
        f"Ticket: <b>{ticket_code}</b>\n"
        f"User: {user_id}\n"
        f"Reason: {action.reason}\n"
        + (f"Order: {action.order_code}\n" if action.order_code else "")
        + "\nRespond via admin ticket panel."
    )
    await _notify_ids(maintainers, notify_text)
    return {
        "success": True,
        "ticket_code": ticket_code,
        "ticket_id": ticket_id,
        "relay_target": "store_admins",
    }
