import asyncio
import datetime
from decimal import Decimal
from functools import wraps

from sqlalchemy import func
from sqlalchemy.orm import joinedload

from bot.caching import get_cache_manager
from bot.database.models import (
    BotSettings,
    BoughtGoods,
    Brand,
    BrandStaff,
    Categories,
    Database,
    Goods,
    Operations,
    Order,
    OrderItem,
    Permission,
    ReferralEarnings,
    Role,
    ShoppingCart,
    User,
)


# Wrapper for synchronous functions to asynchronous functions with caching
def async_cached(ttl: int = 300, key_prefix: str = ""):
    def decorator(sync_func):
        @wraps(sync_func)
        async def async_wrapper(*args, **kwargs):
            # Generate the cache key
            cache_key = f"{key_prefix or sync_func.__name__}:{':'.join(str(arg) for arg in args)}"

            cache = get_cache_manager()
            if cache:
                # Trying to get it from the cache
                cached_value = await cache.get(cache_key)
                if cached_value is not None:
                    # LOGIC-23 fix: Handle None sentinel
                    return None if cached_value == "__NONE__" else cached_value

            # Execute synchronous function in executor
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, sync_func, *args)

            # LOGIC-23 fix: Cache None results too (use sentinel to distinguish cache miss)
            if cache:
                cache_value = result if result is not None else "__NONE__"
                await cache.set(cache_key, cache_value, ttl)

            return result

        return async_wrapper

    return decorator


def _day_window(date_str: str) -> tuple[datetime.datetime, datetime.datetime]:
    d = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    start = datetime.datetime.combine(d, datetime.time.min)
    end = start + datetime.timedelta(days=1)
    return start, end


def check_user(telegram_id: int | str) -> dict | None:
    """Return user dict by Telegram ID or None if not found.
    LOGIC-19 fix: Filter out SQLAlchemy internal state from __dict__."""
    with Database().session() as s:
        result = s.query(User).filter(User.telegram_id == telegram_id).one_or_none()
        if not result:
            return None
        return {k: v for k, v in result.__dict__.items() if not k.startswith('_')}


def check_role(telegram_id: int) -> int:
    """Return permission bitmask for user (0 if none).
    LOGIC-29 fix: Single join query instead of two separate queries."""
    with Database().session() as s:
        result = (
            s.query(Role.permissions)
            .join(User, User.role_id == Role.id)
            .filter(User.telegram_id == telegram_id)
            .scalar()
        )
        return result or 0


def get_role_id_by_name(role_name: str) -> int | None:
    """Return role id by name or None."""
    with Database().session() as s:
        return s.query(Role.id).filter(Role.name == role_name).scalar()


def check_role_name_by_id(role_id: int) -> str:
    """Return role name by id (raises if not found)."""
    with Database().session() as s:
        return s.query(Role.name).filter(Role.id == role_id).one()[0]


def select_max_role_id() -> int | None:
    """Return max role id (or None if no roles)."""
    with Database().session() as s:
        return s.query(func.max(Role.id)).scalar()


def select_today_users(date: str) -> int:
    """Return count of users registered on given date (YYYY-MM-DD)."""
    start_of_day, end_of_day = _day_window(date)
    with Database().session() as s:
        return s.query(User).filter(
            User.registration_date >= start_of_day,
            User.registration_date < end_of_day
        ).count()


def get_user_count() -> int:
    """Return total users count."""
    with Database().session() as s:
        return s.query(User).count()


def select_admins() -> int:
    """Return count of users with role_id > 1."""
    with Database().session() as s:
        return s.query(func.count(User.telegram_id)).filter(User.role_id > 1).scalar() or 0


def get_all_users() -> list[tuple[int]]:
    """Return list of all user telegram_ids (as tuples)."""
    with Database().session() as s:
        return s.query(User.telegram_id).all()


def get_bought_item_info(item_id: str) -> dict | None:
    """Return bought item row as dict by row id, or None."""
    with Database().session() as s:
        result = s.query(BoughtGoods).filter(BoughtGoods.id == item_id).first()
        return result.__dict__ if result else None


def get_item_info(item_name: str) -> dict | None:
    """Return item (position) row as dict by name, or None."""
    with Database().session() as s:
        result = s.query(Goods).filter(Goods.name == item_name).first()
        return result.__dict__ if result else None


# Aliases kept for backward compatibility — all do the same thing.
get_goods_info = get_item_info
check_item = get_item_info


def check_category(category_name: str) -> dict | None:
    """Return category as dict by name, or None."""
    with Database().session() as s:
        result = s.query(Categories).filter(Categories.name == category_name).first()
        return result.__dict__ if result else None


def select_item_values_amount(item_name: str) -> int:
    """Return available stock for an item (stock_quantity - reserved_quantity)."""
    with Database().session() as s:
        goods = s.query(Goods).filter(Goods.name == item_name).first()
        if not goods:
            return 0
        return goods.available_quantity


def check_value(item_name: str) -> bool:
    """Return True if item has unlimited stock (prepared items with stock_quantity=0)."""
    with Database().session() as s:
        goods = s.query(Goods).filter_by(name=item_name).first()
        if not goods:
            return False
        # Prepared items with stock_quantity=0 are unlimited (made to order)
        return goods.is_prepared and goods.stock_quantity == 0


def select_user_items(buyer_id: int | str) -> int:
    """Return count of bought items for user."""
    with Database().session() as s:
        return s.query(func.count()).filter(BoughtGoods.buyer_id == buyer_id).scalar() or 0


def select_bought_item(unique_id: int) -> dict | None:
    """Return one bought item by unique_id as dict, or None."""
    with Database().session() as s:
        result = s.query(BoughtGoods).filter(BoughtGoods.unique_id == unique_id).first()
        return result.__dict__ if result else None


def select_count_items() -> int:
    """Return total stock quantity across all goods."""
    with Database().session() as s:
        result = s.query(func.sum(Goods.stock_quantity)).scalar()
        return int(result) if result else 0


def select_count_goods() -> int:
    """Return total count of goods (positions)."""
    with Database().session() as s:
        return s.query(Goods).count()


def select_count_categories() -> int:
    """Return total count of categories."""
    with Database().session() as s:
        return s.query(Categories).count()


def select_count_bought_items() -> int:
    """Return total count of bought items."""
    with Database().session() as s:
        return s.query(BoughtGoods).count()


def select_today_orders(date: str) -> Decimal:
    """Return total revenue for given date (YYYY-MM-DD)."""
    start_of_day, end_of_day = _day_window(date)
    with Database().session() as s:
        res = (
            s.query(func.sum(BoughtGoods.price))
            .filter(
                BoughtGoods.bought_datetime >= start_of_day,
                BoughtGoods.bought_datetime < end_of_day
            )
            .scalar()
        )
        return res or Decimal(0)


def select_all_orders() -> Decimal:
    """Return total revenue for all time (sum of BoughtGoods.price)."""
    with Database().session() as s:
        return s.query(func.sum(BoughtGoods.price)).scalar() or Decimal(0)


def select_today_operations(date: str) -> Decimal:
    """Return total operations value for given date (YYYY-MM-DD)."""
    start_of_day, end_of_day = _day_window(date)
    with Database().session() as s:
        res = (
            s.query(func.sum(Operations.operation_value))
            .filter(
                Operations.operation_time >= start_of_day,
                Operations.operation_time < end_of_day
            )
            .scalar()
        )
        return res or Decimal(0)


def select_all_operations() -> Decimal:
    """Return total operations value for all time."""
    with Database().session() as s:
        return s.query(func.sum(Operations.operation_value)).scalar() or Decimal(0)


def select_user_operations(user_id: int | str) -> list[float]:
    """Return list of operation amounts for user."""
    with Database().session() as s:
        return [row[0] for row in s.query(Operations.operation_value).filter(Operations.user_id == user_id).all()]


def check_user_referrals(user_id: int) -> int:
    """Return count of referrals of the user."""
    with Database().session() as s:
        return s.query(User).filter(User.referral_id == user_id).count()


def get_user_referral(user_id: int) -> int | None:
    """Return referral_id of the user or None."""
    with Database().session() as s:
        result = s.query(User.referral_id).filter(User.telegram_id == user_id).first()
        return result[0] if result else None


def get_referral_earnings_stats(referrer_id: int) -> dict:
    """
    Get statistics on user referral charges.
    """
    with Database().session() as s:
        stats = s.query(
            func.count(ReferralEarnings.id).label('total_earnings_count'),
            func.sum(ReferralEarnings.amount).label('total_amount'),
            func.sum(ReferralEarnings.original_amount).label('total_original_amount'),
            func.count(func.distinct(ReferralEarnings.referral_id)).label('active_referrals_count')
        ).filter(
            ReferralEarnings.referrer_id == referrer_id
        ).first()

        return {
            'total_earnings_count': stats.total_earnings_count or 0,
            'total_amount': stats.total_amount or Decimal(0),
            'total_original_amount': stats.total_original_amount or Decimal(0),
            'active_referrals_count': stats.active_referrals_count or 0
        }


def get_one_referral_earning(earning_id: int) -> dict | None:
    """
    Get one user referral earning info.
    """
    with Database().session() as s:
        result = s.query(ReferralEarnings).filter(ReferralEarnings.id == earning_id).first()
        return result.__dict__ if result else None


def get_reference_bonus_percent(brand_id: int = None) -> Decimal:
    """
    Get reference_bonus_percent from bot_settings.
    Tries brand-specific first, then global fallback.
    Returns Decimal value (default 0).
    """
    with Database().session() as s:
        setting = None
        if brand_id is not None:
            setting = s.query(BotSettings).filter(
                BotSettings.setting_key == 'reference_bonus_percent',
                BotSettings.brand_id == brand_id
            ).first()
        if not setting:
            setting = s.query(BotSettings).filter(
                BotSettings.setting_key == 'reference_bonus_percent',
                BotSettings.brand_id.is_(None)
            ).first()
        if setting and setting.setting_value:
            try:
                return Decimal(str(setting.setting_value))
            except (ValueError, TypeError):
                return Decimal(0)
        return Decimal(0)


def get_bot_setting(setting_key: str, default: str = None, value_type: type = str,
                    brand_id: int = None) -> any:
    """
    Get a setting value from BotSettings.
    If brand_id is given, tries brand-specific first, then falls back to global (brand_id=NULL).

    Args:
        setting_key: The setting key to retrieve
        default: Default value if setting not found or invalid
        value_type: Type to convert the value to (str, int, float, Decimal)
        brand_id: Optional brand ID for brand-specific settings

    Returns:
        Setting value converted to specified type, or default value
    """
    with Database().session() as s:
        setting = None
        # Try brand-specific first
        if brand_id is not None:
            setting = s.query(BotSettings).filter(
                BotSettings.setting_key == setting_key,
                BotSettings.brand_id == brand_id
            ).first()
        # Fall back to global
        if not setting:
            setting = s.query(BotSettings).filter(
                BotSettings.setting_key == setting_key,
                BotSettings.brand_id.is_(None)
            ).first()
        if setting and setting.setting_value:
            try:
                if value_type == int:
                    return int(setting.setting_value)
                if value_type == float:
                    return float(setting.setting_value)
                if value_type == Decimal:
                    return Decimal(str(setting.setting_value))
                return str(setting.setting_value)
            except (ValueError, TypeError):
                pass  # Fall through to return default

        # Convert default to the requested type if needed
        if default is not None:
            try:
                if value_type == int and not isinstance(default, int):
                    return int(default)
                if value_type == float and not isinstance(default, float):
                    return float(default)
                if value_type == Decimal and not isinstance(default, Decimal):
                    return Decimal(str(default))
            except (ValueError, TypeError):
                pass

        return default


async def get_cart_items(user_id: int) -> list:
    """
    Get all items in user's cart with product details

    Args:
        user_id: User's telegram ID

    Returns:
        List of cart items with product info (includes selected_modifiers and modifier-adjusted price)
    """
    from bot.utils.modifiers import calculate_item_price

    with Database().session() as session:
        cart_items = session.query(ShoppingCart, Goods).join(
            Goods, ShoppingCart.item_name == Goods.name
        ).filter(
            ShoppingCart.user_id == user_id
        ).all()

        result = []
        for cart_item, good in cart_items:
            # Calculate price with modifier adjustments (Card 8)
            unit_price = calculate_item_price(
                good.price, good.modifiers, cart_item.selected_modifiers
            )
            result.append({
                'cart_id': cart_item.id,
                'item_name': cart_item.item_name,
                'quantity': cart_item.quantity,
                'price': unit_price,
                'total': unit_price * cart_item.quantity,
                'selected_modifiers': cart_item.selected_modifiers,
                'modifiers_schema': good.modifiers,
            })
        return result


async def query_user_orders(user_id: int, status: str = None, limit: int = 10, offset: int = 0):
    """
    Query user's orders with optional status filter

    Args:
        user_id: User's telegram ID
        status: Order status filter (pending, completed, cancelled) or None for all
        limit: Number of orders to return
        offset: Offset for pagination

    Returns:
        List of Order objects with items
    """
    with Database().session() as session:
        query = session.query(Order).options(
            joinedload(Order.items)
        ).filter(Order.buyer_id == user_id)

        if status:
            query = query.filter(Order.order_status == status)

        query = query.order_by(Order.created_at.desc())

        orders = query.limit(limit).offset(offset).all()

        # Return order data as dicts to avoid session issues
        result = []
        for order in orders:
            items_data = [{
                'item_name': item.item_name,
                'price': float(item.price),
                'quantity': item.quantity
            } for item in order.items]

            result.append({
                'id': order.id,
                'order_code': order.order_code,
                'total_price': float(order.total_price) if order.total_price else 0,
                'bonus_applied': float(order.bonus_applied) if order.bonus_applied else 0,
                'payment_method': order.payment_method,
                'delivery_address': order.delivery_address,
                'phone_number': order.phone_number,
                'delivery_note': order.delivery_note,
                'bitcoin_address': order.bitcoin_address,
                'order_status': order.order_status,
                'created_at': order.created_at,
                'completed_at': order.completed_at,
                'delivery_time': order.delivery_time,
                'items': items_data
            })

        return result


async def count_user_orders(user_id: int, status: str = None) -> int:
    """
    Count user's orders

    Args:
        user_id: User's telegram ID
        status: Order status filter or None for all

    Returns:
        Number of orders
    """
    with Database().session() as session:
        query = session.query(Order).filter(Order.buyer_id == user_id)

        if status:
            query = query.filter(Order.order_status == status)

        return query.count()


async def calculate_cart_total(user_id: int) -> int:
    """Calculate total price of all items in cart"""
    items = await get_cart_items(user_id)
    return sum(item['total'] for item in items)


@async_cached(ttl=60, key_prefix="user")
def check_user_cached(telegram_id: int | str):
    """Cached version of check_user"""
    return check_user(telegram_id)


@async_cached(ttl=300, key_prefix="role")
def check_role_cached(telegram_id: int):
    """Cached Role Verification"""
    return check_role(telegram_id)


@async_cached(ttl=1800, key_prefix="category")
def check_category_cached(category_name: str):
    """Cached Category Check"""
    return check_category(category_name)


@async_cached(ttl=1800, key_prefix="item")
def check_item_cached(item_name: str):
    """Cached product verification"""
    return check_item(item_name)


@async_cached(ttl=900, key_prefix="item_info")
def get_item_info_cached(item_name: str):
    """Cached product information"""
    return get_item_info(item_name)


@async_cached(ttl=300, key_prefix="item_stock")
def select_item_values_amount_cached(item_name: str):
    """Cached available quantity of goods (stock - reserved)"""
    return select_item_values_amount(item_name)


@async_cached(ttl=60, key_prefix="user_count")
def get_user_count_cached():
    """Cached number of users"""
    return get_user_count()


@async_cached(ttl=60, key_prefix="admin_count")
def select_admins_cached():
    """Cached number of admins"""
    return select_admins()


# ── Brand / multi-store queries ───────────────────────────────────────

def _brand_to_dict(b) -> dict:
    """Convert a Brand ORM instance to a plain dict."""
    return {
        'id': b.id, 'name': b.name, 'slug': b.slug,
        'description': b.description, 'logo_file_id': b.logo_file_id,
        'is_active': b.is_active, 'promptpay_id': b.promptpay_id,
        'promptpay_name': b.promptpay_name, 'timezone': b.timezone,
    }


def get_all_brands(active_only: bool = True) -> list[dict]:
    """Return list of brands as dicts."""
    with Database().session() as s:
        q = s.query(Brand)
        if active_only:
            q = q.filter(Brand.is_active.is_(True))
        brands = q.order_by(Brand.name).all()
        return [_brand_to_dict(b) for b in brands]


def get_brand(brand_id: int) -> dict | None:
    """Return brand by ID as dict, or None."""
    with Database().session() as s:
        b = s.query(Brand).filter_by(id=brand_id).first()
        if not b:
            return None
        return _brand_to_dict(b)


def get_brand_by_slug(slug: str) -> dict | None:
    """Return brand by slug as dict, or None."""
    with Database().session() as s:
        b = s.query(Brand).filter_by(slug=slug).first()
        if not b:
            return None
        return _brand_to_dict(b)


def get_stores_for_brand(brand_id: int, active_only: bool = True) -> list[dict]:
    """Return list of stores/branches for a brand."""
    with Database().session() as s:
        from bot.database.models.main import Store
        q = s.query(Store).filter(Store.brand_id == brand_id)
        if active_only:
            q = q.filter(Store.is_active.is_(True))
        stores = q.order_by(Store.name).all()
        return [
            {
                'id': st.id, 'name': st.name, 'address': st.address,
                'latitude': st.latitude, 'longitude': st.longitude,
                'phone': st.phone, 'is_active': st.is_active,
                'is_default': st.is_default,
                'kitchen_group_id': st.kitchen_group_id,
                'rider_group_id': st.rider_group_id,
            }
            for st in stores
        ]


def can_manage_brand(user_id: int, brand_id: int) -> bool:
    """Check if a user can manage a brand (SUPERADMIN or brand staff with owner/admin role)."""
    with Database().session() as s:
        # Check SUPERADMIN
        user = s.query(User).filter_by(telegram_id=user_id).first()
        if user:
            role = s.query(Role).filter_by(id=user.role_id).first()
            if role and role.has_permission(Permission.SUPER):
                return True

        # Check BrandStaff
        staff = s.query(BrandStaff).filter(
            BrandStaff.user_id == user_id,
            BrandStaff.brand_id == brand_id,
            BrandStaff.role.in_(['owner', 'admin'])
        ).first()
        return staff is not None


def get_user_brands(user_id: int) -> list[dict]:
    """Return brands that a user has staff access to."""
    with Database().session() as s:
        # Check if superadmin
        user = s.query(User).filter_by(telegram_id=user_id).first()
        if user:
            role = s.query(Role).filter_by(id=user.role_id).first()
            if role and role.has_permission(Permission.SUPER):
                return get_all_brands(active_only=False)

        # Get brands via staff assignment
        staff_entries = s.query(BrandStaff).filter_by(user_id=user_id).all()
        brand_ids = list(set(entry.brand_id for entry in staff_entries))
        if not brand_ids:
            return []

        brands = s.query(Brand).filter(Brand.id.in_(brand_ids)).order_by(Brand.name).all()
        return [_brand_to_dict(b) for b in brands]


def is_superadmin(user_id: int) -> bool:
    """Check if user has SUPERADMIN (SUPER permission)."""
    with Database().session() as s:
        user = s.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            return False
        role = s.query(Role).filter_by(id=user.role_id).first()
        if not role:
            return False
        return role.has_permission(Permission.SUPER)


# Cache invalidation functions
async def invalidate_user_cache(user_id: int):
    """Invalidate user cache"""
    cache = get_cache_manager()
    if cache:
        await cache.delete(f"user:{user_id}")
        await cache.delete(f"role:{user_id}")
        await cache.invalidate_pattern(f"user_stats:{user_id}:*")
        await cache.invalidate_pattern(f"user_items:{user_id}:*")


async def invalidate_item_cache(item_name: str):
    """Invalidate product cache"""
    cache = get_cache_manager()
    if cache:
        await cache.delete(f"item:{item_name}")
        await cache.delete(f"item_info:{item_name}")
        await cache.delete(f"item_stock:{item_name}")  # Updated from item_values
        # Also invalidate categories, as the number of items may have changed
        await cache.invalidate_pattern("category:*")


async def invalidate_category_cache(category_name: str):
    """Invalidate category cache"""
    cache = get_cache_manager()
    if cache:
        await cache.delete(f"category:{category_name}")
        await cache.invalidate_pattern(f"category_items:{category_name}:*")
