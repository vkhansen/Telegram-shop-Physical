"""Order query application service (CARD-32) — list/detail as plain DTOs."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import joinedload

from bot.database.main import Database
from bot.database.models.main import Order
from bot.services.dto import ServiceResult


def _order_to_dict(order: Order) -> dict[str, Any]:
    items = []
    for it in order.items or []:
        items.append(
            {
                "item_name": it.item_name,
                "quantity": it.quantity,
                "price": str(it.price),
                "selected_modifiers": it.selected_modifiers,
            }
        )
    return {
        "id": order.id,
        "order_code": order.order_code,
        "order_status": order.order_status,
        "payment_method": order.payment_method,
        "total_price": str(order.total_price),
        "bonus_applied": str(order.bonus_applied or 0),
        "delivery_address": order.delivery_address,
        "phone_number": order.phone_number,
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "brand_id": order.brand_id,
        "store_id": order.store_id,
        "items": items,
    }


def list_orders(
    user_id: int,
    *,
    status: str | None = None,
    limit: int = 10,
    offset: int = 0,
) -> ServiceResult:
    with Database().session() as session:
        query = (
            session.query(Order)
            .options(joinedload(Order.items))
            .filter(Order.buyer_id == user_id)
        )
        if status:
            query = query.filter(Order.order_status == status)
        rows = query.order_by(Order.created_at.desc()).offset(offset).limit(limit).all()
        return ServiceResult.success(orders=[_order_to_dict(o) for o in rows], count=len(rows))


def get_order(
    user_id: int,
    *,
    order_id: int | None = None,
    order_code: str | None = None,
) -> ServiceResult:
    if order_id is None and not order_code:
        return ServiceResult.fail("order.query.missing_id")
    with Database().session() as session:
        q = session.query(Order).options(joinedload(Order.items)).filter(Order.buyer_id == user_id)
        if order_id is not None:
            q = q.filter(Order.id == order_id)
        if order_code:
            q = q.filter(Order.order_code == order_code)
        order = q.first()
        if not order:
            return ServiceResult.fail("order.query.not_found")
        return ServiceResult.success(order=_order_to_dict(order))
