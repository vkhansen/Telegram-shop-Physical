"""Tests for delivery chat relay and live location (Card 13)"""
import pytest
from datetime import datetime, timezone
from decimal import Decimal

from bot.database.models.main import Order, User, DeliveryChatMessage


@pytest.mark.unit
@pytest.mark.models
class TestDeliveryChatMessageModel:
    """Test DeliveryChatMessage model for driver-customer chat recording"""

    def test_create_driver_text_message(self, db_with_roles, db_session):
        """Driver text message recorded correctly"""
        user = User(telegram_id=200001, registration_date=datetime.now(timezone.utc))
        driver = User(telegram_id=200002, registration_date=datetime.now(timezone.utc))
        db_session.add_all([user, driver])
        db_session.commit()

        order = Order(
            buyer_id=200001, total_price=Decimal("100.00"),
            payment_method="cash", delivery_address="Test",
            phone_number="0812345678", order_status="out_for_delivery"
        )
        db_session.add(order)
        db_session.flush()

        msg = DeliveryChatMessage(
            order_id=order.id,
            sender_id=200002,
            sender_role="driver",
            message_text="I'm at the lobby, where should I go?",
            telegram_message_id=12345
        )
        db_session.add(msg)
        db_session.commit()
        db_session.refresh(msg)

        assert msg.sender_role == "driver"
        assert msg.message_text == "I'm at the lobby, where should I go?"
        assert msg.order_id == order.id
        assert msg.created_at is not None

    def test_create_customer_text_message(self, db_with_roles, db_session):
        """Customer text message recorded correctly"""
        user = User(telegram_id=200003, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        order = Order(
            buyer_id=200003, total_price=Decimal("200.00"),
            payment_method="cash", delivery_address="Test",
            phone_number="0812345678", order_status="out_for_delivery"
        )
        db_session.add(order)
        db_session.flush()

        msg = DeliveryChatMessage(
            order_id=order.id,
            sender_id=200003,
            sender_role="customer",
            message_text="Go to Building B, 3rd floor"
        )
        db_session.add(msg)
        db_session.commit()

        assert msg.sender_role == "customer"
        assert msg.message_text == "Go to Building B, 3rd floor"

    def test_record_photo_message(self, db_with_roles, db_session):
        """Photo messages are recorded with file_id"""
        user = User(telegram_id=200004, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        order = Order(
            buyer_id=200004, total_price=Decimal("150.00"),
            payment_method="cash", delivery_address="Test",
            phone_number="0812345678"
        )
        db_session.add(order)
        db_session.flush()

        msg = DeliveryChatMessage(
            order_id=order.id,
            sender_id=200004,
            sender_role="driver",
            photo_file_id="AgACAgIAAxk_photo_123"
        )
        db_session.add(msg)
        db_session.commit()

        assert msg.photo_file_id == "AgACAgIAAxk_photo_123"
        assert msg.message_text is None

    def test_record_location_message(self, db_with_roles, db_session):
        """Location messages are recorded with coordinates"""
        user = User(telegram_id=200005, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        order = Order(
            buyer_id=200005, total_price=Decimal("100.00"),
            payment_method="cash", delivery_address="Test",
            phone_number="0812345678"
        )
        db_session.add(order)
        db_session.flush()

        msg = DeliveryChatMessage(
            order_id=order.id,
            sender_id=200005,
            sender_role="driver",
            location_lat=13.7563,
            location_lng=100.5018
        )
        db_session.add(msg)
        db_session.commit()

        assert msg.location_lat == pytest.approx(13.7563, abs=0.001)
        assert msg.location_lng == pytest.approx(100.5018, abs=0.001)

    def test_chat_history_ordered(self, db_with_roles, db_session):
        """Chat messages ordered by creation time"""
        user = User(telegram_id=200006, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        order = Order(
            buyer_id=200006, total_price=Decimal("100.00"),
            payment_method="cash", delivery_address="Test",
            phone_number="0812345678"
        )
        db_session.add(order)
        db_session.flush()

        msgs = [
            DeliveryChatMessage(order_id=order.id, sender_id=200006, sender_role="driver", message_text="msg1"),
            DeliveryChatMessage(order_id=order.id, sender_id=200006, sender_role="customer", message_text="msg2"),
            DeliveryChatMessage(order_id=order.id, sender_id=200006, sender_role="driver", message_text="msg3"),
        ]
        for m in msgs:
            db_session.add(m)
        db_session.commit()

        history = db_session.query(DeliveryChatMessage).filter_by(
            order_id=order.id
        ).order_by(DeliveryChatMessage.created_at).all()

        assert len(history) == 3
        assert history[0].message_text == "msg1"
        assert history[1].sender_role == "customer"
        assert history[2].message_text == "msg3"


@pytest.mark.unit
@pytest.mark.models
class TestDriverLiveLocationFields:
    """Test driver live location tracking fields on Order"""

    def test_driver_fields_nullable(self, db_with_roles, db_session):
        """Driver tracking fields default to None"""
        user = User(telegram_id=200010, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        order = Order(
            buyer_id=200010, total_price=Decimal("100.00"),
            payment_method="cash", delivery_address="Test",
            phone_number="0812345678"
        )
        db_session.add(order)
        db_session.commit()

        assert order.driver_live_location_message_id is None
        assert order.driver_id is None

    def test_assign_driver_and_live_location(self, db_with_roles, db_session):
        """Can assign driver and track live location message"""
        user = User(telegram_id=200011, registration_date=datetime.now(timezone.utc))
        driver = User(telegram_id=200012, registration_date=datetime.now(timezone.utc))
        db_session.add_all([user, driver])
        db_session.commit()

        order = Order(
            buyer_id=200011, total_price=Decimal("200.00"),
            payment_method="cash", delivery_address="Test",
            phone_number="0812345678", order_status="out_for_delivery"
        )
        db_session.add(order)
        db_session.commit()

        order.driver_id = 200012
        order.driver_live_location_message_id = 99999
        db_session.commit()
        db_session.refresh(order)

        assert order.driver_id == 200012
        assert order.driver_live_location_message_id == 99999


@pytest.mark.unit
@pytest.mark.models
class TestDeliveryChatEdgeCases:
    """Edge case tests for DeliveryChatMessage model and querying"""

    def _create_order(self, db_session, buyer_id):
        """Helper to create a user and order for testing."""
        user = User(telegram_id=buyer_id, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        order = Order(
            buyer_id=buyer_id, total_price=Decimal("100.00"),
            payment_method="cash", delivery_address="Test Address",
            phone_number="0812345678", order_status="out_for_delivery"
        )
        db_session.add(order)
        db_session.flush()
        return order

    def test_message_with_both_text_and_photo(self, db_with_roles, db_session):
        """Message can have both text and photo_file_id set (photo with caption)"""
        order = self._create_order(db_session, 300001)

        msg = DeliveryChatMessage(
            order_id=order.id,
            sender_id=300001,
            sender_role="driver",
            message_text="Here is a photo of the entrance",
            photo_file_id="AgACAgIAAxk_photo_456"
        )
        db_session.add(msg)
        db_session.commit()
        db_session.refresh(msg)

        assert msg.message_text == "Here is a photo of the entrance"
        assert msg.photo_file_id == "AgACAgIAAxk_photo_456"
        assert msg.location_lat is None
        assert msg.location_lng is None

    def test_message_with_both_text_and_location(self, db_with_roles, db_session):
        """Message can have both text and location fields set"""
        order = self._create_order(db_session, 300002)

        msg = DeliveryChatMessage(
            order_id=order.id,
            sender_id=300002,
            sender_role="customer",
            message_text="I am here at this location",
            location_lat=13.7563,
            location_lng=100.5018
        )
        db_session.add(msg)
        db_session.commit()
        db_session.refresh(msg)

        assert msg.message_text == "I am here at this location"
        assert msg.location_lat == pytest.approx(13.7563, abs=0.001)
        assert msg.location_lng == pytest.approx(100.5018, abs=0.001)

    def test_message_with_empty_string_text(self, db_with_roles, db_session):
        """Message with empty string text is stored as empty string"""
        order = self._create_order(db_session, 300003)

        msg = DeliveryChatMessage(
            order_id=order.id,
            sender_id=300003,
            sender_role="driver",
            message_text=""
        )
        db_session.add(msg)
        db_session.commit()
        db_session.refresh(msg)

        assert msg.message_text == ""

    def test_message_with_very_long_text(self, db_with_roles, db_session):
        """Message with 1000+ character text is stored correctly"""
        order = self._create_order(db_session, 300004)

        long_text = "A" * 2000
        msg = DeliveryChatMessage(
            order_id=order.id,
            sender_id=300004,
            sender_role="customer",
            message_text=long_text
        )
        db_session.add(msg)
        db_session.commit()
        db_session.refresh(msg)

        assert len(msg.message_text) == 2000
        assert msg.message_text == long_text

    def test_messages_across_multiple_orders_filtering(self, db_with_roles, db_session):
        """Messages are correctly filtered by order_id across multiple orders"""
        order1 = self._create_order(db_session, 300005)

        user2 = User(telegram_id=300006, registration_date=datetime.now(timezone.utc))
        db_session.add(user2)
        db_session.commit()
        order2 = Order(
            buyer_id=300006, total_price=Decimal("200.00"),
            payment_method="cash", delivery_address="Other Address",
            phone_number="0899999999", order_status="out_for_delivery"
        )
        db_session.add(order2)
        db_session.flush()

        # Add messages to order1
        msg1 = DeliveryChatMessage(
            order_id=order1.id, sender_id=300005,
            sender_role="driver", message_text="Order 1 msg A"
        )
        msg2 = DeliveryChatMessage(
            order_id=order1.id, sender_id=300005,
            sender_role="customer", message_text="Order 1 msg B"
        )
        # Add messages to order2
        msg3 = DeliveryChatMessage(
            order_id=order2.id, sender_id=300006,
            sender_role="driver", message_text="Order 2 msg A"
        )
        db_session.add_all([msg1, msg2, msg3])
        db_session.commit()

        # Query order1 messages
        order1_msgs = db_session.query(DeliveryChatMessage).filter_by(
            order_id=order1.id
        ).order_by(DeliveryChatMessage.created_at).all()
        assert len(order1_msgs) == 2
        assert all(m.order_id == order1.id for m in order1_msgs)

        # Query order2 messages
        order2_msgs = db_session.query(DeliveryChatMessage).filter_by(
            order_id=order2.id
        ).order_by(DeliveryChatMessage.created_at).all()
        assert len(order2_msgs) == 1
        assert order2_msgs[0].message_text == "Order 2 msg A"

    def test_order_with_no_messages_empty_result(self, db_with_roles, db_session):
        """Order with no chat messages returns empty query result"""
        order = self._create_order(db_session, 300007)

        messages = db_session.query(DeliveryChatMessage).filter_by(
            order_id=order.id
        ).order_by(DeliveryChatMessage.created_at).all()

        assert messages == []
        assert len(messages) == 0
