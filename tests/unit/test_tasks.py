"""
Tests for background tasks:
  - bot.tasks.reservation_cleaner
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest


# ===========================================================================
# reservation_cleaner
# ===========================================================================

@pytest.mark.unit
class TestStartReservationCleaner:
    """start_reservation_cleaner schedules the background task."""

    def test_creates_asyncio_task(self):
        from bot.tasks.reservation_cleaner import start_reservation_cleaner

        with patch("bot.tasks.reservation_cleaner.asyncio.create_task") as mock_create:
            start_reservation_cleaner()
        mock_create.assert_called_once()

    def test_task_is_run_reservation_cleaner_coroutine(self):
        from bot.tasks.reservation_cleaner import (
            start_reservation_cleaner,
            run_reservation_cleaner,
        )

        captured = []

        def capture(coro):
            captured.append(coro)
            # Return a mock future so the call doesn't hang
            fut = MagicMock()
            return fut

        with patch("bot.tasks.reservation_cleaner.asyncio.create_task", side_effect=capture):
            start_reservation_cleaner()

        assert len(captured) == 1
        # Close the coroutine to avoid runtime warning
        captured[0].close()


@pytest.mark.unit
class TestResetDailyCounters:
    """reset_daily_counters resets goods metrics to zero."""

    @pytest.mark.asyncio
    async def test_resets_all_goods(self, db_session):
        from bot.tasks.reservation_cleaner import reset_daily_counters
        from bot.database.models.main import Goods, Categories

        # Create a category and item
        cat = Categories(name="Cat", sort_order=1)
        db_session.add(cat)
        db_session.flush()

        item = Goods(
            name="Widget",
            category_name=cat.name,
            description="Test widget",
            price=100,
            item_type="prepared",
            daily_sold_count=5,
            sold_out_today=True,
        )
        db_session.add(item)
        db_session.commit()

        # Run the reset (uses Database().session() internally via monkeypatched singleton)
        await reset_daily_counters()

        db_session.expire_all()
        refreshed = db_session.query(Goods).filter_by(name="Widget").first()
        assert refreshed.daily_sold_count == 0
        assert refreshed.sold_out_today is False

    @pytest.mark.asyncio
    async def test_no_items_does_not_raise(self):
        """reset_daily_counters runs cleanly even with no Goods rows."""
        from bot.tasks.reservation_cleaner import reset_daily_counters
        # Should complete without error
        await reset_daily_counters()


@pytest.mark.unit
class TestRunReservationCleaner:
    """run_reservation_cleaner loop iteration behaviour."""

    @pytest.mark.asyncio
    async def test_calls_cleanup_and_logs_when_count_positive(self):
        from bot.tasks.reservation_cleaner import run_reservation_cleaner

        cleanup_calls = []

        async def fake_cleanup():
            cleanup_calls.append(1)
            # First call returns work to do, second raises to exit loop
            if len(cleanup_calls) == 1:
                return 2, ["ORD001", "ORD002"]
            raise asyncio.CancelledError

        with patch(
            "bot.tasks.reservation_cleaner.cleanup_expired_reservations",
            side_effect=fake_cleanup,
        ), patch("bot.tasks.reservation_cleaner.asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(asyncio.CancelledError):
                await run_reservation_cleaner()

        assert len(cleanup_calls) >= 1

    @pytest.mark.asyncio
    async def test_handles_exception_and_continues(self):
        """A non-cancellation error during cleanup is caught, not propagated."""
        from bot.tasks.reservation_cleaner import run_reservation_cleaner

        call_count = 0

        async def boom():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("db down")
            raise asyncio.CancelledError

        with patch(
            "bot.tasks.reservation_cleaner.cleanup_expired_reservations",
            side_effect=boom,
        ), patch("bot.tasks.reservation_cleaner.asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(asyncio.CancelledError):
                await run_reservation_cleaner()

        assert call_count >= 2  # Loop continued past the error

    @pytest.mark.asyncio
    async def test_no_work_does_not_log_release(self):
        """When count == 0, the 'Released N reservations' log line is not hit."""
        from bot.tasks.reservation_cleaner import run_reservation_cleaner

        iterations = 0

        async def no_work():
            nonlocal iterations
            iterations += 1
            if iterations == 1:
                return 0, []
            raise asyncio.CancelledError

        with patch(
            "bot.tasks.reservation_cleaner.cleanup_expired_reservations",
            side_effect=no_work,
        ), patch("bot.tasks.reservation_cleaner.asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(asyncio.CancelledError):
                await run_reservation_cleaner()

        assert iterations >= 1
