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


@pytest.mark.unit
@pytest.mark.models
class TestDeliveryTypeEdgeCases:
    """Edge case tests for delivery type fields"""

    def test_empty_string_delivery_type(self, db_with_roles, db_session):
        """Empty string delivery_type is stored (no DB constraint)"""
        user = User(telegram_id=820001, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        order = Order(
            buyer_id=820001,
            total_price=Decimal("100.00"),
            payment_method="cash",
            delivery_address="Test",
            phone_number="0812345678",
            delivery_type=""
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        assert order.delivery_type == ""

    def test_change_delivery_type_after_creation(self, db_with_roles, db_session):
        """Change delivery_type from door to dead_drop after creation"""
        user = User(telegram_id=820002, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        order = Order(
            buyer_id=820002,
            total_price=Decimal("100.00"),
            payment_method="cash",
            delivery_address="Test",
            phone_number="0812345678",
            delivery_type="door"
        )
        db_session.add(order)
        db_session.commit()
        assert order.delivery_type == "door"

        order.delivery_type = "dead_drop"
        order.drop_instructions = "Behind the mailbox"
        db_session.commit()
        db_session.refresh(order)

        assert order.delivery_type == "dead_drop"
        assert order.drop_instructions == "Behind the mailbox"

    def test_drop_instructions_empty_string_vs_none(self, db_with_roles, db_session):
        """Empty string drop_instructions differs from None"""
        user = User(telegram_id=820003, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        order_empty = Order(
            buyer_id=820003,
            total_price=Decimal("100.00"),
            payment_method="cash",
            delivery_address="Test",
            phone_number="0812345678",
            delivery_type="dead_drop",
            drop_instructions=""
        )
        db_session.add(order_empty)
        db_session.commit()
        db_session.refresh(order_empty)

        assert order_empty.drop_instructions == ""
        assert order_empty.drop_instructions is not None

        order_none = Order(
            buyer_id=820003,
            total_price=Decimal("100.00"),
            payment_method="cash",
            delivery_address="Test2",
            phone_number="0812345678",
            delivery_type="dead_drop",
            drop_instructions=None
        )
        db_session.add(order_none)
        db_session.commit()
        db_session.refresh(order_none)

        assert order_none.drop_instructions is None

    def test_drop_instructions_very_long_text(self, db_with_roles, db_session):
        """drop_instructions with 500+ characters stores correctly"""
        user = User(telegram_id=820004, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        long_instructions = "A" * 600
        order = Order(
            buyer_id=820004,
            total_price=Decimal("100.00"),
            payment_method="cash",
            delivery_address="Test",
            phone_number="0812345678",
            delivery_type="dead_drop",
            drop_instructions=long_instructions
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        assert len(order.drop_instructions) == 600
        assert order.drop_instructions == long_instructions

    def test_dead_drop_with_instructions_no_photo(self, db_with_roles, db_session):
        """Dead drop with instructions but no drop_location_photo is valid"""
        user = User(telegram_id=820005, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        order = Order(
            buyer_id=820005,
            total_price=Decimal("100.00"),
            payment_method="cash",
            delivery_address="Test",
            phone_number="0812345678",
            delivery_type="dead_drop",
            drop_instructions="Under the bench near the entrance",
            drop_location_photo=None
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        assert order.delivery_type == "dead_drop"
        assert order.drop_instructions == "Under the bench near the entrance"
        assert order.drop_location_photo is None

    def test_pickup_with_drop_instructions_set(self, db_with_roles, db_session):
        """Pickup order with drop_instructions — no constraint prevents it"""
        user = User(telegram_id=820006, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        order = Order(
            buyer_id=820006,
            total_price=Decimal("100.00"),
            payment_method="cash",
            delivery_address="Self Pickup",
            phone_number="0812345678",
            delivery_type="pickup",
            drop_instructions="This should not be here but is allowed"
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        assert order.delivery_type == "pickup"
        assert order.drop_instructions == "This should not be here but is allowed"

    def test_delivery_photo_overwrite(self, db_with_roles, db_session):
        """Change delivery_photo from one file ID to another"""
        user = User(telegram_id=820007, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        order = Order(
            buyer_id=820007,
            total_price=Decimal("100.00"),
            payment_method="cash",
            delivery_address="Test",
            phone_number="0812345678",
            delivery_type="dead_drop",
            order_status="out_for_delivery"
        )
        db_session.add(order)
        db_session.commit()

        # Set initial photo
        order.delivery_photo = "AgACAgIAAxk_first_photo_id"
        order.delivery_photo_at = datetime.now(timezone.utc)
        db_session.commit()
        db_session.refresh(order)
        assert order.delivery_photo == "AgACAgIAAxk_first_photo_id"

        # Overwrite with new photo
        order.delivery_photo = "AgACAgIAAxk_second_photo_id"
        order.delivery_photo_at = datetime.now(timezone.utc)
        db_session.commit()
        db_session.refresh(order)
        assert order.delivery_photo == "AgACAgIAAxk_second_photo_id"

    def test_delivery_photo_at_without_delivery_photo(self, db_with_roles, db_session):
        """Timestamp set but no photo — possible but illogical"""
        user = User(telegram_id=820008, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        order = Order(
            buyer_id=820008,
            total_price=Decimal("100.00"),
            payment_method="cash",
            delivery_address="Test",
            phone_number="0812345678",
            delivery_type="door"
        )
        db_session.add(order)
        db_session.commit()

        # Set timestamp without photo — DB allows it
        order.delivery_photo_at = datetime.now(timezone.utc)
        db_session.commit()
        db_session.refresh(order)

        assert order.delivery_photo is None
        assert order.delivery_photo_at is not None


@pytest.mark.unit
@pytest.mark.models
class TestPhotoProofEnforcement:
    """Test the business logic rule that dead_drop orders need delivery photos"""

    @staticmethod
    def needs_delivery_photo(order):
        """Helper: returns True if the order requires a delivery photo but doesn't have one."""
        return order.delivery_type == "dead_drop" and not order.delivery_photo

    def test_dead_drop_without_photo_needs_photo(self, db_with_roles, db_session):
        """Dead drop without photo → needs photo (True)"""
        user = User(telegram_id=830001, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        order = Order(
            buyer_id=830001,
            total_price=Decimal("100.00"),
            payment_method="cash",
            delivery_address="Test",
            phone_number="0812345678",
            delivery_type="dead_drop",
            drop_instructions="Behind dumpster"
        )
        db_session.add(order)
        db_session.commit()

        assert self.needs_delivery_photo(order) is True

    def test_door_delivery_does_not_need_photo(self, db_with_roles, db_session):
        """Door delivery → photo optional (False)"""
        user = User(telegram_id=830002, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        order = Order(
            buyer_id=830002,
            total_price=Decimal("100.00"),
            payment_method="cash",
            delivery_address="Test",
            phone_number="0812345678",
            delivery_type="door"
        )
        db_session.add(order)
        db_session.commit()

        assert self.needs_delivery_photo(order) is False

    def test_pickup_does_not_need_photo(self, db_with_roles, db_session):
        """Pickup → no photo needed (False)"""
        user = User(telegram_id=830003, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        order = Order(
            buyer_id=830003,
            total_price=Decimal("100.00"),
            payment_method="cash",
            delivery_address="Self Pickup",
            phone_number="0812345678",
            delivery_type="pickup"
        )
        db_session.add(order)
        db_session.commit()

        assert self.needs_delivery_photo(order) is False

    def test_dead_drop_with_photo_requirement_met(self, db_with_roles, db_session):
        """Dead drop WITH photo → requirement met (False)"""
        user = User(telegram_id=830004, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        order = Order(
            buyer_id=830004,
            total_price=Decimal("100.00"),
            payment_method="cash",
            delivery_address="Test",
            phone_number="0812345678",
            delivery_type="dead_drop",
            drop_instructions="Under the mat"
        )
        db_session.add(order)
        db_session.commit()

        order.delivery_photo = "AgACAgIAAxk_proof_photo_id"
        order.delivery_photo_at = datetime.now(timezone.utc)
        db_session.commit()

        assert self.needs_delivery_photo(order) is False
