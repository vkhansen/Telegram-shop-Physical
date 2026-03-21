"""
Shared order creation helpers to eliminate duplication across payment flows.

Extracts common patterns from order_handler.py:
- Order object creation from CustomerInfo
- OrderItem creation from cart items
- Item summary formatting
- Google Maps link generation
"""
from decimal import Decimal

from bot.config.env import EnvKeys
from bot.database.models.main import Order, OrderItem


def build_google_maps_link(latitude: float | None, longitude: float | None) -> str | None:
    """Generate Google Maps link from coordinates, or None if no GPS data."""
    if latitude is not None and longitude is not None:
        return f"https://www.google.com/maps?q={latitude},{longitude}"
    return None


def create_order_from_customer(
    session,
    user_id: int,
    customer_info,
    payment_method: str,
    total_amount: Decimal,
    bonus_applied: Decimal = Decimal("0"),
    bitcoin_address: str | None = None,
) -> Order:
    """
    Create an Order from CustomerInfo and cart data.

    Returns the Order (already added to session + flushed to get ID).
    """
    from bot.utils import generate_unique_order_code

    order = Order(
        buyer_id=user_id,
        total_price=Decimal(str(total_amount)),
        bonus_applied=bonus_applied,
        payment_method=payment_method,
        delivery_address=customer_info.delivery_address or "",
        phone_number=customer_info.phone_number or "",
        delivery_note=customer_info.delivery_note or "",
        bitcoin_address=bitcoin_address,
        order_status="pending",
        latitude=customer_info.latitude,
        longitude=customer_info.longitude,
        google_maps_link=build_google_maps_link(customer_info.latitude, customer_info.longitude),
    )
    session.add(order)
    session.flush()

    order.order_code = generate_unique_order_code(session)
    return order


def create_order_items(session, order_id: int, cart_items: list) -> tuple[list[str], list[dict]]:
    """
    Create OrderItem records from cart items.

    Returns:
        (items_summary, items_to_reserve)
    """
    items_summary = []
    items_to_reserve = []

    for cart_item in cart_items:
        item_name = cart_item['item_name']
        quantity = cart_item['quantity']
        price = cart_item['price']

        order_item = OrderItem(
            order_id=order_id,
            item_name=item_name,
            price=Decimal(str(price)),
            quantity=quantity,
        )
        session.add(order_item)

        items_summary.append(f"{item_name} x{quantity} = {cart_item['total']} {EnvKeys.PAY_CURRENCY}")
        items_to_reserve.append({'item_name': item_name, 'quantity': quantity})

    return items_summary, items_to_reserve


def format_items_summary(cart_items: list) -> list[str]:
    """Format cart items as display strings."""
    return [
        f"{item['item_name']} x{item['quantity']} = {item['total']} {EnvKeys.PAY_CURRENCY}"
        for item in cart_items
    ]
