"""
Tests for R1 refactor: table-driven quick-transition handlers in
bot/handlers/admin/order_management.py.

These tests pin the behavior of QUICK_TRANSITIONS so that:
  - Adding a new transition is a one-dict-entry change safe to land.
  - Removing/reordering hooks is caught by structural assertions.
  - The row-lock + is_valid_transition invariants cannot regress.
"""
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.database.models.main import Order
from bot.handlers.admin import order_management as om


def _make_call(data: str, user_id: int = 555):
    call = MagicMock()
    call.data = data
    call.from_user.id = user_id
    call.bot = MagicMock()
    call.message = MagicMock()
    call.message.text = "Order #T1"
    call.message.edit_text = AsyncMock()
    call.answer = AsyncMock()
    return call


# ---------------------------------------------------------------------------
# Table integrity
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestQuickTransitionTable:
    def test_all_prefixes_end_with_underscore(self):
        for prefix in om.QUICK_TRANSITIONS:
            assert prefix.endswith("_"), (
                f"{prefix!r} must end with '_' so removeprefix strips exactly the prefix"
            )

    def test_target_statuses_are_valid_destinations(self):
        from bot.utils.order_status import ALL_STATUSES
        for spec in om.QUICK_TRANSITIONS.values():
            assert spec.target_status in ALL_STATUSES, (
                f"Unknown target status {spec.target_status!r} in QUICK_TRANSITIONS"
            )

    def test_expected_transitions_present(self):
        prefixes = set(om.QUICK_TRANSITIONS.keys())
        assert prefixes == {
            "kitchen_preparing_",
            "kitchen_ready_",
            "rider_picked_",
            "rider_delivered_",
        }

    def test_hooks_are_all_async_callables(self):
        import asyncio
        for spec in om.QUICK_TRANSITIONS.values():
            for hook in (*spec.pre_commit, *spec.post_commit):
                assert callable(hook)
                assert asyncio.iscoroutinefunction(hook), (
                    f"{hook.__name__} must be async"
                )

    def test_spec_is_frozen_dataclass(self):
        spec = om.QUICK_TRANSITIONS["kitchen_preparing_"]
        with pytest.raises((AttributeError, Exception)):
            spec.target_status = "something_else"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Dispatch body
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestExecuteQuickTransition:
    """Exercise _execute_quick_transition with mocked DB session."""

    def _patch_session(self, order):
        session = MagicMock()
        query = MagicMock()
        query.filter_by.return_value = query
        query.with_for_update.return_value = query
        query.first.return_value = order
        session.query.return_value = query
        session.commit = MagicMock()
        cm = MagicMock()
        cm.__enter__ = MagicMock(return_value=session)
        cm.__exit__ = MagicMock(return_value=None)
        db = MagicMock()
        db.session.return_value = cm
        return db, session

    async def test_invalid_order_id_alerts(self):
        call = _make_call("kitchen_preparing_notanint")
        await om._execute_quick_transition(
            call, "kitchen_preparing_", om.QUICK_TRANSITIONS["kitchen_preparing_"],
        )
        call.answer.assert_awaited_once_with("Invalid order", show_alert=True)
        call.message.edit_text.assert_not_called()

    async def test_missing_order_alerts_and_returns(self):
        call = _make_call("kitchen_preparing_999")
        db, session = self._patch_session(order=None)
        with patch.object(om, "Database", return_value=db):
            await om._execute_quick_transition(
                call, "kitchen_preparing_", om.QUICK_TRANSITIONS["kitchen_preparing_"],
            )
        call.answer.assert_awaited_with("Cannot change status", show_alert=True)
        session.commit.assert_not_called()

    async def test_invalid_transition_rejected_no_mutation(self):
        call = _make_call("kitchen_preparing_1")
        order = MagicMock(spec=Order)
        order.order_status = "delivered"  # terminal — cannot transition to preparing
        order.order_code = "T1"
        order.driver_id = None
        db, session = self._patch_session(order)
        with patch.object(om, "Database", return_value=db):
            await om._execute_quick_transition(
                call, "kitchen_preparing_", om.QUICK_TRANSITIONS["kitchen_preparing_"],
            )
        assert order.order_status == "delivered"  # unchanged
        session.commit.assert_not_called()
        call.answer.assert_awaited_with("Cannot change status", show_alert=True)

    async def test_happy_path_preparing_commits_and_notifies(self):
        call = _make_call("kitchen_preparing_42")
        order = MagicMock(spec=Order)
        order.order_status = "confirmed"  # pending → reserved → confirmed → preparing OK
        order.order_code = "T1"
        db, session = self._patch_session(order)

        with patch.object(om, "Database", return_value=db), \
             patch.object(om, "_notify_customer_status", new=AsyncMock()) as notify:
            await om._execute_quick_transition(
                call, "kitchen_preparing_", om.QUICK_TRANSITIONS["kitchen_preparing_"],
            )

        assert order.order_status == "preparing"
        session.commit.assert_called_once()
        notify.assert_awaited_once_with(call.bot, order)
        call.answer.assert_awaited_with("Status: Preparing")
        call.message.edit_text.assert_awaited_once()
        assert "PREPARING" in call.message.edit_text.await_args.args[0]

    async def test_rider_picked_assigns_driver_and_prompts_gps(self):
        call = _make_call("rider_picked_7", user_id=999)
        order = MagicMock(spec=Order)
        order.order_status = "ready"
        order.driver_id = None
        order.order_code = "T1"
        db, session = self._patch_session(order)

        notify_customer = AsyncMock()
        prompt = AsyncMock()
        with patch.object(om, "Database", return_value=db), \
             patch.object(om, "_notify_customer_status", new=notify_customer), \
             patch("bot.handlers.user.delivery_chat_handler.prompt_customer_gps",
                   new=prompt, create=True):
            await om._execute_quick_transition(
                call, "rider_picked_", om.QUICK_TRANSITIONS["rider_picked_"],
            )

        assert order.driver_id == 999
        assert order.order_status == "out_for_delivery"
        notify_customer.assert_awaited_once()
        prompt.assert_awaited_once()

    async def test_rider_delivered_sets_completed_at(self):
        call = _make_call("rider_delivered_3")
        order = MagicMock(spec=Order)
        order.order_status = "out_for_delivery"
        order.order_code = "T1"
        order.completed_at = None
        db, session = self._patch_session(order)

        with patch.object(om, "Database", return_value=db), \
             patch.object(om, "_notify_customer_status", new=AsyncMock()), \
             patch("bot.handlers.user.delivery_chat_handler.set_post_delivery_window",
                   create=True) as set_window:
            await om._execute_quick_transition(
                call, "rider_delivered_", om.QUICK_TRANSITIONS["rider_delivered_"],
            )

        assert order.order_status == "delivered"
        assert isinstance(order.completed_at, datetime)
        set_window.assert_called_once_with(session, order)

    async def test_kitchen_ready_notifies_rider_then_customer(self):
        """Pin ordering: rider notified BEFORE customer (old behavior preserved)."""
        call = _make_call("kitchen_ready_1")
        order = MagicMock(spec=Order)
        order.order_status = "preparing"
        order.order_code = "T1"
        db, session = self._patch_session(order)

        call_order = []
        notify_rider = AsyncMock(side_effect=lambda *a, **k: call_order.append("rider"))
        notify_customer = AsyncMock(side_effect=lambda *a, **k: call_order.append("customer"))
        with patch.object(om, "Database", return_value=db), \
             patch.object(om, "_send_rider_notification", new=notify_rider), \
             patch.object(om, "_notify_customer_status", new=notify_customer):
            await om._execute_quick_transition(
                call, "kitchen_ready_", om.QUICK_TRANSITIONS["kitchen_ready_"],
            )

        assert order.order_status == "ready"
        assert call_order == ["rider", "customer"]
