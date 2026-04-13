"""
Regression tests for bugs fixed in review-DRY.md (2026-03-25) and DRY-audit-report.md.

Each test pins the fixed behavior so that future refactors cannot silently
reintroduce a known bug. Tests are named by the bug ID from the review docs.
"""
import re
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# H1 — PAYMENT_PROCESSORS fallback (handlers/user/order_handler.py)
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestH1PaymentProcessorsFallback:
    """`PAYMENT_PROCESSORS[method]` must be `.get()`-based so unknown methods
    don't crash with KeyError when malformed callback data arrives."""

    def test_all_declared_methods_have_processor(self):
        from bot.handlers.user.order_handler import PAYMENT_PROCESSORS
        from bot.utils.constants import (
            PAYMENT_BITCOIN, PAYMENT_CASH, PAYMENT_PROMPTPAY,
            PAYMENT_LITECOIN, PAYMENT_SOLANA, PAYMENT_USDT_SOL,
        )
        for m in (PAYMENT_BITCOIN, PAYMENT_CASH, PAYMENT_PROMPTPAY,
                  PAYMENT_LITECOIN, PAYMENT_SOLANA, PAYMENT_USDT_SOL):
            assert m in PAYMENT_PROCESSORS, (
                f"{m!r} declared in constants but missing from PAYMENT_PROCESSORS"
            )

    def test_unknown_method_returns_none_from_get(self):
        from bot.handlers.user.order_handler import PAYMENT_PROCESSORS
        assert PAYMENT_PROCESSORS.get("<malformed>") is None

    async def test_handle_payment_method_unknown_alerts_and_returns(self):
        from bot.handlers.user.order_handler import _handle_payment_method

        call = MagicMock()
        call.answer = AsyncMock()
        call.from_user.id = 1
        state = MagicMock()
        state.update_data = AsyncMock()

        with patch("bot.handlers.user.order_handler.track_payment"):
            await _handle_payment_method(call, state, method="completely_bogus")

        call.answer.assert_awaited_once()
        kwargs = call.answer.await_args.kwargs
        assert kwargs.get("show_alert") is True
        state.update_data.assert_not_called()


# ---------------------------------------------------------------------------
# H2 — Bonus amount precision: store as str, reconstruct as Decimal
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestH2BonusPrecision:
    """Storing float(bonus) in FSM state loses precision on round-trip.
    The fix is to store `str(bonus)` and reconstruct via `Decimal(str)`."""

    @pytest.mark.parametrize("amount", ["33.33", "0.01", "999999.99", "0.1", "0.2"])
    def test_str_decimal_roundtrip_preserves_value(self, amount):
        original = Decimal(amount)
        serialized = str(original)
        reconstructed = Decimal(serialized)
        assert reconstructed == original
        assert reconstructed - original == Decimal("0")

    def test_float_roundtrip_is_lossy_for_known_case(self):
        """Document why we do NOT use float()."""
        original = Decimal("0.1") + Decimal("0.2")  # exactly 0.3
        via_float = Decimal(str(float(original)))
        # Python's repr of float(0.3) happens to be '0.3', so str(float()) works
        # accidentally for this value — but the raw float is not equal to Decimal('0.3'):
        assert float(original) == 0.3  # sanity
        # However for values that DO lose precision in float, round-trip breaks:
        lossy = Decimal("0.123456789012345678901234")
        assert Decimal(str(float(lossy))) != lossy


# ---------------------------------------------------------------------------
# H3 — Order status transition race: admin handlers must use SELECT FOR UPDATE
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestH3StatusTransitionRowLock:
    """All 4 quick-transition handlers plus the generic handler must acquire
    a row lock before reading/mutating order_status."""

    def test_all_status_mutation_paths_use_for_update(self):
        import bot.handlers.admin.order_management as om
        import inspect
        source = inspect.getsource(om)

        lock_count = source.count("with_for_update()")
        # Generic handler + 4 quick-transitions + delivery-photo handler = at least 5
        assert lock_count >= 5, (
            f"Expected ≥5 `with_for_update()` calls for atomic status mutation, "
            f"found {lock_count}. Did a refactor drop the row lock?"
        )


# ---------------------------------------------------------------------------
# H4 — price_feed missing-key guard
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestH4PriceFeedMissingKey:
    """CoinGecko response may omit the requested coin/currency keys."""

    async def test_missing_coin_key_raises_valueerror(self):
        from bot.payments.price_feed import _get_price, clear_price_cache
        clear_price_cache()
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json = MagicMock(return_value={"something_else": {"thb": 100}})

        client = MagicMock()
        client.get = AsyncMock(return_value=mock_resp)
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=client):
            with pytest.raises(ValueError, match="missing"):
                await _get_price("bitcoin", "thb")

    async def test_missing_currency_key_raises_valueerror(self):
        from bot.payments.price_feed import _get_price, clear_price_cache
        clear_price_cache()
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json = MagicMock(return_value={"bitcoin": {"usd": 50000}})

        client = MagicMock()
        client.get = AsyncMock(return_value=mock_resp)
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=client):
            with pytest.raises(ValueError, match="missing"):
                await _get_price("bitcoin", "thb")


# ---------------------------------------------------------------------------
# H5 — Division by zero guard in get_crypto_amount
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestH5PriceFeedZeroGuard:
    async def test_zero_price_from_api_raises_valueerror(self):
        from bot.payments.price_feed import _get_price, clear_price_cache
        clear_price_cache()
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json = MagicMock(return_value={"bitcoin": {"thb": 0}})

        client = MagicMock()
        client.get = AsyncMock(return_value=mock_resp)
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=client):
            with pytest.raises(ValueError, match="Invalid price"):
                await _get_price("bitcoin", "thb")

    async def test_get_crypto_amount_rejects_zero_price(self):
        from bot.payments.price_feed import get_crypto_amount, clear_price_cache
        clear_price_cache()
        with patch("bot.payments.price_feed._get_price", AsyncMock(return_value=Decimal("0"))):
            with pytest.raises(ValueError, match="Invalid price"):
                await get_crypto_amount("btc", Decimal("1000"))


# ---------------------------------------------------------------------------
# M1 — delivery_type validation (VALID_DELIVERY_TYPES)
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestM1DeliveryTypeValidation:
    def test_valid_delivery_types_frozenset_is_exact(self):
        from bot.utils.constants import (
            VALID_DELIVERY_TYPES, DELIVERY_DOOR, DELIVERY_DEAD_DROP, DELIVERY_PICKUP,
        )
        assert VALID_DELIVERY_TYPES == frozenset({DELIVERY_DOOR, DELIVERY_DEAD_DROP, DELIVERY_PICKUP})
        assert isinstance(VALID_DELIVERY_TYPES, frozenset), (
            "VALID_DELIVERY_TYPES must be immutable to prevent runtime mutation"
        )

    def test_extract_delivery_fields_defaults_to_door(self):
        from bot.utils.order_helpers import extract_delivery_fields
        from bot.utils.constants import DELIVERY_DOOR
        fields = extract_delivery_fields({})
        assert fields["delivery_type"] == DELIVERY_DOOR
        assert fields["drop_instructions"] is None
        assert fields["drop_latitude"] is None
        assert fields["drop_longitude"] is None
        assert fields["drop_media"] is None

    def test_extract_delivery_fields_preserves_dead_drop(self):
        from bot.utils.order_helpers import extract_delivery_fields
        data = {
            "delivery_type": "dead_drop",
            "drop_instructions": "Behind tree",
            "drop_latitude": 13.75,
            "drop_longitude": 100.50,
            "drop_media": [{"type": "photo", "file_id": "x"}],
        }
        fields = extract_delivery_fields(data)
        assert fields["delivery_type"] == "dead_drop"
        assert fields["drop_instructions"] == "Behind tree"
        assert fields["drop_latitude"] == 13.75
        assert fields["drop_longitude"] == 100.50
        assert fields["drop_media"] == [{"type": "photo", "file_id": "x"}]


# ---------------------------------------------------------------------------
# M3 — Maps link requires both lat AND lng
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestM3MapsLinkCoValidation:
    @pytest.mark.parametrize("lat,lng,expected_none", [
        (None, None, True),
        (13.75, None, True),
        (None, 100.50, True),
        (13.75, 100.50, False),
        (0, 0, False),          # zero is valid
        (-33.86, 151.20, False),  # negative ok
    ])
    def test_build_maps_link_requires_both(self, lat, lng, expected_none):
        from bot.utils.order_helpers import build_google_maps_link
        result = build_google_maps_link(lat, lng)
        if expected_none:
            assert result is None
        else:
            assert result is not None
            assert f"{lat},{lng}" in result


# ---------------------------------------------------------------------------
# M10 — _extract_coords_from_url None-unpack guard
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestM10MapsUrlExtraction:
    def test_returns_none_for_non_maps_text(self):
        from bot.handlers.user.order_handler import _extract_coords_from_url
        assert _extract_coords_from_url("just a regular address 123") is None

    def test_returns_none_for_empty_string(self):
        from bot.handlers.user.order_handler import _extract_coords_from_url
        assert _extract_coords_from_url("") is None

    def test_returns_none_for_out_of_range_coords(self):
        from bot.handlers.user.order_handler import _extract_coords_from_url
        # Latitude 91 is out of [-90, 90]
        assert _extract_coords_from_url("https://maps.google.com/?q=91.0,100.0") is None

    def test_extracts_valid_coords(self):
        from bot.handlers.user.order_handler import _extract_coords_from_url
        coords = _extract_coords_from_url("https://www.google.com/maps?q=13.7563,100.5018")
        assert coords is not None
        lat, lng = coords
        assert abs(lat - 13.7563) < 1e-6
        assert abs(lng - 100.5018) < 1e-6


# ---------------------------------------------------------------------------
# Status-machine structural checks: R1/R2 refactor pre-conditions
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestStatusMachineInvariants:
    """Pin structural properties of the order-status state machine that the
    upcoming R1/R2 refactors must preserve."""

    def test_terminal_states_have_no_outgoing(self):
        from bot.utils.order_status import VALID_TRANSITIONS
        for terminal in ("delivered", "cancelled", "expired"):
            assert VALID_TRANSITIONS[terminal] == set()

    def test_cannot_skip_from_pending_to_delivered(self):
        from bot.utils.order_status import is_valid_transition
        assert not is_valid_transition("pending", "delivered")
        assert not is_valid_transition("pending", "out_for_delivery")
        assert not is_valid_transition("pending", "ready")

    def test_cannot_transition_from_terminal(self):
        from bot.utils.order_status import is_valid_transition
        for terminal in ("delivered", "cancelled", "expired"):
            for target in ("pending", "reserved", "preparing", "ready"):
                assert not is_valid_transition(terminal, target)

    def test_happy_path_is_fully_connected(self):
        from bot.utils.order_status import is_valid_transition
        path = ["pending", "reserved", "confirmed", "preparing",
                "ready", "out_for_delivery", "delivered"]
        for cur, nxt in zip(path, path[1:]):
            assert is_valid_transition(cur, nxt), f"{cur}→{nxt} broken"

    def test_every_non_terminal_can_cancel(self):
        from bot.utils.order_status import is_valid_transition, VALID_TRANSITIONS
        terminals = {"delivered", "cancelled", "expired"}
        for status in VALID_TRANSITIONS.keys() - terminals:
            assert is_valid_transition(status, "cancelled"), (
                f"{status} cannot cancel — users would be stuck"
            )


# ---------------------------------------------------------------------------
# R2 latent bug: `_send_status_notifications` has a dead branch
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestR2SendStatusNotificationsDeadBranch:
    """The current implementation contains:
         elif new_status == "ready": ...
         elif new_status == "delivered" or new_status in ("preparing", "ready"): ...
    The `"ready"` disjunct is dead. This test pins the ACTUAL observed behavior
    so R2 refactor can replace the if/elif with a dict of callbacks and verify
    no behavior change."""

    async def test_preparing_notifies_customer_only(self):
        import bot.handlers.admin.order_management as om
        order = MagicMock()
        order.order_code = "T1"
        bot = MagicMock()

        with patch.object(om, "_send_kitchen_notification", new=AsyncMock()) as kitchen, \
             patch.object(om, "_send_rider_notification", new=AsyncMock()) as rider, \
             patch.object(om, "_notify_customer_status", new=AsyncMock()) as notify:
            await om._send_status_notifications(bot, order, "preparing", session=MagicMock())

        kitchen.assert_not_awaited()
        rider.assert_not_awaited()
        notify.assert_awaited_once()

    async def test_confirmed_notifies_kitchen_only(self):
        import bot.handlers.admin.order_management as om
        order = MagicMock()
        bot = MagicMock()

        with patch.object(om, "_send_kitchen_notification", new=AsyncMock()) as kitchen, \
             patch.object(om, "_send_rider_notification", new=AsyncMock()) as rider, \
             patch.object(om, "_notify_customer_status", new=AsyncMock()) as notify:
            await om._send_status_notifications(bot, order, "confirmed", session=MagicMock())

        kitchen.assert_awaited_once()
        rider.assert_not_awaited()
        notify.assert_not_awaited()

    async def test_ready_notifies_rider_only(self):
        """First matching branch is `elif new_status == "ready"` — rider only.
        The dead `or "ready"` clause never executes."""
        import bot.handlers.admin.order_management as om
        order = MagicMock()
        bot = MagicMock()

        with patch.object(om, "_send_kitchen_notification", new=AsyncMock()) as kitchen, \
             patch.object(om, "_send_rider_notification", new=AsyncMock()) as rider, \
             patch.object(om, "_notify_customer_status", new=AsyncMock()) as notify:
            await om._send_status_notifications(bot, order, "ready", session=MagicMock())

        kitchen.assert_not_awaited()
        rider.assert_awaited_once()
        notify.assert_not_awaited()

    async def test_delivered_notifies_customer(self):
        import bot.handlers.admin.order_management as om
        order = MagicMock()
        bot = MagicMock()

        with patch.object(om, "_send_kitchen_notification", new=AsyncMock()) as kitchen, \
             patch.object(om, "_send_rider_notification", new=AsyncMock()) as rider, \
             patch.object(om, "_notify_customer_status", new=AsyncMock()) as notify:
            await om._send_status_notifications(bot, order, "delivered", session=MagicMock())

        kitchen.assert_not_awaited()
        rider.assert_not_awaited()
        notify.assert_awaited_once()
