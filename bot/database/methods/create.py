from datetime import datetime, timedelta, timezone

from sqlalchemy import exists
from sqlalchemy.exc import IntegrityError

from bot.config import EnvKeys
from bot.database import Database
from bot.database.models import Brand, Categories, Goods, ShoppingCart, User
from bot.logger_mesh import logger


def create_user(telegram_id: int, registration_date: datetime, referral_id: int | None,
                role: int = 1, locale: str = None) -> None:
    """Create user if missing; commit."""
    with Database().session() as s:
        if s.query(exists().where(User.telegram_id == telegram_id)).scalar():
            return
        s.add(
            User(
                telegram_id=telegram_id,
                role_id=role,
                registration_date=registration_date,
                referral_id=referral_id,
                locale=locale,
            )
        )


def create_item(item_name: str, item_description: str, item_price: int, category_name: str,
                image_file_id: str = None, media: list = None,
                prep_time_minutes: int = None, allergens: str = None,
                daily_limit: int = None, available_from: str = None,
                available_until: str = None, calories: int = None,
                brand_id: int = None, item_type: str = 'prepared') -> None:
    """Insert item (goods); commit.

    item_type: 'product' for packaged/shelf-stable goods (e.g., bottled water),
               'prepared' for made-to-order/perishable items (e.g., pad thai).
    """
    with Database().session() as s:
        if s.query(exists().where(Goods.name == item_name)).scalar():
            return
        s.add(
            Goods(
                name=item_name,
                description=item_description,
                price=item_price,
                category_name=category_name,
                image_file_id=image_file_id,
                media=media,
                prep_time_minutes=prep_time_minutes,
                allergens=allergens,
                daily_limit=daily_limit,
                available_from=available_from,
                available_until=available_until,
                calories=calories,
                brand_id=brand_id,
                item_type=item_type,
            )
        )


def create_category(category_name: str, brand_id: int = None) -> None:
    """Insert category; commit."""
    with Database().session() as s:
        if s.query(exists().where(Categories.name == category_name)).scalar():
            return
        s.add(Categories(name=category_name, brand_id=brand_id))


async def add_to_cart(user_id: int, item_name: str, quantity: int = 1,
                      selected_modifiers: dict = None,
                      brand_id: int = None, store_id: int = None) -> tuple[bool, str]:
    """
    Add item to cart or update quantity if already exists

    Args:
        user_id: User's telegram ID
        item_name: Name of the item to add
        quantity: Quantity to add (default 1)
        selected_modifiers: Selected modifier choices (Card 8)
        brand_id: Brand ID for multi-brand support
        store_id: Store/branch ID for multi-store support

    Returns:
        Tuple of (success, message)
    """
    # Import here to avoid circular import
    from bot.database.methods.read import check_value, select_item_values_amount_cached

    try:
        with Database().session() as session:
            # LOGIC-01 fix: Lock item row to prevent overselling race condition
            good = session.query(Goods).filter_by(name=item_name).with_for_update().first()
            if not good:
                return False, "Item not found"

            # Check item is active and available
            if not good.is_active:
                return False, "This item is currently unavailable"
            if good.sold_out_today:
                return False, "This item is sold out for today"
            if good.daily_limit is not None:
                if good.daily_sold_count >= good.daily_limit:
                    return False, "Daily limit reached for this item"
            # Time window check
            if good.available_from and good.available_until:
                from bot.config.timezone import get_current_time
                try:
                    now_str = get_current_time().strftime("%H:%M")
                    if now_str < good.available_from or now_str > good.available_until:
                        return False, f"This item is only available {good.available_from}-{good.available_until}"
                except Exception:
                    pass  # If timezone fails, allow the order

            # Check stock availability using locked row data
            is_unlimited = check_value(item_name)
            if not is_unlimited:
                available_stock = good.stock_quantity - good.reserved_quantity
                existing_cart = session.query(ShoppingCart).filter_by(
                    user_id=user_id, item_name=item_name
                ).with_for_update().first()

                current_cart_qty = existing_cart.quantity if existing_cart else 0
                total_requested = current_cart_qty + quantity

                if available_stock < total_requested:
                    return False, f"Only {available_stock} items available in stock"

            # Add or update cart item (scoped by brand)
            cart_filter = {'user_id': user_id, 'item_name': item_name}
            if brand_id is not None:
                cart_filter['brand_id'] = brand_id

            cart_item = session.query(ShoppingCart).filter_by(**cart_filter).first()

            # Card 21: reset TTL on every add-to-cart
            new_expires_at = datetime.now(timezone.utc) + timedelta(
                minutes=EnvKeys.CART_TTL_MINUTES
            )

            if cart_item:
                cart_item.quantity += quantity
                # Update modifiers if provided (replace previous selection)
                if selected_modifiers is not None:
                    cart_item.selected_modifiers = selected_modifiers
            else:
                cart_item = ShoppingCart(
                    user_id=user_id,
                    item_name=item_name,
                    quantity=quantity,
                    selected_modifiers=selected_modifiers,
                    brand_id=brand_id,
                    store_id=store_id,
                    expires_at=new_expires_at,
                )
                session.add(cart_item)

            session.flush()

            # Card 21: bulk-reset expiry across the whole user's cart so one
            # TTL governs the entire cart, not per-row.
            session.query(ShoppingCart).filter_by(user_id=user_id).update(
                {ShoppingCart.expires_at: new_expires_at},
                synchronize_session=False,
            )

            session.commit()
            return True, "Item added to cart"

    except Exception as e:
        logger.error(f"Error adding to cart: {e}")
        return False, "An error occurred while adding the item to cart"


def save_cart_snapshot(user_id: int, brand_id: int, store_id: int | None,
                       items_json: list, original_total) -> bool:
    """Card 21: Persist current cart as a SavedCart row for brand-switch restore.

    items_json format: [{"name": str, "quantity": int, "modifiers": dict|None,
                         "unit_price": str, "schema_version": 1}]
    """
    try:
        from bot.database.models.main import SavedCart
        with Database().session() as s:
            snapshot = SavedCart(
                user_id=user_id,
                brand_id=brand_id,
                store_id=store_id,
                items_json={"schema_version": 1, "items": items_json},
                original_total=original_total,
            )
            s.add(snapshot)
            s.commit()
        return True
    except Exception as e:
        logger.error(f"save_cart_snapshot error: {e}")
        return False


def create_brand(name: str, slug: str, description: str = None,
                 logo_file_id: str = None, promptpay_id: str = None,
                 promptpay_name: str = None, timezone: str = None) -> int | None:
    """Create a new brand. Returns brand ID or None if name/slug already exists.
    LOGIC-02 fix: Catch IntegrityError for concurrent insert race condition."""
    try:
        with Database().session() as s:
            if s.query(exists().where(Brand.slug == slug)).scalar():
                return None
            if s.query(exists().where(Brand.name == name)).scalar():
                return None
            brand = Brand(
                name=name,
                slug=slug,
                description=description,
                logo_file_id=logo_file_id,
                promptpay_id=promptpay_id,
                promptpay_name=promptpay_name,
                timezone=timezone,
            )
            s.add(brand)
            s.flush()
            brand_id = brand.id
            s.commit()
            return brand_id
    except IntegrityError:
        logger.warning(f"Brand creation race condition: name={name}, slug={slug}")
        return None
