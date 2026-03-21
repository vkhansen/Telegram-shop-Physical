"""Tests for GPS live tracking + delivery chat session (Card 15)"""
import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from bot.database.models.main import Order, User, DeliveryChatMessage


@pytest.mark.unit
@pytest.mark.models
class TestOrderCard15Fields:
    """Test Card 15 fields on the Order model"""

    def _create_order(self, db_session, buyer_id, **kwargs):
        user = User(telegram_id=buyer_id, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        order = Order(
            buyer_id=buyer_id, total_price=Decimal("100.00"),
            payment_method="cash", delivery_address="Test",
            phone_number="0812345678", **kwargs
        )
        db_session.add(order)
        db_session.commit()
        return order

    def test_customer_live_location_fields_nullable(self, db_with_roles, db_session):
        """Card 15 fields default to None"""
        order = self._create_order(db_session, 400001)

        assert order.customer_live_location_message_id is None
        assert order.chat_opened_at is None
        assert order.chat_closed_at is None
        assert order.chat_post_delivery_until is None

    def test_set_customer_live_location_message_id(self, db_with_roles, db_session):
        """Can store customer's live location message ID"""
        order = self._create_order(db_session, 400002, order_status="out_for_delivery")

        order.customer_live_location_message_id = 55555
        db_session.commit()
        db_session.refresh(order)

        assert order.customer_live_location_message_id == 55555

    def test_chat_session_timestamps(self, db_with_roles, db_session):
        """Can set chat session open/close timestamps"""
        order = self._create_order(db_session, 400003, order_status="out_for_delivery")

        now = datetime.now(timezone.utc)
        order.chat_opened_at = now
        order.chat_closed_at = now + timedelta(hours=1)
        order.chat_post_delivery_until = now + timedelta(minutes=30)
        db_session.commit()
        db_session.refresh(order)

        assert order.chat_opened_at is not None
        assert order.chat_closed_at is not None
        assert order.chat_post_delivery_until is not None
        assert order.chat_closed_at > order.chat_opened_at


@pytest.mark.unit
@pytest.mark.models
class TestDeliveryChatMessageCard15Fields:
    """Test Card 15 GPS metadata fields on DeliveryChatMessage"""

    def _create_order(self, db_session, buyer_id):
        user = User(telegram_id=buyer_id, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()
        order = Order(
            buyer_id=buyer_id, total_price=Decimal("100.00"),
            payment_method="cash", delivery_address="Test",
            phone_number="0812345678", order_status="out_for_delivery"
        )
        db_session.add(order)
        db_session.flush()
        return order

    def test_is_live_location_default_false(self, db_with_roles, db_session):
        """is_live_location defaults to False"""
        order = self._create_order(db_session, 400010)

        msg = DeliveryChatMessage(
            order_id=order.id,
            sender_id=400010,
            sender_role="customer",
            location_lat=13.7563,
            location_lng=100.5018,
        )
        db_session.add(msg)
        db_session.commit()
        db_session.refresh(msg)

        assert msg.is_live_location is False
        assert msg.live_location_update_count is None

    def test_customer_static_location_logged(self, db_with_roles, db_session):
        """Static GPS from customer recorded with is_live_location=False"""
        order = self._create_order(db_session, 400011)

        msg = DeliveryChatMessage(
            order_id=order.id,
            sender_id=400011,
            sender_role="customer",
            location_lat=13.7563,
            location_lng=100.5018,
            is_live_location=False,
        )
        db_session.add(msg)
        db_session.commit()
        db_session.refresh(msg)

        assert msg.is_live_location is False
        assert msg.location_lat == pytest.approx(13.7563, abs=0.001)

    def test_customer_live_location_logged(self, db_with_roles, db_session):
        """Live GPS from customer recorded with is_live_location=True"""
        order = self._create_order(db_session, 400012)

        msg = DeliveryChatMessage(
            order_id=order.id,
            sender_id=400012,
            sender_role="customer",
            location_lat=13.7563,
            location_lng=100.5018,
            is_live_location=True,
            live_location_update_count=0,
        )
        db_session.add(msg)
        db_session.commit()
        db_session.refresh(msg)

        assert msg.is_live_location is True
        assert msg.live_location_update_count == 0

    def test_live_location_updates_counted(self, db_with_roles, db_session):
        """Each live location update has incrementing update count"""
        order = self._create_order(db_session, 400013)

        for i in range(5):
            msg = DeliveryChatMessage(
                order_id=order.id,
                sender_id=400013,
                sender_role="driver",
                location_lat=13.7563 + (i * 0.001),
                location_lng=100.5018 + (i * 0.001),
                is_live_location=True,
                live_location_update_count=i,
            )
            db_session.add(msg)
        db_session.commit()

        updates = db_session.query(DeliveryChatMessage).filter_by(
            order_id=order.id, is_live_location=True
        ).order_by(DeliveryChatMessage.live_location_update_count).all()

        assert len(updates) == 5
        assert updates[0].live_location_update_count == 0
        assert updates[4].live_location_update_count == 4
        # Verify locations are different (driver moved)
        assert updates[0].location_lat != updates[4].location_lat

    def test_driver_live_location_logged(self, db_with_roles, db_session):
        """Driver live location recorded with correct role and flag"""
        order = self._create_order(db_session, 400014)

        msg = DeliveryChatMessage(
            order_id=order.id,
            sender_id=999999,  # driver ID
            sender_role="driver",
            location_lat=13.75,
            location_lng=100.50,
            is_live_location=True,
            live_location_update_count=0,
        )
        db_session.add(msg)
        db_session.commit()
        db_session.refresh(msg)

        assert msg.sender_role == "driver"
        assert msg.is_live_location is True

    def test_chat_history_includes_gps_metadata(self, db_with_roles, db_session):
        """Query returns is_live_location and update_count fields"""
        order = self._create_order(db_session, 400015)

        msgs = [
            DeliveryChatMessage(
                order_id=order.id, sender_id=400015, sender_role="customer",
                message_text="Hello driver",
            ),
            DeliveryChatMessage(
                order_id=order.id, sender_id=400015, sender_role="customer",
                location_lat=13.75, location_lng=100.50,
                is_live_location=False,
            ),
            DeliveryChatMessage(
                order_id=order.id, sender_id=999999, sender_role="driver",
                location_lat=13.76, location_lng=100.51,
                is_live_location=True, live_location_update_count=0,
            ),
            DeliveryChatMessage(
                order_id=order.id, sender_id=999999, sender_role="driver",
                location_lat=13.77, location_lng=100.52,
                is_live_location=True, live_location_update_count=1,
            ),
        ]
        for m in msgs:
            db_session.add(m)
        db_session.commit()

        history = db_session.query(DeliveryChatMessage).filter_by(
            order_id=order.id
        ).order_by(DeliveryChatMessage.created_at).all()

        assert len(history) == 4
        # Text message — no GPS
        assert history[0].is_live_location is False
        assert history[0].location_lat is None
        # Static location
        assert history[1].is_live_location is False
        assert history[1].location_lat is not None
        # Live location updates
        assert history[2].is_live_location is True
        assert history[2].live_location_update_count == 0
        assert history[3].is_live_location is True
        assert history[3].live_location_update_count == 1

    def test_location_trail_query(self, db_with_roles, db_session):
        """Can query only location messages filtered by sender role"""
        order = self._create_order(db_session, 400016)

        # Mix of text and location messages
        db_session.add(DeliveryChatMessage(
            order_id=order.id, sender_id=400016, sender_role="customer",
            message_text="text only",
        ))
        db_session.add(DeliveryChatMessage(
            order_id=order.id, sender_id=400016, sender_role="customer",
            location_lat=13.75, location_lng=100.50, is_live_location=True,
        ))
        db_session.add(DeliveryChatMessage(
            order_id=order.id, sender_id=999999, sender_role="driver",
            location_lat=13.76, location_lng=100.51, is_live_location=True,
        ))
        db_session.commit()

        # All locations
        all_locs = db_session.query(DeliveryChatMessage).filter(
            DeliveryChatMessage.order_id == order.id,
            DeliveryChatMessage.location_lat.isnot(None),
        ).all()
        assert len(all_locs) == 2

        # Customer locations only
        customer_locs = db_session.query(DeliveryChatMessage).filter(
            DeliveryChatMessage.order_id == order.id,
            DeliveryChatMessage.location_lat.isnot(None),
            DeliveryChatMessage.sender_role == "customer",
        ).all()
        assert len(customer_locs) == 1
        assert customer_locs[0].sender_role == "customer"

        # Driver locations only
        driver_locs = db_session.query(DeliveryChatMessage).filter(
            DeliveryChatMessage.order_id == order.id,
            DeliveryChatMessage.location_lat.isnot(None),
            DeliveryChatMessage.sender_role == "driver",
        ).all()
        assert len(driver_locs) == 1
        assert driver_locs[0].sender_role == "driver"


@pytest.mark.unit
@pytest.mark.models
class TestChatSessionLifecycle:
    """Test the is_chat_active logic (Card 15)"""

    def _create_order(self, db_session, buyer_id, **kwargs):
        user = User(telegram_id=buyer_id, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()
        order = Order(
            buyer_id=buyer_id, total_price=Decimal("100.00"),
            payment_method="cash", delivery_address="Test",
            phone_number="0812345678", **kwargs
        )
        db_session.add(order)
        db_session.commit()
        return order

    def test_chat_active_during_confirmed(self, db_with_roles, db_session):
        """Chat is active when order is confirmed"""
        from bot.handlers.user.delivery_chat_handler import is_chat_active
        order = self._create_order(db_session, 400020, order_status="confirmed")
        assert is_chat_active(order) is True

    def test_chat_active_during_preparing(self, db_with_roles, db_session):
        """Chat is active when order is preparing"""
        from bot.handlers.user.delivery_chat_handler import is_chat_active
        order = self._create_order(db_session, 400021, order_status="preparing")
        assert is_chat_active(order) is True

    def test_chat_active_during_out_for_delivery(self, db_with_roles, db_session):
        """Chat is active when order is out for delivery"""
        from bot.handlers.user.delivery_chat_handler import is_chat_active
        order = self._create_order(db_session, 400022, order_status="out_for_delivery")
        assert is_chat_active(order) is True

    def test_chat_active_post_delivery_within_window(self, db_with_roles, db_session):
        """Chat is active within post-delivery window"""
        from bot.handlers.user.delivery_chat_handler import is_chat_active
        order = self._create_order(db_session, 400023, order_status="delivered")
        order.chat_post_delivery_until = datetime.now(timezone.utc) + timedelta(minutes=15)
        db_session.commit()

        assert is_chat_active(order) is True

    def test_chat_inactive_post_delivery_after_window(self, db_with_roles, db_session):
        """Chat is inactive after post-delivery window expires"""
        from bot.handlers.user.delivery_chat_handler import is_chat_active
        order = self._create_order(db_session, 400024, order_status="delivered")
        order.chat_post_delivery_until = datetime.now(timezone.utc) - timedelta(minutes=5)
        db_session.commit()

        assert is_chat_active(order) is False

    def test_chat_inactive_delivered_no_window(self, db_with_roles, db_session):
        """Chat is inactive for delivered orders with no post-delivery window set"""
        from bot.handlers.user.delivery_chat_handler import is_chat_active
        order = self._create_order(db_session, 400025, order_status="delivered")
        assert is_chat_active(order) is False

    def test_chat_inactive_cancelled(self, db_with_roles, db_session):
        """Chat is inactive for cancelled orders"""
        from bot.handlers.user.delivery_chat_handler import is_chat_active
        order = self._create_order(db_session, 400026, order_status="cancelled")
        assert is_chat_active(order) is False

    def test_chat_inactive_pending(self, db_with_roles, db_session):
        """Chat is inactive for pending orders (not yet confirmed)"""
        from bot.handlers.user.delivery_chat_handler import is_chat_active
        order = self._create_order(db_session, 400027, order_status="pending")
        assert is_chat_active(order) is False

    def test_chat_active_ready(self, db_with_roles, db_session):
        """Chat is active when order is ready for pickup/delivery"""
        from bot.handlers.user.delivery_chat_handler import is_chat_active
        order = self._create_order(db_session, 400028, order_status="ready")
        assert is_chat_active(order) is True
