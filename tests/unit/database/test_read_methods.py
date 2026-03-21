"""
Tests for bot/database/methods/read.py - comprehensive coverage of all read functions.
"""
import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, AsyncMock

from bot.database.methods.read import (
    check_user,
    check_role,
    get_role_id_by_name,
    check_role_name_by_id,
    select_max_role_id,
    select_today_users,
    get_user_count,
    select_admins,
    get_all_users,
    get_bought_item_info,
    get_item_info,
    get_goods_info,
    check_item,
    check_category,
    select_item_values_amount,
    check_value,
    select_user_items,
    select_bought_item,
    select_count_items,
    select_count_goods,
    select_count_categories,
    select_count_bought_items,
    select_today_orders,
    select_all_orders,
    select_today_operations,
    select_all_operations,
    select_user_operations,
    check_user_referrals,
    get_user_referral,
    get_referral_earnings_stats,
    get_one_referral_earning,
    get_reference_bonus_percent,
    get_bot_setting,
    get_cart_items,
    query_user_orders,
    count_user_orders,
    calculate_cart_total,
    check_user_cached,
    check_role_cached,
    select_item_values_amount_cached,
    _day_window,
)
from bot.database.models.main import (
    User, Goods, Categories, BoughtGoods, Operations,
    ReferralEarnings, BotSettings, ShoppingCart, Order, OrderItem, Role,
)


@pytest.mark.unit
@pytest.mark.database
class TestDayWindow:
    """Tests for the _day_window helper"""

    def test_day_window_returns_start_and_end(self):
        start, end = _day_window("2025-06-15")
        assert start == datetime(2025, 6, 15, 0, 0, 0)
        assert end == datetime(2025, 6, 16, 0, 0, 0)

    def test_day_window_span_is_one_day(self):
        start, end = _day_window("2025-01-01")
        assert (end - start) == timedelta(days=1)


@pytest.mark.unit
@pytest.mark.database
class TestCheckUser:
    """Tests for check_user()"""

    def test_check_user_exists(self, db_with_roles, test_user):
        result = check_user(test_user.telegram_id)
        assert result is not None
        assert result['telegram_id'] == test_user.telegram_id

    def test_check_user_not_found(self, db_with_roles):
        result = check_user(999999999)
        assert result is None

    def test_check_user_with_string_id(self, db_with_roles, test_user):
        result = check_user(str(test_user.telegram_id))
        assert result is not None


@pytest.mark.unit
@pytest.mark.database
class TestCheckRole:
    """Tests for check_role()"""

    def test_check_role_user(self, db_with_roles, test_user):
        perms = check_role(test_user.telegram_id)
        assert perms == 1  # USER role permissions

    def test_check_role_admin(self, db_with_roles, test_admin):
        perms = check_role(test_admin.telegram_id)
        assert perms == 31  # ADMIN role permissions

    def test_check_role_nonexistent_user(self, db_with_roles):
        perms = check_role(999999999)
        assert perms == 0


@pytest.mark.unit
@pytest.mark.database
class TestRoleLookups:
    """Tests for role lookup functions"""

    def test_get_role_id_by_name_user(self, db_with_roles):
        role_id = get_role_id_by_name("USER")
        assert role_id is not None
        assert role_id == 1

    def test_get_role_id_by_name_admin(self, db_with_roles):
        role_id = get_role_id_by_name("ADMIN")
        assert role_id is not None
        assert role_id == 2

    def test_get_role_id_by_name_owner(self, db_with_roles):
        role_id = get_role_id_by_name("OWNER")
        assert role_id is not None
        assert role_id == 3

    def test_get_role_id_by_name_nonexistent(self, db_with_roles):
        role_id = get_role_id_by_name("NONEXISTENT")
        assert role_id is None

    def test_check_role_name_by_id(self, db_with_roles):
        name = check_role_name_by_id(1)
        assert name == "USER"

    def test_check_role_name_by_id_admin(self, db_with_roles):
        name = check_role_name_by_id(2)
        assert name == "ADMIN"

    def test_select_max_role_id(self, db_with_roles):
        max_id = select_max_role_id()
        assert max_id == 3  # OWNER role

    def test_select_max_role_id_empty(self, db_session):
        """With no roles, should return None"""
        max_id = select_max_role_id()
        assert max_id is None


@pytest.mark.unit
@pytest.mark.database
class TestUserCounts:
    """Tests for user counting functions"""

    def test_get_user_count_empty(self, db_with_roles):
        count = get_user_count()
        assert count == 0

    def test_get_user_count_with_users(self, db_with_roles, test_user, test_admin):
        count = get_user_count()
        assert count == 2

    def test_select_admins_none(self, db_with_roles, test_user):
        """User with role_id=1 should not be counted as admin"""
        count = select_admins()
        assert count == 0

    def test_select_admins_with_admin(self, db_with_roles, test_user, test_admin):
        count = select_admins()
        assert count == 1  # test_admin has role_id=2

    def test_select_today_users(self, db_with_roles, test_user):
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        count = select_today_users(today)
        assert count >= 1

    def test_select_today_users_no_registrations(self, db_with_roles):
        count = select_today_users("2000-01-01")
        assert count == 0

    def test_get_all_users(self, db_with_roles, test_user, test_admin):
        users = get_all_users()
        assert len(users) == 2
        telegram_ids = [u[0] for u in users]
        assert test_user.telegram_id in telegram_ids
        assert test_admin.telegram_id in telegram_ids

    def test_get_all_users_empty(self, db_with_roles):
        users = get_all_users()
        assert len(users) == 0


@pytest.mark.unit
@pytest.mark.database
class TestItemInfo:
    """Tests for item/goods info functions"""

    def test_get_item_info_exists(self, db_session, test_goods):
        result = get_item_info(test_goods.name)
        assert result is not None
        assert result['name'] == test_goods.name
        assert Decimal(str(result['price'])) == test_goods.price

    def test_get_item_info_not_found(self, db_session):
        result = get_item_info("Nonexistent Product")
        assert result is None

    def test_get_goods_info_is_alias(self, db_session, test_goods):
        """get_goods_info should be same as get_item_info"""
        result = get_goods_info(test_goods.name)
        assert result is not None
        assert result['name'] == test_goods.name

    def test_check_item_is_alias(self, db_session, test_goods):
        """check_item should be same as get_item_info"""
        result = check_item(test_goods.name)
        assert result is not None
        assert result['name'] == test_goods.name

    def test_check_category_exists(self, db_session, test_category):
        result = check_category(test_category.name)
        assert result is not None
        assert result['name'] == test_category.name

    def test_check_category_not_found(self, db_session):
        result = check_category("Nonexistent Category")
        assert result is None


@pytest.mark.unit
@pytest.mark.database
class TestItemStock:
    """Tests for stock/inventory read functions"""

    def test_select_item_values_amount(self, db_session, test_goods):
        amount = select_item_values_amount(test_goods.name)
        assert amount == 100  # stock_quantity=100, reserved_quantity=0

    def test_select_item_values_amount_with_reserved(self, db_session, test_category):
        goods = Goods(
            name="Reserved Product",
            price=Decimal("50.00"),
            description="Has reserved stock",
            category_name=test_category.name,
            stock_quantity=100,
            reserved_quantity=30
        )
        db_session.add(goods)
        db_session.commit()

        amount = select_item_values_amount("Reserved Product")
        assert amount == 70  # 100 - 30

    def test_select_item_values_amount_not_found(self, db_session):
        amount = select_item_values_amount("Nonexistent")
        assert amount == 0

    def test_check_value_always_false(self):
        """check_value for physical goods always returns False"""
        assert check_value("anything") is False
        assert check_value("") is False

    def test_select_count_items(self, db_session, test_goods):
        count = select_count_items()
        assert count == test_goods.stock_quantity

    def test_select_count_items_empty(self, db_session):
        count = select_count_items()
        assert count == 0

    def test_select_count_goods(self, db_session, test_goods):
        count = select_count_goods()
        assert count == 1

    def test_select_count_goods_multiple(self, db_session, multiple_products):
        count = select_count_goods()
        assert count == 5

    def test_select_count_categories(self, db_session, test_category):
        count = select_count_categories()
        assert count == 1

    def test_select_count_categories_multiple(self, db_session, multiple_categories):
        count = select_count_categories()
        assert count == 3


@pytest.mark.unit
@pytest.mark.database
class TestBoughtItems:
    """Tests for bought item functions"""

    def test_get_bought_item_info_not_found(self, db_session):
        result = get_bought_item_info(999)
        assert result is None

    def test_get_bought_item_info_exists(self, db_with_roles, test_user, test_goods):
        bought = BoughtGoods(
            name=test_goods.name,
            value="item value",
            price=test_goods.price,
            buyer_id=test_user.telegram_id,
            bought_datetime=datetime.now(timezone.utc),
            unique_id=111111
        )
        db_with_roles.add(bought)
        db_with_roles.commit()

        result = get_bought_item_info(bought.id)
        assert result is not None
        assert result['item_name'] == test_goods.name

    def test_select_bought_item_by_unique_id(self, db_with_roles, test_user, test_goods):
        bought = BoughtGoods(
            name=test_goods.name,
            value="test value",
            price=Decimal("99.99"),
            buyer_id=test_user.telegram_id,
            bought_datetime=datetime.now(timezone.utc),
            unique_id=222222
        )
        db_with_roles.add(bought)
        db_with_roles.commit()

        result = select_bought_item(222222)
        assert result is not None
        assert result['unique_id'] == 222222

    def test_select_bought_item_not_found(self, db_session):
        result = select_bought_item(999999)
        assert result is None

    def test_select_user_items_count(self, db_with_roles, test_user, test_goods):
        for i in range(3):
            bought = BoughtGoods(
                name=test_goods.name,
                value=f"value_{i}",
                price=Decimal("10.00"),
                buyer_id=test_user.telegram_id,
                bought_datetime=datetime.now(timezone.utc),
                unique_id=300000 + i
            )
            db_with_roles.add(bought)
        db_with_roles.commit()

        count = select_user_items(test_user.telegram_id)
        assert count == 3

    def test_select_user_items_none(self, db_with_roles, test_user):
        count = select_user_items(test_user.telegram_id)
        assert count == 0

    def test_select_count_bought_items(self, db_with_roles, test_user, test_goods):
        bought = BoughtGoods(
            name=test_goods.name,
            value="v",
            price=Decimal("10.00"),
            buyer_id=test_user.telegram_id,
            bought_datetime=datetime.now(timezone.utc),
            unique_id=400000
        )
        db_with_roles.add(bought)
        db_with_roles.commit()

        count = select_count_bought_items()
        assert count == 1

    def test_select_count_bought_items_empty(self, db_session):
        count = select_count_bought_items()
        assert count == 0


@pytest.mark.unit
@pytest.mark.database
class TestOrderRevenue:
    """Tests for revenue/order read functions"""

    def test_select_today_orders_no_orders(self, db_session):
        result = select_today_orders("2025-01-01")
        assert result == Decimal(0)

    def test_select_today_orders_with_data(self, db_with_roles, test_user, test_goods):
        now = datetime.now(timezone.utc)
        bought = BoughtGoods(
            name=test_goods.name,
            value="v",
            price=Decimal("50.00"),
            buyer_id=test_user.telegram_id,
            bought_datetime=now,
            unique_id=500000
        )
        db_with_roles.add(bought)
        db_with_roles.commit()

        today_str = now.strftime("%Y-%m-%d")
        result = select_today_orders(today_str)
        assert result == Decimal("50.00")

    def test_select_all_orders_empty(self, db_session):
        result = select_all_orders()
        assert result == Decimal(0)

    def test_select_all_orders_with_data(self, db_with_roles, test_user, test_goods):
        for i in range(3):
            bought = BoughtGoods(
                name=test_goods.name,
                value=f"v{i}",
                price=Decimal("25.00"),
                buyer_id=test_user.telegram_id,
                bought_datetime=datetime.now(timezone.utc),
                unique_id=600000 + i
            )
            db_with_roles.add(bought)
        db_with_roles.commit()

        result = select_all_orders()
        assert result == Decimal("75.00")


@pytest.mark.unit
@pytest.mark.database
class TestOperations:
    """Tests for operations read functions"""

    def test_select_today_operations_empty(self, db_session):
        result = select_today_operations("2025-01-01")
        assert result == Decimal(0)

    def test_select_today_operations_with_data(self, db_with_roles, test_user):
        now = datetime.now(timezone.utc)
        op = Operations(
            user_id=test_user.telegram_id,
            operation_value=Decimal("100.00"),
            operation_time=now
        )
        db_with_roles.add(op)
        db_with_roles.commit()

        today_str = now.strftime("%Y-%m-%d")
        result = select_today_operations(today_str)
        assert result == Decimal("100.00")

    def test_select_all_operations_empty(self, db_session):
        result = select_all_operations()
        assert result == Decimal(0)

    def test_select_all_operations_with_data(self, db_with_roles, test_user):
        op = Operations(
            user_id=test_user.telegram_id,
            operation_value=Decimal("200.00"),
            operation_time=datetime.now(timezone.utc)
        )
        db_with_roles.add(op)
        db_with_roles.commit()

        result = select_all_operations()
        assert result == Decimal("200.00")

    def test_select_user_operations(self, db_with_roles, test_user):
        for val in [Decimal("10.00"), Decimal("20.00"), Decimal("30.00")]:
            op = Operations(
                user_id=test_user.telegram_id,
                operation_value=val,
                operation_time=datetime.now(timezone.utc)
            )
            db_with_roles.add(op)
        db_with_roles.commit()

        ops = select_user_operations(test_user.telegram_id)
        assert len(ops) == 3

    def test_select_user_operations_empty(self, db_with_roles, test_user):
        ops = select_user_operations(test_user.telegram_id)
        assert ops == []


@pytest.mark.unit
@pytest.mark.database
class TestReferrals:
    """Tests for referral read functions"""

    def test_check_user_referrals_none(self, db_with_roles, test_user):
        count = check_user_referrals(test_user.telegram_id)
        assert count == 0

    def test_check_user_referrals_with_referrals(self, db_with_roles, test_user):
        # Create users who were referred by test_user
        for i in range(3):
            ref_user = User(
                telegram_id=700000 + i,
                role_id=1,
                registration_date=datetime.now(timezone.utc),
                referral_id=test_user.telegram_id
            )
            db_with_roles.add(ref_user)
        db_with_roles.commit()

        count = check_user_referrals(test_user.telegram_id)
        assert count == 3

    def test_get_user_referral_none(self, db_with_roles, test_user):
        ref = get_user_referral(test_user.telegram_id)
        assert ref is None

    def test_get_user_referral_exists(self, db_with_roles, test_user):
        referred = User(
            telegram_id=750000,
            role_id=1,
            registration_date=datetime.now(timezone.utc),
            referral_id=test_user.telegram_id
        )
        db_with_roles.add(referred)
        db_with_roles.commit()

        ref = get_user_referral(750000)
        assert ref == test_user.telegram_id

    def test_get_user_referral_nonexistent_user(self, db_with_roles):
        ref = get_user_referral(999999999)
        assert ref is None


@pytest.mark.unit
@pytest.mark.database
class TestReferralEarnings:
    """Tests for referral earnings stats"""

    def test_get_referral_earnings_stats_empty(self, db_with_roles, test_user):
        stats = get_referral_earnings_stats(test_user.telegram_id)
        assert stats['total_earnings_count'] == 0
        assert stats['total_amount'] == Decimal(0)
        assert stats['total_original_amount'] == Decimal(0)
        assert stats['active_referrals_count'] == 0

    def test_get_referral_earnings_stats_with_data(self, db_with_roles, test_user, test_admin):
        earning = ReferralEarnings(
            referrer_id=test_user.telegram_id,
            referral_id=test_admin.telegram_id,
            amount=Decimal("5.00"),
            original_amount=Decimal("100.00")
        )
        db_with_roles.add(earning)
        db_with_roles.commit()

        stats = get_referral_earnings_stats(test_user.telegram_id)
        assert stats['total_earnings_count'] == 1
        assert stats['total_amount'] == Decimal("5.00")
        assert stats['total_original_amount'] == Decimal("100.00")
        assert stats['active_referrals_count'] == 1

    def test_get_one_referral_earning_not_found(self, db_session):
        result = get_one_referral_earning(999)
        assert result is None

    def test_get_one_referral_earning_exists(self, db_with_roles, test_user, test_admin):
        earning = ReferralEarnings(
            referrer_id=test_user.telegram_id,
            referral_id=test_admin.telegram_id,
            amount=Decimal("10.00"),
            original_amount=Decimal("200.00")
        )
        db_with_roles.add(earning)
        db_with_roles.commit()

        result = get_one_referral_earning(earning.id)
        assert result is not None
        assert Decimal(str(result['amount'])) == Decimal("10.00")


@pytest.mark.unit
@pytest.mark.database
class TestBotSettings:
    """Tests for bot settings read functions"""

    def test_get_reference_bonus_percent_default(self, db_session):
        result = get_reference_bonus_percent()
        assert result == Decimal(0)

    def test_get_reference_bonus_percent_configured(self, db_session, test_bot_settings):
        result = get_reference_bonus_percent()
        assert result == Decimal("5")

    def test_get_bot_setting_string(self, db_session, test_bot_settings):
        result = get_bot_setting('timezone')
        assert result == 'Asia/Bangkok'

    def test_get_bot_setting_int(self, db_session, test_bot_settings):
        result = get_bot_setting('cash_order_timeout_hours', value_type=int)
        assert result == 24
        assert isinstance(result, int)

    def test_get_bot_setting_decimal(self, db_session, test_bot_settings):
        result = get_bot_setting('reference_bonus_percent', value_type=Decimal)
        assert result == Decimal("5")

    def test_get_bot_setting_float(self, db_session, test_bot_settings):
        result = get_bot_setting('reference_bonus_percent', value_type=float)
        assert result == 5.0

    def test_get_bot_setting_not_found_with_default(self, db_session):
        result = get_bot_setting('nonexistent', default='fallback')
        assert result == 'fallback'

    def test_get_bot_setting_not_found_no_default(self, db_session):
        result = get_bot_setting('nonexistent')
        assert result is None

    def test_get_bot_setting_int_default_conversion(self, db_session):
        result = get_bot_setting('nonexistent', default='42', value_type=int)
        assert result == 42

    def test_get_bot_setting_invalid_value_returns_default(self, db_session):
        setting = BotSettings(setting_key='bad_int', setting_value='not_a_number')
        db_session.add(setting)
        db_session.commit()

        result = get_bot_setting('bad_int', default='0', value_type=int)
        assert result == 0


@pytest.mark.unit
@pytest.mark.database
class TestCartItems:
    """Tests for cart read functions"""

    @pytest.mark.asyncio
    async def test_get_cart_items_with_items(self, db_session, test_shopping_cart, test_goods):
        items = await get_cart_items(test_shopping_cart.user_id)
        assert len(items) == 1
        assert items[0]['item_name'] == test_goods.name
        assert items[0]['quantity'] == 2
        assert 'price' in items[0]
        assert 'total' in items[0]
        assert 'cart_id' in items[0]

    @pytest.mark.asyncio
    async def test_get_cart_items_empty_cart(self, db_with_roles, test_user):
        items = await get_cart_items(test_user.telegram_id)
        assert items == []

    @pytest.mark.asyncio
    async def test_calculate_cart_total(self, db_session, test_shopping_cart, test_goods):
        total = await calculate_cart_total(test_shopping_cart.user_id)
        expected = test_goods.price * test_shopping_cart.quantity
        assert total == expected

    @pytest.mark.asyncio
    async def test_calculate_cart_total_empty(self, db_with_roles, test_user):
        total = await calculate_cart_total(test_user.telegram_id)
        assert total == 0


@pytest.mark.unit
@pytest.mark.database
class TestUserOrders:
    """Tests for order query functions"""

    @pytest.mark.asyncio
    async def test_query_user_orders_with_orders(self, db_session, test_order, test_user):
        orders = await query_user_orders(test_user.telegram_id)
        assert len(orders) == 1
        assert orders[0]['order_code'] == "TEST01"
        assert orders[0]['order_status'] == "pending"
        assert len(orders[0]['items']) >= 1

    @pytest.mark.asyncio
    async def test_query_user_orders_no_orders(self, db_with_roles, test_user):
        orders = await query_user_orders(test_user.telegram_id)
        assert orders == []

    @pytest.mark.asyncio
    async def test_query_user_orders_status_filter(self, db_session, test_order, test_user):
        # Filter by the status that exists
        orders = await query_user_orders(test_user.telegram_id, status="pending")
        assert len(orders) == 1

        # Filter by status that doesn't exist
        orders = await query_user_orders(test_user.telegram_id, status="completed")
        assert len(orders) == 0

    @pytest.mark.asyncio
    async def test_query_user_orders_pagination(self, db_with_roles, test_user, test_category):
        goods = Goods(
            name="Paginate Product",
            price=Decimal("10.00"),
            description="desc",
            category_name=test_category.name,
            stock_quantity=100
        )
        db_with_roles.add(goods)
        db_with_roles.commit()

        # Create multiple orders
        for i in range(5):
            order = Order(
                buyer_id=test_user.telegram_id,
                total_price=Decimal("10.00"),
                payment_method="cash",
                delivery_address="Test",
                phone_number="0812345678",
                order_status="pending",
                order_code=f"PG{i:04d}"
            )
            db_with_roles.add(order)
        db_with_roles.commit()

        # Limit to 2
        orders = await query_user_orders(test_user.telegram_id, limit=2)
        assert len(orders) == 2

        # Offset
        orders = await query_user_orders(test_user.telegram_id, limit=2, offset=3)
        assert len(orders) == 2

    @pytest.mark.asyncio
    async def test_count_user_orders_all(self, db_session, test_order, test_user):
        count = await count_user_orders(test_user.telegram_id)
        assert count == 1

    @pytest.mark.asyncio
    async def test_count_user_orders_by_status(self, db_session, test_order, test_user):
        count = await count_user_orders(test_user.telegram_id, status="pending")
        assert count == 1

        count = await count_user_orders(test_user.telegram_id, status="completed")
        assert count == 0

    @pytest.mark.asyncio
    async def test_count_user_orders_no_orders(self, db_with_roles, test_user):
        count = await count_user_orders(test_user.telegram_id)
        assert count == 0


@pytest.mark.unit
@pytest.mark.database
class TestCachedFunctions:
    """Tests for async_cached wrapper functions"""

    @pytest.mark.asyncio
    async def test_check_user_cached(self, db_with_roles, test_user):
        with patch('bot.database.methods.read.get_cache_manager', return_value=None):
            result = await check_user_cached(test_user.telegram_id)
            assert result is not None
            assert result['telegram_id'] == test_user.telegram_id

    @pytest.mark.asyncio
    async def test_check_role_cached(self, db_with_roles, test_user):
        with patch('bot.database.methods.read.get_cache_manager', return_value=None):
            result = await check_role_cached(test_user.telegram_id)
            assert result == 1

    @pytest.mark.asyncio
    async def test_select_item_values_amount_cached(self, db_session, test_goods):
        with patch('bot.database.methods.read.get_cache_manager', return_value=None):
            result = await select_item_values_amount_cached(test_goods.name)
            assert result == 100
