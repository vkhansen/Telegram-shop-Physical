# Card 2: GPS-Enabled Delivery Address + Live Location

**Phase:** 1 — Core Thailand Differentiators
**Priority:** High
**Effort:** Low (half day)
**Dependencies:** None

---

## Why

Bangkok addresses are notoriously messy — soi numbers, moo, unnamed roads, condos with identical names across districts. Grab, LINE MAN, and Robinhood all use GPS pin + live location sharing as the primary delivery method. This is table stakes for Thai delivery.

## Scope

- User can share Telegram location (GPS pin) during checkout
- User can optionally share live location for rider tracking
- Store lat/lng and generate Google Maps link
- Display location on admin order view and CLI
- Keep text address as fallback (not replaced)

## Files to Modify

| File | Changes |
|------|---------|
| `bot/database/models/main.py` | Add `latitude` (Float), `longitude` (Float), `google_maps_link` (String 255) to `Order` and `CustomerInfo` |
| `bot/handlers/user/order_handler.py` | After address text entry: offer "Share Location" button. Handle `message.location` and `message.venue`. Generate Google Maps link. Allow skip. |
| `bot/states/user_state.py` | Add `waiting_location` state to `OrderStates` |
| `bot/keyboards/inline.py` | Add location-sharing request button (`KeyboardButton` with `request_location=True`) |
| `bot_cli.py` | Display lat/lng + Maps link in order details view |
| `bot/handlers/admin/main.py` | Show Google Maps link in admin order notification |
| `bot/payments/notifications.py` | Include Maps link in order confirmation/notification messages |
| `bot/i18n/strings.py` | Add location-related strings |

## Implementation Details

### Checkout Flow Change
```
Current:  Address (text) → Phone → Note → Payment
New:      Address (text) → "Share Location" (optional) → Phone → Note → Payment
```

### Location Handling
```python
@router.message(OrderStates.waiting_location)
async def process_location(message: Message, state: FSMContext):
    if message.location:
        lat = message.location.latitude
        lng = message.location.longitude
        maps_link = f"https://www.google.com/maps?q={lat},{lng}"
        await state.update_data(latitude=lat, longitude=lng, google_maps_link=maps_link)
```

### Telegram Location Button
```python
location_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Share My Location", request_location=True)]],
    resize_keyboard=True, one_time_keyboard=True
)
```

### Live Location (bonus)
- Telegram supports `live_period` in location messages
- Bot can receive location updates for 1-8 hours
- Store latest location for rider reference
- Listen for `edited_message` with location updates

### Model Changes
```python
# Add to Order class
latitude = Column(Float, nullable=True)
longitude = Column(Float, nullable=True)
google_maps_link = Column(String(255), nullable=True)

# Add to CustomerInfo class (save for reuse)
latitude = Column(Float, nullable=True)
longitude = Column(Float, nullable=True)
```

## Acceptance Criteria

- [ ] User can share GPS location during checkout
- [ ] Location is optional (text address still works alone)
- [ ] Google Maps link auto-generated from coordinates
- [ ] Admin sees Maps link in order view
- [ ] CLI displays coordinates and Maps link
- [ ] Saved to CustomerInfo for future orders
- [ ] Live location updates handled (if shared)

## Test Plan

| Test File | Tests | What to Assert |
|-----------|-------|----------------|
| `tests/unit/database/test_models.py` | `test_order_gps_fields` | `latitude`, `longitude`, `google_maps_link` nullable, stored as Float/String |
| | `test_customer_info_gps_fields` | CustomerInfo stores lat/lng for reuse |
| `tests/unit/database/test_crud.py` | `test_save_order_location` | GPS coordinates + maps link persist on order |
| | `test_order_without_location` | Order valid with text address only (no GPS) |
| `tests/unit/utils/test_validators.py` | `test_validate_latitude_range` | Reject lat outside -90 to 90 |
| | `test_validate_longitude_range` | Reject lng outside -180 to 180 |
| | `test_generate_maps_link` | Returns correct Google Maps URL format |
