from decimal import Decimal
from datetime import datetime
from bot.database import Database
from bot.database.models.main import Order, OrderItem
from bot.config import EnvKeys
from bot.i18n import localize


def generate_invoice_text(order_id: int) -> str | None:
    """Generate a text-based invoice/receipt for an order.
    Returns formatted text string or None if order not found.
    """
    with Database().session() as session:
        order = session.query(Order).filter_by(id=order_id).first()
        if not order:
            return None

        items = session.query(OrderItem).filter_by(order_id=order.id).all()

        currency = EnvKeys.PAY_CURRENCY

        lines = []
        lines.append("=" * 32)
        lines.append("        RECEIPT / INVOICE")
        lines.append("=" * 32)
        lines.append("")
        lines.append(f"Order: #{order.order_code}")
        lines.append(f"Date: {order.created_at.strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"Payment: {order.payment_method.upper()}")
        if order.store_id:
            from bot.database.models.main import Store
            store = session.query(Store).filter_by(id=order.store_id).first()
            if store:
                lines.append(f"Store: {store.name}")
        lines.append("")
        lines.append("-" * 32)
        lines.append("Items:")
        lines.append("-" * 32)

        subtotal = Decimal(0)
        for item in items:
            item_total = item.price * item.quantity
            subtotal += item_total
            lines.append(f"  {item.item_name}")
            lines.append(f"    {item.quantity} x {item.price} = {item_total} {currency}")

        lines.append("-" * 32)
        lines.append(f"Subtotal: {subtotal} {currency}")

        if order.delivery_fee and order.delivery_fee > 0:
            lines.append(f"Delivery Fee: {order.delivery_fee} {currency}")

        if order.coupon_discount and order.coupon_discount > 0:
            lines.append(f"Coupon ({order.coupon_code}): -{order.coupon_discount} {currency}")

        if order.bonus_applied and order.bonus_applied > 0:
            lines.append(f"Bonus Applied: -{order.bonus_applied} {currency}")

        lines.append(f"TOTAL: {order.total_price} {currency}")
        lines.append("")
        lines.append("-" * 32)
        lines.append(f"Delivery: {order.delivery_address}")
        lines.append(f"Phone: {order.phone_number}")
        if order.delivery_type != 'door':
            lines.append(f"Type: {order.delivery_type}")
        lines.append("")
        lines.append("=" * 32)
        lines.append("     Thank you for your order!")
        lines.append("=" * 32)

        return "\n".join(lines)
