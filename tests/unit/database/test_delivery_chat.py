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
