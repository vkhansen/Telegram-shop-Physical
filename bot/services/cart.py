"""Cart application service (CARD-32) — channel-agnostic cart ops.

Wraps existing database methods. Adapters (Telegram, web, LINE) call here
instead of importing methods directly for new code.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from bot.database.methods.create import add_to_cart as _add_to_cart
from bot.database.methods.delete import clear_cart as _clear_cart
from bot.database.methods.delete import remove_from_cart as _remove_from_cart
from bot.database.methods.read import calculate_cart_total as _calculate_cart_total
from bot.database.methods.read import get_cart_items as _get_cart_items
from bot.services.dto import ServiceResult


async def list_items(user_id: int) -> ServiceResult:
    """Return cart line items for *user_id*."""
    items = await _get_cart_items(user_id)
    total = await _calculate_cart_total(user_id)
    return ServiceResult.success(
        items=items,
        item_count=len(items),
        total=total,
        total_decimal=Decimal(str(total)),
        empty=len(items) == 0,
    )


async def get_total(user_id: int) -> ServiceResult:
    total = await _calculate_cart_total(user_id)
    return ServiceResult.success(total=total, total_decimal=Decimal(str(total)))


async def add_item(
    user_id: int,
    item_name: str,
    quantity: int = 1,
    *,
    selected_modifiers: dict | None = None,
    brand_id: int | None = None,
    store_id: int | None = None,
) -> ServiceResult:
    ok, message = await _add_to_cart(
        user_id,
        item_name,
        quantity,
        selected_modifiers=selected_modifiers,
        brand_id=brand_id,
        store_id=store_id,
    )
    if not ok:
        return ServiceResult.fail("cart.add_failed", error_detail=message, message=message)
    return ServiceResult.success(message=message)


async def remove_item(cart_id: int, user_id: int) -> ServiceResult:
    ok, message = await _remove_from_cart(cart_id, user_id)
    if not ok:
        return ServiceResult.fail("cart.remove_failed", error_detail=message, message=message)
    return ServiceResult.success(message=message)


async def clear(user_id: int) -> ServiceResult:
    ok, message = await _clear_cart(user_id)
    if not ok:
        return ServiceResult.fail("cart.clear_failed", error_detail=message, message=message)
    return ServiceResult.success(message=message)


def remove_items_by_name(user_id: int, item_names: list[str]) -> ServiceResult:
    """Drop named lines (e.g. store-switch unavailable items). Sync DB helper."""
    from bot.database.methods.delete import remove_items_from_cart as _remove_names

    if not item_names:
        return ServiceResult.success(removed=0)
    _remove_names(user_id, item_names)
    return ServiceResult.success(removed=len(item_names))


def cart_items_as_plain(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Ensure cart lines are plain dicts (JSON-serializable)."""
    out = []
    for it in items:
        out.append(
            {
                "cart_id": it.get("cart_id"),
                "item_name": it.get("item_name"),
                "quantity": it.get("quantity"),
                "price": str(it.get("price")),
                "total": str(it.get("total")),
                "selected_modifiers": it.get("selected_modifiers"),
                "brand_id": it.get("brand_id"),
                "store_id": it.get("store_id"),
            }
        )
    return out
