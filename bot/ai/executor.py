"""Action executor — validated Pydantic models to database calls (Card 17)."""

import asyncio
import datetime
import logging
from decimal import Decimal
from functools import partial

from pydantic import BaseModel


def _escape_like(value: str) -> str:
    """Escape SQL LIKE wildcards to prevent wildcard injection (SEC-05, SEC-10)."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

from bot.database import Database
from bot.database.methods.create import create_category, create_item
from bot.database.methods.delete import delete_category, delete_item
from bot.database.methods.inventory import add_inventory, log_inventory_change
from bot.database.methods.read import (
    check_category,
    check_user,
    check_user_referrals,
    get_item_info,
    get_user_count,
    query_user_orders,
    select_all_orders,
    select_count_categories,
    select_count_goods,
    select_count_items,
    select_today_orders,
    select_today_users,
)
from bot.database.methods.update import ban_user, unban_user, update_item
from bot.database.models.main import (
    Categories,
    Coupon,
    DeliveryChatMessage,
    Goods,
    Order,
    OrderItem,
    ReferenceCode,
    Store,
    User,
)
from bot.utils.order_status import is_valid_transition, get_allowed_transitions

logger = logging.getLogger(__name__)


def _day_start(date_str: str) -> datetime.datetime:
    d = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    return datetime.datetime.combine(d, datetime.time.min)


def _day_end(date_str: str) -> datetime.datetime:
    d = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    return datetime.datetime.combine(d, datetime.time.min) + datetime.timedelta(days=1)


async def _run_sync(func, *args):
    """Run a synchronous function in a thread executor to avoid blocking the event loop."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(func, *args))


async def execute_query(action: BaseModel) -> dict:
    """Execute read-only database queries."""
    match action.action:
        case "search_orders":
            return await _run_sync(_search_orders, action)
        case "search_chat":
            return await _run_sync(_search_chat, action)
        case "search_deliveries":
            return await _run_sync(_search_deliveries, action)
        case "view_inventory":
            return await _run_sync(_view_inventory, action)
        case "get_stats":
            return await _run_sync(_get_stats, action)
        case "lookup_user":
            return await _run_sync(_lookup_user, action)
        case "propose_mapping":
            return {"mapping": action.model_dump()}
        case "list_item_media":
            from bot.ai.image_gen import list_item_media
            return await _run_sync(list_item_media, action.item_name)
        case "list_coupons":
            return await _run_sync(_list_coupons, action)
        case "list_refcodes":
            return await _run_sync(_list_refcodes, action)
        case "list_stores":
            return await _run_sync(_list_stores, action)
        case "revenue_report":
            return await _run_sync(_revenue_report, action)
        case _:
            return {"error": f"Unknown query action: {action.action}"}


async def execute_mutation(action: BaseModel, admin_id: int) -> dict:
    """Execute validated mutation with audit logging."""
    match action.action:
        case "create_item":
            return await _run_sync(_exec_create_item, action, admin_id)
        case "update_item":
            return await _run_sync(_exec_update_item, action, admin_id)
        case "update_item_image":
            return await _run_sync(_exec_update_item_image, action, admin_id)
        case "generate_item_images":
            # Handled specially in grok_assistant.py (needs bot instance)
            return {"error": "generate_item_images must be handled by the conversation handler"}
        case "remove_item_media":
            return await _run_sync(_exec_remove_item_media, action, admin_id)
        case "delete_item":
            return await _run_sync(_exec_delete_item, action, admin_id)
        case "bulk_price_update":
            return await _run_sync(_exec_bulk_price_update, action, admin_id)
        case "adjust_stock":
            return await _run_sync(_exec_adjust_stock, action, admin_id)
        case "create_category":
            return await _run_sync(_exec_create_category, action, admin_id)
        case "delete_category":
            return await _run_sync(_exec_delete_category, action, admin_id)
        case "import_menu":
            return await _run_sync(_exec_import_menu, action, admin_id)
        case "change_order_status":
            return await _run_sync(_exec_change_order_status, action, admin_id)
        case "assign_driver":
            return await _run_sync(_exec_assign_driver, action, admin_id)
        case "ban_user":
            return await _run_sync(_exec_ban_user, action, admin_id)
        case "unban_user":
            return await _run_sync(_exec_unban_user, action, admin_id)
        case "create_coupon":
            return await _run_sync(_exec_create_coupon, action, admin_id)
        case "toggle_coupon":
            return await _run_sync(_exec_toggle_coupon, action, admin_id)
        case "create_refcode":
            return await _run_sync(_exec_create_refcode, action, admin_id)
        case "deactivate_refcode":
            return await _run_sync(_exec_deactivate_refcode, action, admin_id)
        case "send_broadcast":
            return await _exec_send_broadcast(action, admin_id)
        case "toggle_store":
            return await _run_sync(_exec_toggle_store, action, admin_id)
        case _:
            return {"error": f"Unknown mutation action: {action.action}"}


# ── Query implementations ────────────────────────────────────────────

def _search_orders(action) -> dict:
    with Database().session() as s:
        q = s.query(Order)
        if action.order_code:
            q = q.filter(Order.order_code == action.order_code)
        if action.buyer_id:
            q = q.filter(Order.buyer_id == action.buyer_id)
        if action.status:
            q = q.filter(Order.order_status == action.status)
        if action.payment_method:
            q = q.filter(Order.payment_method == action.payment_method)
        if action.delivery_type:
            q = q.filter(Order.delivery_type == action.delivery_type)
        if action.date_from:
            q = q.filter(Order.created_at >= _day_start(action.date_from))
        if action.date_to:
            q = q.filter(Order.created_at < _day_end(action.date_to))

        orders = q.order_by(Order.created_at.desc()).limit(action.limit).all()

        result = []
        for o in orders:
            items = s.query(OrderItem).filter(OrderItem.order_id == o.id).all()
            result.append({
                "id": o.id,
                "order_code": o.order_code,
                "buyer_id": o.buyer_id,
                "total_price": str(o.total_price),
                "payment_method": o.payment_method,
                "delivery_type": o.delivery_type,
                "delivery_address": o.delivery_address,
                "status": o.order_status,
                "created_at": str(o.created_at),
                "items": [
                    {"name": it.item_name, "price": str(it.price), "qty": it.quantity}
                    for it in items
                ],
            })
        return {"orders": result, "count": len(result)}


def _search_chat(action) -> dict:
    with Database().session() as s:
        q = s.query(DeliveryChatMessage)
        if action.order_id:
            q = q.filter(DeliveryChatMessage.order_id == action.order_id)
        if action.order_code:
            order = s.query(Order).filter(Order.order_code == action.order_code).first()
            if order:
                q = q.filter(DeliveryChatMessage.order_id == order.id)
            else:
                return {"messages": [], "count": 0}
        if action.sender_role:
            q = q.filter(DeliveryChatMessage.sender_role == action.sender_role)
        if action.keyword:
            escaped = _escape_like(action.keyword)
            q = q.filter(DeliveryChatMessage.message_text.ilike(f"%{escaped}%", escape="\\"))
        if action.has_photo is not None:
            if action.has_photo:
                q = q.filter(DeliveryChatMessage.photo_file_id.isnot(None))
            else:
                q = q.filter(DeliveryChatMessage.photo_file_id.is_(None))
        if action.has_location is not None:
            if action.has_location:
                q = q.filter(DeliveryChatMessage.location_lat.isnot(None))
            else:
                q = q.filter(DeliveryChatMessage.location_lat.is_(None))
        if action.date_from:
            q = q.filter(DeliveryChatMessage.created_at >= _day_start(action.date_from))
        if action.date_to:
            q = q.filter(DeliveryChatMessage.created_at < _day_end(action.date_to))

        msgs = q.order_by(DeliveryChatMessage.created_at.desc()).limit(action.limit).all()
        result = []
        for m in msgs:
            result.append({
                "order_id": m.order_id,
                "sender_role": m.sender_role,
                "sender_id": m.sender_id,
                "text": m.message_text,
                "has_photo": m.photo_file_id is not None,
                "sent_at": str(m.created_at),
            })
        return {"messages": result, "count": len(result)}


def _search_deliveries(action) -> dict:
    with Database().session() as s:
        q = s.query(Order).filter(Order.order_status.in_(
            ["out_for_delivery", "delivered"]
        ))
        if action.delivery_zone:
            q = q.filter(Order.delivery_zone == action.delivery_zone)
        if action.has_delivery_photo is not None:
            if action.has_delivery_photo:
                q = q.filter(Order.delivery_photo.isnot(None))
            else:
                q = q.filter(Order.delivery_photo.is_(None))
        if action.has_gps is not None:
            if action.has_gps:
                q = q.filter(Order.latitude.isnot(None))
            else:
                q = q.filter(Order.latitude.is_(None))
        if action.driver_id:
            q = q.filter(Order.driver_id == action.driver_id)
        if action.delivery_type:
            q = q.filter(Order.delivery_type == action.delivery_type)
        if action.date_from:
            q = q.filter(Order.created_at >= _day_start(action.date_from))
        if action.date_to:
            q = q.filter(Order.created_at < _day_end(action.date_to))

        orders = q.order_by(Order.created_at.desc()).limit(action.limit).all()
        result = []
        for o in orders:
            result.append({
                "order_code": o.order_code,
                "delivery_type": o.delivery_type,
                "delivery_zone": o.delivery_zone,
                "driver_id": o.driver_id,
                "has_photo": o.delivery_photo is not None,
                "has_gps": o.latitude is not None,
                "status": o.order_status,
                "created_at": str(o.created_at),
            })
        return {"deliveries": result, "count": len(result)}


def _view_inventory(action) -> dict:
    with Database().session() as s:
        q = s.query(Goods)
        if action.category_filter:
            q = q.filter(Goods.category_name == action.category_filter)
        if action.only_low_stock:
            q = q.filter(
                (Goods.stock_quantity - Goods.reserved_quantity) <= action.low_stock_threshold
            )

        items = q.order_by(Goods.category_name, Goods.name).all()
        result = []
        for g in items:
            result.append({
                "name": g.name,
                "category": g.category_name,
                "price": str(g.price),
                "stock": g.stock_quantity,
                "reserved": g.reserved_quantity,
                "available": g.available_quantity,
                "item_type": g.item_type,
                "is_active": g.is_active,
            })
        return {"inventory": result, "count": len(result)}


def _get_stats(action) -> dict:
    today = datetime.date.today().isoformat()
    stats = {
        "total_users": get_user_count(),
        "total_items": select_count_goods(),
        "total_categories": select_count_categories(),
        "total_stock_units": select_count_items(),
    }

    if action.include_revenue:
        stats["today_revenue"] = str(select_today_orders(today))
        stats["all_time_revenue"] = str(select_all_orders())

    if action.include_user_growth:
        stats["today_new_users"] = select_today_users(today)

    if action.include_top_items:
        with Database().session() as s:
            from sqlalchemy import func
            top = s.query(
                OrderItem.item_name,
                func.sum(OrderItem.quantity).label("total_qty")
            ).group_by(OrderItem.item_name).order_by(
                func.sum(OrderItem.quantity).desc()
            ).limit(10).all()
            stats["top_items"] = [
                {"name": name, "total_sold": int(qty)} for name, qty in top
            ]

    return stats


def _lookup_user(action) -> dict:
    if action.telegram_id:
        user = check_user(action.telegram_id)
    elif action.phone_number:
        from bot.database.models.main import CustomerInfo
        with Database().session() as s:
            ci = s.query(CustomerInfo).filter(
                CustomerInfo.phone_number == action.phone_number
            ).first()
            if ci:
                user = check_user(ci.telegram_id)
            else:
                return {"error": "User not found by phone number"}
    else:
        return {"error": "Provide telegram_id or phone_number"}

    if not user:
        return {"error": "User not found"}

    result = {
        "telegram_id": user["telegram_id"],
        "role_id": user["role_id"],
        "is_banned": user.get("is_banned", False),
        "registration_date": str(user.get("registration_date")),
    }

    if action.include_referrals:
        result["referral_count"] = check_user_referrals(user["telegram_id"])

    return {"user": result}


# ── Mutation implementations ─────────────────────────────────────────

def _exec_create_item(action, admin_id: int) -> dict:
    existing = get_item_info(action.item_name)
    if existing:
        return {"error": f"Item '{action.item_name}' already exists"}

    create_item(
        action.item_name,
        action.description,
        float(action.price),
        action.category_name,
        item_type=action.item_type,
    )
    if action.stock_quantity > 0:
        add_inventory(
            action.item_name, action.stock_quantity,
            admin_id, comment="AI assistant create"
        )
    logger.info("AI admin %s created item '%s'", admin_id, action.item_name)
    return {"success": True, "created": action.item_name}


def _exec_update_item(action, admin_id: int) -> dict:
    existing = get_item_info(action.item_name)
    if not existing:
        return {"error": f"Item '{action.item_name}' not found"}

    new_name = action.new_name or action.item_name
    new_desc = action.new_description or existing["description"]
    new_price = float(action.new_price) if action.new_price else existing["price"]
    new_cat = action.new_category or existing["category_name"]

    success, error = update_item(action.item_name, new_name, new_desc, new_price, new_cat)
    if not success:
        return {"error": error or "Update failed"}

    logger.info("AI admin %s updated item '%s'", admin_id, action.item_name)
    return {"success": True, "updated": action.item_name}


def _exec_update_item_image(action, admin_id: int) -> dict:
    if not action.photo_file_id:
        return {"error": "No photo attached. Please send a photo with your message to update the item image."}

    existing = get_item_info(action.item_name)
    if not existing:
        return {"error": f"Item '{action.item_name}' not found"}

    from bot.ai.image_gen import _add_media_entry
    media_id = _add_media_entry(
        action.item_name, action.photo_file_id,
        is_ai_generated=False,
    )

    logger.info("AI admin %s added image for '%s' (media_id=%s)",
                admin_id, action.item_name, media_id)
    return {"success": True, "updated_image": action.item_name, "media_id": media_id}


def _exec_remove_item_media(action, admin_id: int) -> dict:
    if not action.confirm:
        return {"error": "Media removal requires confirm=True"}

    from bot.ai.image_gen import remove_media_entry
    result = remove_media_entry(action.item_name, action.media_id)
    if result.get("success"):
        logger.info("AI admin %s removed media '%s' from '%s'",
                    admin_id, action.media_id, action.item_name)
    return result


def _exec_delete_item(action, admin_id: int) -> dict:
    if not action.confirm:
        return {"error": "Deletion requires confirm=True"}

    existing = get_item_info(action.item_name)
    if not existing:
        return {"error": f"Item '{action.item_name}' not found"}

    delete_item(action.item_name)
    logger.info("AI admin %s deleted item '%s'", admin_id, action.item_name)
    return {"success": True, "deleted": action.item_name}


def _exec_bulk_price_update(action, admin_id: int) -> dict:
    results = []
    errors = []
    for upd in action.updates:
        item_name = upd.item_name
        new_price = upd.new_price

        existing = get_item_info(item_name)
        if not existing:
            errors.append(f"Item '{item_name}' not found")
            continue

        success, error = update_item(
            item_name, item_name,
            existing["description"],
            float(new_price),
            existing["category_name"]
        )
        if success:
            results.append(item_name)
        else:
            errors.append(f"{item_name}: {error}")

    logger.info("AI admin %s bulk price update: %d items", admin_id, len(results))
    return {"success": True, "updated": results, "errors": errors}


def _exec_adjust_stock(action, admin_id: int) -> dict:
    existing = get_item_info(action.item_name)
    if not existing:
        return {"error": f"Item '{action.item_name}' not found"}

    if action.operation == "set":
        with Database().session() as s:
            goods = s.query(Goods).filter(Goods.name == action.item_name).first()
            if goods:
                old_qty = goods.stock_quantity
                goods.stock_quantity = action.quantity
                log_inventory_change(
                    action.item_name, "manual",
                    action.quantity - old_qty,
                    admin_id=admin_id,
                    comment=action.comment or "AI assistant set stock",
                    session=s,
                )
                s.commit()
    elif action.operation == "add":
        add_inventory(
            action.item_name, action.quantity,
            admin_id, comment=action.comment or "AI assistant add stock"
        )
    elif action.operation == "remove":
        with Database().session() as s:
            goods = s.query(Goods).filter(Goods.name == action.item_name).first()
            if goods:
                if goods.stock_quantity < action.quantity:
                    return {"error": f"Cannot remove {action.quantity}, only {goods.stock_quantity} in stock"}
                goods.stock_quantity -= action.quantity
                log_inventory_change(
                    action.item_name, "manual",
                    -action.quantity,
                    admin_id=admin_id,
                    comment=action.comment or "AI assistant remove stock",
                    session=s,
                )
                s.commit()

    logger.info("AI admin %s adjusted stock '%s': %s %d", admin_id, action.item_name, action.operation, action.quantity)
    return {"success": True, "item": action.item_name, "operation": action.operation, "quantity": action.quantity}


def _exec_create_category(action, admin_id: int) -> dict:
    existing = check_category(action.category_name)
    if existing:
        return {"error": f"Category '{action.category_name}' already exists"}

    create_category(action.category_name)
    logger.info("AI admin %s created category '%s'", admin_id, action.category_name)
    return {"success": True, "created": action.category_name}


def _exec_delete_category(action, admin_id: int) -> dict:
    if not action.confirm:
        return {"error": "Deletion requires confirm=True"}

    existing = check_category(action.category_name)
    if not existing:
        return {"error": f"Category '{action.category_name}' not found"}

    delete_category(action.category_name)
    logger.info("AI admin %s deleted category '%s'", admin_id, action.category_name)
    return {"success": True, "deleted": action.category_name}


def _exec_import_menu(action, admin_id: int) -> dict:
    created, skipped, failed = [], [], []

    if action.create_missing_categories:
        with Database().session() as s:
            existing_cats = {c.name for c in s.query(Categories).all()}
        needed = {row.category_name for row in action.items} - existing_cats
        for cat in needed:
            create_category(cat)

    for row in action.items:
        # LOGIC-32 fix: Wrap item operations in try/except to populate failed list
        try:
            existing = get_item_info(row.item_name)
            if existing and action.skip_existing:
                skipped.append(row.item_name)
                continue
            if existing and action.overwrite_existing:
                update_item(
                    row.item_name, row.item_name,
                    row.description, float(row.price),
                    row.category_name
                )
                created.append(row.item_name)
            elif not existing:
                create_item(
                    row.item_name, row.description,
                    float(row.price), row.category_name,
                    item_type=row.item_type,
                )
                if row.stock_quantity > 0:
                    add_inventory(
                        row.item_name, row.stock_quantity,
                        admin_id, comment="AI bulk import"
                    )
                created.append(row.item_name)
            else:
                skipped.append(row.item_name)
        except Exception as e:
            logger.error("AI import failed for item '%s': %s", row.item_name, e)
            failed.append(row.item_name)

    logger.info(
        "AI admin %s import: %d created, %d skipped",
        admin_id, len(created), len(skipped),
    )
    return {
        "success": True,
        "created": len(created),
        "skipped": len(skipped),
        "failed": len(failed),
    }


# ── Order management ────────────────────────────────────────────────

def _exec_change_order_status(action, admin_id: int) -> dict:
    with Database().session() as s:
        order = s.query(Order).filter(Order.order_code == action.order_code).first()
        if not order:
            return {"error": f"Order '{action.order_code}' not found"}
        if not action.confirm:
            return {"error": "Status change requires confirm=True"}

        current = order.order_status
        if not is_valid_transition(current, action.new_status):
            allowed = get_allowed_transitions(current)
            return {
                "error": f"Cannot transition from '{current}' to '{action.new_status}'",
                "allowed_transitions": list(allowed),
            }

        order.order_status = action.new_status
        if action.new_status == "delivered":
            order.completed_at = datetime.datetime.now(datetime.UTC)
        s.commit()

    logger.info("AI admin %s changed order %s: %s → %s",
                admin_id, action.order_code, current, action.new_status)
    return {
        "success": True,
        "order_code": action.order_code,
        "old_status": current,
        "new_status": action.new_status,
    }


def _exec_assign_driver(action, admin_id: int) -> dict:
    with Database().session() as s:
        order = s.query(Order).filter(Order.order_code == action.order_code).first()
        if not order:
            return {"error": f"Order '{action.order_code}' not found"}

        order.driver_id = action.driver_id
        s.commit()

    logger.info("AI admin %s assigned driver %d to order %s",
                admin_id, action.driver_id, action.order_code)
    return {"success": True, "order_code": action.order_code, "driver_id": action.driver_id}


# ── User management ────────────────────────────────────────────────

def _exec_ban_user(action, admin_id: int) -> dict:
    if not action.confirm:
        return {"error": "Ban requires confirm=True"}

    user = check_user(action.telegram_id)
    if not user:
        return {"error": f"User {action.telegram_id} not found"}

    success = ban_user(action.telegram_id, banned_by=admin_id, reason=action.reason)
    if not success:
        return {"error": f"Could not ban user {action.telegram_id} (already banned or is owner)"}

    logger.info("AI admin %s banned user %s, reason: %s",
                admin_id, action.telegram_id, action.reason)
    return {"success": True, "banned": action.telegram_id}


def _exec_unban_user(action, admin_id: int) -> dict:
    if not action.confirm:
        return {"error": "Unban requires confirm=True"}

    success = unban_user(action.telegram_id)
    if not success:
        return {"error": f"Could not unban user {action.telegram_id} (not found or not banned)"}

    logger.info("AI admin %s unbanned user %s", admin_id, action.telegram_id)
    return {"success": True, "unbanned": action.telegram_id}


# ── Coupon management ──────────────────────────────────────────────

def _exec_create_coupon(action, admin_id: int) -> dict:
    with Database().session() as s:
        existing = s.query(Coupon).filter(Coupon.code == action.code.upper()).first()
        if existing:
            return {"error": f"Coupon '{action.code.upper()}' already exists"}

        valid_until = None
        if action.valid_until:
            valid_until = datetime.datetime.strptime(action.valid_until, "%Y-%m-%d")

        coupon = Coupon(
            code=action.code.upper(),
            discount_type=action.discount_type,
            discount_value=float(action.discount_value),
            min_order=float(action.min_order),
            max_discount=float(action.max_discount) if action.max_discount else None,
            max_uses=action.max_uses,
            max_uses_per_user=action.max_uses_per_user,
            valid_until=valid_until,
            created_by=admin_id,
            note=action.note,
        )
        s.add(coupon)
        s.commit()

    logger.info("AI admin %s created coupon '%s'", admin_id, action.code.upper())
    return {"success": True, "created": action.code.upper()}


def _list_coupons(action) -> dict:
    with Database().session() as s:
        q = s.query(Coupon)
        if action.active_only:
            q = q.filter(Coupon.is_active.is_(True))
        coupons = q.order_by(Coupon.created_at.desc()).limit(action.limit).all()
        result = []
        for c in coupons:
            result.append({
                "code": c.code,
                "discount_type": c.discount_type,
                "discount_value": str(c.discount_value),
                "min_order": str(c.min_order) if c.min_order else "0",
                "max_uses": c.max_uses,
                "current_uses": c.current_uses,
                "is_active": c.is_active,
                "valid_until": str(c.valid_until) if c.valid_until else None,
                "note": c.note,
            })
        return {"coupons": result, "count": len(result)}


def _exec_toggle_coupon(action, admin_id: int) -> dict:
    with Database().session() as s:
        coupon = s.query(Coupon).filter(Coupon.code == action.code.upper()).first()
        if not coupon:
            return {"error": f"Coupon '{action.code.upper()}' not found"}
        coupon.is_active = action.is_active
        s.commit()

    logger.info("AI admin %s toggled coupon '%s' to %s",
                admin_id, action.code.upper(), action.is_active)
    return {"success": True, "code": action.code.upper(), "is_active": action.is_active}


# ── Reference code management ─────────────────────────────────────

def _exec_create_refcode(action, admin_id: int) -> dict:
    import random
    import string

    code = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

    expires_at = None
    if action.expires_in_hours > 0:
        expires_at = datetime.datetime.now(datetime.UTC) + datetime.timedelta(
            hours=action.expires_in_hours
        )

    with Database().session() as s:
        refcode = ReferenceCode(
            code=code,
            created_by=admin_id,
            expires_at=expires_at,
            max_uses=action.max_uses if action.max_uses > 0 else None,
            note=action.note,
            is_admin_code=True,
        )
        s.add(refcode)
        s.commit()

    logger.info("AI admin %s created refcode '%s'", admin_id, code)
    return {"success": True, "code": code, "expires_at": str(expires_at) if expires_at else None}


def _list_refcodes(action) -> dict:
    with Database().session() as s:
        q = s.query(ReferenceCode)
        if action.active_only:
            q = q.filter(ReferenceCode.is_active.is_(True))
        codes = q.order_by(ReferenceCode.created_at.desc()).limit(action.limit).all()
        result = []
        for rc in codes:
            result.append({
                "code": rc.code,
                "is_active": rc.is_active,
                "max_uses": rc.max_uses,
                "current_uses": rc.current_uses,
                "expires_at": str(rc.expires_at) if rc.expires_at else None,
                "note": rc.note,
                "created_at": str(rc.created_at),
            })
        return {"reference_codes": result, "count": len(result)}


def _exec_deactivate_refcode(action, admin_id: int) -> dict:
    with Database().session() as s:
        refcode = s.query(ReferenceCode).filter(ReferenceCode.code == action.code).first()
        if not refcode:
            return {"error": f"Reference code '{action.code}' not found"}
        refcode.is_active = False
        s.commit()

    logger.info("AI admin %s deactivated refcode '%s'", admin_id, action.code)
    return {"success": True, "deactivated": action.code}


# ── Broadcast ──────────────────────────────────────────────────────

async def _exec_send_broadcast(action, admin_id: int) -> dict:
    if not action.confirm:
        return {"error": "Broadcast requires confirm=True"}

    from bot.database.methods.read import get_all_users

    # Determine target user IDs
    if action.segment == "all":
        user_ids = get_all_users()
    else:
        user_ids = _get_segment_users(action.segment)

    if not user_ids:
        return {"error": f"No users found in segment '{action.segment}'"}

    # We return the count for Grok to confirm — actual sending is handled
    # by the conversation handler which has access to the bot instance.
    logger.info("AI admin %s broadcast to %d users (segment: %s)",
                admin_id, len(user_ids), action.segment)
    # LOGIC-33 fix: Don't return full user_ids list to AI (wastes tokens)
    return {
        "success": True,
        "segment": action.segment,
        "target_count": len(user_ids),
        "message_preview": action.message[:100],
    }


def _get_segment_users(segment: str) -> list[int]:
    """Get user IDs for a broadcast segment."""
    with Database().session() as s:
        from bot.database.models.main import CustomerInfo
        now = datetime.datetime.now(datetime.UTC)

        if segment == "high_spenders":
            from sqlalchemy import func
            avg_spend = s.query(func.avg(CustomerInfo.total_spendings)).scalar() or 0
            threshold = float(avg_spend) * 2
            users = s.query(CustomerInfo.telegram_id).filter(
                CustomerInfo.total_spendings >= threshold
            ).all()
            return [u[0] for u in users]

        elif segment == "recent_buyers":
            cutoff = now - datetime.timedelta(days=7)
            users = s.query(Order.buyer_id).filter(
                Order.created_at >= cutoff
            ).distinct().all()
            return [u[0] for u in users if u[0]]

        elif segment == "inactive":
            cutoff = now - datetime.timedelta(days=30)
            active = {u[0] for u in s.query(Order.buyer_id).filter(
                Order.created_at >= cutoff
            ).distinct().all() if u[0]}
            all_users = {u[0] for u in s.query(User.telegram_id).all()}
            return list(all_users - active)

        elif segment == "new_users":
            cutoff = now - datetime.timedelta(days=7)
            users = s.query(User.telegram_id).filter(
                User.registration_date >= cutoff
            ).all()
            return [u[0] for u in users]

        return []


# ── Store management ───────────────────────────────────────────────

def _list_stores(action) -> dict:
    with Database().session() as s:
        q = s.query(Store)
        if action.active_only:
            q = q.filter(Store.is_active.is_(True))
        stores = q.order_by(Store.name).all()
        result = []
        for st in stores:
            result.append({
                "id": st.id,
                "name": st.name,
                "address": st.address,
                "phone": st.phone,
                "is_active": st.is_active,
                "is_default": st.is_default,
                "latitude": st.latitude,
                "longitude": st.longitude,
            })
        return {"stores": result, "count": len(result)}


def _exec_toggle_store(action, admin_id: int) -> dict:
    with Database().session() as s:
        store = s.query(Store).filter(Store.name == action.store_name).first()
        if not store:
            return {"error": f"Store '{action.store_name}' not found"}
        store.is_active = action.is_active
        s.commit()

    logger.info("AI admin %s toggled store '%s' to %s",
                admin_id, action.store_name, action.is_active)
    return {"success": True, "store": action.store_name, "is_active": action.is_active}


# ── Revenue report ─────────────────────────────────────────────────

def _revenue_report(action) -> dict:
    now = datetime.datetime.now(datetime.UTC)
    periods = {
        "today": now.replace(hour=0, minute=0, second=0, microsecond=0),
        "week": now - datetime.timedelta(days=7),
        "month": now - datetime.timedelta(days=30),
        "all": datetime.datetime(2000, 1, 1),
    }
    since = periods[action.period]

    with Database().session() as s:
        from sqlalchemy import func

        q = s.query(Order).filter(
            Order.created_at >= since,
            Order.order_status == "delivered",
        )
        orders = q.all()

        total_revenue = sum(float(o.total_price) for o in orders)
        order_count = len(orders)
        avg_value = total_revenue / order_count if order_count else 0

        result = {
            "period": action.period,
            "total_revenue": f"{total_revenue:.2f}",
            "order_count": order_count,
            "avg_order_value": f"{avg_value:.2f}",
        }

        if action.include_by_payment:
            by_payment = {}
            for o in orders:
                method = o.payment_method or "unknown"
                by_payment[method] = by_payment.get(method, 0) + float(o.total_price)
            result["by_payment_method"] = {
                k: f"{v:.2f}" for k, v in by_payment.items()
            }

        if action.include_top_products:
            items = s.query(
                OrderItem.item_name,
                func.sum(OrderItem.quantity).label("qty"),
                func.sum(OrderItem.price * OrderItem.quantity).label("revenue"),
            ).join(Order).filter(
                Order.created_at >= since,
                Order.order_status == "delivered",
            ).group_by(OrderItem.item_name).order_by(
                func.sum(OrderItem.price * OrderItem.quantity).desc()
            ).limit(10).all()
            result["top_products"] = [
                {"name": name, "qty_sold": int(qty), "revenue": f"{float(rev):.2f}"}
                for name, qty, rev in items
            ]

        return result
