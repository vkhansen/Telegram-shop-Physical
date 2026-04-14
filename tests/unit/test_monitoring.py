"""
Tests for bot.monitoring.metrics — MetricsCollector and helpers.

All tests in this file operate purely in-memory with no external
dependencies, so they run fast and never require the database or Redis.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.monitoring.metrics import (
    AnalyticsMiddleware,
    MetricsCollector,
    get_metrics,
    init_metrics,
)


# ===========================================================================
# MetricsCollector — basic tracking
# ===========================================================================

@pytest.mark.unit
class TestMetricsCollectorInit:
    """MetricsCollector initialises with empty state."""

    def test_events_empty(self):
        mc = MetricsCollector()
        assert len(mc.events) == 0

    def test_timings_empty(self):
        mc = MetricsCollector()
        assert len(mc.timings) == 0

    def test_errors_empty(self):
        mc = MetricsCollector()
        assert len(mc.errors) == 0

    def test_conversions_empty(self):
        mc = MetricsCollector()
        assert len(mc.conversions) == 0


@pytest.mark.unit
class TestMetricsCollectorTrackEvent:
    """track_event correctly increments counters."""

    def test_increments_counter(self):
        mc = MetricsCollector()
        mc.track_event("my_event")
        assert mc.events["my_event"] == 1

    def test_increments_counter_twice(self):
        mc = MetricsCollector()
        mc.track_event("click")
        mc.track_event("click")
        assert mc.events["click"] == 2

    def test_important_event_with_user_id(self):
        mc = MetricsCollector()
        mc.track_event("order_created", user_id=42, metadata={"total": 100})
        assert mc.events["order_created"] == 1

    def test_multiple_different_events(self):
        mc = MetricsCollector()
        mc.track_event("order_created")
        mc.track_event("order_completed")
        mc.track_event("order_created")
        assert mc.events["order_created"] == 2
        assert mc.events["order_completed"] == 1

    def test_no_user_id_ok(self):
        mc = MetricsCollector()
        mc.track_event("shop_view")
        assert mc.events["shop_view"] == 1

    def test_security_event_tracked(self):
        mc = MetricsCollector()
        mc.track_event("security_suspicious_callback", user_id=1, metadata={"data": "x"})
        assert mc.events["security_suspicious_callback"] == 1

    def test_cache_event_tracked(self):
        mc = MetricsCollector()
        mc.track_event("cache_hit")
        assert mc.events["cache_hit"] == 1


@pytest.mark.unit
class TestMetricsCollectorTrackTiming:
    """track_timing stores durations correctly."""

    def test_stores_duration(self):
        mc = MetricsCollector()
        mc.track_timing("db_query", 0.05)
        assert 0.05 in mc.timings["db_query"]

    def test_multiple_timings(self):
        mc = MetricsCollector()
        mc.track_timing("op", 1.0)
        mc.track_timing("op", 2.0)
        assert len(mc.timings["op"]) == 2

    def test_trims_to_1000(self):
        mc = MetricsCollector()
        for i in range(1050):
            mc.track_timing("op", float(i))
        assert len(mc.timings["op"]) == 1000

    def test_different_operations_independent(self):
        mc = MetricsCollector()
        mc.track_timing("a", 1.0)
        mc.track_timing("b", 2.0)
        assert mc.timings["a"] == [1.0]
        assert mc.timings["b"] == [2.0]


@pytest.mark.unit
class TestMetricsCollectorTrackError:
    """track_error increments error counters."""

    def test_increments_error(self):
        mc = MetricsCollector()
        mc.track_error("TimeoutError")
        assert mc.errors["TimeoutError"] == 1

    def test_multiple_same_errors(self):
        mc = MetricsCollector()
        mc.track_error("DBError")
        mc.track_error("DBError")
        assert mc.errors["DBError"] == 2

    def test_with_message(self):
        mc = MetricsCollector()
        mc.track_error("ValueError", "bad value")
        assert mc.errors["ValueError"] == 1


# ===========================================================================
# MetricsCollector — track_conversion
# ===========================================================================

@pytest.mark.unit
class TestMetricsCollectorTrackConversion:
    """track_conversion populates conversion funnels."""

    def test_creates_funnel(self):
        mc = MetricsCollector()
        mc.track_conversion("customer_journey", "shop_view", 1)
        assert "customer_journey" in mc.conversions

    def test_adds_user_to_step(self):
        mc = MetricsCollector()
        mc.track_conversion("customer_journey", "shop_view", 42)
        assert 42 in mc.conversions["customer_journey"]["shop_view"]

    def test_multiple_users_in_step(self):
        mc = MetricsCollector()
        for uid in range(5):
            mc.track_conversion("customer_journey", "cart_add", uid)
        assert len(mc.conversions["customer_journey"]["cart_add"]) == 5

    def test_same_user_not_duplicated(self):
        mc = MetricsCollector()
        mc.track_conversion("customer_journey", "shop_view", 1)
        mc.track_conversion("customer_journey", "shop_view", 1)
        assert len(mc.conversions["customer_journey"]["shop_view"]) == 1

    def test_prunes_when_max_exceeded(self):
        mc = MetricsCollector()
        # Add more than MAX_CONVERSION_SET_SIZE users
        for i in range(MetricsCollector.MAX_CONVERSION_SET_SIZE + 10):
            mc.track_conversion("funnel", "step", i)
        size = len(mc.conversions["funnel"]["step"])
        assert size <= MetricsCollector.MAX_CONVERSION_SET_SIZE


# ===========================================================================
# MetricsCollector — get_metrics_summary
# ===========================================================================

@pytest.mark.unit
class TestMetricsCollectorGetSummary:
    """get_metrics_summary returns structured data."""

    def test_summary_has_required_keys(self):
        mc = MetricsCollector()
        summary = mc.get_metrics_summary()
        assert "uptime_seconds" in summary
        assert "events" in summary
        assert "timings" in summary
        assert "errors" in summary
        assert "conversions" in summary
        assert "timestamp" in summary

    def test_uptime_positive(self):
        mc = MetricsCollector()
        summary = mc.get_metrics_summary()
        assert summary["uptime_seconds"] >= 0

    def test_events_reflected_in_summary(self):
        mc = MetricsCollector()
        mc.track_event("order_created")
        mc.track_event("order_created")
        summary = mc.get_metrics_summary()
        assert summary["events"]["order_created"] == 2

    def test_avg_timing_in_summary(self):
        mc = MetricsCollector()
        mc.track_timing("op", 1.0)
        mc.track_timing("op", 3.0)
        summary = mc.get_metrics_summary()
        assert "op" in summary["timings"]
        assert summary["timings"]["op"]["avg"] == 2.0
        assert summary["timings"]["op"]["count"] == 2

    def test_customer_journey_conversion_rates(self):
        mc = MetricsCollector()
        mc.track_conversion("customer_journey", "shop_view", 1)
        mc.track_conversion("customer_journey", "shop_view", 2)
        mc.track_conversion("customer_journey", "cart_add", 1)
        summary = mc.get_metrics_summary()
        cj = summary["conversions"]["customer_journey"]
        assert "shop_to_category" in cj
        assert "total_conversion" in cj

    def test_referral_conversion_rates(self):
        mc = MetricsCollector()
        mc.track_conversion("referral_program", "code_created", 1)
        mc.track_conversion("referral_program", "code_used", 1)
        summary = mc.get_metrics_summary()
        ref = summary["conversions"]["referral_program"]
        assert "code_usage_rate" in ref
        assert ref["code_usage_rate"] == 100.0


# ===========================================================================
# MetricsCollector — analytics helpers
# ===========================================================================

@pytest.mark.unit
class TestCustomerJourneyAnalytics:
    """get_customer_journey_analytics returns cart/order metrics."""

    def test_empty_metrics_all_zero(self):
        mc = MetricsCollector()
        analytics = mc.get_customer_journey_analytics()
        assert analytics["cart_metrics"]["total_cart_adds"] == 0
        assert analytics["cart_metrics"]["cart_to_checkout_rate"] == 0
        assert analytics["order_metrics"]["orders_created"] == 0

    def test_cart_abandoned(self):
        mc = MetricsCollector()
        mc.track_event("cart_add")
        mc.track_event("cart_add")
        # No checkout_start
        analytics = mc.get_customer_journey_analytics()
        assert analytics["cart_metrics"]["abandoned_carts"] == 2

    def test_completion_rate_calculated(self):
        mc = MetricsCollector()
        mc.track_event("order_created")
        mc.track_event("order_created")
        mc.track_event("order_completed")
        analytics = mc.get_customer_journey_analytics()
        assert analytics["order_metrics"]["completion_rate"] == 50.0

    def test_cancellation_rate_calculated(self):
        mc = MetricsCollector()
        mc.track_event("order_created")
        mc.track_event("order_cancelled")
        analytics = mc.get_customer_journey_analytics()
        assert analytics["order_metrics"]["cancellation_rate"] == 100.0


@pytest.mark.unit
class TestReferralAnalytics:
    """get_referral_analytics returns referral program metrics."""

    def test_empty_returns_zeros(self):
        mc = MetricsCollector()
        analytics = mc.get_referral_analytics()
        assert analytics["codes_created"] == 0
        assert analytics["usage_rate"] == 0

    def test_usage_rate_calculated(self):
        mc = MetricsCollector()
        mc.track_event("referral_code_created")
        mc.track_event("referral_code_created")
        mc.track_event("referral_code_used")
        analytics = mc.get_referral_analytics()
        assert analytics["usage_rate"] == 50.0

    def test_bonus_payment_rate_calculated(self):
        mc = MetricsCollector()
        mc.track_event("referral_code_used")
        mc.track_event("referral_code_used")
        mc.track_event("referral_bonus_paid")
        analytics = mc.get_referral_analytics()
        assert analytics["bonus_payment_rate"] == 50.0


@pytest.mark.unit
class TestPaymentAnalytics:
    """get_payment_analytics returns payment breakdown."""

    def test_empty_state(self):
        mc = MetricsCollector()
        analytics = mc.get_payment_analytics()
        assert analytics["payment_methods"]["bitcoin"]["count"] == 0
        assert analytics["payment_methods"]["cash"]["count"] == 0

    def test_bitcoin_percentage(self):
        mc = MetricsCollector()
        mc.track_event("payment_bitcoin_initiated")
        mc.track_event("payment_bitcoin_initiated")
        mc.track_event("payment_cash_initiated")
        analytics = mc.get_payment_analytics()
        methods = analytics["payment_methods"]
        assert abs(methods["bitcoin"]["percentage"] - 66.67) < 0.1
        assert abs(methods["cash"]["percentage"] - 33.33) < 0.1

    def test_bonus_usage_rate(self):
        mc = MetricsCollector()
        mc.track_event("payment_bitcoin_initiated")
        mc.track_event("payment_cash_initiated")
        mc.track_event("payment_bonus_applied")
        analytics = mc.get_payment_analytics()
        assert analytics["bonus_usage"]["bonus_applied_count"] == 1


@pytest.mark.unit
class TestInventoryAnalytics:
    """get_inventory_analytics returns inventory movement metrics."""

    def test_empty_state(self):
        mc = MetricsCollector()
        analytics = mc.get_inventory_analytics()
        assert analytics["inventory_reserved"] == 0
        assert analytics["inventory_released"] == 0

    def test_reservation_success_rate(self):
        mc = MetricsCollector()
        mc.track_event("inventory_reserved")
        mc.track_event("inventory_reserved")
        mc.track_event("inventory_deducted")
        analytics = mc.get_inventory_analytics()
        assert analytics["reservation_success_rate"] == 50.0


# ===========================================================================
# MetricsCollector — export_to_prometheus
# ===========================================================================

@pytest.mark.unit
class TestExportToPrometheus:
    """export_to_prometheus generates valid Prometheus text format."""

    def test_empty_collector_has_uptime(self):
        mc = MetricsCollector()
        output = mc.export_to_prometheus()
        assert "bot_uptime_seconds" in output

    def test_event_appears_in_output(self):
        mc = MetricsCollector()
        mc.track_event("order_created")
        output = mc.export_to_prometheus()
        assert "order_created" in output
        assert "bot_events_total" in output

    def test_error_appears_in_output(self):
        mc = MetricsCollector()
        mc.track_error("DBError")
        output = mc.export_to_prometheus()
        assert "DBError" in output
        assert "bot_errors_total" in output

    def test_timing_appears_in_output(self):
        mc = MetricsCollector()
        mc.track_timing("db_query", 0.1)
        output = mc.export_to_prometheus()
        assert "db_query" in output
        assert "bot_operation_duration_seconds" in output

    def test_special_chars_sanitized(self):
        mc = MetricsCollector()
        mc.track_event("my-special/event name")
        output = mc.export_to_prometheus()
        # Dashes spaces and slashes replaced with underscores
        assert "my_special_event_name" in output


# ===========================================================================
# AnalyticsMiddleware
# ===========================================================================

@pytest.mark.unit
class TestAnalyticsMiddleware:
    """AnalyticsMiddleware tracks events and timings."""

    @pytest.mark.asyncio
    async def test_tracks_message_event(self):
        mc = MetricsCollector()
        middleware = AnalyticsMiddleware(mc)

        event = MagicMock()
        event.from_user.id = 1
        event.text = "hello"
        event.data = MagicMock(side_effect=AttributeError)

        handler = AsyncMock(return_value="ok")
        await middleware(handler, event, {})

        # Should have tracked a bot_message event
        assert any("bot_" in k for k in mc.events)

    @pytest.mark.asyncio
    async def test_tracks_timing(self):
        mc = MetricsCollector()
        middleware = AnalyticsMiddleware(mc)

        event = MagicMock()
        event.from_user.id = 1
        event.text = "/start"

        handler = AsyncMock(return_value="ok")
        await middleware(handler, event, {})

        assert len(mc.timings) >= 1

    @pytest.mark.asyncio
    async def test_tracks_errors_on_exception(self):
        mc = MetricsCollector()
        middleware = AnalyticsMiddleware(mc)

        event = MagicMock()
        event.from_user.id = 1
        event.text = "test"

        handler = AsyncMock(side_effect=ValueError("boom"))

        with pytest.raises(ValueError):
            await middleware(handler, event, {})

        assert mc.errors.get("ValueError", 0) == 1

    @pytest.mark.asyncio
    async def test_callback_event_type(self):
        mc = MetricsCollector()
        middleware = AnalyticsMiddleware(mc)

        event = MagicMock()
        event.from_user.id = 2
        # Callback-like: has .data attribute, no .text
        del event.text
        event.data = "shop_main"

        handler = AsyncMock(return_value="cb")
        await middleware(handler, event, {})

        assert any("shop" in k or "bot_" in k for k in mc.events)


# ===========================================================================
# Module-level functions — init_metrics / get_metrics
# ===========================================================================

@pytest.mark.unit
class TestInitAndGetMetrics:
    """init_metrics and get_metrics manage the global collector."""

    def test_get_metrics_returns_none_initially(self):
        import bot.monitoring.metrics as m_module
        original = m_module._metrics_collector
        m_module._metrics_collector = None
        try:
            assert get_metrics() is None
        finally:
            m_module._metrics_collector = original

    def test_init_metrics_returns_collector(self):
        import bot.monitoring.metrics as m_module
        original = m_module._metrics_collector
        try:
            collector = init_metrics()
            assert isinstance(collector, MetricsCollector)
        finally:
            m_module._metrics_collector = original

    def test_get_metrics_returns_collector_after_init(self):
        import bot.monitoring.metrics as m_module
        original = m_module._metrics_collector
        try:
            init_metrics()
            assert isinstance(get_metrics(), MetricsCollector)
        finally:
            m_module._metrics_collector = original
