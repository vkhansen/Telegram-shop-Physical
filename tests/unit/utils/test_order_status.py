"""Tests for order status workflow (Card 9)"""
import pytest
from datetime import datetime, timezone
from decimal import Decimal

from bot.utils.order_status import is_valid_transition, get_allowed_transitions, EXPIRABLE_STATUSES, ALL_STATUSES, VALID_TRANSITIONS


@pytest.mark.unit
class TestOrderStatusTransitions:
    """Test status transition validation"""

    def test_pending_to_reserved(self):
        assert is_valid_transition("pending", "reserved") is True

    def test_reserved_to_confirmed(self):
        assert is_valid_transition("reserved", "confirmed") is True

    def test_confirmed_to_preparing(self):
        assert is_valid_transition("confirmed", "preparing") is True

    def test_preparing_to_ready(self):
        assert is_valid_transition("preparing", "ready") is True

    def test_ready_to_out_for_delivery(self):
        assert is_valid_transition("ready", "out_for_delivery") is True

    def test_out_for_delivery_to_delivered(self):
        assert is_valid_transition("out_for_delivery", "delivered") is True

    def test_cannot_skip_statuses(self):
        """Cannot jump from confirmed directly to delivered"""
        assert is_valid_transition("confirmed", "delivered") is False

    def test_cannot_skip_preparing(self):
        assert is_valid_transition("confirmed", "ready") is False

    def test_any_active_to_cancelled(self):
        """Any active status can be cancelled"""
        for status in ["reserved", "confirmed", "preparing", "ready", "out_for_delivery"]:
            assert is_valid_transition(status, "cancelled") is True

    def test_delivered_is_terminal(self):
        """Delivered is a terminal state"""
        assert get_allowed_transitions("delivered") == set()

    def test_cancelled_is_terminal(self):
        assert get_allowed_transitions("cancelled") == set()

    def test_expired_is_terminal(self):
        assert get_allowed_transitions("expired") == set()

    def test_reservation_cleaner_only_expires_reserved(self):
        """Only 'reserved' orders should be auto-expired"""
        assert EXPIRABLE_STATUSES == {"reserved"}
        assert "preparing" not in EXPIRABLE_STATUSES
        assert "ready" not in EXPIRABLE_STATUSES


@pytest.mark.unit
@pytest.mark.models
class TestExtendedStatusFields:
    """Test extended order status model fields"""

    def test_order_extended_statuses(self, db_with_roles, db_session):
        """All extended statuses can be stored"""
        from bot.database.models.main import Order, User

        user = User(telegram_id=400001, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        for status in ["pending", "reserved", "confirmed", "preparing", "ready",
                        "out_for_delivery", "delivered", "cancelled", "expired"]:
            order = Order(
                buyer_id=400001, total_price=Decimal("100.00"),
                payment_method="cash", delivery_address="Test",
                phone_number="0812345678", order_status=status
            )
            db_session.add(order)
            db_session.commit()
            assert order.order_status == status

    def test_order_group_message_ids(self, db_with_roles, db_session):
        """Kitchen and rider group message IDs are nullable"""
        from bot.database.models.main import Order, User

        user = User(telegram_id=400002, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        order = Order(
            buyer_id=400002, total_price=Decimal("100.00"),
            payment_method="cash", delivery_address="Test",
            phone_number="0812345678"
        )
        db_session.add(order)
        db_session.commit()

        assert order.kitchen_group_message_id is None
        assert order.rider_group_message_id is None

        order.kitchen_group_message_id = 12345
        order.rider_group_message_id = 67890
        db_session.commit()
        db_session.refresh(order)

        assert order.kitchen_group_message_id == 12345
        assert order.rider_group_message_id == 67890


@pytest.mark.unit
class TestStatusTransitionEdgeCases:
    """Edge case tests for order status transitions"""

    def test_nonexistent_status_returns_false(self):
        """Non-existent status string returns False for any transition"""
        assert is_valid_transition("nonexistent", "confirmed") is False
        assert is_valid_transition("nonexistent", "pending") is False
        assert is_valid_transition("nonexistent", "delivered") is False

    def test_empty_string_status_returns_false(self):
        """Empty string status returns False for any transition"""
        assert is_valid_transition("", "confirmed") is False
        assert is_valid_transition("", "pending") is False
        assert is_valid_transition("pending", "") is False
        assert is_valid_transition("", "") is False

    def test_self_transition_returns_false(self):
        """Self-transition (same status to same status) returns False"""
        for status in ALL_STATUSES:
            assert is_valid_transition(status, status) is False, (
                f"Self-transition should be invalid for '{status}'"
            )

    def test_get_allowed_transitions_pending(self):
        """Pending can transition to reserved or cancelled"""
        assert get_allowed_transitions("pending") == {"reserved", "cancelled"}

    def test_get_allowed_transitions_reserved(self):
        """Reserved can transition to confirmed, cancelled, or expired"""
        assert get_allowed_transitions("reserved") == {"confirmed", "cancelled", "expired"}

    def test_get_allowed_transitions_confirmed(self):
        """Confirmed can transition to preparing or cancelled"""
        assert get_allowed_transitions("confirmed") == {"preparing", "cancelled"}

    def test_get_allowed_transitions_preparing(self):
        """Preparing can transition to ready or cancelled"""
        assert get_allowed_transitions("preparing") == {"ready", "cancelled"}

    def test_get_allowed_transitions_ready(self):
        """Ready can transition to out_for_delivery or cancelled"""
        assert get_allowed_transitions("ready") == {"out_for_delivery", "cancelled"}

    def test_get_allowed_transitions_out_for_delivery(self):
        """Out for delivery can transition to delivered or cancelled"""
        assert get_allowed_transitions("out_for_delivery") == {"delivered", "cancelled"}

    def test_get_allowed_transitions_delivered(self):
        """Delivered is terminal — no transitions"""
        assert get_allowed_transitions("delivered") == set()

    def test_get_allowed_transitions_cancelled(self):
        """Cancelled is terminal — no transitions"""
        assert get_allowed_transitions("cancelled") == set()

    def test_get_allowed_transitions_expired(self):
        """Expired is terminal — no transitions"""
        assert get_allowed_transitions("expired") == set()

    def test_get_allowed_transitions_unknown_status(self):
        """Unknown status returns empty set"""
        assert get_allowed_transitions("unknown") == set()
        assert get_allowed_transitions("") == set()

    def test_all_statuses_contains_exactly_nine(self):
        """ALL_STATUSES constant contains exactly 9 statuses"""
        assert len(ALL_STATUSES) == 9
        expected = {
            "pending", "reserved", "confirmed", "preparing", "ready",
            "out_for_delivery", "delivered", "cancelled", "expired"
        }
        assert ALL_STATUSES == expected

    def test_pending_to_cancelled_is_valid(self):
        """Pending can be cancelled"""
        assert is_valid_transition("pending", "cancelled") is True

    def test_pending_to_expired_is_not_valid(self):
        """Pending cannot expire — only reserved can expire"""
        assert is_valid_transition("pending", "expired") is False

    def test_cancelled_to_anything_is_not_valid(self):
        """Cancelled is terminal — cannot transition to any status"""
        for status in ALL_STATUSES:
            assert is_valid_transition("cancelled", status) is False, (
                f"Cancelled should not transition to '{status}'"
            )

    def test_expired_to_anything_is_not_valid(self):
        """Expired is terminal — cannot transition to any status"""
        for status in ALL_STATUSES:
            assert is_valid_transition("expired", status) is False, (
                f"Expired should not transition to '{status}'"
            )
