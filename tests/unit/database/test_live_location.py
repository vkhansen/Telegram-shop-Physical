"""
Tests for Card 15: GPS Live Tracking + Delivery Chat Session.

Tests:
- Chat session lifecycle (is_chat_active)
- Post-delivery chat window
- Live location message logging
- Location trail retrieval
- Customer GPS choice flow
"""
import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from bot.database.main import Database
from bot.database.models.main import Order, DeliveryChatMessage, User, Role


@pytest.fixture
def order_out_for_delivery(db_with_roles, test_user):
    """Create an order in out_for_delivery status."""
    session = db_with_roles
    order = Order(
        buyer_id=test_user.telegram_id,
        total_price=Decimal("500.00"),
        payment_method="cash",
        delivery_address="123 Sukhumvit Rd",
        phone_number="+66812345678",
        order_status="out_for_delivery",
        order_code="GPS001",
        driver_id=111222333,
    )
    session.add(order)
    session.commit()
    session.refresh(order)
    return order


@pytest.fixture
def order_delivered_with_window(db_with_roles, test_user):
    """Create a delivered order with active post-delivery chat window."""
    session = db_with_roles
    order = Order(
        buyer_id=test_user.telegram_id,
        total_price=Decimal("300.00"),
        payment_method="cash",
        delivery_address="456 Silom Rd",
        phone_number="+66898765432",
        order_status="delivered",
        order_code="GPS002",
        driver_id=111222333,
    )
    session.add(order)
    session.flush()
    # Use naive datetime since SQLite strips timezone info
    order.chat_post_delivery_until = datetime.utcnow() + timedelta(minutes=30)
    session.commit()
    session.refresh(order)
    return order


@pytest.fixture
def order_delivered_window_expired(db_with_roles, test_user):
    """Create a delivered order with expired post-delivery chat window."""
    session = db_with_roles
    order = Order(
        buyer_id=test_user.telegram_id,
        total_price=Decimal("200.00"),
        payment_method="cash",
        delivery_address="789 Rama IV",
        phone_number="+66876543210",
        order_status="delivered",
        order_code="GPS003",
        driver_id=111222333,
    )
    session.add(order)
    session.flush()
    # Use naive datetime since SQLite strips timezone info
    order.chat_post_delivery_until = datetime.utcnow() - timedelta(minutes=5)
    session.commit()
    session.refresh(order)
    return order


class TestChatSessionLifecycle:
    """Test is_chat_active() for various order states."""

    def test_chat_active_confirmed(self, db_with_roles, test_user):
        """Chat should be active when order is confirmed."""
        from bot.handlers.user.delivery_chat_handler import is_chat_active

        session = db_with_roles
        order = Order(
            buyer_id=test_user.telegram_id,
            total_price=Decimal("100"),
            payment_method="cash",
            delivery_address="test",
            phone_number="+66",
            order_status="confirmed",
            order_code="ACT001",
        )
        session.add(order)
        session.commit()

        assert is_chat_active(order) is True

    def test_chat_active_preparing(self, db_with_roles, test_user):
        """Chat should be active when order is preparing."""
        from bot.handlers.user.delivery_chat_handler import is_chat_active

        session = db_with_roles
        order = Order(
            buyer_id=test_user.telegram_id,
            total_price=Decimal("100"),
            payment_method="cash",
            delivery_address="test",
            phone_number="+66",
            order_status="preparing",
            order_code="ACT002",
        )
        session.add(order)
        session.commit()

        assert is_chat_active(order) is True

    def test_chat_active_ready(self, db_with_roles, test_user):
        """Chat should be active when order is ready."""
        from bot.handlers.user.delivery_chat_handler import is_chat_active

        session = db_with_roles
        order = Order(
            buyer_id=test_user.telegram_id,
            total_price=Decimal("100"),
            payment_method="cash",
            delivery_address="test",
            phone_number="+66",
            order_status="ready",
            order_code="ACT003",
        )
        session.add(order)
        session.commit()

        assert is_chat_active(order) is True

    def test_chat_active_out_for_delivery(self, order_out_for_delivery):
        """Chat should be active when order is out_for_delivery."""
        from bot.handlers.user.delivery_chat_handler import is_chat_active
        assert is_chat_active(order_out_for_delivery) is True

    def test_chat_active_delivered_within_window(self, order_delivered_with_window):
        """Chat should be active during post-delivery window."""
        from bot.handlers.user.delivery_chat_handler import is_chat_active
        assert is_chat_active(order_delivered_with_window) is True

    def test_chat_inactive_delivered_window_expired(self, order_delivered_window_expired):
        """Chat should be inactive after post-delivery window expires."""
        from bot.handlers.user.delivery_chat_handler import is_chat_active
        assert is_chat_active(order_delivered_window_expired) is False

    def test_chat_inactive_pending(self, db_with_roles, test_user):
        """Chat should be inactive for pending orders."""
        from bot.handlers.user.delivery_chat_handler import is_chat_active

        session = db_with_roles
        order = Order(
            buyer_id=test_user.telegram_id,
            total_price=Decimal("100"),
            payment_method="cash",
            delivery_address="test",
            phone_number="+66",
            order_status="pending",
            order_code="ACT004",
        )
        session.add(order)
        session.commit()

        assert is_chat_active(order) is False

    def test_chat_inactive_cancelled(self, db_with_roles, test_user):
        """Chat should be inactive for cancelled orders."""
        from bot.handlers.user.delivery_chat_handler import is_chat_active

        session = db_with_roles
        order = Order(
            buyer_id=test_user.telegram_id,
            total_price=Decimal("100"),
            payment_method="cash",
            delivery_address="test",
            phone_number="+66",
            order_status="cancelled",
            order_code="ACT005",
        )
        session.add(order)
        session.commit()

        assert is_chat_active(order) is False

    def test_chat_inactive_delivered_no_window(self, db_with_roles, test_user):
        """Chat should be inactive for delivered order with no window set."""
        from bot.handlers.user.delivery_chat_handler import is_chat_active

        session = db_with_roles
        order = Order(
            buyer_id=test_user.telegram_id,
            total_price=Decimal("100"),
            payment_method="cash",
            delivery_address="test",
            phone_number="+66",
            order_status="delivered",
            order_code="ACT006",
        )
        session.add(order)
        session.commit()

        assert is_chat_active(order) is False


class TestChatSessionManagement:
    """Test open/close chat session and post-delivery window."""

    def test_open_chat_session(self, db_with_roles, order_out_for_delivery):
        """Opening a chat session should set chat_opened_at."""
        from bot.handlers.user.delivery_chat_handler import open_chat_session

        session = db_with_roles
        assert order_out_for_delivery.chat_opened_at is None

        open_chat_session(session, order_out_for_delivery)
        session.commit()

        refreshed = session.query(Order).filter_by(id=order_out_for_delivery.id).first()
        assert refreshed.chat_opened_at is not None

    def test_open_chat_session_idempotent(self, db_with_roles, order_out_for_delivery):
        """Opening a chat session twice should not change the timestamp."""
        from bot.handlers.user.delivery_chat_handler import open_chat_session

        session = db_with_roles
        open_chat_session(session, order_out_for_delivery)
        session.commit()

        refreshed = session.query(Order).filter_by(id=order_out_for_delivery.id).first()
        first_open = refreshed.chat_opened_at

        open_chat_session(session, refreshed)
        session.commit()

        refreshed2 = session.query(Order).filter_by(id=order_out_for_delivery.id).first()
        assert refreshed2.chat_opened_at == first_open

    def test_close_chat_session(self, db_with_roles, order_out_for_delivery):
        """Closing a chat session should set chat_closed_at."""
        from bot.handlers.user.delivery_chat_handler import close_chat_session

        session = db_with_roles
        assert order_out_for_delivery.chat_closed_at is None

        close_chat_session(session, order_out_for_delivery)
        session.commit()

        refreshed = session.query(Order).filter_by(id=order_out_for_delivery.id).first()
        assert refreshed.chat_closed_at is not None

    def test_set_post_delivery_window(self, db_with_roles, order_out_for_delivery):
        """Setting post-delivery window should set chat_post_delivery_until."""
        from bot.handlers.user.delivery_chat_handler import set_post_delivery_window

        session = db_with_roles
        assert order_out_for_delivery.chat_post_delivery_until is None

        set_post_delivery_window(session, order_out_for_delivery)
        session.commit()

        refreshed = session.query(Order).filter_by(id=order_out_for_delivery.id).first()
        assert refreshed.chat_post_delivery_until is not None
        # Should be approximately 30 minutes from now (default POST_DELIVERY_CHAT_MINUTES)
        expected = datetime.now(timezone.utc) + timedelta(minutes=30)
        diff = abs((refreshed.chat_post_delivery_until - expected).total_seconds())
        assert diff < 5  # Within 5 seconds


class TestLiveLocationLogging:
    """Test live location message recording."""

    def test_log_live_location_message(self, db_with_roles, order_out_for_delivery):
        """Live location messages should be stored with is_live_location=True."""
        session = db_with_roles
        msg = DeliveryChatMessage(
            order_id=order_out_for_delivery.id,
            sender_id=111222333,
            sender_role="driver",
            location_lat=13.7563,
            location_lng=100.5018,
            is_live_location=True,
            live_location_update_count=0,
            telegram_message_id=9999,
        )
        session.add(msg)
        session.commit()

        stored = session.query(DeliveryChatMessage).filter_by(
            order_id=order_out_for_delivery.id
        ).first()

        assert stored.is_live_location is True
        assert stored.live_location_update_count == 0
        assert stored.location_lat == pytest.approx(13.7563)
        assert stored.location_lng == pytest.approx(100.5018)
        assert stored.sender_role == "driver"

    def test_log_multiple_live_updates(self, db_with_roles, order_out_for_delivery):
        """Multiple live location updates should be logged with incrementing counts."""
        session = db_with_roles
        for i in range(5):
            msg = DeliveryChatMessage(
                order_id=order_out_for_delivery.id,
                sender_id=111222333,
                sender_role="driver",
                location_lat=13.7563 + (i * 0.001),
                location_lng=100.5018 + (i * 0.001),
                is_live_location=True,
                live_location_update_count=i,
                telegram_message_id=9999 + i,
            )
            session.add(msg)
        session.commit()

        msgs = session.query(DeliveryChatMessage).filter_by(
            order_id=order_out_for_delivery.id,
            is_live_location=True,
        ).order_by(DeliveryChatMessage.created_at).all()

        assert len(msgs) == 5
        for i, msg in enumerate(msgs):
            assert msg.live_location_update_count == i

    def test_log_static_location(self, db_with_roles, order_out_for_delivery):
        """Static location messages should have is_live_location=False."""
        session = db_with_roles
        msg = DeliveryChatMessage(
            order_id=order_out_for_delivery.id,
            sender_id=order_out_for_delivery.buyer_id,
            sender_role="customer",
            location_lat=13.7400,
            location_lng=100.5100,
            is_live_location=False,
            telegram_message_id=8888,
        )
        session.add(msg)
        session.commit()

        stored = session.query(DeliveryChatMessage).filter_by(
            order_id=order_out_for_delivery.id
        ).first()

        assert stored.is_live_location is False
        assert stored.live_location_update_count is None

    def test_customer_live_location_message_id(self, db_with_roles, order_out_for_delivery):
        """Storing customer live location message ID on order."""
        session = db_with_roles
        order = session.query(Order).filter_by(id=order_out_for_delivery.id).first()
        assert order.customer_live_location_message_id is None

        order.customer_live_location_message_id = 12345
        session.commit()

        refreshed = session.query(Order).filter_by(id=order_out_for_delivery.id).first()
        assert refreshed.customer_live_location_message_id == 12345


class TestLocationTrail:
    """Test get_location_trail functionality."""

    @pytest.mark.asyncio
    async def test_get_location_trail_all(self, db_with_roles, order_out_for_delivery):
        """Get all GPS points for an order."""
        from bot.handlers.user.delivery_chat_handler import get_location_trail

        session = db_with_roles
        # Add driver locations
        for i in range(3):
            session.add(DeliveryChatMessage(
                order_id=order_out_for_delivery.id,
                sender_id=111222333,
                sender_role="driver",
                location_lat=13.75 + (i * 0.01),
                location_lng=100.50 + (i * 0.01),
                is_live_location=True,
                live_location_update_count=i,
            ))
        # Add customer location
        session.add(DeliveryChatMessage(
            order_id=order_out_for_delivery.id,
            sender_id=order_out_for_delivery.buyer_id,
            sender_role="customer",
            location_lat=13.74,
            location_lng=100.49,
            is_live_location=False,
        ))
        session.commit()

        trail = await get_location_trail(order_out_for_delivery.id)
        assert len(trail) == 4

    @pytest.mark.asyncio
    async def test_get_location_trail_by_role(self, db_with_roles, order_out_for_delivery):
        """Get GPS points filtered by sender role."""
        from bot.handlers.user.delivery_chat_handler import get_location_trail

        session = db_with_roles
        # Add driver and customer locations
        session.add(DeliveryChatMessage(
            order_id=order_out_for_delivery.id,
            sender_id=111222333,
            sender_role="driver",
            location_lat=13.75,
            location_lng=100.50,
            is_live_location=True,
            live_location_update_count=0,
        ))
        session.add(DeliveryChatMessage(
            order_id=order_out_for_delivery.id,
            sender_id=order_out_for_delivery.buyer_id,
            sender_role="customer",
            location_lat=13.74,
            location_lng=100.49,
            is_live_location=False,
        ))
        session.commit()

        driver_trail = await get_location_trail(order_out_for_delivery.id, sender_role="driver")
        assert len(driver_trail) == 1
        assert driver_trail[0]["sender_role"] == "driver"

        customer_trail = await get_location_trail(order_out_for_delivery.id, sender_role="customer")
        assert len(customer_trail) == 1
        assert customer_trail[0]["sender_role"] == "customer"

    @pytest.mark.asyncio
    async def test_get_location_trail_empty(self, db_with_roles, order_out_for_delivery):
        """Empty trail for order with no location messages."""
        from bot.handlers.user.delivery_chat_handler import get_location_trail

        trail = await get_location_trail(order_out_for_delivery.id)
        assert trail == []


class TestChatHistory:
    """Test get_chat_history functionality."""

    @pytest.mark.asyncio
    async def test_get_chat_history(self, db_with_roles, order_out_for_delivery):
        """Retrieve full chat history for an order."""
        from bot.handlers.user.delivery_chat_handler import get_chat_history

        session = db_with_roles
        session.add(DeliveryChatMessage(
            order_id=order_out_for_delivery.id,
            sender_id=111222333,
            sender_role="driver",
            message_text="I'm on my way!",
        ))
        session.add(DeliveryChatMessage(
            order_id=order_out_for_delivery.id,
            sender_id=order_out_for_delivery.buyer_id,
            sender_role="customer",
            message_text="Great, I'm waiting outside.",
        ))
        session.add(DeliveryChatMessage(
            order_id=order_out_for_delivery.id,
            sender_id=111222333,
            sender_role="driver",
            location_lat=13.75,
            location_lng=100.50,
            is_live_location=True,
            live_location_update_count=0,
        ))
        session.commit()

        history = await get_chat_history(order_out_for_delivery.id)
        assert len(history) == 3
        assert history[0]["sender_role"] == "driver"
        assert history[0]["message_text"] == "I'm on my way!"
        assert history[1]["sender_role"] == "customer"
        assert history[2]["is_live_location"] is True

    @pytest.mark.asyncio
    async def test_get_chat_history_empty(self, db_with_roles, order_out_for_delivery):
        """Empty history for order with no messages."""
        from bot.handlers.user.delivery_chat_handler import get_chat_history

        history = await get_chat_history(order_out_for_delivery.id)
        assert history == []


class TestOrderCardFields:
    """Test Card 15 specific fields on Order model."""

    def test_card_15_fields_default_null(self, db_with_roles, test_user):
        """All Card 15 fields should default to None."""
        session = db_with_roles
        order = Order(
            buyer_id=test_user.telegram_id,
            total_price=Decimal("100"),
            payment_method="cash",
            delivery_address="test",
            phone_number="+66",
            order_code="FLD001",
        )
        session.add(order)
        session.commit()
        session.refresh(order)

        assert order.customer_live_location_message_id is None
        assert order.chat_opened_at is None
        assert order.chat_closed_at is None
        assert order.chat_post_delivery_until is None

    def test_driver_live_location_fields(self, db_with_roles, test_user):
        """Driver live location fields (Card 13) should work correctly."""
        session = db_with_roles
        order = Order(
            buyer_id=test_user.telegram_id,
            total_price=Decimal("100"),
            payment_method="cash",
            delivery_address="test",
            phone_number="+66",
            order_code="FLD002",
        )
        session.add(order)
        session.flush()

        order.driver_id = 999888777
        order.driver_live_location_message_id = 54321
        session.commit()
        session.refresh(order)

        assert order.driver_id == 999888777
        assert order.driver_live_location_message_id == 54321
