"""Tests for coupon validation, discount calculation, and usage recording."""
import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock


@pytest.mark.unit
class TestValidateCoupon:
    """Tests for validate_coupon()."""

    def _make_coupon(self, **overrides):
        """Build a mock Coupon with sensible defaults."""
        coupon = MagicMock()
        coupon.id = overrides.get("id", 1)
        coupon.code = overrides.get("code", "SAVE10")
        coupon.is_active = overrides.get("is_active", True)
        coupon.valid_from = overrides.get("valid_from", None)
        coupon.valid_until = overrides.get("valid_until", None)
        coupon.max_uses = overrides.get("max_uses", None)
        coupon.current_uses = overrides.get("current_uses", 0)
        coupon.max_uses_per_user = overrides.get("max_uses_per_user", 1)
        coupon.min_order = overrides.get("min_order", 0)
        coupon.discount_type = overrides.get("discount_type", "percent")
        coupon.discount_value = overrides.get("discount_value", 10)
        coupon.max_discount = overrides.get("max_discount", None)
        return coupon

    def _patch_session(self, coupon, user_usage_count=0):
        """Return a patch context manager for Database().session() with a mock session."""
        mock_session = MagicMock()
        # coupon query
        mock_query_coupon = MagicMock()
        mock_query_coupon.filter.return_value.first.return_value = coupon

        # usage count query
        mock_query_usage = MagicMock()
        mock_query_usage.filter.return_value.count.return_value = user_usage_count

        def query_side_effect(model):
            from bot.database.models.main import Coupon, CouponUsage
            if model is CouponUsage:
                return mock_query_usage
            return mock_query_coupon

        mock_session.query.side_effect = query_side_effect
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)

        mock_db = MagicMock()
        mock_db.session.return_value = mock_session
        return patch("bot.utils.coupon_utils.Database", return_value=mock_db)

    # --- Happy path ---

    def test_valid_coupon_returns_true(self):
        coupon = self._make_coupon()
        with self._patch_session(coupon):
            from bot.utils.coupon_utils import validate_coupon
            valid, msg, obj = validate_coupon("SAVE10", user_id=100, order_total=Decimal("500"))
        assert valid is True
        assert msg == ""
        assert obj is coupon

    # --- Not found ---

    def test_coupon_not_found(self):
        with self._patch_session(None):
            from bot.utils.coupon_utils import validate_coupon
            valid, msg, obj = validate_coupon("NOEXIST", user_id=100, order_total=Decimal("500"))
        assert valid is False
        assert msg == "coupon.error.not_found"
        assert obj is None

    # --- Inactive ---

    def test_inactive_coupon(self):
        coupon = self._make_coupon(is_active=False)
        with self._patch_session(coupon):
            from bot.utils.coupon_utils import validate_coupon
            valid, msg, _ = validate_coupon("SAVE10", user_id=100, order_total=Decimal("500"))
        assert valid is False
        assert msg == "coupon.error.inactive"

    # --- Expiry ---

    def test_coupon_not_yet_valid(self):
        future = datetime.now(timezone.utc) + timedelta(days=7)
        coupon = self._make_coupon(valid_from=future)
        with self._patch_session(coupon):
            from bot.utils.coupon_utils import validate_coupon
            valid, msg, _ = validate_coupon("SAVE10", user_id=100, order_total=Decimal("500"))
        assert valid is False
        assert msg == "coupon.error.not_yet_valid"

    def test_coupon_expired(self):
        past = datetime.now(timezone.utc) - timedelta(days=1)
        coupon = self._make_coupon(valid_until=past)
        with self._patch_session(coupon):
            from bot.utils.coupon_utils import validate_coupon
            valid, msg, _ = validate_coupon("SAVE10", user_id=100, order_total=Decimal("500"))
        assert valid is False
        assert msg == "coupon.error.expired"

    def test_coupon_within_validity_window(self):
        past = datetime.now(timezone.utc) - timedelta(days=1)
        future = datetime.now(timezone.utc) + timedelta(days=7)
        coupon = self._make_coupon(valid_from=past, valid_until=future)
        with self._patch_session(coupon):
            from bot.utils.coupon_utils import validate_coupon
            valid, msg, _ = validate_coupon("SAVE10", user_id=100, order_total=Decimal("500"))
        assert valid is True

    # --- Global usage limit ---

    def test_max_uses_reached(self):
        coupon = self._make_coupon(max_uses=5, current_uses=5)
        with self._patch_session(coupon):
            from bot.utils.coupon_utils import validate_coupon
            valid, msg, _ = validate_coupon("SAVE10", user_id=100, order_total=Decimal("500"))
        assert valid is False
        assert msg == "coupon.error.max_uses_reached"

    def test_max_uses_not_yet_reached(self):
        coupon = self._make_coupon(max_uses=5, current_uses=4)
        with self._patch_session(coupon):
            from bot.utils.coupon_utils import validate_coupon
            valid, msg, _ = validate_coupon("SAVE10", user_id=100, order_total=Decimal("500"))
        assert valid is True

    def test_unlimited_global_uses(self):
        coupon = self._make_coupon(max_uses=None, current_uses=999)
        with self._patch_session(coupon):
            from bot.utils.coupon_utils import validate_coupon
            valid, msg, _ = validate_coupon("SAVE10", user_id=100, order_total=Decimal("500"))
        assert valid is True

    # --- Per-user usage limit ---

    def test_per_user_limit_reached(self):
        coupon = self._make_coupon(max_uses_per_user=1)
        with self._patch_session(coupon, user_usage_count=1):
            from bot.utils.coupon_utils import validate_coupon
            valid, msg, _ = validate_coupon("SAVE10", user_id=100, order_total=Decimal("500"))
        assert valid is False
        assert msg == "coupon.error.already_used"

    def test_per_user_limit_not_reached(self):
        coupon = self._make_coupon(max_uses_per_user=3)
        with self._patch_session(coupon, user_usage_count=2):
            from bot.utils.coupon_utils import validate_coupon
            valid, msg, _ = validate_coupon("SAVE10", user_id=100, order_total=Decimal("500"))
        assert valid is True

    # --- Minimum order ---

    def test_order_below_minimum(self):
        coupon = self._make_coupon(min_order=100)
        with self._patch_session(coupon):
            from bot.utils.coupon_utils import validate_coupon
            valid, msg, _ = validate_coupon("SAVE10", user_id=100, order_total=Decimal("50"))
        assert valid is False
        assert msg == "coupon.error.min_order_not_met"

    def test_order_at_minimum(self):
        coupon = self._make_coupon(min_order=100)
        with self._patch_session(coupon):
            from bot.utils.coupon_utils import validate_coupon
            valid, msg, _ = validate_coupon("SAVE10", user_id=100, order_total=Decimal("100"))
        assert valid is True

    def test_min_order_none_treated_as_zero(self):
        coupon = self._make_coupon(min_order=None)
        with self._patch_session(coupon):
            from bot.utils.coupon_utils import validate_coupon
            valid, msg, _ = validate_coupon("SAVE10", user_id=100, order_total=Decimal("1"))
        assert valid is True

    # --- Code case-insensitivity ---

    def test_code_uppercased_for_lookup(self):
        """validate_coupon should uppercase the code before querying."""
        coupon = self._make_coupon()
        with self._patch_session(coupon) as db_patch:
            from bot.utils.coupon_utils import validate_coupon
            valid, msg, _ = validate_coupon("save10", user_id=100, order_total=Decimal("500"))
        assert valid is True


@pytest.mark.unit
class TestCalculateDiscount:
    """Tests for calculate_discount()."""

    def _make_coupon(self, **overrides):
        coupon = MagicMock()
        coupon.discount_type = overrides.get("discount_type", "percent")
        coupon.discount_value = overrides.get("discount_value", 10)
        coupon.max_discount = overrides.get("max_discount", None)
        return coupon

    def test_percentage_discount(self):
        from bot.utils.coupon_utils import calculate_discount
        coupon = self._make_coupon(discount_type="percent", discount_value=10)
        result = calculate_discount(coupon, Decimal("1000"))
        assert result == Decimal("100.00")

    def test_percentage_discount_with_max_cap(self):
        from bot.utils.coupon_utils import calculate_discount
        coupon = self._make_coupon(discount_type="percent", discount_value=20, max_discount=50)
        result = calculate_discount(coupon, Decimal("1000"))
        # 20% of 1000 = 200, but capped at 50
        assert result == Decimal("50.00")

    def test_percentage_discount_below_max_cap(self):
        from bot.utils.coupon_utils import calculate_discount
        coupon = self._make_coupon(discount_type="percent", discount_value=5, max_discount=100)
        result = calculate_discount(coupon, Decimal("500"))
        # 5% of 500 = 25, under 100 cap
        assert result == Decimal("25.00")

    def test_fixed_discount_below_order_total(self):
        from bot.utils.coupon_utils import calculate_discount
        coupon = self._make_coupon(discount_type="fixed", discount_value=50)
        result = calculate_discount(coupon, Decimal("200"))
        assert result == Decimal("50.00")

    def test_fixed_discount_exceeds_order_total(self):
        from bot.utils.coupon_utils import calculate_discount
        coupon = self._make_coupon(discount_type="fixed", discount_value=300)
        result = calculate_discount(coupon, Decimal("200"))
        # Fixed discount capped at order total
        assert result == Decimal("200.00")

    def test_percentage_100_percent(self):
        from bot.utils.coupon_utils import calculate_discount
        coupon = self._make_coupon(discount_type="percent", discount_value=100)
        result = calculate_discount(coupon, Decimal("500"))
        assert result == Decimal("500.00")

    def test_zero_order_total(self):
        from bot.utils.coupon_utils import calculate_discount
        coupon = self._make_coupon(discount_type="percent", discount_value=10)
        result = calculate_discount(coupon, Decimal("0"))
        assert result == Decimal("0.00")

    def test_fixed_zero_discount_value(self):
        from bot.utils.coupon_utils import calculate_discount
        coupon = self._make_coupon(discount_type="fixed", discount_value=0)
        result = calculate_discount(coupon, Decimal("500"))
        assert result == Decimal("0.00")

    def test_result_quantized_to_two_decimals(self):
        from bot.utils.coupon_utils import calculate_discount
        coupon = self._make_coupon(discount_type="percent", discount_value=33)
        result = calculate_discount(coupon, Decimal("100"))
        # 33% of 100 = 33.00 — already exact, but verify quantization
        assert result == Decimal("33.00")
        assert result.as_tuple().exponent == -2

    def test_percentage_with_rounding(self):
        from bot.utils.coupon_utils import calculate_discount
        coupon = self._make_coupon(discount_type="percent", discount_value=33)
        result = calculate_discount(coupon, Decimal("99.99"))
        # 33% of 99.99 = 32.9967 → 33.00 rounded
        assert result.as_tuple().exponent == -2


@pytest.mark.unit
class TestApplyCoupon:
    """Tests for apply_coupon()."""

    def test_successful_application(self):
        mock_session = MagicMock()
        mock_coupon = MagicMock()
        mock_coupon.current_uses = 3
        mock_session.query.return_value.filter.return_value.first.return_value = mock_coupon
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)

        mock_db = MagicMock()
        mock_db.session.return_value = mock_session

        with patch("bot.utils.coupon_utils.Database", return_value=mock_db):
            from bot.utils.coupon_utils import apply_coupon
            result = apply_coupon(coupon_id=1, user_id=100, order_id=50, discount=Decimal("25.00"))

        assert result is True
        mock_session.add.assert_called_once()
        assert mock_coupon.current_uses == 4
        mock_session.commit.assert_called_once()

    def test_coupon_not_found_returns_false(self):
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)

        mock_db = MagicMock()
        mock_db.session.return_value = mock_session

        with patch("bot.utils.coupon_utils.Database", return_value=mock_db):
            from bot.utils.coupon_utils import apply_coupon
            result = apply_coupon(coupon_id=999, user_id=100, order_id=50, discount=Decimal("10.00"))

        assert result is False

    def test_exception_returns_false(self):
        mock_db = MagicMock()
        mock_db.session.side_effect = RuntimeError("DB connection failed")

        with patch("bot.utils.coupon_utils.Database", return_value=mock_db):
            from bot.utils.coupon_utils import apply_coupon
            result = apply_coupon(coupon_id=1, user_id=100, order_id=50, discount=Decimal("10.00"))

        assert result is False

    def test_current_uses_none_increments_to_one(self):
        """When current_uses is None (legacy row), it should become 1."""
        mock_session = MagicMock()
        mock_coupon = MagicMock()
        mock_coupon.current_uses = None
        mock_session.query.return_value.filter.return_value.first.return_value = mock_coupon
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)

        mock_db = MagicMock()
        mock_db.session.return_value = mock_session

        with patch("bot.utils.coupon_utils.Database", return_value=mock_db):
            from bot.utils.coupon_utils import apply_coupon
            result = apply_coupon(coupon_id=1, user_id=100, order_id=50, discount=Decimal("5.00"))

        assert result is True
        assert mock_coupon.current_uses == 1
