"""Delivery type helpers (Card 4 - Photo Proof of Delivery)."""

from bot.utils.constants import DELIVERY_DEAD_DROP


def needs_delivery_photo(order) -> bool:
    """Dead drop orders require photo before marking delivered."""
    if not order:
        return False
    if order.delivery_type == DELIVERY_DEAD_DROP:
        return not order.delivery_photo
    return False  # door and pickup don't require photo
