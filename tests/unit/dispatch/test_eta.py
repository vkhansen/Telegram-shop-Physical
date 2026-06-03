"""ETA estimation tests (Card 26)."""

import pytest

from bot.dispatch.eta import estimate_eta_minutes


@pytest.mark.unit
def test_eta_from_distance():
    """ETA is non-decreasing with distance and never below 1 minute."""
    distances = [0, 0.5, 1, 2, 5, 10, 20, 50]
    etas = [estimate_eta_minutes(d) for d in distances]

    # Monotonic non-decreasing: a farther driver is never sooner.
    assert etas == sorted(etas)
    # Strictly later for a clearly farther driver.
    assert estimate_eta_minutes(1) < estimate_eta_minutes(20)
    # Never "0 min away" while still en route.
    assert estimate_eta_minutes(0) >= 1


@pytest.mark.unit
def test_eta_respects_speed():
    """A faster average speed yields a smaller (or equal) ETA for the same distance."""
    fast = estimate_eta_minutes(10, avg_speed_kmh=60)
    slow = estimate_eta_minutes(10, avg_speed_kmh=10)
    assert fast < slow


@pytest.mark.unit
def test_eta_handles_bad_input():
    """Negative distance and non-positive speed don't crash and stay sane."""
    assert estimate_eta_minutes(-5) >= 1
    assert estimate_eta_minutes(5, avg_speed_kmh=0) >= 1
