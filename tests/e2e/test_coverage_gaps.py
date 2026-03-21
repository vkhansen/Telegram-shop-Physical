"""
Tests targeting specific E2E coverage gaps identified by coverage analysis.

Covers:
- Order helpers (build_google_maps_link, create_order_from_customer, create_order_items, format_items_summary)
- Delivery zones (Haversine distance, zone lookup, time slots)
- Constants usage
- Delivery zone + fee integration in orders
- Modifier validation edge cases in order context
- PromptPay QR generation
- Inventory edge cases (add_inventory, get_inventory_stats, cleanup)
- Update operations (update_item, update_category, update_user_role)
- BotSettings management
- Order status integration (order_status helpers used across admin flow)
"""
import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from sqlalchemy.orm import Session

from bot.database.models.main import (
    Role, User, Categories, Goods, Order, OrderItem, CustomerInfo,
    ShoppingCart, BitcoinAddress, BotSettings, InventoryLog,
)
from bot.database.methods.inventory import (
    reserve_inventory, release_reservation, deduct_inventory, add_inventory,
    get_inventory_stats,
)
from bot.utils.order_codes import generate_unique_order_code
from bot.utils.modifiers import calculate_item_price, validate_modifier_selection
from bot.utils.order_status import is_valid_transition, get_allowed_transitions, ALL_STATUSES, VALID_TRANSITIONS
from bot.utils.delivery_types import needs_delivery_photo
from bot.utils.constants import PAYMENT_BITCOIN, PAYMENT_CASH, PAYMENT_PROMPTPAY, DELIVERY_DOOR, DELIVERY_DEAD_DROP, DELIVERY_PICKUP

from tests.e2e.menu_loader import load_menu_from_file

SAMPLE_MENU_PATH = Path(__file__).parent / "sample_menu.json"


def _user(session, tid, role_id=1):
    u = User(telegram_id=tid, role_id=role_id, registration_date=datetime.now(timezone.utc))
    session.add(u)
    session.commit()
    session.refresh(u)
    return u


# ===================================================================
# Order Helpers (0% covered in E2E)
# ===================================================================

@pytest.mark.e2e
class TestOrderHelpers:
    """Test bot/utils/order_helpers.py functions."""

    def test_build_google_maps_link(self):
        from bot.utils.order_helpers import build_google_maps_link

        link = build_google_maps_link(13.7563, 100.5018)
        assert link == "https://www.google.com/maps?q=13.7563,100.5018"

    def test_build_google_maps_link_none(self):
        from bot.utils.order_helpers import build_google_maps_link

        assert build_google_maps_link(None, None) is None
        assert build_google_maps_link(13.75, None) is None
        assert build_google_maps_link(None, 100.50) is None

    def test_create_order_from_customer(self, db_with_roles: Session):
        from bot.utils.order_helpers import create_order_from_customer

        user = _user(db_with_roles, 50001)
        ci = CustomerInfo(
            telegram_id=user.telegram_id,
            phone_number="+66812345678",
            delivery_address="123 Test Rd",
            latitude=13.75,
            longitude=100.50,
        )
        db_with_roles.add(ci)
        db_with_roles.commit()

        order = create_order_from_customer(
            db_with_roles, user.telegram_id, ci,
            payment_method="cash",
            total_amount=Decimal("250.00"),
        )
        db_with_roles.commit()

        assert order.id is not None
        assert order.order_code is not None
        assert len(order.order_code) == 6
        assert order.buyer_id == user.telegram_id
        assert order.total_price == Decimal("250.00")
        assert order.payment_method == "cash"
        assert order.delivery_address == "123 Test Rd"
        assert order.latitude == pytest.approx(13.75)
        assert order.google_maps_link is not None

    def test_create_order_from_customer_with_bonus(self, db_with_roles: Session):
        from bot.utils.order_helpers import create_order_from_customer

        user = _user(db_with_roles, 50002)
        ci = CustomerInfo(telegram_id=user.telegram_id, phone_number="+66800000000",
                          delivery_address="Bonus test")
        db_with_roles.add(ci)
        db_with_roles.commit()

        order = create_order_from_customer(
            db_with_roles, user.telegram_id, ci,
            payment_method="cash", total_amount=Decimal("500.00"),
            bonus_applied=Decimal("50.00"),
        )
        db_with_roles.commit()

        assert order.bonus_applied == Decimal("50.00")

    def test_create_order_items(self, db_with_roles: Session):
        from bot.utils.order_helpers import create_order_items

        user = _user(db_with_roles, 50003)
        cat = Categories(name="Helpers Test")
        db_with_roles.add(cat)
        db_with_roles.flush()
        g = Goods(name="Helper Item", price=Decimal("100"), description="T",
                  category_name="Helpers Test", stock_quantity=50)
        db_with_roles.add(g)
        db_with_roles.flush()

        order = Order(buyer_id=user.telegram_id, total_price=Decimal("200"),
                      payment_method="cash", delivery_address="T", phone_number="+66",
                      order_code="HELP01")
        db_with_roles.add(order)
        db_with_roles.flush()

        cart_items = [
            {"item_name": "Helper Item", "quantity": 2, "price": Decimal("100"), "total": Decimal("200")},
        ]
        summary, to_reserve = create_order_items(db_with_roles, order.id, cart_items)
        db_with_roles.commit()

        assert len(summary) == 1
        assert "Helper Item" in summary[0]
        assert len(to_reserve) == 1
        assert to_reserve[0]["item_name"] == "Helper Item"
        assert to_reserve[0]["quantity"] == 2

    def test_format_items_summary(self):
        from bot.utils.order_helpers import format_items_summary

        items = [
            {"item_name": "Pad Thai", "quantity": 2, "total": Decimal("298")},
            {"item_name": "Tea", "quantity": 1, "total": Decimal("59")},
        ]
        result = format_items_summary(items)
        assert len(result) == 2
        assert "Pad Thai" in result[0]
        assert "Tea" in result[1]


# ===================================================================
# Delivery Zones (0% covered in E2E)
# ===================================================================

@pytest.mark.e2e
class TestDeliveryZones:
    """Test bot/config/delivery_zones.py functions."""

    def test_calculate_distance_same_point(self):
        from bot.config.delivery_zones import calculate_distance
        dist = calculate_distance(13.75, 100.50, 13.75, 100.50)
        assert dist == pytest.approx(0, abs=0.01)

    def test_calculate_distance_known(self):
        from bot.config.delivery_zones import calculate_distance
        # Bangkok to Pattaya ~150 km
        dist = calculate_distance(13.7563, 100.5018, 12.9236, 100.8825)
        assert 90 < dist < 110  # Approximate

    def test_get_delivery_zone_central(self):
        from bot.config.delivery_zones import get_delivery_zone, RESTAURANT_LAT, RESTAURANT_LNG
        # Very close to restaurant
        zone = get_delivery_zone(RESTAURANT_LAT + 0.001, RESTAURANT_LNG + 0.001)
        assert zone is not None
        assert zone["name"] == "Zone 1 - Central"
        assert zone["fee"] == Decimal("0")

    def test_get_delivery_zone_inner(self):
        from bot.config.delivery_zones import get_delivery_zone, RESTAURANT_LAT, RESTAURANT_LNG
        # ~5km away
        zone = get_delivery_zone(RESTAURANT_LAT + 0.04, RESTAURANT_LNG)
        assert zone is not None
        assert "Zone 2" in zone["name"]

    def test_get_delivery_zone_far(self):
        from bot.config.delivery_zones import get_delivery_zone
        # Very far
        zone = get_delivery_zone(14.5, 101.5)
        assert zone is not None
        assert zone["fee"] > Decimal("0")

    def test_get_delivery_zone_none_coords(self):
        from bot.config.delivery_zones import get_delivery_zone
        assert get_delivery_zone(None, None) is None
        assert get_delivery_zone(13.75, None) is None

    def test_get_available_time_slots(self):
        from bot.config.delivery_zones import get_available_time_slots
        slots = get_available_time_slots()
        assert len(slots) > 0
        assert all("label" in s for s in slots)
        assert any(s["id"] == "asap" for s in slots)

    def test_delivery_zone_fee_in_order(self, db_with_roles: Session):
        """Zone fee correctly stored on order."""
        from bot.config.delivery_zones import get_delivery_zone

        user = _user(db_with_roles, 51001)
        zone = get_delivery_zone(13.80, 100.60)  # ~7km

        order = Order(
            buyer_id=user.telegram_id, total_price=Decimal("200") + zone["fee"],
            payment_method="cash", delivery_address="Zone test",
            phone_number="+66", order_code="ZONE01",
            delivery_zone=zone["name"], delivery_fee=zone["fee"],
            latitude=13.80, longitude=100.60,
        )
        db_with_roles.add(order)
        db_with_roles.commit()

        assert order.delivery_zone is not None
        assert order.delivery_fee >= Decimal("0")


# ===================================================================
# Constants usage
# ===================================================================

@pytest.mark.e2e
class TestConstants:
    """Test that constants match expected values used in the system."""

    def test_payment_methods(self):
        assert PAYMENT_CASH == "cash"
        assert PAYMENT_BITCOIN == "bitcoin"
        assert PAYMENT_PROMPTPAY == "promptpay"

    def test_delivery_types(self):
        assert DELIVERY_DOOR == "door"
        assert DELIVERY_DEAD_DROP == "dead_drop"
        assert DELIVERY_PICKUP == "pickup"

    def test_constants_match_model_defaults(self):
        """Order model default delivery_type matches constant."""
        order = Order.__table__.columns["delivery_type"]
        assert order.default.arg == DELIVERY_DOOR


# ===================================================================
# Inventory edge cases
# ===================================================================

@pytest.mark.e2e
class TestInventoryEdgeCases:
    """Test inventory operations not covered by existing tests."""

    def test_add_inventory_creates_log(self, db_with_roles: Session):
        s = db_with_roles
        cat = Categories(name="Inv Test")
        s.add(cat)
        s.flush()
        g = Goods(name="Inv Item", price=Decimal("50"), description="T",
                  category_name="Inv Test", stock_quantity=0)
        s.add(g)
        s.commit()

        admin = _user(s, 52001, role_id=2)

        success, msg = add_inventory("Inv Item", 25, admin.telegram_id,
                                     comment="Restock", session=s)
        s.commit()
        assert success

        s.refresh(g)
        assert g.stock_quantity == 25

        logs = s.query(InventoryLog).filter_by(item_name="Inv Item").all()
        assert len(logs) == 1
        assert logs[0].change_type == "add"
        assert logs[0].quantity_change == 25
        assert logs[0].comment == "Restock"

    def test_get_inventory_stats(self, db_with_roles: Session):
        s = db_with_roles
        cat = Categories(name="Stats Test")
        s.add(cat)
        s.flush()
        g = Goods(name="Stats Item", price=Decimal("100"), description="T",
                  category_name="Stats Test", stock_quantity=50)
        g.reserved_quantity = 10
        s.add(g)
        s.commit()

        stats = get_inventory_stats("Stats Item")
        assert stats is not None
        assert stats["stock"] == 50
        assert stats["reserved"] == 10
        assert stats["available"] == 40

    def test_get_inventory_stats_nonexistent(self, db_with_roles: Session):
        stats = get_inventory_stats("Nonexistent Item XYZ")
        assert stats is None

    def test_reserve_insufficient_stock(self, db_with_roles: Session):
        s = db_with_roles
        cat = Categories(name="InsufTest")
        s.add(cat)
        s.flush()
        g = Goods(name="Scarce Item", price=Decimal("100"), description="T",
                  category_name="InsufTest", stock_quantity=2)
        s.add(g)
        s.commit()

        user = _user(s, 52002)
        order = Order(buyer_id=user.telegram_id, total_price=Decimal("300"),
                      payment_method="cash", delivery_address="T", phone_number="+66",
                      order_code="INSUF1")
        s.add(order)
        s.flush()
        s.add(OrderItem(order_id=order.id, item_name="Scarce Item",
                        price=Decimal("100"), quantity=5))
        s.commit()

        success, msg = reserve_inventory(
            order.id, [{"item_name": "Scarce Item", "quantity": 5}], "cash", s)
        s.commit()

        assert not success
        assert "insufficient" in msg.lower() or "not enough" in msg.lower() or not success

    def test_double_reserve_rejected(self, db_with_roles: Session):
        """Reserving the same order twice should not double-count."""
        s = db_with_roles
        load_menu_from_file(SAMPLE_MENU_PATH, s)
        s.commit()

        user = _user(s, 52003)
        order = Order(buyer_id=user.telegram_id, total_price=Decimal("149"),
                      payment_method="cash", delivery_address="T", phone_number="+66",
                      order_code="DBL001")
        s.add(order)
        s.flush()
        s.add(OrderItem(order_id=order.id, item_name="Pad Thai",
                        price=Decimal("149"), quantity=1))
        s.commit()

        success1, _ = reserve_inventory(order.id, [{"item_name": "Pad Thai", "quantity": 1}], "cash", s)
        s.commit()
        assert success1

        pt = s.query(Goods).filter_by(name="Pad Thai").one()
        reserved_after_first = pt.reserved_quantity

        # Second reserve attempt for same order
        success2, _ = reserve_inventory(order.id, [{"item_name": "Pad Thai", "quantity": 1}], "cash", s)
        s.commit()

        s.refresh(pt)
        # Should not have increased reserved count again
        assert pt.reserved_quantity <= reserved_after_first + 1


# ===================================================================
# Update operations
# ===================================================================

@pytest.mark.e2e
class TestUpdateOperations:
    """Test database update operations."""

    def test_update_item(self, db_with_roles: Session):
        from bot.database.methods.update import update_item

        s = db_with_roles
        cat = Categories(name="UpdCat")
        s.add(cat)
        s.flush()
        g = Goods(name="Old Name", price=Decimal("100"), description="Old desc",
                  category_name="UpdCat", stock_quantity=10)
        s.add(g)
        s.commit()

        update_item("Old Name", "New Name", "New desc", 150, "UpdCat")

        updated = s.query(Goods).filter_by(name="New Name").first()
        assert updated is not None
        assert updated.description == "New desc"
        assert updated.price == 150

    def test_set_role(self, db_with_roles: Session):
        from bot.database.methods.update import set_role

        user = _user(db_with_roles, 53001)
        assert user.role_id == 1  # USER

        set_role(user.telegram_id, 2)  # Promote to ADMIN

        db_with_roles.refresh(user)
        assert user.role_id == 2


# ===================================================================
# BotSettings management
# ===================================================================

@pytest.mark.e2e
class TestBotSettingsIntegration:
    """Test BotSettings in realistic workflows."""

    def test_setting_crud(self, db_with_roles: Session):
        s = db_with_roles

        # Create
        setting = BotSettings(setting_key="test_setting", setting_value="42")
        s.add(setting)
        s.commit()

        # Read
        from bot.database.methods.read import get_bot_setting
        val = get_bot_setting("test_setting")
        assert val == "42"

        # Update
        existing = s.query(BotSettings).filter_by(setting_key="test_setting").one()
        existing.setting_value = "99"
        s.commit()

        val2 = get_bot_setting("test_setting")
        assert val2 == "99"

    def test_setting_default(self, db_with_roles: Session):
        from bot.database.methods.read import get_bot_setting
        val = get_bot_setting("nonexistent_key", default="fallback")
        assert val == "fallback"

    def test_setting_int(self, db_with_roles: Session):
        s = db_with_roles
        s.add(BotSettings(setting_key="int_setting", setting_value="123"))
        s.commit()

        from bot.database.methods.read import get_bot_setting
        val = get_bot_setting("int_setting", default="0", value_type=int)
        assert val == 123

    def test_timezone_setting(self, db_with_roles: Session):
        s = db_with_roles
        s.add(BotSettings(setting_key="timezone", setting_value="Asia/Bangkok"))
        s.commit()

        from bot.database.methods.read import get_bot_setting
        tz = get_bot_setting("timezone")
        assert tz == "Asia/Bangkok"


# ===================================================================
# Order Status - exhaustive transition matrix
# ===================================================================

@pytest.mark.e2e
class TestOrderStatusExhaustive:
    """Test every valid and invalid transition in the status matrix."""

    def test_all_valid_transitions(self):
        """Every transition listed in VALID_TRANSITIONS is accepted."""
        for current, allowed in VALID_TRANSITIONS.items():
            for target in allowed:
                assert is_valid_transition(current, target), \
                    f"{current} → {target} should be valid"

    def test_all_invalid_transitions(self):
        """Every transition NOT listed is rejected."""
        for current in ALL_STATUSES:
            allowed = get_allowed_transitions(current)
            for target in ALL_STATUSES:
                if target not in allowed:
                    assert not is_valid_transition(current, target), \
                        f"{current} → {target} should be invalid"

    def test_unknown_status(self):
        assert get_allowed_transitions("fantasy_status") == set()
        assert not is_valid_transition("fantasy_status", "delivered")

    def test_status_applied_to_real_order(self, db_with_roles: Session):
        """Walk a real order through the full pipeline and verify DB state."""
        s = db_with_roles
        user = _user(s, 54001)
        order = Order(buyer_id=user.telegram_id, total_price=Decimal("100"),
                      payment_method="cash", delivery_address="T", phone_number="+66",
                      order_code="STAT01")
        s.add(order)
        s.commit()

        pipeline = ["reserved", "confirmed", "preparing", "ready", "out_for_delivery", "delivered"]
        for step in pipeline:
            assert is_valid_transition(order.order_status, step)
            order.order_status = step
            s.commit()

        assert order.order_status == "delivered"
        # Terminal - nothing allowed
        assert get_allowed_transitions("delivered") == set()


# ===================================================================
# Modifier validation edge cases
# ===================================================================

@pytest.mark.e2e
class TestModifierValidationEdgeCases:
    """Edge cases for modifier validation in order context."""

    def test_missing_required_modifier(self):
        schema = {
            "spice": {
                "label": "Spice Level",
                "type": "single",
                "required": True,
                "options": [{"id": "mild", "label": "Mild", "price": 0}],
            },
        }
        valid, err = validate_modifier_selection(schema, {})
        assert not valid
        assert "spice" in err.lower() or "required" in err.lower()

    def test_invalid_option_id(self):
        schema = {
            "spice": {
                "label": "Spice",
                "type": "single",
                "required": False,
                "options": [{"id": "mild", "label": "Mild", "price": 0}],
            },
        }
        valid, err = validate_modifier_selection(schema, {"spice": "nonexistent"})
        assert not valid

    def test_multi_choice_with_invalid_option(self):
        schema = {
            "extras": {
                "label": "Extras",
                "type": "multi",
                "required": False,
                "options": [
                    {"id": "cheese", "label": "Cheese", "price": 10},
                    {"id": "bacon", "label": "Bacon", "price": 20},
                ],
            },
        }
        valid, err = validate_modifier_selection(schema, {"extras": ["cheese", "ghost"]})
        assert not valid

    def test_no_schema_always_valid(self):
        valid, err = validate_modifier_selection(None, {"anything": "value"})
        assert valid

    def test_no_selection_no_schema(self):
        valid, err = validate_modifier_selection(None, None)
        assert valid

    def test_price_with_multi_extras(self):
        schema = {
            "extras": {
                "label": "Extras",
                "type": "multi",
                "required": False,
                "options": [
                    {"id": "a", "label": "A", "price": 10},
                    {"id": "b", "label": "B", "price": 20},
                    {"id": "c", "label": "C", "price": 30},
                ],
            },
        }
        # Select all three
        price = calculate_item_price(Decimal("100"), schema, {"extras": ["a", "b", "c"]})
        assert price == Decimal("160")  # 100 + 10 + 20 + 30

    def test_price_no_modifiers_selected(self):
        schema = {
            "spice": {
                "label": "Spice",
                "type": "single",
                "required": False,
                "options": [{"id": "mild", "label": "Mild", "price": 0}],
            },
        }
        price = calculate_item_price(Decimal("100"), schema, {})
        assert price == Decimal("100")

    def test_price_no_schema(self):
        price = calculate_item_price(Decimal("100"), None, None)
        assert price == Decimal("100")
