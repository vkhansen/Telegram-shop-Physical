"""Tests for menu modifier utilities (Card 8)"""
import pytest
from decimal import Decimal
from datetime import datetime, timezone

from bot.utils.modifiers import calculate_item_price, validate_modifier_selection


SAMPLE_MODIFIERS = {
    "spice_level": {
        "label": "Spice Level",
        "type": "single",
        "required": True,
        "options": [
            {"id": "mild", "label": "Mild", "price": 0},
            {"id": "medium", "label": "Medium", "price": 0},
            {"id": "hot", "label": "Hot", "price": 0},
            {"id": "thai_hot", "label": "Thai Hot", "price": 10},
        ]
    },
    "extras": {
        "label": "Extras",
        "type": "multi",
        "required": False,
        "options": [
            {"id": "extra_rice", "label": "Extra Rice", "price": 20},
            {"id": "egg", "label": "Fried Egg", "price": 15},
            {"id": "extra_meat", "label": "Extra Meat", "price": 40},
        ]
    },
    "removals": {
        "label": "Remove",
        "type": "multi",
        "required": False,
        "options": [
            {"id": "no_onion", "label": "No Onion", "price": 0},
            {"id": "no_cilantro", "label": "No Cilantro", "price": 0},
        ]
    }
}


@pytest.mark.unit
class TestCalculateItemPrice:
    """Test modifier price calculations"""

    def test_no_modifiers(self):
        """Base price unchanged with no modifiers"""
        result = calculate_item_price(Decimal("100"), None, None)
        assert result == Decimal("100")

    def test_no_selected_modifiers(self):
        """Base price unchanged when no selections made"""
        result = calculate_item_price(Decimal("100"), SAMPLE_MODIFIERS, None)
        assert result == Decimal("100")

    def test_single_choice_free(self):
        """Single choice with price=0 doesn't change total"""
        result = calculate_item_price(
            Decimal("100"), SAMPLE_MODIFIERS,
            {"spice_level": "mild"}
        )
        assert result == Decimal("100")

    def test_single_choice_with_price(self):
        """Single choice with price adds to total"""
        result = calculate_item_price(
            Decimal("100"), SAMPLE_MODIFIERS,
            {"spice_level": "thai_hot"}
        )
        assert result == Decimal("110")

    def test_multi_extras_sum(self):
        """Multiple extras prices sum correctly"""
        result = calculate_item_price(
            Decimal("100"), SAMPLE_MODIFIERS,
            {"extras": ["extra_rice", "egg"]}
        )
        assert result == Decimal("135")  # 100 + 20 + 15

    def test_free_removals(self):
        """Removals with price=0 don't change total"""
        result = calculate_item_price(
            Decimal("100"), SAMPLE_MODIFIERS,
            {"removals": ["no_onion", "no_cilantro"]}
        )
        assert result == Decimal("100")

    def test_combined_modifiers(self):
        """All modifier types combined"""
        result = calculate_item_price(
            Decimal("100"), SAMPLE_MODIFIERS,
            {
                "spice_level": "thai_hot",     # +10
                "extras": ["extra_rice", "egg"],  # +20 +15
                "removals": ["no_onion"]        # +0
            }
        )
        assert result == Decimal("145")  # 100 + 10 + 20 + 15

    def test_empty_schema(self):
        """Empty modifier schema returns base price"""
        result = calculate_item_price(Decimal("100"), {}, {"spice_level": "hot"})
        assert result == Decimal("100")


@pytest.mark.unit
class TestValidateModifierSelection:
    """Test modifier validation"""

    def test_valid_selection(self):
        """Valid selection passes"""
        is_valid, err = validate_modifier_selection(
            SAMPLE_MODIFIERS,
            {"spice_level": "hot", "extras": ["egg"]}
        )
        assert is_valid is True
        assert err == ""

    def test_missing_required(self):
        """Missing required modifier fails"""
        is_valid, err = validate_modifier_selection(
            SAMPLE_MODIFIERS,
            {"extras": ["egg"]}  # spice_level is required but missing
        )
        assert is_valid is False
        assert "required" in err.lower() or "Spice" in err

    def test_invalid_option_id(self):
        """Invalid option ID fails"""
        is_valid, err = validate_modifier_selection(
            SAMPLE_MODIFIERS,
            {"spice_level": "nuclear"}  # not a valid option
        )
        assert is_valid is False
        assert "Invalid" in err

    def test_no_schema(self):
        """No schema always valid"""
        is_valid, _ = validate_modifier_selection(None, {"anything": "goes"})
        assert is_valid is True

    def test_no_selection_with_optional(self):
        """No selection valid when all optional"""
        schema = {
            "extras": {
                "label": "Extras",
                "type": "multi",
                "required": False,
                "options": [{"id": "egg", "label": "Egg", "price": 15}]
            }
        }
        is_valid, _ = validate_modifier_selection(schema, {})
        assert is_valid is True


@pytest.mark.unit
@pytest.mark.models
class TestModifierModelFields:
    """Test modifier-related model fields"""

    def test_goods_modifiers_json(self, db_with_roles, db_session):
        """Goods stores modifier schema as JSON"""
        from bot.database.models.main import Goods, Categories

        cat = Categories(name="Mains")
        db_session.add(cat)
        db_session.commit()

        goods = Goods(
            name="Pad Thai",
            price=Decimal("120.00"),
            description="Classic Thai noodles",
            category_name="Mains",
            stock_quantity=50
        )
        goods.modifiers = SAMPLE_MODIFIERS
        db_session.add(goods)
        db_session.commit()
        db_session.refresh(goods)

        assert goods.modifiers is not None
        assert "spice_level" in goods.modifiers
        assert goods.modifiers["extras"]["options"][0]["price"] == 20

    def test_order_item_selected_modifiers(self, db_with_roles, db_session):
        """OrderItem stores selected modifier choices"""
        from bot.database.models.main import Order, OrderItem, User

        user = User(telegram_id=500001, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        order = Order(
            buyer_id=500001, total_price=Decimal("145.00"),
            payment_method="cash", delivery_address="Test", phone_number="0812345678"
        )
        db_session.add(order)
        db_session.flush()

        selected = {"spice_level": "thai_hot", "extras": ["egg"], "removals": ["no_onion"]}
        item = OrderItem(
            order_id=order.id, item_name="Pad Thai",
            price=Decimal("145.00"), quantity=1,
            selected_modifiers=selected
        )
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)

        assert item.selected_modifiers["spice_level"] == "thai_hot"
        assert "egg" in item.selected_modifiers["extras"]

    def test_cart_item_selected_modifiers(self, db_with_roles, db_session):
        """ShoppingCart stores selected modifiers"""
        from bot.database.models.main import ShoppingCart, User, Goods, Categories

        user = User(telegram_id=500002, registration_date=datetime.now(timezone.utc))
        cat = Categories(name="TestCat")
        db_session.add_all([user, cat])
        db_session.commit()

        goods = Goods(name="Som Tam", price=Decimal("80"), description="Papaya salad",
                      category_name="TestCat", stock_quantity=20)
        db_session.add(goods)
        db_session.commit()

        cart = ShoppingCart(
            user_id=500002, item_name="Som Tam", quantity=1,
            selected_modifiers={"spice_level": "hot"}
        )
        db_session.add(cart)
        db_session.commit()
        db_session.refresh(cart)

        assert cart.selected_modifiers["spice_level"] == "hot"

    def test_categories_sort_order(self, db_with_roles, db_session):
        """Categories have sort_order for menu ordering"""
        from bot.database.models.main import Categories

        cats = [
            Categories(name="Starters", sort_order=1),
            Categories(name="Mains2", sort_order=2),
            Categories(name="Drinks", sort_order=3),
            Categories(name="Desserts", sort_order=4),
        ]
        db_session.add_all(cats)
        db_session.commit()

        result = db_session.query(Categories).order_by(Categories.sort_order).all()
        assert [c.name for c in result] == ["Starters", "Mains2", "Drinks", "Desserts"]

    def test_categories_sort_order_default(self, db_with_roles, db_session):
        """Categories default sort_order is 0"""
        from bot.database.models.main import Categories

        cat = Categories(name="Uncategorized")
        db_session.add(cat)
        db_session.commit()

        assert cat.sort_order == 0
