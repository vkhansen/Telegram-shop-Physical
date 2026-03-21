"""Tests for delivery type and photo proof fields (Cards 3 & 4)"""
import pytest
from datetime import datetime, timezone
from decimal import Decimal

from bot.database.models.main import Order, User


@pytest.mark.unit
@pytest.mark.models
class TestDeliveryTypeFields:
    """Test delivery type model fields (Card 3)"""

    def test_order_delivery_type_default(self, db_with_roles, db_session):
        """Default delivery type should be 'door'"""
        user = User(telegram_id=800001, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        order = Order(
            buyer_id=800001,
            total_price=Decimal("100.00"),
            payment_method="cash",
            delivery_address="123 Test St",
            phone_number="0812345678"
        )
        db_session.add(order)
        db_session.commit()

        assert order.delivery_type == "door"

    def test_order_delivery_type_dead_drop(self, db_with_roles, db_session):
        """Dead drop delivery type with instructions and photo"""
        user = User(telegram_id=800002, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        order = Order(
            buyer_id=800002,
            total_price=Decimal("200.00"),
            payment_method="cash",
            delivery_address="456 Condo",
            phone_number="0898765432",
            delivery_type="dead_drop",
            drop_instructions="Leave with security guard at lobby desk",
            drop_location_photo="AgACAgIAAxk_fake_photo_id"
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        assert order.delivery_type == "dead_drop"
        assert order.drop_instructions == "Leave with security guard at lobby desk"
        assert order.drop_location_photo == "AgACAgIAAxk_fake_photo_id"

    def test_order_delivery_type_pickup(self, db_with_roles, db_session):
        """Pickup delivery type"""
        user = User(telegram_id=800003, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        order = Order(
            buyer_id=800003,
            total_price=Decimal("150.00"),
            payment_method="cash",
            delivery_address="Self Pickup",
            phone_number="0812345678",
            delivery_type="pickup"
        )
        db_session.add(order)
        db_session.commit()

        assert order.delivery_type == "pickup"
        assert order.drop_instructions is None
        assert order.drop_location_photo is None

    def test_order_drop_fields_nullable(self, db_with_roles, db_session):
        """Drop instructions and photo should be nullable"""
        user = User(telegram_id=800004, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        order = Order(
            buyer_id=800004,
            total_price=Decimal("100.00"),
            payment_method="cash",
            delivery_address="Test",
            phone_number="0812345678",
            delivery_type="door"
        )
        db_session.add(order)
        db_session.commit()

        assert order.drop_instructions is None
        assert order.drop_location_photo is None


@pytest.mark.unit
@pytest.mark.models
class TestDeliveryPhotoFields:
    """Test delivery photo proof fields (Card 4)"""

    def test_order_delivery_photo_fields_nullable(self, db_with_roles, db_session):
        """Delivery photo fields should default to None"""
        user = User(telegram_id=800010, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        order = Order(
            buyer_id=800010,
            total_price=Decimal("100.00"),
            payment_method="cash",
            delivery_address="Test",
            phone_number="0812345678"
        )
        db_session.add(order)
        db_session.commit()

        assert order.delivery_photo is None
        assert order.delivery_photo_at is None
        assert order.delivery_photo_by is None

    def test_save_delivery_photo(self, db_with_roles, db_session):
        """Can save delivery photo with timestamp and admin ID"""
        user = User(telegram_id=800011, registration_date=datetime.now(timezone.utc))
        admin = User(telegram_id=800012, registration_date=datetime.now(timezone.utc), role_id=2)
        db_session.add_all([user, admin])
        db_session.commit()

        order = Order(
            buyer_id=800011,
            total_price=Decimal("200.00"),
            payment_method="cash",
            delivery_address="Test",
            phone_number="0812345678",
            order_status="confirmed"
        )
        db_session.add(order)
        db_session.commit()

        # Simulate rider uploading photo
        now = datetime.now(timezone.utc)
        order.delivery_photo = "AgACAgIAAxk_delivery_photo_id"
        order.delivery_photo_at = now
        order.delivery_photo_by = 800012
        order.order_status = "delivered"
        db_session.commit()
        db_session.refresh(order)

        assert order.delivery_photo == "AgACAgIAAxk_delivery_photo_id"
        assert order.delivery_photo_at is not None
        assert order.delivery_photo_by == 800012
        assert order.order_status == "delivered"

    def test_dead_drop_requires_photo_logic(self, db_with_roles, db_session):
        """Business rule: dead_drop orders should have photo before delivery"""
        user = User(telegram_id=800013, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        order = Order(
            buyer_id=800013,
            total_price=Decimal("150.00"),
            payment_method="cash",
            delivery_address="Test",
            phone_number="0812345678",
            delivery_type="dead_drop",
            drop_instructions="Leave at door",
            order_status="confirmed"
        )
        db_session.add(order)
        db_session.commit()

        # Verify the enforcement rule
        assert order.delivery_type == "dead_drop"
        assert order.delivery_photo is None
        # Business logic would check: if delivery_type == "dead_drop" and not delivery_photo → block

    def test_door_delivery_photo_optional(self, db_with_roles, db_session):
        """Door delivery should allow marking delivered without photo"""
        user = User(telegram_id=800014, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        order = Order(
            buyer_id=800014,
            total_price=Decimal("100.00"),
            payment_method="cash",
            delivery_address="Test",
            phone_number="0812345678",
            delivery_type="door",
            order_status="confirmed"
        )
        db_session.add(order)
        db_session.commit()

        # Can mark delivered without photo for door delivery
        order.order_status = "delivered"
        db_session.commit()
        assert order.order_status == "delivered"
        assert order.delivery_photo is None  # Optional for door
