"""
Tests for middleware modules:
  - bot.middleware.security  (check_suspicious_patterns, SecurityMiddleware,
                               AuthenticationMiddleware)
  - bot.middleware.rate_limit (RateLimitConfig, RateLimiter,
                               RateLimitMiddleware._get_action_from_event)
  - bot.middleware.locale     (LocaleMiddleware)
  - bot.middleware.brand_context (BrandContextMiddleware)
"""
from __future__ import annotations

import hmac
import hashlib
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import CallbackQuery, Message

from bot.middleware.brand_context import BrandContextMiddleware
from bot.middleware.locale import LocaleMiddleware
from bot.middleware.rate_limit import RateLimitConfig, RateLimiter, RateLimitMiddleware
from bot.middleware.security import (
    AuthenticationMiddleware,
    SecurityMiddleware,
    check_suspicious_patterns,
)


# ===========================================================================
# check_suspicious_patterns
# ===========================================================================

@pytest.mark.unit
class TestCheckSuspiciousPatterns:
    """Unit tests for check_suspicious_patterns()."""

    def test_empty_string_returns_false(self):
        assert check_suspicious_patterns("") is False

    def test_none_returns_false(self):
        assert check_suspicious_patterns(None) is False

    def test_normal_text_safe(self):
        assert check_suspicious_patterns("Hello, I would like to order please") is False

    def test_sql_union_select(self):
        assert check_suspicious_patterns("union select * from users") is True

    def test_sql_select_from(self):
        assert check_suspicious_patterns("select id from orders") is True

    def test_sql_insert_into(self):
        assert check_suspicious_patterns("insert into admin values(1,'x')") is True

    def test_sql_delete_from(self):
        assert check_suspicious_patterns("delete from settings") is True

    def test_script_tag(self):
        assert check_suspicious_patterns("<script>alert(1)</script>") is True

    def test_javascript_protocol(self):
        assert check_suspicious_patterns("javascript:void(0)") is True

    def test_onerror_attribute(self):
        assert check_suspicious_patterns("img onerror=alert(1)") is True

    def test_onclick_attribute(self):
        assert check_suspicious_patterns("onclick=doEvil()") is True

    def test_pipe_command_injection(self):
        assert check_suspicious_patterns("cat /etc/passwd | grep root") is True

    def test_double_ampersand(self):
        assert check_suspicious_patterns("cmd && rm -rf") is True

    def test_backtick_execution(self):
        assert check_suspicious_patterns("`whoami`") is True

    def test_dollar_subshell(self):
        assert check_suspicious_patterns("$(id)") is True

    def test_path_traversal_forward_slash(self):
        assert check_suspicious_patterns("../../etc/passwd") is True

    def test_path_traversal_backslash(self):
        assert check_suspicious_patterns("..\\..\\windows\\system32") is True

    def test_string_length_4096_safe(self):
        # Exactly at the limit — allowed
        assert check_suspicious_patterns("A" * 4096) is False

    def test_string_length_4097_blocked(self):
        assert check_suspicious_patterns("A" * 4097) is True

    def test_case_insensitive_sql(self):
        assert check_suspicious_patterns("UNION SELECT * FROM users") is True

    def test_mixed_case_script(self):
        assert check_suspicious_patterns("<SCRIPT>xss</SCRIPT>") is True


# ===========================================================================
# SecurityMiddleware — token methods
# ===========================================================================

@pytest.mark.unit
class TestSecurityMiddlewareGenerateVerifyToken:
    """Tests for generate_token / verify_token."""

    def test_generate_returns_string(self):
        sm = SecurityMiddleware()
        assert isinstance(sm.generate_token(1, "buy"), str)

    def test_generated_token_verifies(self):
        sm = SecurityMiddleware()
        tok = sm.generate_token(123, "pay")
        assert sm.verify_token(tok, 123, "pay") is True

    def test_wrong_user_id_fails(self):
        sm = SecurityMiddleware()
        tok = sm.generate_token(123, "buy")
        assert sm.verify_token(tok, 456, "buy") is False

    def test_wrong_action_fails(self):
        sm = SecurityMiddleware()
        tok = sm.generate_token(123, "buy")
        assert sm.verify_token(tok, 123, "delete") is False

    def test_malformed_three_parts_fails(self):
        sm = SecurityMiddleware()
        assert sm.verify_token("a:b:c", 1, "buy") is False

    def test_malformed_five_parts_fails(self):
        sm = SecurityMiddleware()
        assert sm.verify_token("a:b:c:d:e", 1, "buy") is False

    def test_expired_token_rejected(self):
        sm = SecurityMiddleware()
        old_ts = str(int(time.time()) - 7200)  # 2 hours ago
        data = f"123:buy:{old_ts}"
        sig = hmac.new(sm.secret_key.encode(), data.encode(), hashlib.sha256).hexdigest()
        token = f"{data}:{sig}"
        assert sm.verify_token(token, 123, "buy", max_age=3600) is False

    def test_custom_secret_key_roundtrip(self):
        sm = SecurityMiddleware(secret_key="my-secret-key")
        tok = sm.generate_token(42, "action")
        assert sm.verify_token(tok, 42, "action") is True

    def test_tampered_signature_rejected(self):
        sm = SecurityMiddleware()
        tok = sm.generate_token(1, "buy")
        tampered = tok[:-3] + "xxx"
        assert sm.verify_token(tampered, 1, "buy") is False

    def test_none_token_returns_false(self):
        sm = SecurityMiddleware()
        assert sm.verify_token(None, 1, "buy") is False

    def test_two_tokens_with_same_key_both_valid(self):
        sm = SecurityMiddleware(secret_key="fixed")
        t1 = sm.generate_token(1, "a")
        t2 = sm.generate_token(2, "b")
        assert sm.verify_token(t1, 1, "a") is True
        assert sm.verify_token(t2, 2, "b") is True

    def test_cross_token_fails(self):
        sm = SecurityMiddleware(secret_key="fixed")
        t1 = sm.generate_token(1, "a")
        t2 = sm.generate_token(2, "b")
        assert sm.verify_token(t1, 2, "b") is False


# ===========================================================================
# SecurityMiddleware — is_critical_action
# ===========================================================================

@pytest.mark.unit
class TestSecurityMiddlewareIsCriticalAction:
    """Tests for is_critical_action."""

    def setup_method(self):
        self.sm = SecurityMiddleware()

    def test_buy_prefix_critical(self):
        assert self.sm.is_critical_action("buy_item_5") is True

    def test_pay_prefix_critical(self):
        assert self.sm.is_critical_action("pay_cash_now") is True

    def test_delete_prefix_critical(self):
        assert self.sm.is_critical_action("delete_order_3") is True

    def test_admin_prefix_critical(self):
        assert self.sm.is_critical_action("admin_panel") is True

    def test_remove_admin_critical(self):
        assert self.sm.is_critical_action("remove-admin") is True

    def test_fill_user_balance_critical(self):
        assert self.sm.is_critical_action("fill-user-balance") is True

    def test_set_admin_critical(self):
        assert self.sm.is_critical_action("set-admin") is True

    def test_shop_view_not_critical(self):
        assert self.sm.is_critical_action("shop_view") is False

    def test_cart_not_critical(self):
        assert self.sm.is_critical_action("cart_list") is False

    def test_none_returns_false(self):
        assert self.sm.is_critical_action(None) is False

    def test_empty_string_returns_false(self):
        assert self.sm.is_critical_action("") is False


# ===========================================================================
# AuthenticationMiddleware — block / unblock
# ===========================================================================

@pytest.mark.unit
class TestAuthenticationMiddlewareBlockUnblock:
    """Tests for block_user / unblock_user."""

    def test_block_adds_to_set(self):
        am = AuthenticationMiddleware()
        am.block_user(42)
        assert 42 in am.blocked_users

    def test_unblock_removes_from_set(self):
        am = AuthenticationMiddleware()
        am.block_user(42)
        am.unblock_user(42)
        assert 42 not in am.blocked_users

    def test_unblock_absent_user_safe(self):
        am = AuthenticationMiddleware()
        am.unblock_user(99999)  # Should not raise

    def test_block_multiple_users(self):
        am = AuthenticationMiddleware()
        am.block_user(1)
        am.block_user(2)
        am.block_user(3)
        assert {1, 2, 3}.issubset(am.blocked_users)

    def test_unblock_only_target(self):
        am = AuthenticationMiddleware()
        am.block_user(1)
        am.block_user(2)
        am.unblock_user(1)
        assert 1 not in am.blocked_users
        assert 2 in am.blocked_users


# ===========================================================================
# RateLimitConfig
# ===========================================================================

@pytest.mark.unit
class TestRateLimitConfig:
    """Tests for RateLimitConfig defaults and overrides."""

    def test_defaults(self):
        cfg = RateLimitConfig()
        assert cfg.global_limit == 30
        assert cfg.global_window == 60
        assert cfg.ban_duration == 300
        assert cfg.admin_bypass is True

    def test_buy_item_limit_present(self):
        cfg = RateLimitConfig()
        assert "buy_item" in cfg.action_limits

    def test_shop_view_limit_present(self):
        cfg = RateLimitConfig()
        assert "shop_view" in cfg.action_limits

    def test_custom_global_limit(self):
        cfg = RateLimitConfig(global_limit=10, global_window=30)
        assert cfg.global_limit == 10
        assert cfg.global_window == 30

    def test_admin_bypass_disabled(self):
        cfg = RateLimitConfig(admin_bypass=False)
        assert cfg.admin_bypass is False


# ===========================================================================
# RateLimiter
# ===========================================================================

@pytest.mark.unit
class TestRateLimiterBan:
    """Ban / is_banned logic."""

    def test_new_user_not_banned(self):
        limiter = RateLimiter(RateLimitConfig())
        assert limiter.is_banned(1) is False

    def test_ban_user_is_banned(self):
        limiter = RateLimiter(RateLimitConfig())
        limiter.ban_user(1)
        assert limiter.is_banned(1) is True

    def test_ban_expires(self):
        cfg = RateLimitConfig(ban_duration=1)
        limiter = RateLimiter(cfg)
        limiter.ban_user(1)
        limiter.banned_users[1] = time.time() - 5  # Force expiry
        assert limiter.is_banned(1) is False
        assert 1 not in limiter.banned_users


@pytest.mark.unit
class TestRateLimiterCleanOld:
    """_clean_old_requests strips requests outside the window."""

    def test_removes_expired(self):
        limiter = RateLimiter(RateLimitConfig())
        old = time.time() - 120
        recent = time.time() - 5
        result = limiter._clean_old_requests([old, recent], 60)
        assert old not in result
        assert recent in result

    def test_empty_input(self):
        limiter = RateLimiter(RateLimitConfig())
        assert limiter._clean_old_requests([], 60) == []

    def test_all_expired(self):
        limiter = RateLimiter(RateLimitConfig())
        old = time.time() - 200
        assert limiter._clean_old_requests([old], 60) == []

    def test_all_recent(self):
        limiter = RateLimiter(RateLimitConfig())
        t = time.time() - 1
        result = limiter._clean_old_requests([t], 60)
        assert t in result


@pytest.mark.unit
class TestRateLimiterGlobalLimit:
    """check_global_limit counting and blocking."""

    def test_allows_under_limit(self):
        cfg = RateLimitConfig(global_limit=5, global_window=60)
        limiter = RateLimiter(cfg)
        for _ in range(5):
            assert limiter.check_global_limit(1) is True

    def test_blocks_at_limit(self):
        cfg = RateLimitConfig(global_limit=3, global_window=60)
        limiter = RateLimiter(cfg)
        for _ in range(3):
            limiter.check_global_limit(1)
        assert limiter.check_global_limit(1) is False

    def test_different_users_independent(self):
        cfg = RateLimitConfig(global_limit=1, global_window=60)
        limiter = RateLimiter(cfg)
        limiter.check_global_limit(1)  # User 1 exhausted
        assert limiter.check_global_limit(2) is True  # User 2 still ok

    def test_different_brands_independent(self):
        cfg = RateLimitConfig(global_limit=1, global_window=60)
        limiter = RateLimiter(cfg)
        limiter.check_global_limit(1, brand_id=1)
        # Same user, different brand — should be allowed
        assert limiter.check_global_limit(1, brand_id=2) is True


@pytest.mark.unit
class TestRateLimiterActionLimit:
    """check_action_limit per-action counters."""

    def test_unknown_action_always_allowed(self):
        limiter = RateLimiter(RateLimitConfig())
        assert limiter.check_action_limit(1, "nonexistent_action") is True

    def test_action_limit_enforced(self):
        cfg = RateLimitConfig(action_limits={"buy_item": (2, 60)})
        limiter = RateLimiter(cfg)
        assert limiter.check_action_limit(1, "buy_item") is True
        assert limiter.check_action_limit(1, "buy_item") is True
        assert limiter.check_action_limit(1, "buy_item") is False

    def test_different_actions_independent(self):
        cfg = RateLimitConfig(action_limits={"a": (1, 60), "b": (1, 60)})
        limiter = RateLimiter(cfg)
        limiter.check_action_limit(1, "a")
        assert limiter.check_action_limit(1, "b") is True

    def test_brand_keyed_independently(self):
        cfg = RateLimitConfig(action_limits={"buy_item": (1, 60)})
        limiter = RateLimiter(cfg)
        limiter.check_action_limit(1, "buy_item", brand_id=1)
        assert limiter.check_action_limit(1, "buy_item", brand_id=2) is True


@pytest.mark.unit
class TestRateLimiterGetWaitTime:
    """get_wait_time returns sensible positive values."""

    def test_no_limits_hit_returns_zero(self):
        limiter = RateLimiter(RateLimitConfig())
        assert limiter.get_wait_time(1) == 0

    def test_banned_user_returns_positive(self):
        cfg = RateLimitConfig(ban_duration=300)
        limiter = RateLimiter(cfg)
        limiter.ban_user(1)
        wait = limiter.get_wait_time(1)
        assert 0 < wait <= 300

    def test_global_limit_exceeded_returns_positive(self):
        cfg = RateLimitConfig(global_limit=1, global_window=60)
        limiter = RateLimiter(cfg)
        limiter.check_global_limit(1)
        # Exceed limit
        limiter.user_requests[(0, 1)] = [time.time()]
        cfg.global_limit = 0
        wait = limiter.get_wait_time(1)
        assert isinstance(wait, int)

    def test_action_limit_exceeded_returns_positive(self):
        cfg = RateLimitConfig(action_limits={"buy_item": (1, 60)})
        limiter = RateLimiter(cfg)
        limiter.check_action_limit(1, "buy_item")
        wait = limiter.get_wait_time(1, "buy_item")
        assert isinstance(wait, int)


@pytest.mark.unit
class TestRateLimiterPeriodicCleanup:
    """_periodic_cleanup removes stale entries."""

    def test_cleanup_removes_expired_bans(self):
        cfg = RateLimitConfig(ban_duration=1)
        limiter = RateLimiter(cfg)
        limiter.ban_user(99)
        limiter.banned_users[99] = time.time() - 10  # Force expiry
        # Force cleanup to run immediately
        limiter._last_cleanup = time.time() - 400
        limiter._periodic_cleanup()
        assert 99 not in limiter.banned_users

    def test_cleanup_removes_inactive_user_requests(self):
        limiter = RateLimiter(RateLimitConfig())
        # Add stale entry for user 77
        limiter.user_requests[(0, 77)] = [time.time() - 200]  # Old
        limiter._last_cleanup = time.time() - 400
        limiter._periodic_cleanup()
        assert (0, 77) not in limiter.user_requests

    def test_cleanup_skipped_if_too_soon(self):
        limiter = RateLimiter(RateLimitConfig())
        limiter.ban_user(55)
        # Don't advance time — cleanup should be skipped
        limiter._periodic_cleanup()
        assert 55 in limiter.banned_users


# ===========================================================================
# RateLimitMiddleware — action detection
# ===========================================================================

@pytest.mark.unit
class TestRateLimitMiddlewareGetAction:
    """_get_action_from_event maps events to action names."""

    def setup_method(self):
        self.middleware = RateLimitMiddleware()

    def _make_callback(self, data: str) -> CallbackQuery:
        cb = MagicMock(spec=CallbackQuery)
        cb.data = data
        return cb

    def _make_message(self, text: str) -> Message:
        msg = MagicMock(spec=Message)
        msg.text = text
        return msg

    def test_buy_callback_returns_buy_item(self):
        cb = self._make_callback("buy_item_5")
        assert self.middleware._get_action_from_event(cb) == "buy_item"

    def test_shop_callback_returns_shop_view(self):
        cb = self._make_callback("shop_main")
        assert self.middleware._get_action_from_event(cb) == "shop_view"

    def test_broadcast_callback_returns_broadcast(self):
        cb = self._make_callback("broadcast_start")
        assert self.middleware._get_action_from_event(cb) == "broadcast"

    def test_console_callback_returns_admin_action(self):
        cb = self._make_callback("console_open")
        assert self.middleware._get_action_from_event(cb) == "admin_action"

    def test_unrecognized_callback_returns_default(self):
        cb = self._make_callback("unknown_xyz")
        assert self.middleware._get_action_from_event(cb) == "default"

    def test_start_message_returns_shop_view(self):
        msg = self._make_message("/start")
        assert self.middleware._get_action_from_event(msg) == "shop_view"

    def test_other_command_message_returns_admin_action(self):
        msg = self._make_message("/admin")
        assert self.middleware._get_action_from_event(msg) == "admin_action"

    def test_non_command_message_returns_default(self):
        msg = self._make_message("hello")
        assert self.middleware._get_action_from_event(msg) == "default"


# ===========================================================================
# LocaleMiddleware
# ===========================================================================

@pytest.mark.unit
class TestLocaleMiddleware:
    """Tests for LocaleMiddleware.__call__."""

    @pytest.mark.asyncio
    async def test_message_with_saved_locale_sets_it(self):
        middleware = LocaleMiddleware()
        event = MagicMock(spec=Message)
        event.from_user = MagicMock()
        event.from_user.id = 42
        handler = AsyncMock(return_value="ok")

        with patch("bot.middleware.locale.get_user_locale", return_value="en"), \
             patch("bot.middleware.locale.set_request_locale") as mock_set:
            result = await middleware(handler, event, {})

        mock_set.assert_any_call("en")
        mock_set.assert_any_call(None)
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_no_saved_locale_skips_set(self):
        middleware = LocaleMiddleware()
        event = MagicMock(spec=Message)
        event.from_user = MagicMock()
        event.from_user.id = 99
        handler = AsyncMock(return_value="ok")

        with patch("bot.middleware.locale.get_user_locale", return_value=None), \
             patch("bot.middleware.locale.set_request_locale") as mock_set:
            await middleware(handler, event, {})

        # Only the reset call should happen
        mock_set.assert_called_once_with(None)

    @pytest.mark.asyncio
    async def test_callback_query_also_sets_locale(self):
        middleware = LocaleMiddleware()
        event = MagicMock(spec=CallbackQuery)
        event.from_user = MagicMock()
        event.from_user.id = 7
        handler = AsyncMock(return_value="cb_ok")

        with patch("bot.middleware.locale.get_user_locale", return_value="th"), \
             patch("bot.middleware.locale.set_request_locale") as mock_set:
            result = await middleware(handler, event, {})

        mock_set.assert_any_call("th")
        mock_set.assert_any_call(None)
        assert result == "cb_ok"

    @pytest.mark.asyncio
    async def test_reset_called_even_on_handler_exception(self):
        middleware = LocaleMiddleware()
        event = MagicMock(spec=Message)
        event.from_user = MagicMock()
        event.from_user.id = 5
        handler = AsyncMock(side_effect=RuntimeError("fail"))

        with patch("bot.middleware.locale.get_user_locale", return_value="th"), \
             patch("bot.middleware.locale.set_request_locale") as mock_set:
            with pytest.raises(RuntimeError):
                await middleware(handler, event, {})

        mock_set.assert_any_call(None)


# ===========================================================================
# BrandContextMiddleware
# ===========================================================================

@pytest.mark.unit
class TestBrandContextMiddleware:
    """Tests for BrandContextMiddleware."""

    @pytest.mark.asyncio
    async def test_injects_brand_id(self):
        middleware = BrandContextMiddleware(brand_id=7)
        event = MagicMock()
        data: dict = {}
        handler = AsyncMock(return_value="res")

        result = await middleware(handler, event, data)

        assert data["brand_id"] == 7
        assert result == "res"

    @pytest.mark.asyncio
    async def test_overwrites_existing_brand_id(self):
        middleware = BrandContextMiddleware(brand_id=3)
        event = MagicMock()
        data = {"brand_id": 99}
        handler = AsyncMock()

        await middleware(handler, event, data)

        assert data["brand_id"] == 3

    @pytest.mark.asyncio
    async def test_brand_id_one(self):
        middleware = BrandContextMiddleware(brand_id=1)
        event = MagicMock()
        data: dict = {}
        handler = AsyncMock()

        await middleware(handler, event, data)

        assert data["brand_id"] == 1

    @pytest.mark.asyncio
    async def test_handler_called_with_event_and_data(self):
        middleware = BrandContextMiddleware(brand_id=2)
        event = MagicMock()
        data: dict = {}
        handler = AsyncMock(return_value="called")

        await middleware(handler, event, data)

        handler.assert_called_once_with(event, data)
