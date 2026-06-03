"""Distance → ETA estimation for live driver tracking (Card 26).

A deliberately simple model: straight-line distance over an average urban
delivery speed, plus a small fixed handling buffer. Monotonic in distance, which
is the property dispatch and the customer-facing ETA rely on.
"""

import math

from bot.config import EnvKeys

# Fixed minutes added on top of travel time (parking, handoff, building access).
HANDLING_BUFFER_MIN = 2


def estimate_eta_minutes(distance_km: float, avg_speed_kmh: float | None = None) -> int:
    """Estimate minutes for a driver ``distance_km`` away to arrive.

    Always returns at least 1 minute so a customer never sees "0 min away" while
    the driver is still en route. Strictly non-decreasing with distance.
    """
    if distance_km < 0:
        distance_km = 0.0
    if avg_speed_kmh is None:
        avg_speed_kmh = EnvKeys.DRIVER_AVG_SPEED_KMH
    if avg_speed_kmh <= 0:
        avg_speed_kmh = 25.0

    travel_min = (distance_km / avg_speed_kmh) * 60.0
    total = math.ceil(travel_min + HANDLING_BUFFER_MIN)
    return max(1, total)
