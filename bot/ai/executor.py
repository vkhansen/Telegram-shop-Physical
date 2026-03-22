"""Action executor — validated Pydantic models to database calls (Card 17)."""

import datetime
import logging
from decimal import Decimal

from pydantic import BaseModel

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
from bot.database.methods.update import update_item
from bot.database.models.main import (
    Categories,
    DeliveryChatMessage,
    Goods,
    Order,
    OrderItem,
    User,
)

logger = logging.getLogger(__name__)


def _day_start(date_str: str) -> datetime.datetime:
    d = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    return datetime.datetime.combine(d, datetime.time.min)


def _day_end(date_str: str) -> datetime.datetime:
    d = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    return datetime.datetime.combine(d, datetime.time.min) + datetime.timedelta(days=1)


async def execute_query(action: BaseModel) -> dict:
    """Execute read-only database queries."""
    match action.action:
        case "search_orders":
            return _search_orders(action)
        case "search_chat":
            return _search_chat(action)
        case "search_deliveries":
            return _search_deliveries(action)
        case "view_inventory":
            return _view_inventory(action)
        case "get_stats":
            return _get_stats(action)
        case "lookup_user":
            return _lookup_user(action)
        case "propose_mapping":
            return {"mapping": action.model_dump()}
        case _:
            return {"error": f"Unknown query action: {action.action}"}


async def execute_mutation(action: BaseModel, admin_id: int) -> dict:
    """Execute validated mutation with audit logging."""
    match action.action:
        case "create_item":
            return _exec_create_item(action, admin_id)
        case "update_item":
            return _exec_update_item(action, admin_id)
        case "delete_item":
            return _exec_delete_item(action, admin_id)
        case "bulk_price_update":
            return _exec_bulk_price_update(action, admin_id)
        case "adjust_stock":
            return _exec_adjust_stock(action, admin_id)
        case "create_category":
            return _exec_create_category(action, admin_id)
        case "delete_category":
            return _exec_delete_category(action, admin_id)
        case "import_menu":
            return _exec_import_menu(action, admin_id)
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
            q = q.filter(DeliveryChatMessage.message_text.ilike(f"%{action.keyword}%"))
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
            q = q.filter(DeliveryChatMessage.sent_at >= _day_start(action.date_from))
        if action.date_to:
            q = q.filter(DeliveryChatMessage.sent_at < _day_end(action.date_to))

        msgs = q.order_by(DeliveryChatMessage.sent_at.desc()).limit(action.limit).all()
        result = []
        for m in msgs:
            result.append({
                "order_id": m.order_id,
                "sender_role": m.sender_role,
                "sender_id": m.sender_id,
                "text": m.message_text,
                "has_photo": m.photo_file_id is not None,
                "sent_at": str(m.sent_at),
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
