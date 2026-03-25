"""
Coupon validation and application utilities.

Provides functions for:
- Validating coupon codes against all business rules
- Calculating discount amounts (percent or fixed)
- Recording coupon usage after order placement
"""
import logging
from decimal import Decimal
from datetime import datetime, timezone

from bot.database import Database
from bot.database.models.main import Coupon, CouponUsage


def validate_coupon(code: str, user_id: int, order_total: Decimal) -> tuple[bool, str, Coupon | None]:
    """
    Validate a coupon code against all business rules.

    Returns:
        (valid, error_message, coupon_object)
        - If valid: (True, "", coupon)
        - If invalid: (False, "reason", None)
    """
    with Database().session() as session:
        coupon = session.query(Coupon).filter(Coupon.code == code.upper()).first()

        if not coupon:
            return False, "coupon.error.not_found", None

        if not coupon.is_active:
            return False, "coupon.error.inactive", None

        # Check expiry
        now = datetime.now(timezone.utc)
        if coupon.valid_from and now < coupon.valid_from:
            return False, "coupon.error.not_yet_valid", None
        if coupon.valid_until and now > coupon.valid_until:
            return False, "coupon.error.expired", None

        # Check global usage limit
        if coupon.max_uses is not None and coupon.current_uses >= coupon.max_uses:
            return False, "coupon.error.max_uses_reached", None

        # Check per-user usage limit
        user_usage_count = (
            session.query(CouponUsage)
            .filter(CouponUsage.coupon_id == coupon.id, CouponUsage.user_id == user_id)
            .count()
        )
        if user_usage_count >= coupon.max_uses_per_user:
            return False, "coupon.error.already_used", None

        # Check minimum order amount
        min_order = Decimal(str(coupon.min_order)) if coupon.min_order else Decimal("0")
        if order_total < min_order:
            return False, "coupon.error.min_order_not_met", None

        # Detach-safe: expunge so the object survives session close
        session.expunge(coupon)

    return True, "", coupon


def calculate_discount(coupon: Coupon, order_total: Decimal) -> Decimal:
    """
    Calculate discount amount from a coupon.

    For percent type: order_total * (discount_value / 100), capped by max_discount.
    For fixed type: min(discount_value, order_total) so discount never exceeds the total.

    Returns:
        The discount amount as a Decimal, always >= 0 and <= order_total.
    """
    discount_value = Decimal(str(coupon.discount_value))

    if coupon.discount_type == "percent":
        discount = order_total * discount_value / Decimal("100")
        # Apply max_discount cap if set
        if coupon.max_discount:
            max_cap = Decimal(str(coupon.max_discount))
            discount = min(discount, max_cap)
    else:
        # Fixed discount
        discount = min(discount_value, order_total)

    # Ensure discount is never negative and never exceeds order total
    discount = max(Decimal("0"), min(discount, order_total))

    return discount.quantize(Decimal("0.01"))


def apply_coupon(coupon_id: int, user_id: int, order_id: int, discount: Decimal) -> bool:
    """
    Record coupon usage and increment the coupon's current_uses counter.

    Args:
        coupon_id: The coupon's database ID.
        user_id: The Telegram user ID applying the coupon.
        order_id: The order ID the coupon is applied to.
        discount: The discount amount that was applied.

    Returns:
        True if the usage was recorded successfully, False otherwise.
    """
    try:
        with Database().session() as session:
            coupon = session.query(Coupon).filter(Coupon.id == coupon_id).first()
            if not coupon:
                return False

            usage = CouponUsage(
                coupon_id=coupon_id,
                user_id=user_id,
                order_id=order_id,
                discount_applied=discount,
            )
            session.add(usage)

            coupon.current_uses = (coupon.current_uses or 0) + 1
            session.commit()

        return True
    except Exception as e:
        logging.getLogger(__name__).error("Failed to apply coupon: %s", e)
        return False
