# Card 4: Photo Proof of Delivery

**Phase:** 1 — Core Thailand Differentiators
**Priority:** High
**Effort:** Medium (1 day)
**Dependencies:** Card 3 (delivery types — dead drop requires photo)

---

## Why

Standard in Grab/Foodpanda/LINE MAN — rider takes photo of food at door/dead drop as proof of delivery. Prevents disputes ("I never received it") and builds trust. Critical for dead drop orders where the customer isn't physically present.

## Scope

- After order status = `confirmed`, admin/rider must upload delivery photo before marking `delivered`
- Photo sent automatically to customer as confirmation
- Audit trail: photo stored with order permanently
- Required for dead_drop orders, optional for door delivery, skipped for pickup

## Files to Modify

| File | Changes |
|------|---------|
| `bot/database/models/main.py` | Add `delivery_photo` (String, file_id), `delivery_photo_at` (DateTime), `delivery_photo_by` (BigInteger) to `Order` |
| `bot/handlers/admin/main.py` | Add "Upload Delivery Photo" button on confirmed orders. Handle photo upload. Auto-transition to delivered after photo for dead_drop. |
| `bot/states/user_state.py` or new `bot/states/admin_state.py` | Add `waiting_delivery_photo` admin state |
| `bot_cli.py` | Add `--delivery-photo` flag to `order --status-delivered`. Block delivery without photo for dead_drop orders. |
| `bot/payments/notifications.py` | Add `notify_delivery_with_photo()`: send delivery photo to customer |
| `bot/keyboards/inline.py` | Add upload photo button for admin order view |
| `bot/i18n/strings.py` | Add delivery photo strings |

## Implementation Details

### Admin Delivery Flow
```
Current:  Admin clicks "Mark Delivered" → done
New:      Admin clicks "Upload Delivery Photo" → sends photo →
          Bot saves file_id → auto-marks delivered →
          Photo sent to customer with delivery confirmation
```

### Enforcement Rules
```python
if order.delivery_type == "dead_drop" and not order.delivery_photo:
    raise ValueError("Dead drop orders require delivery photo proof")
# Door delivery: photo recommended but not required
# Pickup: no photo needed
```

### Customer Notification
```python
async def notify_delivery_with_photo(bot, order):
    caption = f"Order {order.order_code} delivered!\n"
    if order.delivery_type == "dead_drop":
        caption += f"Left at: {order.drop_instructions}\n"
    caption += "Thank you for your order!"
    await bot.send_photo(order.buyer_id, order.delivery_photo, caption=caption)
```

### Model Changes
```python
# Add to Order class
delivery_photo = Column(String(255), nullable=True)    # Telegram file_id
delivery_photo_at = Column(DateTime, nullable=True)
delivery_photo_by = Column(BigInteger, nullable=True)  # Admin/rider who took photo
```

## Acceptance Criteria

- [ ] Admin can upload delivery photo via bot
- [ ] Photo auto-sent to customer on delivery
- [ ] Dead drop orders require photo before marking delivered
- [ ] Door delivery orders allow optional photo
- [ ] Pickup orders skip photo requirement
- [ ] Photo stored in Order record with timestamp
- [ ] CLI supports delivery photo workflow
- [ ] Customer receives photo with delivery confirmation message

## Test Plan

| Test File | Tests | What to Assert |
|-----------|-------|----------------|
| `tests/unit/database/test_models.py` | `test_order_delivery_photo_fields` | `delivery_photo`, `delivery_photo_at`, `delivery_photo_by` nullable |
| `tests/unit/database/test_crud.py` | `test_save_delivery_photo` | Updates delivery_photo + timestamp + admin_id on order |
| | `test_mark_delivered_with_photo` | Order transitions to delivered when photo is set |
| | `test_block_delivery_dead_drop_no_photo` | Raises error if dead_drop order has no delivery_photo |
| | `test_allow_delivery_door_no_photo` | Door delivery can mark delivered without photo |
| | `test_skip_photo_pickup` | Pickup orders skip photo requirement entirely |
| `tests/integration/test_order_lifecycle.py` | `test_delivery_photo_proof_flow` | Confirmed → upload photo → delivered → customer notified |
| | `test_dead_drop_requires_photo` | dead_drop order blocks delivery without photo |
