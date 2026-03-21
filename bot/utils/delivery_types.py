"""Delivery type helpers (Card 4 - Photo Proof of Delivery)."""


def needs_delivery_photo(order) -> bool:
    """Dead drop orders require photo before marking delivered."""
    if order.delivery_type == "dead_drop":
        return not order.delivery_photo
    return False  # door and pickup don't require photo
