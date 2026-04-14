from bot.database.methods import invalidate_item_cache, invalidate_category_cache
from bot.database.methods.cache_utils import safe_create_task
from bot.database.models import Database, Goods, Categories, ShoppingCart
from bot.logger_mesh import logger


def delete_item(item_name: str) -> None:
    """Delete a product and all of its stock entries."""
    with Database().session() as s:
        s.query(Goods).filter(Goods.name == item_name).delete(synchronize_session=False)

    # Invalidate the cache
    safe_create_task(invalidate_item_cache(item_name))


def delete_category(category_name: str) -> None:
    """Delete a category and its products.
    LOGIC-13 fix: InventoryLog FK changed to SET NULL so audit trail is preserved."""
    with Database().session() as s:
        s.query(Categories).filter(Categories.name == category_name).delete(synchronize_session=False)

    # Invalidate the cache
    safe_create_task(invalidate_category_cache(category_name))


async def remove_from_cart(cart_id: int, user_id: int) -> tuple[bool, str]:
    """
    Remove item from cart

    Args:
        cart_id: Cart item ID
        user_id: User's telegram ID (for verification)

    Returns:
        Tuple of (success, message)
    """
    try:
        with Database().session() as session:
            cart_item = session.query(ShoppingCart).filter_by(
                id=cart_id, user_id=user_id
            ).first()

            if not cart_item:
                return False, "Item not found in cart"

            session.delete(cart_item)
            session.commit()
            return True, "Item removed from cart"

    except Exception as e:
        logger.error(f"Error removing from cart: {e}")
        return False, "An error occurred while removing the item from cart"


async def clear_cart(user_id: int) -> tuple[bool, str]:
    """
    Clear all items from user's cart

    Args:
        user_id: User's telegram ID

    Returns:
        Tuple of (success, message)
    """
    try:
        with Database().session() as session:
            session.query(ShoppingCart).filter_by(user_id=user_id).delete()
            session.commit()
            return True, "Cart cleared"

    except Exception as e:
        logger.error(f"Error clearing cart: {e}")
        return False, "An error occurred while clearing the cart"


def remove_items_from_cart(user_id: int, item_names: list[str]) -> None:
    """Card 21: Delete specific items from a user's cart (unavailable after store switch)."""
    if not item_names:
        return
    try:
        with Database().session() as session:
            session.query(ShoppingCart).filter(
                ShoppingCart.user_id == user_id,
                ShoppingCart.item_name.in_(item_names),
            ).delete(synchronize_session=False)
            session.commit()
    except Exception as e:
        logger.error(f"remove_items_from_cart error: {e}")
