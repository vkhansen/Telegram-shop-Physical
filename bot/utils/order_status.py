"""
Order status workflow management (Card 9).

Defines valid status transitions for the kitchen & delivery workflow:
pending → reserved → confirmed → preparing → ready → out_for_delivery → delivered
                   ↘ cancelled
                   ↘ expired
"""

# Valid status transitions: current_status → set of allowed next statuses
VALID_TRANSITIONS = {
    "pending": {"reserved", "cancelled"},
    "reserved": {"confirmed", "cancelled", "expired"},
    "confirmed": {"preparing", "cancelled"},
    "preparing": {"ready", "cancelled"},
    "ready": {"out_for_delivery", "cancelled"},
    "out_for_delivery": {"delivered", "cancelled"},
    "delivered": set(),  # Terminal state
    "cancelled": set(),  # Terminal state
    "expired": set(),    # Terminal state
}

ALL_STATUSES = set(VALID_TRANSITIONS.keys())

# Statuses that the reservation cleaner should expire
EXPIRABLE_STATUSES = {"reserved"}


def is_valid_transition(current_status: str, new_status: str) -> bool:
    """Check if a status transition is valid."""
    allowed = VALID_TRANSITIONS.get(current_status, set())
    return new_status in allowed


def get_allowed_transitions(current_status: str) -> set[str]:
    """Get the set of valid next statuses from current status."""
    return VALID_TRANSITIONS.get(current_status, set())
