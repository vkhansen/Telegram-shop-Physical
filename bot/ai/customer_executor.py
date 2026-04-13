"""Customer Grok assistant executor — DB queries scoped to the authenticated user (Card 22).

Security invariant: every query that touches user-owned data is filtered by
``user_id`` sourced from ``message.from_user.id`` (Telegram auth), never
from the AI tool call payload itself.
"""

import logging
import math
import random
import string
from datetime import datetime, timezone

from bot.config.env import EnvKeys
from bot.database import Database
from bot.database.models.main import (
    Categories,
    CustomerInfo,
    Coupon,
    Goods,
    Order,
    Store,
    SupportTicket,
    TicketMessage,
    User,
)
from bot.ai.customer_schemas import (
    BrowseMenuAction,
    CheckCouponAction,
    FindDealsAction,
    FindNearbyStoresAction,
    GetMyAccountAction,
    GetOrderStatusAction,
    GetTodaySpecialsAction,
    OpenSupportTicketAction,
    StartAppLiveChatAction,
    StartStoreLiveChatAction,
)

logger = logging.getLogger(__name__)


def _generate_ticket_code() -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=8))


def _get_maintainer_ids() -> list[int]:
    raw = EnvKeys.MAINTAINER_IDS or ""
    ids = []
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            ids.append(int(part))
    if not ids and EnvKeys.OWNER_ID:
        try:
            ids.append(int(EnvKeys.OWNER_ID))
        except (ValueError, TypeError):
            pass
    return ids


async def _notify_ids(bot, ids: list[int], text: str) -> None:
    for uid in ids:
        try:
            await bot.send_message(uid, text)
        except Exception as e:
            logger.warning("Failed to notify %s: %s", uid, e)
    support_chat = EnvKeys.SUPPORT_CHAT_ID
    if support_chat:
        try:
            await bot.send_message(int(support_chat), text)
        except Exception as e:
            logger.warning("Failed to notify support chat: %s", e)


def _bangkok_now() -> datetime:
    """Return current Bangkok time (UTC+7)."""
    from datetime import timezone, timedelta
    tz = timezone(timedelta(hours=7))
    return datetime.now(tz)


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ── Catalog tools (no user_id needed) ────────────────────────────────────────

def execute_browse_menu(action: BrowseMenuAction) -> dict:
    with Database().session() as s:
        q = s.query(Goods).filter(Goods.is_active.is_(True))
        if action.in_stock_only:
            # For products: available_quantity > 0; for prepared: stock_quantity=0 means unlimited
            q = q.filter(
                (Goods.sold_out_today.is_(False))
            )
        if action.keyword:
            kw = f"%{action.keyword}%"
            q = q.filter(
                (Goods.name.ilike(kw)) | (Goods.description.ilike(kw)) | (Goods.allergens.ilike(kw))
            )
        if action.category:
            q = q.filter(Goods.category_name.ilike(f"%{action.category}%"))
        if action.max_price is not None:
            q = q.filter(Goods.price <= action.max_price)
        if action.min_price is not None:
            q = q.filter(Goods.price >= action.min_price)
        items = q.order_by(Goods.price).limit(action.limit).all()
        return {
            "items": [
                {
                    "name": g.name,
                    "price": str(g.price),
                    "category": g.category_name,
                    "description": g.description[:200] if g.description else None,
                    "allergens": g.allergens,
                    "prep_time_minutes": g.prep_time_minutes,
                    "calories": g.calories,
                    "available": g.is_currently_available,
                }
                for g in items
            ],
            "count": len(items),
        }


def execute_get_today_specials(action: GetTodaySpecialsAction) -> dict:
    now = _bangkok_now()
    current_time = now.strftime("%H:%M")

    with Database().session() as s:
        q = s.query(Goods).filter(
            Goods.is_active.is_(True),
            Goods.sold_out_today.is_(False),
            Goods.available_from.isnot(None),
            Goods.available_until.isnot(None),
        )
        if action.category:
            q = q.filter(Goods.category_name.ilike(f"%{action.category}%"))
        all_items = q.all()

        active = [
            g for g in all_items
            if g.available_from <= current_time <= g.available_until
        ]
        return {
            "current_time_bangkok": current_time,
            "items": [
                {
                    "name": g.name,
                    "price": str(g.price),
                    "category": g.category_name,
                    "available_from": g.available_from,
                    "available_until": g.available_until,
                }
                for g in active
            ],
            "count": len(active),
        }


def execute_find_deals(action: FindDealsAction) -> dict:
    now = datetime.now(timezone.utc)
    with Database().session() as s:
        q = s.query(Coupon).filter(
            Coupon.is_active.is_(True),
            (Coupon.valid_until.is_(None)) | (Coupon.valid_until >= now),
            (Coupon.valid_from.is_(None)) | (Coupon.valid_from <= now),
            (Coupon.max_uses.is_(None)) | (Coupon.current_uses < Coupon.max_uses),
        )
        if action.min_order_max is not None:
            q = q.filter(
                (Coupon.min_order.is_(None)) | (Coupon.min_order <= action.min_order_max)
            )
        coupons = q.order_by(Coupon.discount_value.desc()).all()
        return {
            "deals": [
                {
                    "code": c.code,
                    "discount_type": c.discount_type,
                    "discount_value": str(c.discount_value),
                    "min_order": str(c.min_order) if c.min_order else None,
                    "max_discount": str(c.max_discount) if c.max_discount else None,
                    "valid_until": c.valid_until.isoformat() if c.valid_until else None,
                }
                for c in coupons
            ],
            "count": len(coupons),
        }


def execute_find_nearby_stores(action: FindNearbyStoresAction) -> dict:
    with Database().session() as s:
        stores = s.query(Store).filter(
            Store.is_active.is_(True),
            Store.latitude.isnot(None),
            Store.longitude.isnot(None),
        ).all()

    results = []
    for store in stores:
        dist = _haversine_km(action.latitude, action.longitude, store.latitude, store.longitude)
        if dist <= action.max_distance_km:
            results.append({
                "name": store.name,
                "address": store.address,
                "distance_km": round(dist, 2),
                "phone": store.phone,
            })
    results.sort(key=lambda x: x["distance_km"])
    return {"stores": results, "count": len(results)}


def execute_check_coupon(action: CheckCouponAction) -> dict:
    now = datetime.now(timezone.utc)
    with Database().session() as s:
        coupon = s.query(Coupon).filter(
            Coupon.code == action.code.upper(),
        ).first()

    if not coupon:
        return {"valid": False, "reason": "Coupon code not found"}
    if not coupon.is_active:
        return {"valid": False, "reason": "Coupon is inactive"}
    if coupon.valid_from and coupon.valid_from > now:
        return {"valid": False, "reason": "Coupon is not yet active"}
    if coupon.valid_until and coupon.valid_until < now:
        return {"valid": False, "reason": "Coupon has expired"}
    if coupon.max_uses and coupon.current_uses >= coupon.max_uses:
        return {"valid": False, "reason": "Coupon has reached its usage limit"}

    result = {
        "valid": True,
        "code": coupon.code,
        "discount_type": coupon.discount_type,
        "discount_value": str(coupon.discount_value),
        "min_order": str(coupon.min_order) if coupon.min_order else None,
        "max_discount": str(coupon.max_discount) if coupon.max_discount else None,
        "valid_until": coupon.valid_until.isoformat() if coupon.valid_until else None,
    }

    if action.order_total is not None and action.order_total > 0:
        if coupon.min_order and action.order_total < coupon.min_order:
            result["applicable"] = False
            result["reason"] = f"Order minimum is {coupon.min_order}"
        else:
            if coupon.discount_type == "percent":
                raw = action.order_total * coupon.discount_value / 100
                discount = min(raw, coupon.max_discount) if coupon.max_discount else raw
            else:
                discount = coupon.discount_value
            result["applicable"] = True
            result["effective_discount"] = str(round(discount, 2))
            result["final_total"] = str(round(action.order_total - discount, 2))

    return result


# ── Own-account tools (always filtered by user_id from Telegram auth) ─────────

def execute_get_order_status(action: GetOrderStatusAction, user_id: int) -> dict:
    with Database().session() as s:
        q = s.query(Order).filter(Order.buyer_id == user_id)
        if action.order_code:
            q = q.filter(Order.order_code == action.order_code.upper())
        orders = q.order_by(Order.created_at.desc()).limit(action.limit).all()

    if not orders:
        return {"orders": [], "message": "No orders found"}

    return {
        "orders": [
            {
                "order_code": o.order_code,
                "status": o.order_status,
                "total_price": str(o.total_price),
                "payment_method": o.payment_method,
                "delivery_type": o.delivery_type,
                "created_at": o.created_at.isoformat() if o.created_at else None,
                "delivery_time": o.delivery_time.isoformat() if o.delivery_time else None,
            }
            for o in orders
        ]
    }


def execute_get_my_account(user_id: int) -> dict:
    with Database().session() as s:
        user = s.query(User).filter(User.telegram_id == user_id).first()
        info = s.query(CustomerInfo).filter(CustomerInfo.telegram_id == user_id).first()
        if not user:
            return {"error": "User not found"}

        # Count referrals
        referral_count = s.query(User).filter(User.referral_id == user_id).count()

    return {
        "telegram_id": user_id,
        "registered_at": user.registration_date.isoformat() if user.registration_date else None,
        "bonus_balance": str(info.bonus_balance) if info else "0",
        "total_spent": str(info.total_spendings) if info else "0",
        "completed_orders": info.completed_orders_count if info else 0,
        "referral_count": referral_count,
    }


# ── Support tools ─────────────────────────────────────────────────────────────

async def execute_open_support_ticket(
    action: OpenSupportTicketAction, user_id: int, bot
) -> dict:
    ticket_code = _generate_ticket_code()

    # Resolve order_id from order_code if provided
    order_id = None
    if action.order_code:
        with Database().session() as s:
            order = s.query(Order).filter(
                Order.order_code == action.order_code.upper(),
                Order.buyer_id == user_id,  # Security: only own orders
            ).first()
            if order:
                order_id = order.id

    with Database().session() as s:
        ticket = SupportTicket(
            ticket_code=ticket_code,
            user_id=user_id,
            subject=action.subject,
            priority=action.priority,
            order_id=order_id,
        )
        s.add(ticket)
        s.flush()
        s.add(TicketMessage(
            ticket_id=ticket.id,
            sender_id=user_id,
            sender_role="user",
            message_text=action.description,
        ))
        s.commit()

    maintainers = _get_maintainer_ids()
    notify_text = (
        f"🎫 <b>New Support Ticket</b>\n\n"
        f"Code: <b>{ticket_code}</b>\n"
        f"User: {user_id}\n"
        f"Subject: {action.subject}\n"
        f"Priority: {action.priority}\n"
        f"Via: AI Assistant"
    )
    await _notify_ids(bot, maintainers, notify_text)

    return {"success": True, "ticket_code": ticket_code}


async def execute_start_app_live_chat(
    action: StartAppLiveChatAction, user_id: int, bot
) -> dict:
    maintainers = _get_maintainer_ids()
    if not maintainers:
        return {"success": False, "error": "No maintainers configured"}

    ticket_code = _generate_ticket_code()
    with Database().session() as s:
        ticket = SupportTicket(
            ticket_code=ticket_code,
            user_id=user_id,
            subject=f"[APP_LIVE_CHAT] {action.reason[:150]}",
            priority="high",
        )
        s.add(ticket)
        s.flush()
        s.add(TicketMessage(
            ticket_id=ticket.id,
            sender_id=user_id,
            sender_role="user",
            message_text=f"App live chat started. Reason: {action.reason}",
        ))
        s.commit()
        ticket_id = ticket.id

    notify_text = (
        f"💬 <b>App Live Chat Request</b>\n\n"
        f"Ticket: <b>{ticket_code}</b>\n"
        f"User: {user_id}\n"
        f"Reason: {action.reason}\n\n"
        f"Respond via admin ticket panel."
    )
    await _notify_ids(bot, maintainers, notify_text)

    return {
        "success": True,
        "ticket_code": ticket_code,
        "ticket_id": ticket_id,
        "relay_target": "maintainers",
    }


async def execute_start_store_live_chat(
    action: StartStoreLiveChatAction, user_id: int, bot
) -> dict:
    ticket_code = _generate_ticket_code()

    # Resolve order_id from order_code if provided
    order_id = None
    if action.order_code:
        with Database().session() as s:
            order = s.query(Order).filter(
                Order.order_code == action.order_code.upper(),
                Order.buyer_id == user_id,  # Security: only own orders
            ).first()
            if order:
                order_id = order.id

    with Database().session() as s:
        subject = f"[STORE_LIVE_CHAT] {action.reason[:150]}"
        ticket = SupportTicket(
            ticket_code=ticket_code,
            user_id=user_id,
            subject=subject,
            priority="high",
            order_id=order_id,
        )
        s.add(ticket)
        s.flush()
        s.add(TicketMessage(
            ticket_id=ticket.id,
            sender_id=user_id,
            sender_role="user",
            message_text=f"Store live chat started. Reason: {action.reason}",
        ))
        s.commit()
        ticket_id = ticket.id

    # Notify all maintainers (store support uses same channel for now;
    # per-store admin notification can be layered in when USERS_MANAGE permission
    # lookup is available per-brand)
    maintainers = _get_maintainer_ids()
    notify_text = (
        f"🏪 <b>Store Live Chat Request</b>\n\n"
        f"Ticket: <b>{ticket_code}</b>\n"
        f"User: {user_id}\n"
        f"Reason: {action.reason}\n"
        + (f"Order: {action.order_code}\n" if action.order_code else "")
        + "\nRespond via admin ticket panel."
    )
    await _notify_ids(bot, maintainers, notify_text)

    return {
        "success": True,
        "ticket_code": ticket_code,
        "ticket_id": ticket_id,
        "relay_target": "store_admins",
    }
