# Card 10: Delivery Time Slots + Bangkok Zone Pricing

**Phase:** 3 — Restaurant Flow Polish
**Priority:** Low-Medium
**Effort:** Low-Medium (1 day)
**Dependencies:** Card 2 (GPS coordinates for zone detection)

---

## Why

Bangkok traffic makes delivery timing critical. Peak hours (11:30-13:00, 17:30-19:30) need longer slots. Different zones (Sukhumvit, Silom, outskirts) have different delivery fees based on distance. This is standard for Thai delivery apps.

## Scope

- Configurable delivery time slots
- User selects preferred delivery slot at checkout
- Zone-based delivery fee calculation using Haversine distance from restaurant
- Admin configures zones and fees via CLI

## Files to Create

| File | Purpose |
|------|---------|
| `bot/config/delivery_zones.py` | Zone definitions, fee calculation, time slot management |

## Files to Modify

| File | Changes |
|------|---------|
| `bot/database/models/main.py` | Add `delivery_zone` (String), `delivery_fee` (Numeric), `preferred_time_slot` (String) to `Order`. Add `DeliveryZone` model. |
| `bot/config/env.py` | Add `DELIVERY_ZONES_ENABLED`, `TIME_SLOTS_ENABLED`, `RESTAURANT_LAT`, `RESTAURANT_LNG` |
| `bot/handlers/user/order_handler.py` | Auto-detect zone from GPS. Show time slot picker. Add delivery fee to order total. |
| `bot/keyboards/inline.py` | Time slot selection buttons, zone display |
| `bot_cli.py` | Zone management commands: `zone add/edit/remove` |
| `bot/i18n/strings.py` | Time slot and zone strings |

## Implementation Details

### Time Slot System
```python
DEFAULT_TIME_SLOTS = [
    {"id": "lunch_early", "label": "11:00-12:00", "available": True},
    {"id": "lunch_peak",  "label": "12:00-13:00", "available": True},
    {"id": "lunch_late",  "label": "13:00-14:00", "available": True},
    {"id": "afternoon",   "label": "14:00-17:00", "available": True},
    {"id": "dinner_early","label": "17:00-18:30", "available": True},
    {"id": "dinner_peak", "label": "18:30-20:00", "available": True},
    {"id": "dinner_late", "label": "20:00-21:30", "available": True},
    {"id": "asap",        "label": "ASAP",        "available": True},
]
```

### Zone Pricing (distance-based)
```python
DELIVERY_ZONES = [
    {"name": "Zone 1 - Central", "max_km": 3, "fee": 0},
    {"name": "Zone 2 - Inner",   "max_km": 7, "fee": 30},
    {"name": "Zone 3 - Mid",     "max_km": 12, "fee": 50},
    {"name": "Zone 4 - Outer",   "max_km": 20, "fee": 80},
    {"name": "Zone 5 - Far",     "max_km": 99, "fee": 120},
]
```

### Zone Detection (Haversine formula)
```python
from math import radians, sin, cos, sqrt, atan2

def calculate_distance(lat1, lon1, lat2, lon2):
    """Haversine formula — distance in km"""
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1-a))

def get_delivery_zone(lat, lon, restaurant_lat, restaurant_lon):
    distance = calculate_distance(lat, lon, restaurant_lat, restaurant_lon)
    for zone in DELIVERY_ZONES:
        if distance <= zone["max_km"]:
            return zone
    return DELIVERY_ZONES[-1]
```

### Checkout Flow Addition
```
... → Location → Delivery Type → [Time Slot Selection] → [Zone + Fee Display] → Phone → Payment
```

### Model Changes
```python
# Add to Order
delivery_zone = Column(String(50), nullable=True)
delivery_fee = Column(Numeric(12, 2), default=0)
preferred_time_slot = Column(String(50), nullable=True)

# New model
class DeliveryZone(Base):
    __tablename__ = "delivery_zones"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    max_distance_km = Column(Float, nullable=False)
    fee = Column(Numeric(12, 2), default=0)
    is_active = Column(Boolean, default=True)
```

### Config
```env
RESTAURANT_LAT=13.7563
RESTAURANT_LNG=100.5018
DELIVERY_ZONES_ENABLED=true
TIME_SLOTS_ENABLED=true
```

## Acceptance Criteria

- [ ] Time slots configurable and displayed at checkout
- [ ] Zone auto-detected from GPS coordinates
- [ ] Delivery fee calculated and added to order total
- [ ] User sees zone + fee before confirming order
- [ ] Admin can manage zones via CLI
- [ ] Time slots can be enabled/disabled
- [ ] Order stores selected slot and zone

## Test Plan

| Test File | Tests | What to Assert |
|-----------|-------|----------------|
| `tests/unit/utils/test_delivery_zones.py` | `test_haversine_distance` | Known lat/lng pairs return correct km distance |
| | `test_get_zone_central` | 1km from restaurant → Zone 1, fee=0 |
| | `test_get_zone_inner` | 5km → Zone 2, fee=30 |
| | `test_get_zone_far` | 25km → Zone 5, fee=120 |
| | `test_get_zone_no_gps` | Returns None/default when no coordinates |
| | `test_time_slots_default` | All 8 default slots present and available |
| | `test_time_slot_disable` | Disabled slot not returned in available list |
| `tests/unit/database/test_models.py` | `test_order_zone_and_fee_fields` | `delivery_zone`, `delivery_fee`, `preferred_time_slot` persist |
| | `test_delivery_zone_model` | DeliveryZone CRUD operations |
| `tests/integration/test_order_lifecycle.py` | `test_order_with_delivery_fee` | Order total includes delivery fee |
