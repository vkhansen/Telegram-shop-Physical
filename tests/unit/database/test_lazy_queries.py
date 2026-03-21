"""
Tests for bot/database/methods/lazy_queries.py - paginated query functions.
"""
import pytest
from decimal import Decimal
from datetime import datetime, timezone

from bot.database.methods.lazy_queries import (
    query_categories,
    query_items_in_category,
    query_user_bought_items,
    query_all_users,
    query_admins,
    query_user_referrals,
    query_referral_earnings_from_user,
    query_all_referral_earnings,
)
from bot.database.models.main import (
    User, Goods, Categories, BoughtGoods, ReferralEarnings,
)


@pytest.mark.unit
@pytest.mark.database
class TestQueryCategories:
    """Tests for query_categories()"""

    @pytest.mark.asyncio
    async def test_query_categories_empty(self, db_session):
        result = await query_categories()
        assert result == []

    @pytest.mark.asyncio
    async def test_query_categories_returns_names(self, db_session, multiple_categories):
        result = await query_categories()
        assert len(result) == 3
        assert all(isinstance(name, str) for name in result)

    @pytest.mark.asyncio
    async def test_query_categories_sorted_alphabetically(self, db_session, multiple_categories):
        result = await query_categories()
        assert result == sorted(result)

    @pytest.mark.asyncio
    async def test_query_categories_count_only(self, db_session, multiple_categories):
        count = await query_categories(count_only=True)
        assert count == 3

    @pytest.mark.asyncio
    async def test_query_categories_count_only_empty(self, db_session):
        count = await query_categories(count_only=True)
        assert count == 0

    @pytest.mark.asyncio
    async def test_query_categories_pagination(self, db_session, multiple_categories):
        page1 = await query_categories(offset=0, limit=2)
        assert len(page1) == 2

        page2 = await query_categories(offset=2, limit=2)
        assert len(page2) == 1

    @pytest.mark.asyncio
    async def test_query_categories_offset_beyond_data(self, db_session, multiple_categories):
        result = await query_categories(offset=100, limit=10)
        assert result == []


@pytest.mark.unit
@pytest.mark.database
class TestQueryItemsInCategory:
    """Tests for query_items_in_category()"""

    @pytest.mark.asyncio
    async def test_query_items_empty_category(self, db_session, test_category):
        result = await query_items_in_category(test_category.name)
        assert result == []

    @pytest.mark.asyncio
    async def test_query_items_with_products(self, db_session, test_category, multiple_products):
        result = await query_items_in_category(test_category.name)
        assert len(result) == 5
        assert all(isinstance(name, str) for name in result)

    @pytest.mark.asyncio
    async def test_query_items_sorted_alphabetically(self, db_session, test_category, multiple_products):
        result = await query_items_in_category(test_category.name)
        assert result == sorted(result)

    @pytest.mark.asyncio
    async def test_query_items_count_only(self, db_session, test_category, multiple_products):
        count = await query_items_in_category(test_category.name, count_only=True)
        assert count == 5

    @pytest.mark.asyncio
    async def test_query_items_count_only_empty(self, db_session, test_category):
        count = await query_items_in_category(test_category.name, count_only=True)
        assert count == 0

    @pytest.mark.asyncio
    async def test_query_items_pagination(self, db_session, test_category, multiple_products):
        page1 = await query_items_in_category(test_category.name, offset=0, limit=3)
        assert len(page1) == 3

        page2 = await query_items_in_category(test_category.name, offset=3, limit=3)
        assert len(page2) == 2

    @pytest.mark.asyncio
    async def test_query_items_nonexistent_category(self, db_session):
        result = await query_items_in_category("Nonexistent")
        assert result == []


@pytest.mark.unit
@pytest.mark.database
class TestQueryAllUsers:
    """Tests for query_all_users()"""

    @pytest.mark.asyncio
    async def test_query_all_users_empty(self, db_with_roles):
        result = await query_all_users()
        assert result == []

    @pytest.mark.asyncio
    async def test_query_all_users_returns_ids(self, db_with_roles, test_user, test_admin):
        result = await query_all_users()
        assert len(result) == 2
        assert test_user.telegram_id in result
        assert test_admin.telegram_id in result

    @pytest.mark.asyncio
    async def test_query_all_users_count_only(self, db_with_roles, test_user, test_admin):
        count = await query_all_users(count_only=True)
        assert count == 2

    @pytest.mark.asyncio
    async def test_query_all_users_pagination(self, db_with_roles, test_user, test_admin):
        page1 = await query_all_users(offset=0, limit=1)
        assert len(page1) == 1

        page2 = await query_all_users(offset=1, limit=1)
        assert len(page2) == 1

    @pytest.mark.asyncio
    async def test_query_all_users_sorted_by_id(self, db_with_roles, test_user, test_admin):
        result = await query_all_users()
        assert result == sorted(result)


@pytest.mark.unit
@pytest.mark.database
class TestQueryAdmins:
    """Tests for query_admins()"""

    @pytest.mark.asyncio
    async def test_query_admins_empty(self, db_with_roles, test_user):
        """Regular users should not appear in admin query"""
        result = await query_admins()
        assert result == []

    @pytest.mark.asyncio
    async def test_query_admins_with_admin(self, db_with_roles, test_user, test_admin):
        result = await query_admins()
        assert len(result) == 1
        assert test_admin.telegram_id in result

    @pytest.mark.asyncio
    async def test_query_admins_count_only(self, db_with_roles, test_admin):
        count = await query_admins(count_only=True)
        assert count == 1

    @pytest.mark.asyncio
    async def test_query_admins_excludes_regular_users(self, db_with_roles, test_user, test_admin):
        result = await query_admins()
        assert test_user.telegram_id not in result


@pytest.mark.unit
@pytest.mark.database
class TestQueryUserReferrals:
    """Tests for query_user_referrals()"""

    @pytest.mark.asyncio
    async def test_query_user_referrals_none(self, db_with_roles, test_user):
        result = await query_user_referrals(test_user.telegram_id)
        assert result == []

    @pytest.mark.asyncio
    async def test_query_user_referrals_count_only_none(self, db_with_roles, test_user):
        count = await query_user_referrals(test_user.telegram_id, count_only=True)
        assert count == 0

    @pytest.mark.asyncio
    async def test_query_user_referrals_with_referrals(self, db_with_roles, test_user):
        # Create referred users
        for i in range(3):
            ref_user = User(
                telegram_id=800100 + i,
                role_id=1,
                registration_date=datetime.now(timezone.utc),
                referral_id=test_user.telegram_id
            )
            db_with_roles.add(ref_user)
        db_with_roles.commit()

        result = await query_user_referrals(test_user.telegram_id)
        assert len(result) == 3
        assert all('telegram_id' in r for r in result)
        assert all('total_earned' in r for r in result)

    @pytest.mark.asyncio
    async def test_query_user_referrals_count_only(self, db_with_roles, test_user):
        for i in range(2):
            ref_user = User(
                telegram_id=800200 + i,
                role_id=1,
                registration_date=datetime.now(timezone.utc),
                referral_id=test_user.telegram_id
            )
            db_with_roles.add(ref_user)
        db_with_roles.commit()

        count = await query_user_referrals(test_user.telegram_id, count_only=True)
        assert count == 2

    @pytest.mark.asyncio
    async def test_query_user_referrals_sorted_by_earnings(self, db_with_roles, test_user):
        # Create referrals with different earnings
        ref1 = User(telegram_id=800301, role_id=1,
                     registration_date=datetime.now(timezone.utc),
                     referral_id=test_user.telegram_id)
        ref2 = User(telegram_id=800302, role_id=1,
                     registration_date=datetime.now(timezone.utc),
                     referral_id=test_user.telegram_id)
        db_with_roles.add_all([ref1, ref2])
        db_with_roles.commit()

        # Add earnings (ref2 earns more)
        e1 = ReferralEarnings(referrer_id=test_user.telegram_id, referral_id=800301,
                              amount=Decimal("5.00"), original_amount=Decimal("100.00"))
        e2 = ReferralEarnings(referrer_id=test_user.telegram_id, referral_id=800302,
                              amount=Decimal("50.00"), original_amount=Decimal("1000.00"))
        db_with_roles.add_all([e1, e2])
        db_with_roles.commit()

        result = await query_user_referrals(test_user.telegram_id)
        assert len(result) == 2
        # Should be sorted by total_earned descending
        assert result[0]['total_earned'] >= result[1]['total_earned']


@pytest.mark.unit
@pytest.mark.database
class TestQueryReferralEarnings:
    """Tests for referral earnings query functions"""

    @pytest.mark.asyncio
    async def test_query_referral_earnings_from_user_empty(self, db_with_roles, test_user, test_admin):
        result = await query_referral_earnings_from_user(test_user.telegram_id, test_admin.telegram_id)
        assert result == []

    @pytest.mark.asyncio
    async def test_query_referral_earnings_from_user_count_empty(self, db_with_roles, test_user, test_admin):
        count = await query_referral_earnings_from_user(
            test_user.telegram_id, test_admin.telegram_id, count_only=True
        )
        assert count == 0

    @pytest.mark.asyncio
    async def test_query_referral_earnings_from_user_with_data(self, db_with_roles, test_user, test_admin):
        for i in range(3):
            e = ReferralEarnings(
                referrer_id=test_user.telegram_id,
                referral_id=test_admin.telegram_id,
                amount=Decimal("10.00"),
                original_amount=Decimal("200.00")
            )
            db_with_roles.add(e)
        db_with_roles.commit()

        result = await query_referral_earnings_from_user(
            test_user.telegram_id, test_admin.telegram_id
        )
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_query_referral_earnings_from_user_count(self, db_with_roles, test_user, test_admin):
        for i in range(2):
            e = ReferralEarnings(
                referrer_id=test_user.telegram_id,
                referral_id=test_admin.telegram_id,
                amount=Decimal("5.00"),
                original_amount=Decimal("100.00")
            )
            db_with_roles.add(e)
        db_with_roles.commit()

        count = await query_referral_earnings_from_user(
            test_user.telegram_id, test_admin.telegram_id, count_only=True
        )
        assert count == 2

    @pytest.mark.asyncio
    async def test_query_all_referral_earnings_empty(self, db_with_roles, test_user):
        result = await query_all_referral_earnings(test_user.telegram_id)
        assert result == []

    @pytest.mark.asyncio
    async def test_query_all_referral_earnings_count_empty(self, db_with_roles, test_user):
        count = await query_all_referral_earnings(test_user.telegram_id, count_only=True)
        assert count == 0

    @pytest.mark.asyncio
    async def test_query_all_referral_earnings_with_data(self, db_with_roles, test_user, test_admin):
        e = ReferralEarnings(
            referrer_id=test_user.telegram_id,
            referral_id=test_admin.telegram_id,
            amount=Decimal("15.00"),
            original_amount=Decimal("300.00")
        )
        db_with_roles.add(e)
        db_with_roles.commit()

        result = await query_all_referral_earnings(test_user.telegram_id)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_query_all_referral_earnings_pagination(self, db_with_roles, test_user, test_admin):
        for i in range(5):
            e = ReferralEarnings(
                referrer_id=test_user.telegram_id,
                referral_id=test_admin.telegram_id,
                amount=Decimal("1.00"),
                original_amount=Decimal("20.00")
            )
            db_with_roles.add(e)
        db_with_roles.commit()

        page1 = await query_all_referral_earnings(test_user.telegram_id, offset=0, limit=3)
        assert len(page1) == 3

        page2 = await query_all_referral_earnings(test_user.telegram_id, offset=3, limit=3)
        assert len(page2) == 2


@pytest.mark.unit
@pytest.mark.database
class TestQueryUserBoughtItems:
    """Tests for query_user_bought_items()"""

    @pytest.mark.asyncio
    async def test_query_user_bought_items_empty(self, db_with_roles, test_user):
        result = await query_user_bought_items(test_user.telegram_id)
        assert result == []

    @pytest.mark.asyncio
    async def test_query_user_bought_items_count_empty(self, db_with_roles, test_user):
        count = await query_user_bought_items(test_user.telegram_id, count_only=True)
        assert count == 0

    @pytest.mark.asyncio
    async def test_query_user_bought_items_with_data(self, db_with_roles, test_user, test_goods):
        for i in range(3):
            bought = BoughtGoods(
                name=test_goods.name,
                value=f"val_{i}",
                price=Decimal("10.00"),
                buyer_id=test_user.telegram_id,
                bought_datetime=datetime.now(timezone.utc),
                unique_id=900000 + i
            )
            db_with_roles.add(bought)
        db_with_roles.commit()

        result = await query_user_bought_items(test_user.telegram_id)
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_query_user_bought_items_count(self, db_with_roles, test_user, test_goods):
        for i in range(4):
            bought = BoughtGoods(
                name=test_goods.name,
                value=f"v_{i}",
                price=Decimal("10.00"),
                buyer_id=test_user.telegram_id,
                bought_datetime=datetime.now(timezone.utc),
                unique_id=910000 + i
            )
            db_with_roles.add(bought)
        db_with_roles.commit()

        count = await query_user_bought_items(test_user.telegram_id, count_only=True)
        assert count == 4

    @pytest.mark.asyncio
    async def test_query_user_bought_items_pagination(self, db_with_roles, test_user, test_goods):
        for i in range(5):
            bought = BoughtGoods(
                name=test_goods.name,
                value=f"pag_{i}",
                price=Decimal("10.00"),
                buyer_id=test_user.telegram_id,
                bought_datetime=datetime.now(timezone.utc),
                unique_id=920000 + i
            )
            db_with_roles.add(bought)
        db_with_roles.commit()

        page1 = await query_user_bought_items(test_user.telegram_id, offset=0, limit=3)
        assert len(page1) == 3

        page2 = await query_user_bought_items(test_user.telegram_id, offset=3, limit=3)
        assert len(page2) == 2
