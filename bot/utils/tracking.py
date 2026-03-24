"""Thin wrappers around ``get_metrics()`` to eliminate repetitive None-checks.

Every call site previously looked like::

    metrics = get_metrics()
    if metrics:
        metrics.track_event("name", user_id, {...})
        metrics.track_conversion("funnel", "step", user_id)

These helpers collapse that into a single call.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


def _metrics():
    """Lazy import to avoid circular dependencies."""
    from bot.monitoring import get_metrics
    return get_metrics()


def track_event(
    event_name: str,
    user_id: int,
    data: Optional[Dict[str, Any]] = None,
) -> None:
    """Fire a tracking event if metrics are initialised."""
    m = _metrics()
    if m:
        m.track_event(event_name, user_id, data or {})


def track_conversion(
    funnel: str,
    step: str,
    user_id: int,
) -> None:
    """Record a conversion step if metrics are initialised."""
    m = _metrics()
    if m:
        m.track_conversion(funnel, step, user_id)


def track_payment(
    method: str,
    user_id: int,
) -> None:
    """Shorthand: track both payment-initiated event + conversion step."""
    track_event(f"payment_{method}_initiated", user_id)
    track_conversion("customer_journey", "payment_initiated", user_id)
