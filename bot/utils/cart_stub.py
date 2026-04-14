"""Cart stub banner utilities for persistent cart visibility (Card 21).

Provides helpers to build the compact cart summary line shown on every
menu screen while the user has items in their shopping cart.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from bot.config import EnvKeys
from bot.database.main import Database
from bot.database.models.main import Brand, Goods, ShoppingCart, Store
from bot.utils.modifiers import calculate_item_price

logger = logging.getLogger(__name__)


def _cart_ttl() -> timedelta:
    return timedelta(minutes=EnvKeys.CART_TTL_MINUTES)


def _as_aware_utc(dt: datetime | None) -> datetime | None:
    """Return a tz-aware UTC datetime, assuming naive inputs are UTC.

    SQLite strips tzinfo on ``DateTime(timezone=True)`` round-trip; Postgres
    preserves it. This keeps comparisons safe on both backends.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def get_cart_stub_data(user_id: int) -> dict | None:
    """Fetch minimal cart summary data for the stub banner.

    Returns dict with keys: brand_name, store_name, total, item_count, brand_id, store_id
    or None if cart is empty / expired.

    Side-effect: auto-clears expired carts (lazy expiry).
    """
    with Database().session() as session:
        cart_items = session.query(ShoppingCart).filter_by(user_id=user_id).all()
        if not cart_items:
            return None

        # Lazy expiry check: if any item has expires_at in the past, clear all.
        # Normalize to tz-aware UTC for backend-agnostic comparison.
        now = datetime.now(timezone.utc)
        first = cart_items[0]
        first_expires = _as_aware_utc(first.expires_at)
        if first_expires and first_expires < now:
            session.query(ShoppingCart).filter_by(user_id=user_id).delete()
            session.commit()
            return None

        # Compute total with modifier prices
        total = Decimal(0)
        for ci in cart_items:
            good = session.query(Goods).filter_by(name=ci.item_name).first()
            if good:
                unit_price = calculate_item_price(
                    good.price, good.modifiers, ci.selected_modifiers
                )
                total += unit_price * ci.quantity

        brand_name = ""
        store_name = ""
        brand_id = first.brand_id
        store_id = first.store_id

        if brand_id:
            brand = session.query(Brand).filter_by(id=brand_id).first()
            if brand:
                brand_name = brand.name
        if store_id:
            store = session.query(Store).filter_by(id=store_id).first()
            if store:
                store_name = store.name

        return {
            'brand_name': brand_name,
            'store_name': store_name,
            'total': total,
            'item_count': len(cart_items),
            'brand_id': brand_id,
            'store_id': store_id,
        }


def build_cart_stub(user_id: int) -> str:
    """Build the cart stub banner string.

    Returns empty string if cart is empty/expired.
    """
    data = get_cart_stub_data(user_id)
    if not data:
        return ""
    return format_cart_stub(data['brand_name'], data['store_name'], data['total'])


def format_cart_stub(brand_name: str, store_name: str, total) -> str:
    """Format the stub line from components."""
    parts = []
    if brand_name:
        parts.append(brand_name)
    if store_name:
        parts.append(store_name)
    parts.append(f"{EnvKeys.PAY_CURRENCY}{total}")
    return "\U0001f6d2 " + " \u00b7 ".join(parts)


def format_flash_stub(item_name: str, quantity: int, item_total) -> str:
    """Format the flash line shown briefly after adding an item."""
    return f"\U0001f6d2 \u2728 Added: {item_name} x{quantity} \u2014 {EnvKeys.PAY_CURRENCY}{item_total}"


async def async_get_cart_stub_data(user_id: int) -> dict | None:
    """Async wrapper around get_cart_stub_data — runs DB I/O in the thread-pool
    so it does not block the asyncio event loop."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, get_cart_stub_data, user_id)


async def async_build_cart_stub(user_id: int) -> str:
    """Async wrapper around build_cart_stub — runs DB I/O in the thread-pool
    so it does not block the asyncio event loop."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, build_cart_stub, user_id)


def inject_cart_stub(text: str, stub: str) -> str:
    """Prepend cart stub banner to menu text with a separator."""
    if not stub:
        return text
    return f"{stub}\n{'─' * 20}\n{text}"


async def flash_cart_added(message, item_name: str, quantity: int,
                           item_total, settle_text: str, settle_markup,
                           user_id: int):
    """Two-step flash: show 'Added' line, then settle to normal stub + menu.

    Args:
        message: The Telegram Message to edit.
        item_name: Name of item just added.
        quantity: Quantity added.
        item_total: Price of the item added.
        settle_text: The final menu text (with stub already injected).
        settle_markup: The final keyboard markup.
        user_id: User's telegram ID.
    """
    from bot.utils.message_utils import safe_edit_text

    flash_line = format_flash_stub(item_name, quantity, item_total)
    try:
        await safe_edit_text(message, flash_line, reply_markup=settle_markup)
        await asyncio.sleep(EnvKeys.CART_FLASH_SECONDS)
        await safe_edit_text(message, settle_text, reply_markup=settle_markup)
    except Exception:
        # If user tapped another button during flash, the settle edit may conflict
        logger.debug("Cart flash settle edit skipped (message already changed)")
