"""
Tests for bot/database/methods/delete.py - delete operations.
"""
import pytest
from decimal import Decimal
from datetime import datetime, timezone

from bot.database.methods.delete import delete_item, delete_category, remove_from_cart, clear_cart
from bot.database.models.main import Goods, Categories, ShoppingCart, User


@pytest.mark.unit
@pytest.mark.database
class TestDeleteItem:
    """Tests for delete_item()"""

    def test_delete_item_removes_product(self, db_session, test_goods):
        assert db_session.query(Goods).filter_by(name=test_goods.name).first() is not None

        delete_item(test_goods.name)

        result = db_session.query(Goods).filter_by(name=test_goods.name).first()
        assert result is None

    def test_delete_item_nonexistent_no_error(self, db_session):
        """Deleting a nonexistent item should not raise"""
        delete_item("Nonexistent Product")

    def test_delete_item_does_not_affect_other_items(self, db_session, multiple_products):
        initial_count = db_session.query(Goods).count()
        assert initial_count == 5

        delete_item(multiple_products[0].name)

        remaining = db_session.query(Goods).count()
        assert remaining == 4


@pytest.mark.unit
@pytest.mark.database
class TestDeleteCategory:
    """Tests for delete_category()"""

    def test_delete_category_removes_category(self, db_session, test_category):
        assert db_session.query(Categories).filter_by(name=test_category.name).first() is not None

        delete_category(test_category.name)

        result = db_session.query(Categories).filter_by(name=test_category.name).first()
        assert result is None

    def test_delete_category_nonexistent_no_error(self, db_session):
        """Deleting a nonexistent category should not raise"""
        delete_category("Nonexistent Category")

    def test_delete_category_does_not_affect_others(self, db_session, multiple_categories):
        initial_count = db_session.query(Categories).count()
        assert initial_count == 3

        delete_category(multiple_categories[0].name)

        remaining = db_session.query(Categories).count()
        assert remaining == 2


@pytest.mark.unit
@pytest.mark.database
class TestRemoveFromCart:
    """Tests for remove_from_cart()"""

    @pytest.mark.asyncio
    async def test_remove_from_cart_success(self, db_session, test_shopping_cart):
        success, message = await remove_from_cart(
            test_shopping_cart.id,
            test_shopping_cart.user_id
        )
        assert success is True
        assert "removed" in message.lower()

        # Verify item is gone
        result = db_session.query(ShoppingCart).filter_by(id=test_shopping_cart.id).first()
        assert result is None

    @pytest.mark.asyncio
    async def test_remove_from_cart_not_found(self, db_with_roles, test_user):
        success, message = await remove_from_cart(99999, test_user.telegram_id)
        assert success is False
        assert "not found" in message.lower()

    @pytest.mark.asyncio
    async def test_remove_from_cart_wrong_user(self, db_session, test_shopping_cart):
        """Cannot remove another user's cart item"""
        success, message = await remove_from_cart(
            test_shopping_cart.id,
            999999999  # Wrong user
        )
        assert success is False

    @pytest.mark.asyncio
    async def test_remove_from_cart_does_not_affect_other_items(self, db_with_roles, test_user, test_category):
        # Create two products and cart items
        goods1 = Goods(name="Cart Item 1", price=Decimal("10.00"), description="d",
                       category_name=test_category.name, stock_quantity=10)
        goods2 = Goods(name="Cart Item 2", price=Decimal("20.00"), description="d",
                       category_name=test_category.name, stock_quantity=10)
        db_with_roles.add_all([goods1, goods2])
        db_with_roles.commit()

        cart1 = ShoppingCart(user_id=test_user.telegram_id, item_name="Cart Item 1", quantity=1)
        cart2 = ShoppingCart(user_id=test_user.telegram_id, item_name="Cart Item 2", quantity=1)
        db_with_roles.add_all([cart1, cart2])
        db_with_roles.commit()

        # Remove first item
        success, _ = await remove_from_cart(cart1.id, test_user.telegram_id)
        assert success is True

        # Second item should still exist
        remaining = db_with_roles.query(ShoppingCart).filter_by(
            user_id=test_user.telegram_id
        ).all()
        assert len(remaining) == 1
        assert remaining[0].item_name == "Cart Item 2"


@pytest.mark.unit
@pytest.mark.database
class TestClearCart:
    """Tests for clear_cart()"""

    @pytest.mark.asyncio
    async def test_clear_cart_success(self, db_session, test_shopping_cart):
        success, message = await clear_cart(test_shopping_cart.user_id)
        assert success is True
        assert "cleared" in message.lower()

        remaining = db_session.query(ShoppingCart).filter_by(
            user_id=test_shopping_cart.user_id
        ).count()
        assert remaining == 0

    @pytest.mark.asyncio
    async def test_clear_cart_empty_cart(self, db_with_roles, test_user):
        """Clearing an already empty cart should succeed"""
        success, message = await clear_cart(test_user.telegram_id)
        assert success is True

    @pytest.mark.asyncio
    async def test_clear_cart_multiple_items(self, db_with_roles, test_user, test_category):
        # Create products and multiple cart items
        for i in range(3):
            goods = Goods(name=f"Multi Cart {i}", price=Decimal("10.00"), description="d",
                          category_name=test_category.name, stock_quantity=10)
            db_with_roles.add(goods)
        db_with_roles.commit()

        for i in range(3):
            cart = ShoppingCart(user_id=test_user.telegram_id, item_name=f"Multi Cart {i}", quantity=1)
            db_with_roles.add(cart)
        db_with_roles.commit()

        assert db_with_roles.query(ShoppingCart).filter_by(
            user_id=test_user.telegram_id
        ).count() == 3

        success, _ = await clear_cart(test_user.telegram_id)
        assert success is True

        assert db_with_roles.query(ShoppingCart).filter_by(
            user_id=test_user.telegram_id
        ).count() == 0

    @pytest.mark.asyncio
    async def test_clear_cart_does_not_affect_other_users(self, db_with_roles, test_category):
        # Create two users with cart items
        user1 = User(telegram_id=900001, role_id=1, registration_date=datetime.now(timezone.utc))
        user2 = User(telegram_id=900002, role_id=1, registration_date=datetime.now(timezone.utc))
        db_with_roles.add_all([user1, user2])

        goods = Goods(name="Shared Product", price=Decimal("10.00"), description="d",
                      category_name=test_category.name, stock_quantity=50)
        db_with_roles.add(goods)
        db_with_roles.commit()

        cart1 = ShoppingCart(user_id=900001, item_name="Shared Product", quantity=1)
        cart2 = ShoppingCart(user_id=900002, item_name="Shared Product", quantity=2)
        db_with_roles.add_all([cart1, cart2])
        db_with_roles.commit()

        # Clear user1's cart
        success, _ = await clear_cart(900001)
        assert success is True

        # User2's cart should be untouched
        remaining = db_with_roles.query(ShoppingCart).filter_by(user_id=900002).first()
        assert remaining is not None
        assert remaining.quantity == 2
