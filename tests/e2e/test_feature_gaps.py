"""
E2E coverage for user-facing features that previously had no end-to-end tests:

- Coupons        (bot/utils/coupon_utils.py — validate/calculate/apply)
- Reviews        (Review model + bot/handlers/user/review_handler.get_item_rating)
- Support tickets (SupportTicket + TicketMessage models, status lifecycle)

These were identified as gaps: the features ship with handlers, models and i18n
strings but had zero (tickets) or no end-to-end (coupons, reviews) coverage.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from bot.database.models.main import (
    Categories,
    Coupon,
    CouponUsage,
    Goods,
    Order,
    Review,
    SupportTicket,
    TicketMessage,
    User,
)
from bot.utils.coupon_utils import apply_coupon, calculate_discount, validate_coupon


def _user(session, tid, role_id=1):
    u = User(telegram_id=tid, role_id=role_id, registration_date=datetime.now(UTC))
    session.add(u)
    session.commit()
    session.refresh(u)
    return u


def _order(session, buyer_id, code, total="200"):
    order = Order(
        buyer_id=buyer_id,
        total_price=Decimal(total),
        payment_method="cash",
        delivery_address="T",
        phone_number="+66",
        order_code=code,
    )
    session.add(order)
    session.commit()
    session.refresh(order)
    return order


# ===================================================================
# Coupons (no prior E2E coverage)
# ===================================================================
@pytest.mark.e2e
class TestCouponFlow:
    def test_validate_and_calculate_percent_with_cap(self, db_with_roles: Session):
        _user(db_with_roles, 60001)
        db_with_roles.add(
            Coupon(code="SAVE20", discount_type="percent", discount_value=Decimal("20"), max_discount=Decimal("30"))
        )
        db_with_roles.commit()

        ok, err, coupon = validate_coupon("save20", 60001, Decimal("100"))  # case-insensitive
        assert ok and err == "" and coupon is not None
        # 20% of 100 = 20 (below the 30 cap)
        assert calculate_discount(coupon, Decimal("100")) == Decimal("20.00")
        # 20% of 500 = 100, capped at 30
        assert calculate_discount(coupon, Decimal("500")) == Decimal("30.00")

    def test_calculate_fixed_never_exceeds_total(self, db_with_roles: Session):
        _user(db_with_roles, 60002)
        db_with_roles.add(Coupon(code="FLAT50", discount_type="fixed", discount_value=Decimal("50")))
        db_with_roles.commit()

        _, _, coupon = validate_coupon("FLAT50", 60002, Decimal("200"))
        assert calculate_discount(coupon, Decimal("200")) == Decimal("50.00")
        # Discount can never exceed the order total
        assert calculate_discount(coupon, Decimal("30")) == Decimal("30.00")

    def test_not_found(self, db_with_roles: Session):
        _user(db_with_roles, 60003)
        ok, err, coupon = validate_coupon("NOPE", 60003, Decimal("100"))
        assert not ok and coupon is None and "not_found" in err

    def test_inactive(self, db_with_roles: Session):
        _user(db_with_roles, 60004)
        c = Coupon(code="OFF", discount_type="fixed", discount_value=Decimal("10"))
        c.is_active = False
        db_with_roles.add(c)
        db_with_roles.commit()
        ok, err, _ = validate_coupon("OFF", 60004, Decimal("100"))
        assert not ok and "inactive" in err

    def test_expired_and_not_yet_valid(self, db_with_roles: Session):
        _user(db_with_roles, 60005)
        now = datetime.now(UTC)
        db_with_roles.add(
            Coupon(code="OLD", discount_type="fixed", discount_value=Decimal("10"), valid_until=now - timedelta(days=1))
        )
        db_with_roles.add(
            Coupon(code="SOON", discount_type="fixed", discount_value=Decimal("10"), valid_from=now + timedelta(days=1))
        )
        db_with_roles.commit()
        assert "expired" in validate_coupon("OLD", 60005, Decimal("100"))[1]
        assert "not_yet_valid" in validate_coupon("SOON", 60005, Decimal("100"))[1]

    def test_min_order_not_met(self, db_with_roles: Session):
        _user(db_with_roles, 60006)
        db_with_roles.add(
            Coupon(code="BIG", discount_type="fixed", discount_value=Decimal("10"), min_order=Decimal("500"))
        )
        db_with_roles.commit()
        ok, err, _ = validate_coupon("BIG", 60006, Decimal("100"))
        assert not ok and "min_order_not_met" in err

    def test_max_uses_reached(self, db_with_roles: Session):
        _user(db_with_roles, 60007)
        c = Coupon(code="ONCE", discount_type="fixed", discount_value=Decimal("10"), max_uses=1)
        c.current_uses = 1
        db_with_roles.add(c)
        db_with_roles.commit()
        ok, err, _ = validate_coupon("ONCE", 60007, Decimal("100"))
        assert not ok and "max_uses_reached" in err

    def test_apply_records_usage_and_blocks_reuse(self, db_with_roles: Session):
        user = _user(db_with_roles, 60008)
        db_with_roles.add(Coupon(code="WELCOME", discount_type="percent", discount_value=Decimal("10")))
        db_with_roles.commit()
        order = _order(db_with_roles, user.telegram_id, "CPN001")

        ok, _, coupon = validate_coupon("WELCOME", user.telegram_id, Decimal("200"))
        assert ok
        discount = calculate_discount(coupon, Decimal("200"))
        assert apply_coupon(coupon.id, user.telegram_id, order.id, discount) is True

        # Usage recorded and counter incremented
        assert db_with_roles.query(CouponUsage).filter_by(coupon_id=coupon.id).count() == 1
        db_with_roles.expire_all()
        assert db_with_roles.query(Coupon).filter_by(id=coupon.id).first().current_uses == 1

        # Per-user limit (default 1) now blocks reuse
        ok2, err2, _ = validate_coupon("WELCOME", user.telegram_id, Decimal("200"))
        assert not ok2 and "already_used" in err2


# ===================================================================
# Reviews / ratings (no prior E2E coverage)
# ===================================================================
@pytest.mark.e2e
class TestReviewFlow:
    def _good(self, session, name="Pad Thai"):
        session.add(Categories(name="Food"))
        session.flush()
        session.add(Goods(name=name, price=Decimal("100"), description="d", category_name="Food", stock_quantity=10))
        session.commit()

    def test_create_review_and_average_rating(self, db_with_roles: Session):
        from bot.handlers.user.review_handler import get_item_rating

        self._good(db_with_roles)
        u1 = _user(db_with_roles, 61001)
        u2 = _user(db_with_roles, 61002)
        o1 = _order(db_with_roles, u1.telegram_id, "REV001")
        o2 = _order(db_with_roles, u2.telegram_id, "REV002")

        db_with_roles.add(Review(order_id=o1.id, user_id=u1.telegram_id, rating=5, item_name="Pad Thai"))
        db_with_roles.add(Review(order_id=o2.id, user_id=u2.telegram_id, rating=4, item_name="Pad Thai"))
        db_with_roles.commit()

        avg, count = get_item_rating("Pad Thai")
        assert count == 2
        assert avg == pytest.approx(4.5)

    def test_no_reviews_returns_none(self, db_with_roles: Session):
        from bot.handlers.user.review_handler import get_item_rating

        avg, count = get_item_rating("Nonexistent Item")
        assert avg is None and count == 0

    def test_rating_out_of_range_rejected(self, db_with_roles: Session):
        self._good(db_with_roles, name="Som Tam")
        u = _user(db_with_roles, 61003)
        o = _order(db_with_roles, u.telegram_id, "REV003")
        db_with_roles.add(Review(order_id=o.id, user_id=u.telegram_id, rating=6, item_name="Som Tam"))
        with pytest.raises(SQLAlchemyError):
            db_with_roles.commit()
        db_with_roles.rollback()


# ===================================================================
# Support tickets (had ZERO test coverage)
# ===================================================================
@pytest.mark.e2e
class TestSupportTicketFlow:
    def test_ticket_lifecycle_with_messages(self, db_with_roles: Session):
        user = _user(db_with_roles, 62001)

        ticket = SupportTicket(ticket_code="TKT00001", user_id=user.telegram_id, subject="Order missing")
        db_with_roles.add(ticket)
        db_with_roles.commit()
        db_with_roles.refresh(ticket)
        assert ticket.status == "open"
        assert ticket.priority == "normal"

        # User and admin exchange messages
        db_with_roles.add(
            TicketMessage(
                ticket_id=ticket.id, sender_id=user.telegram_id, sender_role="user", message_text="Where is my order?"
            )
        )
        db_with_roles.add(
            TicketMessage(ticket_id=ticket.id, sender_id=999, sender_role="admin", message_text="Looking into it.")
        )
        db_with_roles.commit()

        msgs = db_with_roles.query(TicketMessage).filter_by(ticket_id=ticket.id).order_by(TicketMessage.id).all()
        assert [m.sender_role for m in msgs] == ["user", "admin"]

        # Status lifecycle: open -> in_progress -> resolved -> closed
        for status in ("in_progress", "resolved", "closed"):
            ticket.status = status
            db_with_roles.commit()
            db_with_roles.refresh(ticket)
            assert ticket.status == status

    def test_ticket_code_unique(self, db_with_roles: Session):
        user = _user(db_with_roles, 62002)
        db_with_roles.add(SupportTicket(ticket_code="DUP00001", user_id=user.telegram_id, subject="A"))
        db_with_roles.commit()
        db_with_roles.add(SupportTicket(ticket_code="DUP00001", user_id=user.telegram_id, subject="B"))
        with pytest.raises(SQLAlchemyError):
            db_with_roles.commit()
        db_with_roles.rollback()
