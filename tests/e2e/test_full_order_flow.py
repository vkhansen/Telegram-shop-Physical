"""
Comprehensive E2E test suite for the Telegram shop bot.

Tests simulate the full order lifecycle using the database directly,
covering menu loading, user management, cart operations, order creation,
status workflow, delivery, payments, admin ops, referrals, and chat audit.
"""
import json
import os
import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch, MagicMock

from sqlalchemy.orm import Session

from bot.database.models.main import (
    Role, User, Categories, Goods, Order, OrderItem, CustomerInfo,
    ShoppingCart, BitcoinAddress, BotSettings, ReferenceCode,
    ReferenceCodeUsage, ReferralEarnings, DeliveryChatMessage,
    InventoryLog,
)
from bot.database.methods.inventory import (
    reserve_inventory, release_reservation, deduct_inventory, add_inventory,
)
from bot.utils.order_codes import generate_unique_order_code
from bot.utils.modifiers import calculate_item_price, validate_modifier_selection
from bot.utils.order_status import is_valid_transition, get_allowed_transitions, VALID_TRANSITIONS

from tests.e2e.menu_loader import (
    load_menu_from_file, load_menu_from_dict, validate_menu_schema, MenuValidationError,
)

# Path to sample menu JSON
SAMPLE_MENU_PATH = Path(__file__).parent / "sample_menu.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_sample_menu() -> dict:
    with open(SAMPLE_MENU_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _create_roles(session: Session) -> dict[str, Role]:
    """Create standard roles and return a name->Role mapping."""
    roles = {
        "USER": Role(name="USER", permissions=1),
        "ADMIN": Role(name="ADMIN", permissions=31),
        "OWNER": Role(name="OWNER", permissions=127),
    }
    session.add_all(roles.values())
    session.commit()
    return roles


def _create_user(session: Session, telegram_id: int, role_id: int = 1,
                 locale: str = None, referral_id: int = None) -> User:
    user = User(
        telegram_id=telegram_id,
        role_id=role_id,
        registration_date=datetime.now(timezone.utc),
        referral_id=referral_id,
        locale=locale,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def _create_customer_info(session: Session, telegram_id: int, **kwargs) -> CustomerInfo:
    ci = CustomerInfo(
        telegram_id=telegram_id,
        phone_number=kwargs.get("phone_number", "+66812345678"),
        delivery_address=kwargs.get("delivery_address", "123 Sukhumvit Soi 11, Bangkok"),
    )
    session.add(ci)
    session.commit()
    session.refresh(ci)
    return ci


# ===================================================================
# 1. TestMenuLoading
# ===================================================================

@pytest.mark.e2e
class TestMenuLoading:
    """Test JSON menu loading into the database."""

    def test_load_menu_from_file(self, db_session: Session):
        """Load the sample menu JSON and verify summary counts."""
        summary = load_menu_from_file(SAMPLE_MENU_PATH, db_session)
        db_session.commit()

        assert summary["restaurant_name"] == "Baan Thai Kitchen"
        assert summary["categories"] == 5
        assert summary["items"] >= 18  # 4+4+4+3+5 = 20

    def test_categories_created_with_sort_order(self, db_session: Session):
        """Verify categories are created with correct sort_order."""
        load_menu_from_file(SAMPLE_MENU_PATH, db_session)
        db_session.commit()

        categories = db_session.query(Categories).order_by(Categories.sort_order).all()
        assert len(categories) == 5

        expected = ["Appetizers", "Main Courses", "Noodles", "Desserts", "Drinks"]
        for cat, name in zip(categories, expected):
            assert cat.name == name

        # sort_order should be 1..5
        for i, cat in enumerate(categories, start=1):
            assert cat.sort_order == i

    def test_items_with_modifiers(self, db_session: Session):
        """Verify items carry correct modifier schemas."""
        load_menu_from_file(SAMPLE_MENU_PATH, db_session)
        db_session.commit()

        green_curry = db_session.query(Goods).filter_by(name="Green Curry").one()
        assert green_curry.price == Decimal("179.00")
        assert green_curry.modifiers is not None
        assert "protein" in green_curry.modifiers
        assert "spice" in green_curry.modifiers
        assert "rice" in green_curry.modifiers

        # Items with null modifiers
        coconut = db_session.query(Goods).filter_by(name="Fresh Coconut").one()
        assert coconut.modifiers is None

    def test_clear_and_reload(self, db_session: Session):
        """Test clearing existing data and reloading."""
        # First load
        load_menu_from_file(SAMPLE_MENU_PATH, db_session)
        db_session.commit()

        first_count = db_session.query(Goods).count()
        assert first_count > 0

        # Reload with clear
        summary = load_menu_from_file(SAMPLE_MENU_PATH, db_session, clear_existing=True)
        db_session.commit()

        second_count = db_session.query(Goods).count()
        assert second_count == first_count
        assert summary["categories"] == 5

    def test_validation_catches_missing_keys(self):
        """Schema validation detects missing required keys."""
        bad_data = {"restaurant_name": "Test"}
        errors = validate_menu_schema(bad_data)
        assert any("categories" in e for e in errors)

    def test_validation_catches_bad_modifier(self):
        """Schema validation detects invalid modifier type."""
        data = {
            "restaurant_name": "Test",
            "categories": [{
                "name": "Cat",
                "sort_order": 1,
                "items": [{
                    "name": "Item",
                    "description": "Desc",
                    "price": 100,
                    "stock_quantity": 10,
                    "modifiers": {
                        "grp": {
                            "label": "G",
                            "type": "invalid_type",
                            "required": True,
                            "options": [{"id": "a", "label": "A", "price": 0}]
                        }
                    }
                }]
            }]
        }
        errors = validate_menu_schema(data)
        assert any("type" in e and "single" in e for e in errors)

    def test_load_raises_on_invalid_schema(self, db_session: Session):
        """load_menu_from_dict raises MenuValidationError on bad data."""
        with pytest.raises(MenuValidationError):
            load_menu_from_dict({"bad": True}, db_session)

    def test_stock_quantities_loaded(self, db_session: Session):
        """Verify stock quantities are loaded from JSON."""
        load_menu_from_file(SAMPLE_MENU_PATH, db_session)
        db_session.commit()

        pad_thai = db_session.query(Goods).filter_by(name="Pad Thai").one()
        assert pad_thai.stock_quantity == 90
        assert pad_thai.reserved_quantity == 0
        assert pad_thai.available_quantity == 90


# ===================================================================
# 2. TestUserRegistration
# ===================================================================

@pytest.mark.e2e
class TestUserRegistration:
    """Test user creation and role assignment."""

    def test_create_customer_user(self, db_with_roles: Session):
        """Create a customer with USER role."""
        user = _create_user(db_with_roles, telegram_id=1001, role_id=1)
        assert user.telegram_id == 1001
        assert user.role_id == 1
        assert user.is_banned is False
        assert user.locale is None

    def test_create_admin_user(self, db_with_roles: Session):
        """Create an admin user."""
        user = _create_user(db_with_roles, telegram_id=2001, role_id=2)
        assert user.role_id == 2

        role = db_with_roles.query(Role).filter_by(id=2).one()
        assert role.name == "ADMIN"

    def test_create_driver_user(self, db_with_roles: Session):
        """Create a driver (uses USER role)."""
        user = _create_user(db_with_roles, telegram_id=3001, role_id=1)
        assert user.role_id == 1

    def test_locale_setting(self, db_with_roles: Session):
        """Verify per-user locale is stored."""
        user_th = _create_user(db_with_roles, telegram_id=4001, locale="th")
        user_en = _create_user(db_with_roles, telegram_id=4002, locale="en")

        assert user_th.locale == "th"
        assert user_en.locale == "en"

    def test_referral_relationship(self, db_with_roles: Session):
        """User can have a referral_id pointing to another user."""
        referrer = _create_user(db_with_roles, telegram_id=5001)
        referred = _create_user(db_with_roles, telegram_id=5002, referral_id=referrer.telegram_id)

        assert referred.referral_id == referrer.telegram_id

    def test_roles_have_correct_permissions(self, db_with_roles: Session):
        """Verify role permission bitmasks."""
        user_role = db_with_roles.query(Role).filter_by(name="USER").one()
        admin_role = db_with_roles.query(Role).filter_by(name="ADMIN").one()
        owner_role = db_with_roles.query(Role).filter_by(name="OWNER").one()

        assert user_role.has_permission(1)  # USE
        assert admin_role.has_permission(16)  # SHOP_MANAGE
        assert owner_role.has_permission(64)  # OWN


# ===================================================================
# 3. TestShoppingCart
# ===================================================================

@pytest.mark.e2e
class TestShoppingCart:
    """Test cart operations including modifiers and price calculation."""

    def _setup_menu(self, session: Session) -> dict:
        load_menu_from_file(SAMPLE_MENU_PATH, session)
        session.commit()
        return _load_sample_menu()

    def test_add_item_to_cart(self, db_with_roles: Session):
        """Add a simple item to cart."""
        self._setup_menu(db_with_roles)
        user = _create_user(db_with_roles, telegram_id=6001)

        cart_item = ShoppingCart(
            user_id=user.telegram_id,
            item_name="Pad Thai",
            quantity=2,
        )
        db_with_roles.add(cart_item)
        db_with_roles.commit()

        cart = db_with_roles.query(ShoppingCart).filter_by(user_id=user.telegram_id).all()
        assert len(cart) == 1
        assert cart[0].item_name == "Pad Thai"
        assert cart[0].quantity == 2

    def test_add_item_with_modifiers(self, db_with_roles: Session):
        """Add an item with selected modifiers."""
        self._setup_menu(db_with_roles)
        user = _create_user(db_with_roles, telegram_id=6002)

        selected = {"protein": "shrimp", "extras": ["extra_egg", "extra_peanuts"]}
        cart_item = ShoppingCart(
            user_id=user.telegram_id,
            item_name="Pad Thai",
            quantity=1,
            selected_modifiers=selected,
        )
        db_with_roles.add(cart_item)
        db_with_roles.commit()
        db_with_roles.refresh(cart_item)

        assert cart_item.selected_modifiers == selected

    def test_price_calculation_with_modifiers(self, db_with_roles: Session):
        """Verify price calculation includes modifier surcharges."""
        self._setup_menu(db_with_roles)

        pad_thai = db_with_roles.query(Goods).filter_by(name="Pad Thai").one()
        # base=149, shrimp=+30, extra_egg=+15, extra_peanuts=+10 = 204
        selected = {"protein": "shrimp", "extras": ["extra_egg", "extra_peanuts"]}
        total = calculate_item_price(pad_thai.price, pad_thai.modifiers, selected)
        assert total == Decimal("204.00")

    def test_price_with_no_modifiers(self, db_with_roles: Session):
        """Items without modifiers just use base price."""
        self._setup_menu(db_with_roles)

        coconut = db_with_roles.query(Goods).filter_by(name="Fresh Coconut").one()
        total = calculate_item_price(coconut.price, coconut.modifiers, None)
        assert total == Decimal("49.00")

    def test_remove_item_from_cart(self, db_with_roles: Session):
        """Remove an item from the cart."""
        self._setup_menu(db_with_roles)
        user = _create_user(db_with_roles, telegram_id=6003)

        cart_item = ShoppingCart(user_id=user.telegram_id, item_name="Thai Iced Tea", quantity=3)
        db_with_roles.add(cart_item)
        db_with_roles.commit()

        db_with_roles.delete(cart_item)
        db_with_roles.commit()

        remaining = db_with_roles.query(ShoppingCart).filter_by(user_id=user.telegram_id).count()
        assert remaining == 0

    def test_update_quantity(self, db_with_roles: Session):
        """Update quantity of a cart item."""
        self._setup_menu(db_with_roles)
        user = _create_user(db_with_roles, telegram_id=6004)

        cart_item = ShoppingCart(user_id=user.telegram_id, item_name="Green Curry", quantity=1)
        db_with_roles.add(cart_item)
        db_with_roles.commit()

        cart_item.quantity = 5
        db_with_roles.commit()
        db_with_roles.refresh(cart_item)

        assert cart_item.quantity == 5

    def test_cart_total_calculation(self, db_with_roles: Session):
        """Calculate total across multiple cart items with modifiers."""
        self._setup_menu(db_with_roles)
        user = _create_user(db_with_roles, telegram_id=6005)

        # Item 1: Pad Thai x2 with shrimp (+30) = (149+30)*2 = 358
        c1 = ShoppingCart(
            user_id=user.telegram_id, item_name="Pad Thai", quantity=2,
            selected_modifiers={"protein": "shrimp"},
        )
        db_with_roles.add(c1)
        db_with_roles.flush()

        # Item 2: Mango Sticky Rice x1 no mods = 99
        c2 = ShoppingCart(
            user_id=user.telegram_id, item_name="Mango Sticky Rice", quantity=1,
        )
        db_with_roles.add(c2)
        db_with_roles.commit()

        # Calculate total
        cart_items = db_with_roles.query(ShoppingCart).filter_by(user_id=user.telegram_id).all()
        total = Decimal("0")
        for ci in cart_items:
            goods = db_with_roles.query(Goods).filter_by(name=ci.item_name).one()
            unit_price = calculate_item_price(goods.price, goods.modifiers, ci.selected_modifiers)
            total += unit_price * ci.quantity

        assert total == Decimal("457.00")


# ===================================================================
# 4. TestOrderCreation
# ===================================================================

@pytest.mark.e2e
class TestOrderCreation:
    """Test order placement from cart."""

    def _setup(self, session: Session):
        load_menu_from_file(SAMPLE_MENU_PATH, session)
        session.commit()

    def test_create_order_from_cart(self, db_with_roles: Session):
        """Create an order and verify code, status, items."""
        self._setup(db_with_roles)
        user = _create_user(db_with_roles, telegram_id=7001)

        order_code = generate_unique_order_code(db_with_roles)
        order = Order(
            buyer_id=user.telegram_id,
            total_price=Decimal("179.00"),
            payment_method="cash",
            delivery_address="55 Sukhumvit Soi 24",
            phone_number="+66891234567",
            order_status="pending",
            order_code=order_code,
        )
        db_with_roles.add(order)
        db_with_roles.flush()

        item = OrderItem(
            order_id=order.id,
            item_name="Green Curry",
            price=Decimal("179.00"),
            quantity=1,
            selected_modifiers={"protein": "chicken", "spice": "medium"},
        )
        db_with_roles.add(item)
        db_with_roles.commit()

        assert len(order.order_code) == 6
        assert order.order_status == "pending"
        assert len(order.items) == 1

    def test_order_code_uniqueness(self, db_with_roles: Session):
        """Order codes must be unique."""
        self._setup(db_with_roles)
        user = _create_user(db_with_roles, telegram_id=7002)

        codes = set()
        for _ in range(20):
            code = generate_unique_order_code(db_with_roles)
            assert code not in codes
            codes.add(code)

    def test_inventory_reservation_on_order(self, db_with_roles: Session):
        """Reserve inventory when order is placed."""
        self._setup(db_with_roles)
        user = _create_user(db_with_roles, telegram_id=7003)

        order = Order(
            buyer_id=user.telegram_id,
            total_price=Decimal("298.00"),
            payment_method="cash",
            delivery_address="Test",
            phone_number="+66800000000",
            order_status="pending",
            order_code=generate_unique_order_code(db_with_roles),
        )
        db_with_roles.add(order)
        db_with_roles.flush()

        oi = OrderItem(order_id=order.id, item_name="Pad Thai", price=Decimal("149.00"), quantity=2)
        db_with_roles.add(oi)
        db_with_roles.commit()

        items = [{"item_name": "Pad Thai", "quantity": 2}]
        success, msg = reserve_inventory(order.id, items, "cash", db_with_roles)
        db_with_roles.commit()

        assert success is True
        db_with_roles.refresh(order)
        assert order.order_status == "reserved"

        pad_thai = db_with_roles.query(Goods).filter_by(name="Pad Thai").one()
        assert pad_thai.reserved_quantity == 2

    def test_gps_coordinates_stored(self, db_with_roles: Session):
        """GPS lat/lng are stored on the order."""
        self._setup(db_with_roles)
        user = _create_user(db_with_roles, telegram_id=7004)

        order = Order(
            buyer_id=user.telegram_id,
            total_price=Decimal("100.00"),
            payment_method="cash",
            delivery_address="GPS Test",
            phone_number="+66800000000",
            order_status="pending",
            order_code=generate_unique_order_code(db_with_roles),
            latitude=13.7563,
            longitude=100.5018,
            google_maps_link="https://maps.google.com/?q=13.7563,100.5018",
        )
        db_with_roles.add(order)
        db_with_roles.commit()
        db_with_roles.refresh(order)

        assert order.latitude == pytest.approx(13.7563, abs=1e-4)
        assert order.longitude == pytest.approx(100.5018, abs=1e-4)
        assert "maps.google.com" in order.google_maps_link

    def test_delivery_types(self, db_with_roles: Session):
        """Test door, dead_drop, and pickup delivery types."""
        self._setup(db_with_roles)
        user = _create_user(db_with_roles, telegram_id=7005)

        for dtype in ("door", "dead_drop", "pickup"):
            order = Order(
                buyer_id=user.telegram_id,
                total_price=Decimal("50.00"),
                payment_method="cash",
                delivery_address="Addr",
                phone_number="+66800000000",
                order_status="pending",
                order_code=generate_unique_order_code(db_with_roles),
                delivery_type=dtype,
            )
            db_with_roles.add(order)

        db_with_roles.commit()

        orders = db_with_roles.query(Order).filter_by(buyer_id=user.telegram_id).all()
        types = {o.delivery_type for o in orders}
        assert types == {"door", "dead_drop", "pickup"}

    def test_payment_method_selection(self, db_with_roles: Session):
        """Different payment methods can be set."""
        self._setup(db_with_roles)
        user = _create_user(db_with_roles, telegram_id=7006)

        for method in ("cash", "bitcoin", "promptpay"):
            order = Order(
                buyer_id=user.telegram_id,
                total_price=Decimal("100.00"),
                payment_method=method,
                delivery_address="Addr",
                phone_number="+66800000000",
                order_status="pending",
                order_code=generate_unique_order_code(db_with_roles),
            )
            db_with_roles.add(order)

        db_with_roles.commit()

        methods = {
            o.payment_method
            for o in db_with_roles.query(Order).filter_by(buyer_id=user.telegram_id).all()
        }
        assert methods == {"cash", "bitcoin", "promptpay"}


# ===================================================================
# 5. TestOrderStatusWorkflow
# ===================================================================

@pytest.mark.e2e
class TestOrderStatusWorkflow:
    """Test the full status lifecycle and transition validation."""

    def _setup_order(self, session: Session, status: str = "pending") -> Order:
        load_menu_from_file(SAMPLE_MENU_PATH, session, clear_existing=True)
        session.commit()
        user = _create_user(session, telegram_id=8001)

        order = Order(
            buyer_id=user.telegram_id,
            total_price=Decimal("149.00"),
            payment_method="cash",
            delivery_address="Test",
            phone_number="+66800000000",
            order_status=status,
            order_code=generate_unique_order_code(session),
        )
        session.add(order)
        session.flush()

        oi = OrderItem(order_id=order.id, item_name="Pad Thai", price=Decimal("149.00"), quantity=1)
        session.add(oi)
        session.commit()
        return order

    def test_full_happy_path(self, db_with_roles: Session):
        """pending -> reserved -> confirmed -> preparing -> ready -> out_for_delivery -> delivered"""
        order = self._setup_order(db_with_roles)

        path = ["reserved", "confirmed", "preparing", "ready", "out_for_delivery", "delivered"]
        for next_status in path:
            assert is_valid_transition(order.order_status, next_status)
            order.order_status = next_status

        db_with_roles.commit()
        assert order.order_status == "delivered"

    def test_invalid_transition_rejected(self, db_with_roles: Session):
        """Cannot skip statuses (e.g., pending -> delivered)."""
        assert not is_valid_transition("pending", "delivered")
        assert not is_valid_transition("pending", "preparing")
        assert not is_valid_transition("confirmed", "delivered")

    def test_cancellation_at_each_stage(self, db_with_roles: Session):
        """Order can be cancelled from most statuses."""
        cancellable = ["pending", "reserved", "confirmed", "preparing", "ready", "out_for_delivery"]
        for status in cancellable:
            assert is_valid_transition(status, "cancelled"), f"Should be cancellable from {status}"

    def test_terminal_states(self, db_with_roles: Session):
        """delivered, cancelled, expired have no valid transitions."""
        for terminal in ("delivered", "cancelled", "expired"):
            assert get_allowed_transitions(terminal) == set()

    def test_inventory_release_on_cancel(self, db_with_roles: Session):
        """Cancelling a reserved order releases inventory."""
        order = self._setup_order(db_with_roles)

        items = [{"item_name": "Pad Thai", "quantity": 1}]
        success, _ = reserve_inventory(order.id, items, "cash", db_with_roles)
        db_with_roles.commit()
        assert success

        pad_thai = db_with_roles.query(Goods).filter_by(name="Pad Thai").one()
        assert pad_thai.reserved_quantity == 1

        with patch("bot.database.methods.inventory.get_metrics", return_value=None):
            success, _ = release_reservation(order.id, "Customer cancelled", db_with_roles)
        db_with_roles.commit()

        assert success
        db_with_roles.refresh(pad_thai)
        assert pad_thai.reserved_quantity == 0


# ===================================================================
# 6. TestDeliveryFlow
# ===================================================================

@pytest.mark.e2e
class TestDeliveryFlow:
    """Test delivery mechanics: zones, fees, drivers, photo proof."""

    def _setup(self, session: Session) -> tuple[User, Order]:
        load_menu_from_file(SAMPLE_MENU_PATH, session, clear_existing=True)
        session.commit()

        user = _create_user(session, telegram_id=9001)
        order = Order(
            buyer_id=user.telegram_id,
            total_price=Decimal("200.00"),
            payment_method="cash",
            delivery_address="99 Ratchadaphisek",
            phone_number="+66800000000",
            order_status="pending",
            order_code=generate_unique_order_code(session),
            latitude=13.7563,
            longitude=100.5018,
        )
        session.add(order)
        session.flush()
        oi = OrderItem(order_id=order.id, item_name="Green Curry", price=Decimal("200.00"), quantity=1)
        session.add(oi)
        session.commit()
        return user, order

    def test_delivery_zone_assignment(self, db_with_roles: Session):
        """Delivery zone and fee can be set on order."""
        _, order = self._setup(db_with_roles)

        order.delivery_zone = "zone_a"
        order.delivery_fee = Decimal("30.00")
        db_with_roles.commit()
        db_with_roles.refresh(order)

        assert order.delivery_zone == "zone_a"
        assert order.delivery_fee == Decimal("30.00")

    def test_driver_assignment(self, db_with_roles: Session):
        """A driver can be assigned to an order."""
        _, order = self._setup(db_with_roles)
        driver = _create_user(db_with_roles, telegram_id=9100)

        order.driver_id = driver.telegram_id
        order.order_status = "out_for_delivery"
        db_with_roles.commit()
        db_with_roles.refresh(order)

        assert order.driver_id == driver.telegram_id

    def test_dead_drop_photo_proof(self, db_with_roles: Session):
        """Dead drop orders can have photo proof."""
        _, order = self._setup(db_with_roles)

        order.delivery_type = "dead_drop"
        order.drop_instructions = "Behind the bench near 7-Eleven"
        order.drop_latitude = 13.7500
        order.drop_longitude = 100.4900
        order.drop_media = [
            {"file_id": "photo_abc123", "type": "photo"},
            {"file_id": "video_def456", "type": "video"},
        ]
        db_with_roles.commit()
        db_with_roles.refresh(order)

        assert order.delivery_type == "dead_drop"
        assert len(order.drop_media) == 2

    def test_delivery_photo_proof(self, db_with_roles: Session):
        """Delivery photo is recorded when package is delivered."""
        _, order = self._setup(db_with_roles)
        driver = _create_user(db_with_roles, telegram_id=9200)

        order.driver_id = driver.telegram_id
        order.delivery_photo = "file_id_delivery_proof"
        order.delivery_photo_at = datetime.now(timezone.utc)
        order.delivery_photo_by = driver.telegram_id
        db_with_roles.commit()
        db_with_roles.refresh(order)

        assert order.delivery_photo == "file_id_delivery_proof"
        assert order.delivery_photo_by == driver.telegram_id

    def test_chat_session_lifecycle(self, db_with_roles: Session):
        """Chat session open/close timestamps are recorded."""
        _, order = self._setup(db_with_roles)

        now = datetime.now(timezone.utc)
        order.chat_opened_at = now
        order.chat_post_delivery_until = now + timedelta(minutes=30)
        db_with_roles.commit()

        db_with_roles.refresh(order)
        assert order.chat_opened_at is not None
        assert order.chat_post_delivery_until > order.chat_opened_at

        # Close chat
        order.chat_closed_at = now + timedelta(minutes=45)
        db_with_roles.commit()
        db_with_roles.refresh(order)
        assert order.chat_closed_at is not None


# ===================================================================
# 7. TestPaymentMethods
# ===================================================================

@pytest.mark.e2e
class TestPaymentMethods:
    """Test different payment flows."""

    def _make_order(self, session: Session, method: str, **kwargs) -> Order:
        load_menu_from_file(SAMPLE_MENU_PATH, session, clear_existing=True)
        session.commit()
        user = _create_user(session, telegram_id=10001)

        order = Order(
            buyer_id=user.telegram_id,
            total_price=Decimal("250.00"),
            payment_method=method,
            delivery_address="Payment Test",
            phone_number="+66800000000",
            order_status="pending",
            order_code=generate_unique_order_code(session),
            **kwargs,
        )
        session.add(order)
        session.flush()
        oi = OrderItem(order_id=order.id, item_name="Pad Thai", price=Decimal("149.00"), quantity=1)
        session.add(oi)
        session.commit()
        return order

    def test_cash_on_delivery(self, db_with_roles: Session):
        """Cash orders need no extra fields."""
        order = self._make_order(db_with_roles, "cash")
        assert order.payment_method == "cash"
        assert order.bitcoin_address is None
        assert order.payment_receipt_photo is None

    def test_promptpay_with_receipt(self, db_with_roles: Session):
        """PromptPay orders store receipt photo and verification."""
        order = self._make_order(db_with_roles, "promptpay")
        admin = _create_user(db_with_roles, telegram_id=10002, role_id=2)

        order.payment_receipt_photo = "file_id_promptpay_slip"
        order.payment_verified_by = admin.telegram_id
        order.payment_verified_at = datetime.now(timezone.utc)
        db_with_roles.commit()
        db_with_roles.refresh(order)

        assert order.payment_receipt_photo == "file_id_promptpay_slip"
        assert order.payment_verified_by == admin.telegram_id

    def test_bitcoin_address_assignment(self, db_with_roles: Session):
        """Bitcoin orders get a BTC address assigned."""
        btc = BitcoinAddress(address="bc1qexampleaddress12345678901234567890")
        db_with_roles.add(btc)
        db_with_roles.commit()

        order = self._make_order(db_with_roles, "bitcoin", bitcoin_address=btc.address)

        # Mark address as used
        btc.is_used = True
        btc.used_by = order.buyer_id
        btc.used_at = datetime.now(timezone.utc)
        btc.order_id = order.id
        db_with_roles.commit()

        db_with_roles.refresh(btc)
        assert btc.is_used is True
        assert btc.order_id == order.id
        assert order.bitcoin_address == btc.address


# ===================================================================
# 8. TestAdminOperations
# ===================================================================

@pytest.mark.e2e
class TestAdminOperations:
    """Test admin features: CRUD, stock, order management, bans."""

    def test_product_crud(self, db_with_roles: Session):
        """Admin can create, read, update, delete products."""
        cat = Categories(name="Admin Test Cat", sort_order=99)
        db_with_roles.add(cat)
        db_with_roles.flush()

        # Create
        goods = Goods(
            name="Admin Item",
            price=Decimal("55.00"),
            description="Created by admin",
            category_name="Admin Test Cat",
            stock_quantity=20,
        )
        db_with_roles.add(goods)
        db_with_roles.commit()

        # Read
        fetched = db_with_roles.query(Goods).filter_by(name="Admin Item").one()
        assert fetched.price == Decimal("55.00")

        # Update
        fetched.price = Decimal("65.00")
        fetched.description = "Updated by admin"
        db_with_roles.commit()
        db_with_roles.refresh(fetched)
        assert fetched.price == Decimal("65.00")

        # Delete
        db_with_roles.delete(fetched)
        db_with_roles.commit()
        assert db_with_roles.query(Goods).filter_by(name="Admin Item").first() is None

    def test_category_management(self, db_with_roles: Session):
        """Admin can create and reorder categories."""
        cats = [
            Categories(name="Cat A", sort_order=3),
            Categories(name="Cat B", sort_order=1),
            Categories(name="Cat C", sort_order=2),
        ]
        db_with_roles.add_all(cats)
        db_with_roles.commit()

        ordered = db_with_roles.query(Categories).order_by(Categories.sort_order).all()
        assert [c.name for c in ordered] == ["Cat B", "Cat C", "Cat A"]

        # Reorder
        for c in ordered:
            if c.name == "Cat A":
                c.sort_order = 1
            elif c.name == "Cat B":
                c.sort_order = 3
        db_with_roles.commit()

        reordered = db_with_roles.query(Categories).order_by(Categories.sort_order).all()
        assert reordered[0].name == "Cat A"

    def test_stock_management(self, db_with_roles: Session):
        """Admin can add stock via add_inventory."""
        cat = Categories(name="Stock Cat", sort_order=1)
        db_with_roles.add(cat)
        db_with_roles.flush()

        goods = Goods(name="Stock Item", price=Decimal("10.00"), description="d",
                      category_name="Stock Cat", stock_quantity=10)
        db_with_roles.add(goods)
        db_with_roles.commit()

        success, _ = add_inventory("Stock Item", 25, admin_id=None, session=db_with_roles)
        db_with_roles.commit()

        assert success
        db_with_roles.refresh(goods)
        assert goods.stock_quantity == 35

    def test_order_status_change_by_admin(self, db_with_roles: Session):
        """Admin can move order through statuses."""
        load_menu_from_file(SAMPLE_MENU_PATH, db_with_roles, clear_existing=True)
        db_with_roles.commit()
        user = _create_user(db_with_roles, telegram_id=11001)
        admin = _create_user(db_with_roles, telegram_id=11002, role_id=2)

        order = Order(
            buyer_id=user.telegram_id,
            total_price=Decimal("100.00"),
            payment_method="cash",
            delivery_address="Admin test",
            phone_number="+66800000000",
            order_status="pending",
            order_code=generate_unique_order_code(db_with_roles),
        )
        db_with_roles.add(order)
        db_with_roles.flush()
        oi = OrderItem(order_id=order.id, item_name="Thai Iced Tea", price=Decimal("59.00"), quantity=1)
        db_with_roles.add(oi)
        db_with_roles.commit()

        # Reserve
        items = [{"item_name": "Thai Iced Tea", "quantity": 1}]
        reserve_inventory(order.id, items, "cash", db_with_roles)
        db_with_roles.commit()

        # Confirm + deduct
        order.order_status = "confirmed"
        db_with_roles.commit()

        with patch("bot.database.methods.inventory.get_metrics", return_value=None):
            success, _ = deduct_inventory(order.id, admin.telegram_id, db_with_roles)
        db_with_roles.commit()
        assert success

    def test_user_ban_unban(self, db_with_roles: Session):
        """Admin can ban and unban a user."""
        user = _create_user(db_with_roles, telegram_id=11003)
        admin = _create_user(db_with_roles, telegram_id=11004, role_id=2)

        # Ban
        user.is_banned = True
        user.banned_at = datetime.now(timezone.utc)
        user.banned_by = admin.telegram_id
        user.ban_reason = "Spam"
        db_with_roles.commit()
        db_with_roles.refresh(user)

        assert user.is_banned is True
        assert user.ban_reason == "Spam"

        # Unban
        user.is_banned = False
        user.banned_at = None
        user.banned_by = None
        user.ban_reason = None
        db_with_roles.commit()
        db_with_roles.refresh(user)

        assert user.is_banned is False


# ===================================================================
# 9. TestReferralSystem
# ===================================================================

@pytest.mark.e2e
class TestReferralSystem:
    """Test referral code creation, usage, and earnings."""

    def test_reference_code_creation(self, db_with_roles: Session):
        """Create a reference code."""
        admin = _create_user(db_with_roles, telegram_id=12001, role_id=2)

        ref = ReferenceCode(
            code="TESTAB",
            created_by=admin.telegram_id,
            max_uses=10,
            note="E2E test code",
            is_admin_code=True,
        )
        db_with_roles.add(ref)
        db_with_roles.commit()
        db_with_roles.refresh(ref)

        assert ref.code == "TESTAB"
        assert ref.is_active is True
        assert ref.current_uses == 0

    def test_code_usage(self, db_with_roles: Session):
        """Record code usage by a new user."""
        admin = _create_user(db_with_roles, telegram_id=12002, role_id=2)
        ref = ReferenceCode(code="USE123", created_by=admin.telegram_id, max_uses=5, is_admin_code=True)
        db_with_roles.add(ref)
        db_with_roles.commit()

        new_user = _create_user(db_with_roles, telegram_id=12003, referral_id=admin.telegram_id)
        usage = ReferenceCodeUsage(code="USE123", used_by=new_user.telegram_id)
        db_with_roles.add(usage)

        ref.current_uses += 1
        db_with_roles.commit()

        db_with_roles.refresh(ref)
        assert ref.current_uses == 1

    def test_bonus_calculation(self, db_with_roles: Session):
        """Referral earnings are tracked correctly."""
        referrer = _create_user(db_with_roles, telegram_id=12010)
        referred = _create_user(db_with_roles, telegram_id=12011, referral_id=referrer.telegram_id)

        # Simulate an order of 500 THB with 5% referral bonus = 25 THB
        earning = ReferralEarnings(
            referrer_id=referrer.telegram_id,
            referral_id=referred.telegram_id,
            amount=Decimal("25.00"),
            original_amount=Decimal("500.00"),
        )
        db_with_roles.add(earning)
        db_with_roles.commit()

        total = db_with_roles.query(
            ReferralEarnings
        ).filter_by(referrer_id=referrer.telegram_id).all()

        assert len(total) == 1
        assert total[0].amount == Decimal("25.00")

    def test_earnings_tracking_multiple(self, db_with_roles: Session):
        """Multiple referral earnings accumulate."""
        referrer = _create_user(db_with_roles, telegram_id=12020)
        r1 = _create_user(db_with_roles, telegram_id=12021, referral_id=referrer.telegram_id)
        r2 = _create_user(db_with_roles, telegram_id=12022, referral_id=referrer.telegram_id)

        db_with_roles.add(ReferralEarnings(
            referrer_id=referrer.telegram_id, referral_id=r1.telegram_id,
            amount=Decimal("10.00"), original_amount=Decimal("200.00"),
        ))
        db_with_roles.add(ReferralEarnings(
            referrer_id=referrer.telegram_id, referral_id=r2.telegram_id,
            amount=Decimal("30.00"), original_amount=Decimal("600.00"),
        ))
        db_with_roles.commit()

        from sqlalchemy import func as sqlfunc
        total_earned = db_with_roles.query(
            sqlfunc.sum(ReferralEarnings.amount)
        ).filter_by(referrer_id=referrer.telegram_id).scalar()

        assert total_earned == Decimal("40.00")

    def test_bonus_applied_to_order(self, db_with_roles: Session):
        """Bonus balance can be applied to an order."""
        load_menu_from_file(SAMPLE_MENU_PATH, db_with_roles, clear_existing=True)
        db_with_roles.commit()
        user = _create_user(db_with_roles, telegram_id=12030)
        ci = _create_customer_info(db_with_roles, user.telegram_id)
        ci.bonus_balance = Decimal("50.00")
        db_with_roles.commit()

        order = Order(
            buyer_id=user.telegram_id,
            total_price=Decimal("149.00"),
            bonus_applied=Decimal("50.00"),
            payment_method="cash",
            delivery_address="Bonus test",
            phone_number="+66800000000",
            order_status="pending",
            order_code=generate_unique_order_code(db_with_roles),
        )
        db_with_roles.add(order)
        db_with_roles.commit()

        # Deduct bonus from customer
        ci.bonus_balance -= order.bonus_applied
        db_with_roles.commit()
        db_with_roles.refresh(ci)

        assert ci.bonus_balance == Decimal("0.00")
        assert order.bonus_applied == Decimal("50.00")


# ===================================================================
# 10. TestDeliveryChatAudit
# ===================================================================

@pytest.mark.e2e
class TestDeliveryChatAudit:
    """Test delivery chat message recording and retrieval."""

    def _setup_order_with_driver(self, session: Session) -> tuple[Order, User, User]:
        load_menu_from_file(SAMPLE_MENU_PATH, session, clear_existing=True)
        session.commit()

        customer = _create_user(session, telegram_id=13001)
        driver = _create_user(session, telegram_id=13002)

        order = Order(
            buyer_id=customer.telegram_id,
            total_price=Decimal("179.00"),
            payment_method="cash",
            delivery_address="Chat test",
            phone_number="+66800000000",
            order_status="out_for_delivery",
            order_code=generate_unique_order_code(session),
            driver_id=driver.telegram_id,
            chat_opened_at=datetime.now(timezone.utc),
        )
        session.add(order)
        session.flush()
        oi = OrderItem(order_id=order.id, item_name="Green Curry", price=Decimal("179.00"), quantity=1)
        session.add(oi)
        session.commit()
        return order, customer, driver

    def test_text_message_recording(self, db_with_roles: Session):
        """Record a text message from driver."""
        order, customer, driver = self._setup_order_with_driver(db_with_roles)

        msg = DeliveryChatMessage(
            order_id=order.id,
            sender_id=driver.telegram_id,
            sender_role="driver",
            message_text="I'm at the lobby, where are you?",
            telegram_message_id=100,
        )
        db_with_roles.add(msg)
        db_with_roles.commit()

        msgs = db_with_roles.query(DeliveryChatMessage).filter_by(order_id=order.id).all()
        assert len(msgs) == 1
        assert msgs[0].message_text == "I'm at the lobby, where are you?"
        assert msgs[0].sender_role == "driver"

    def test_photo_message_recording(self, db_with_roles: Session):
        """Record a photo message from customer."""
        order, customer, driver = self._setup_order_with_driver(db_with_roles)

        msg = DeliveryChatMessage(
            order_id=order.id,
            sender_id=customer.telegram_id,
            sender_role="customer",
            photo_file_id="AgACAgIAAxkBAAI_photo_123",
            telegram_message_id=101,
        )
        db_with_roles.add(msg)
        db_with_roles.commit()

        msgs = db_with_roles.query(DeliveryChatMessage).filter_by(
            order_id=order.id, sender_role="customer"
        ).all()
        assert len(msgs) == 1
        assert msgs[0].photo_file_id is not None

    def test_location_message_recording(self, db_with_roles: Session):
        """Record a static location share."""
        order, customer, driver = self._setup_order_with_driver(db_with_roles)

        msg = DeliveryChatMessage(
            order_id=order.id,
            sender_id=driver.telegram_id,
            sender_role="driver",
            location_lat=13.7563,
            location_lng=100.5018,
            is_live_location=False,
            telegram_message_id=102,
        )
        db_with_roles.add(msg)
        db_with_roles.commit()

        msgs = db_with_roles.query(DeliveryChatMessage).filter_by(order_id=order.id).all()
        loc_msg = [m for m in msgs if m.location_lat is not None][0]
        assert loc_msg.location_lat == pytest.approx(13.7563, abs=1e-4)
        assert loc_msg.is_live_location is False

    def test_live_location_tracking(self, db_with_roles: Session):
        """Record live location updates with update counter."""
        order, customer, driver = self._setup_order_with_driver(db_with_roles)

        for i in range(3):
            msg = DeliveryChatMessage(
                order_id=order.id,
                sender_id=driver.telegram_id,
                sender_role="driver",
                location_lat=13.7563 + i * 0.001,
                location_lng=100.5018 + i * 0.001,
                is_live_location=True,
                live_location_update_count=i + 1,
                telegram_message_id=200 + i,
            )
            db_with_roles.add(msg)

        db_with_roles.commit()

        live_msgs = db_with_roles.query(DeliveryChatMessage).filter_by(
            order_id=order.id, is_live_location=True
        ).order_by(DeliveryChatMessage.live_location_update_count).all()

        assert len(live_msgs) == 3
        assert live_msgs[0].live_location_update_count == 1
        assert live_msgs[2].live_location_update_count == 3

    def test_chat_history_retrieval(self, db_with_roles: Session):
        """Retrieve full chat history for an order in chronological order."""
        order, customer, driver = self._setup_order_with_driver(db_with_roles)

        msgs_data = [
            ("driver", "On my way!", None),
            ("customer", "Okay, I'm waiting", None),
            ("driver", None, "AgACAgIAAxkBAAI_photo_456"),
            ("customer", "Thanks, got it!", None),
        ]

        for i, (role, text, photo) in enumerate(msgs_data):
            sender = driver.telegram_id if role == "driver" else customer.telegram_id
            msg = DeliveryChatMessage(
                order_id=order.id,
                sender_id=sender,
                sender_role=role,
                message_text=text,
                photo_file_id=photo,
                telegram_message_id=300 + i,
            )
            db_with_roles.add(msg)

        db_with_roles.commit()

        history = db_with_roles.query(DeliveryChatMessage).filter_by(
            order_id=order.id
        ).order_by(DeliveryChatMessage.id).all()

        assert len(history) == 4
        assert history[0].sender_role == "driver"
        assert history[1].message_text == "Okay, I'm waiting"
        assert history[2].photo_file_id is not None
        assert history[3].message_text == "Thanks, got it!"

    def test_post_delivery_window(self, db_with_roles: Session):
        """Chat window remains open for a period after delivery."""
        order, customer, driver = self._setup_order_with_driver(db_with_roles)

        now = datetime.now(timezone.utc)
        order.order_status = "delivered"
        order.completed_at = now
        order.chat_post_delivery_until = now + timedelta(minutes=30)
        db_with_roles.commit()

        # Message sent within window should be allowed
        within_window = now + timedelta(minutes=15)
        assert within_window < order.chat_post_delivery_until

        # Message sent after window should be blocked
        after_window = now + timedelta(minutes=45)
        assert after_window > order.chat_post_delivery_until
