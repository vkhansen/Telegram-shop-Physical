from bot.database import Database
from bot.database.models.main import Order, OrderItem, Goods, Categories
from sqlalchemy import func, case
from decimal import Decimal
import csv
import io
from datetime import datetime, timedelta, timezone


def _apply_date_filter(query, from_date=None, to_date=None):
    """Apply date range filter to a query on Order.created_at."""
    if from_date is not None:
        query = query.filter(Order.created_at >= from_date)
    if to_date is not None:
        query = query.filter(Order.created_at <= to_date)
    return query


def generate_sales_csv(from_date=None, to_date=None) -> str:
    """Generate a CSV report of completed (delivered) orders in a date range.

    Args:
        from_date: Start datetime (inclusive). None means no lower bound.
        to_date: End datetime (inclusive). None means no upper bound.

    Returns:
        CSV string with columns:
        Order Code, Date, Items, Total, Payment Method, Delivery Fee,
        Coupon Discount, Bonus Applied
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Order Code", "Date", "Items", "Total", "Payment Method",
        "Delivery Fee", "Coupon Discount", "Bonus Applied",
    ])

    with Database().session() as session:
        query = session.query(Order).filter(Order.status == "delivered")
        query = _apply_date_filter(query, from_date, to_date)
        query = query.order_by(Order.created_at.asc())

        for order in query.all():
            items = session.query(OrderItem).filter_by(order_id=order.id).all()
            items_desc = "; ".join(
                f"{item.item_name} x{item.quantity}" for item in items
            )
            writer.writerow([
                order.order_code,
                order.created_at.strftime("%Y-%m-%d %H:%M"),
                items_desc,
                str(order.total_price),
                order.payment_method,
                str(order.delivery_fee or 0),
                str(order.coupon_discount or 0),
                str(order.bonus_applied or 0),
            ])

    return output.getvalue()


def generate_revenue_by_product_csv(from_date=None, to_date=None) -> str:
    """Generate a CSV report of revenue grouped by product.

    Joins OrderItem with Order (delivered only), groups by item_name.

    Args:
        from_date: Start datetime (inclusive). None means no lower bound.
        to_date: End datetime (inclusive). None means no upper bound.

    Returns:
        CSV string with columns: Product, Category, Units Sold, Revenue, Avg Price
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Product", "Category", "Units Sold", "Revenue", "Avg Price"])

    with Database().session() as session:
        query = (
            session.query(
                OrderItem.item_name,
                func.sum(OrderItem.quantity).label("units_sold"),
                func.sum(OrderItem.price * OrderItem.quantity).label("revenue"),
                func.avg(OrderItem.price).label("avg_price"),
            )
            .join(Order, Order.id == OrderItem.order_id)
            .filter(Order.status == "delivered")
        )
        query = _apply_date_filter(query, from_date, to_date)
        query = query.group_by(OrderItem.item_name)
        query = query.order_by(func.sum(OrderItem.price * OrderItem.quantity).desc())

        for row in query.all():
            # Attempt to resolve category from Goods table
            category_name = ""
            good = session.query(Goods).filter_by(name=row.item_name).first()
            if good and good.category_id:
                cat = session.query(Categories).filter_by(id=good.category_id).first()
                if cat:
                    category_name = cat.name

            avg_price = Decimal(str(row.avg_price)).quantize(Decimal("0.01")) if row.avg_price else Decimal(0)
            writer.writerow([
                row.item_name,
                category_name,
                row.units_sold,
                str(row.revenue),
                str(avg_price),
            ])

    return output.getvalue()


def generate_payment_reconciliation_csv(from_date=None, to_date=None) -> str:
    """Generate a CSV report of revenue grouped by payment method.

    Args:
        from_date: Start datetime (inclusive). None means no lower bound.
        to_date: End datetime (inclusive). None means no upper bound.

    Returns:
        CSV string with columns:
        Payment Method, Order Count, Total Revenue, Avg Order Value
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Payment Method", "Order Count", "Total Revenue", "Avg Order Value"])

    with Database().session() as session:
        query = (
            session.query(
                Order.payment_method,
                func.count(Order.id).label("order_count"),
                func.sum(Order.total_price).label("total_revenue"),
                func.avg(Order.total_price).label("avg_order_value"),
            )
            .filter(Order.status == "delivered")
        )
        query = _apply_date_filter(query, from_date, to_date)
        query = query.group_by(Order.payment_method)
        query = query.order_by(func.sum(Order.total_price).desc())

        for row in query.all():
            avg_val = Decimal(str(row.avg_order_value)).quantize(Decimal("0.01")) if row.avg_order_value else Decimal(0)
            writer.writerow([
                row.payment_method,
                row.order_count,
                str(row.total_revenue),
                str(avg_val),
            ])

    return output.getvalue()


def get_revenue_summary(from_date=None, to_date=None) -> dict:
    """Return a summary dict of revenue metrics for delivered orders.

    Args:
        from_date: Start datetime (inclusive). None means no lower bound.
        to_date: End datetime (inclusive). None means no upper bound.

    Returns:
        dict with keys:
            total_revenue (Decimal): Sum of all order totals.
            total_orders (int): Number of delivered orders.
            avg_order_value (Decimal): Average order total.
            revenue_by_payment (dict): {payment_method: Decimal revenue}.
            top_products (list): Top 5 products by revenue, each a dict
                with keys: name, units_sold, revenue.
    """
    with Database().session() as session:
        # --- Aggregate totals ---
        totals_query = (
            session.query(
                func.count(Order.id).label("total_orders"),
                func.coalesce(func.sum(Order.total_price), 0).label("total_revenue"),
                func.avg(Order.total_price).label("avg_order_value"),
            )
            .filter(Order.status == "delivered")
        )
        totals_query = _apply_date_filter(totals_query, from_date, to_date)
        totals = totals_query.one()

        total_orders = totals.total_orders or 0
        total_revenue = Decimal(str(totals.total_revenue)) if totals.total_revenue else Decimal(0)
        avg_order_value = (
            Decimal(str(totals.avg_order_value)).quantize(Decimal("0.01"))
            if totals.avg_order_value
            else Decimal(0)
        )

        # --- Revenue by payment method ---
        payment_query = (
            session.query(
                Order.payment_method,
                func.sum(Order.total_price).label("revenue"),
            )
            .filter(Order.status == "delivered")
        )
        payment_query = _apply_date_filter(payment_query, from_date, to_date)
        payment_query = payment_query.group_by(Order.payment_method)

        revenue_by_payment = {}
        for row in payment_query.all():
            revenue_by_payment[row.payment_method] = Decimal(str(row.revenue)) if row.revenue else Decimal(0)

        # --- Top 5 products by revenue ---
        products_query = (
            session.query(
                OrderItem.item_name,
                func.sum(OrderItem.quantity).label("units_sold"),
                func.sum(OrderItem.price * OrderItem.quantity).label("revenue"),
            )
            .join(Order, Order.id == OrderItem.order_id)
            .filter(Order.status == "delivered")
        )
        products_query = _apply_date_filter(products_query, from_date, to_date)
        products_query = (
            products_query
            .group_by(OrderItem.item_name)
            .order_by(func.sum(OrderItem.price * OrderItem.quantity).desc())
            .limit(5)
        )

        top_products = []
        for row in products_query.all():
            top_products.append({
                "name": row.item_name,
                "units_sold": row.units_sold,
                "revenue": Decimal(str(row.revenue)) if row.revenue else Decimal(0),
            })

    return {
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "avg_order_value": avg_order_value,
        "revenue_by_payment": revenue_by_payment,
        "top_products": top_products,
    }
