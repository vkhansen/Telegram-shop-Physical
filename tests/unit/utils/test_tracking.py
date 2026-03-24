"""Tests for bot.utils.tracking — metrics wrappers."""

import pytest
from unittest.mock import patch, MagicMock

from bot.utils.tracking import track_event, track_conversion, track_payment


@pytest.mark.unit
class TestTrackingWrappers:
    """Tests for the tracking helper functions."""

    @patch("bot.utils.tracking._metrics")
    def test_track_event_with_metrics(self, mock_metrics):
        m = MagicMock()
        mock_metrics.return_value = m
        track_event("cart_add", 123, {"item": "pizza"})
        m.track_event.assert_called_once_with("cart_add", 123, {"item": "pizza"})

    @patch("bot.utils.tracking._metrics")
    def test_track_event_without_metrics(self, mock_metrics):
        mock_metrics.return_value = None
        # Should not raise
        track_event("cart_add", 123)

    @patch("bot.utils.tracking._metrics")
    def test_track_event_default_data(self, mock_metrics):
        m = MagicMock()
        mock_metrics.return_value = m
        track_event("test", 1)
        m.track_event.assert_called_once_with("test", 1, {})

    @patch("bot.utils.tracking._metrics")
    def test_track_conversion_with_metrics(self, mock_metrics):
        m = MagicMock()
        mock_metrics.return_value = m
        track_conversion("customer_journey", "checkout_start", 456)
        m.track_conversion.assert_called_once_with("customer_journey", "checkout_start", 456)

    @patch("bot.utils.tracking._metrics")
    def test_track_conversion_without_metrics(self, mock_metrics):
        mock_metrics.return_value = None
        track_conversion("funnel", "step", 1)

    @patch("bot.utils.tracking.track_event")
    @patch("bot.utils.tracking.track_conversion")
    def test_track_payment(self, mock_conv, mock_event):
        track_payment("bitcoin", 789)
        mock_event.assert_called_once_with("payment_bitcoin_initiated", 789)
        mock_conv.assert_called_once_with("customer_journey", "payment_initiated", 789)
