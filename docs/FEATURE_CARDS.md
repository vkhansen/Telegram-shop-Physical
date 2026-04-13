# Thailand Restaurant Delivery Conversion — Feature Cards

> **Planning companion:** See [`docs/ROADMAP.md`](docs/ROADMAP.md) for the master plan — milestones, dependency graph, and exit criteria. This file is the status board (what shipped, what's in flight).
>
> **Base repo:** Telegram-shop-Physical (inventory reservation, address+phone collection, order statuses `pending→reserved→confirmed→delivered`, COD, BTC, timezone config)
>
> **Target:** Bangkok restaurant delivery bot with PromptPay QR, GPS delivery, dead drops, photo proof, Thai language, THB currency, kitchen workflow

---

## Status Board

### DONE

| Card | Name | Phase | Detail |
|------|------|-------|--------|
| CARD-01 | PromptPay QR Payment | Phase 1 | [docs/done/CARD-01](done/CARD-01-promptpay-qr-payment.md) |
| CARD-02 | GPS Delivery Address | Phase 1 | [docs/done/CARD-02](done/CARD-02-gps-delivery-address.md) |
| CARD-03 | Dead Drop Delivery | Phase 1 | [docs/done/CARD-03](done/CARD-03-dead-drop-delivery.md) |
| CARD-04 | Photo Proof of Delivery | Phase 1 | [docs/done/CARD-04](done/CARD-04-photo-proof-delivery.md) |
| CARD-05 | Thai Language i18n | Phase 2 | [docs/done/CARD-05](done/CARD-05-thai-language-i18n.md) |
| CARD-06 | THB Currency | Phase 2 | [docs/done/CARD-06](done/CARD-06-thb-currency.md) |
| CARD-07 | Thai Address Format | Phase 2 | [docs/done/CARD-07](done/CARD-07-thai-address-format.md) |
| CARD-08 | Menu Modifiers | Phase 3 | [docs/done/CARD-08](done/CARD-08-menu-modifiers.md) |
| CARD-09 | Kitchen & Delivery Workflow | Phase 3 | [docs/done/CARD-09](done/CARD-09-kitchen-delivery-workflow.md) |
| CARD-10 | Delivery Zones & Timeslots | Phase 3 | [docs/done/CARD-10](done/CARD-10-delivery-zones-timeslots.md) |
| CARD-11 | COD Thai Localization | Phase 3 | [docs/done/CARD-11](done/CARD-11-cod-thai-localization.md) |
| CARD-12 | Timezone Bangkok | Phase 3 | [docs/done/CARD-12](done/CARD-12-timezone-bangkok.md) |
| CARD-13 | Driver Chat + Live Location | Phase 3 | [docs/done/CARD-13](done/CARD-13-driver-chat-live-location.md) |
| CARD-14 | Language Picker | Phase 3 | [docs/done/CARD-14](done/CARD-14-language-picker.md) |
| CARD-15 | GPS Live Tracking & Delivery Chat | Phase 3 | [docs/done/CARD-15](done/CARD-15-gps-live-tracking-delivery-chat.md) |
| CARD-18 | Multi-Crypto Payments (SOL/USDT/LTC) | Phase 2 | [docs/done/CARD-18](done/CARD-18-crypto-payment-verification.md) |
| CARD-RC1 | Multi-Media Menu Items | Restaurant Core | [see below](#restaurant-core-cards) |
| CARD-RC2 | Prep Time + Kitchen Tracking | Restaurant Core | [see below](#restaurant-core-cards) |
| CARD-RC3 | Allergen Management | Restaurant Core | [see below](#restaurant-core-cards) |
| CARD-RC4 | Availability Windows + Daily Limits | Restaurant Core | [see below](#restaurant-core-cards) |
| CARD-RC5 | Multi-Currency | Restaurant Core | [see below](#restaurant-core-cards) |
| CARD-RC6 | Menu Import/Export | Restaurant Core | [see below](#restaurant-core-cards) |
| CARD-RC7 | Interactive Modifier Builder | Restaurant Core | [see below](#restaurant-core-cards) |
| CARD-FC1 | Product Search | Feature | [see below](#restaurant-core-cards) |
| CARD-FC2 | Reorder Button | Feature | [see below](#restaurant-core-cards) |
| CARD-FC3 | Coupon / Promo Codes | Feature | [see below](#restaurant-core-cards) |
| CARD-FC4 | Review / Rating System | Feature | [see below](#restaurant-core-cards) |
| CARD-FC5 | Invoice / Receipt Generation | Feature | [see below](#restaurant-core-cards) |
| CARD-FC6 | Support Ticketing | Feature | [see below](#restaurant-core-cards) |
| CARD-FC7 | Accounting / Revenue Export | Feature | [see below](#restaurant-core-cards) |
| CARD-FC8 | Customer Segmentation | Feature | [see below](#restaurant-core-cards) |
| CARD-FC9 | Multi-Store / Multi-Location | Feature | [see below](#restaurant-core-cards) |

### BACKLOG (Not Started)

Prioritized, highest-impact first. See [Next Up](#next-up-prioritized-backlog) below for rationale.

| # | Card | Name | Phase | Progress | Priority | Effort | Detail |
|---|------|------|-------|----------|----------|--------|--------|
| 1 | CARD-21 | Persistent Cart Stub + Brand/Store Switch Guards | UX Polish | 0% | High | Medium (3–5d) | [CARD-21](CARD-21-persistent-cart-stub.md) |
| 2 | CARD-19 | Multi-Brand Bot Coordination | Phase 3 — Platform Scale | 15% | High | Very High (10–14d) | [CARD-19](CARD-19-multi-brand-bot-coordination.md) |
| 3 | CARD-17 | Grok AI Admin Assistant | Phase 5 — Admin Intelligence | 100% | Medium | High (5–7d) | [CARD-17](CARD-17-grok-admin-assistant.md) |
| 4 | CARD-22 | Grok AI Customer Assistant | Phase 5 — Customer Intelligence | 0% | Medium | Medium (3–5d) | [CARD-22](CARD-22-grok-customer-assistant.md) |
| 5 | CARD-16 | Line API Integration | Phase 5 — Multi-Platform | 0% | Medium-High | High (5–8d) | [CARD-16](CARD-16-line-api-integration.md) |

### Next Up (Prioritized Backlog)

1. **CARD-21 — Persistent Cart Stub.** Cheapest and highest immediate UX win. No new infra; pure handler/model work on a feature users hit every session. Unblocks cleaner multi-brand UX (prereq for CARD-19's brand switching flow).
2. **CARD-19 — Multi-Brand Coordination.** DB models already exist (15%). This is the strategic growth lever — one backend serving N brands — and every other backlog item benefits from the brand context it establishes. Large effort; plan as a multi-week epic.
3. **CARD-17 — Grok Admin Assistant.** ✅ Done (100%). Unlocks bulk menu ops and natural-language admin.
4. **CARD-22 — Grok Customer Assistant.** Builds directly on Card 17's reusable Grok client, rate limiter, and tool-call loop. Customer-facing: natural language menu search, deals, nearby stores, order status, and AI-driven support ticket creation. Medium effort — most infrastructure already exists from Card 17.
5. **CARD-16 — Line API Integration.** Highest theoretical market expansion but highest architectural cost (requires transport-layer abstraction across every handler). Defer until CARD-19's brand context is stable — otherwise the refactor compounds.

---

## Current Test Coverage Analysis

### Existing Test Suite (171 tests, ~2,769 lines)

| Test File | Tests | What's Covered |
|-----------|-------|----------------|
| `tests/conftest.py` | 19 fixtures | SQLite in-memory DB, roles, users, products, orders, payments, carts |
| `tests/unit/database/test_models.py` | 17 | Role permissions, User creation/banning, Goods, Order+OrderItems, CustomerInfo, BitcoinAddress, ReferenceCode, ShoppingCart, InventoryLog |
| `tests/unit/database/test_crud.py` | 37 | Create/Read/Update/Delete operations, ban/unban flows, duplicate prevention |
| `tests/unit/database/test_inventory.py` | 16 | Reserve/release/deduct/add inventory, insufficient stock, stats, logging |
| `tests/unit/database/test_cart.py` | 7 | Cart items, totals, add/update/exceeding stock |
| `tests/unit/payments/test_bitcoin.py` | 12 | Address loading, retrieval, usage tracking, bulk add, stats |
| `tests/unit/referrals/test_reference_codes.py` | 30 | Code generation, creation, validation (8 cases), usage, deactivation, queries |
| `tests/unit/utils/test_validators.py` | 23 | UserDataUpdate, CategoryRequest, BroadcastMessage, SearchQuery, helper validators |
| `tests/unit/utils/test_order_codes.py` | 4 | Code generation, randomness, uniqueness, max-attempts |
| `tests/integration/test_order_lifecycle.py` | 5 | Full cash order, cancellation, multi-item, customer stats, insufficient stock |

### Test Patterns Used
- **Async:** `@pytest.mark.asyncio` with `async def` tests
- **DB:** SQLite in-memory, `expire_on_commit=False`, fresh tables per test
- **Mocking:** `patch()` for file I/O, cache invalidation (globally mocked), logging, metrics
- **Markers:** `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.models`, `@pytest.mark.crud`, etc.

### Coverage Gaps (No Tests Exist For)
- **Handler layer** — No Telegram command/callback/message handler tests
- **Notification system** — `bot/payments/notifications.py` untested
- **Referral bonus calculations** — Business logic for bonus distribution
- **Admin operations** — Broadcast, statistics, user management beyond ban
- **Timezone handling** — `bot/config/timezone.py`
- **i18n/localization** — String resolution, locale switching
- **Concurrent operations** — Race conditions in inventory
- **CLI** — `bot_cli.py` (1460+ lines, zero tests)

### How New Features Should Be Tested
Each feature card below includes a **Test Plan** section following the existing patterns:
- Unit tests for new model fields/methods → `tests/unit/database/`
- Unit tests for new business logic (QR gen, zone calc, modifier pricing) → `tests/unit/`
- Integration tests for new order flows → `tests/integration/`
- New fixtures in `conftest.py` for Thailand-specific test data
- All tests async-compatible using existing `db_session` / `async_db_session` fixtures

---

## Phase 1: Core Thailand Differentiators (Cards 1–4) — DONE

These cards deliver the minimum viable Thailand restaurant delivery experience.

---

### Card 1: PromptPay QR Payment Generation + Verification — DONE

**Why:** PromptPay is Thailand's #1 payment (90%+ adoption). Users expect to scan a QR from SCB/KBank/TrueMoney and pay instantly. The current repo only supports Bitcoin and COD.

**Scope:**
- New payment method `promptpay` alongside existing `bitcoin` and `cash`
- Generate dynamic PromptPay QR code with amount embedded
- User uploads payment receipt photo after paying
- Admin verifies payment manually via bot button or CLI

**Files to Create:**
| File | Purpose |
|------|---------|
| `bot/payments/promptpay.py` | QR generation using `promptpay` + `qrcode` Python libs |
| `bot/handlers/user/payment_promptpay_handler.py` | User-facing receipt upload flow |

**Files to Modify:**
| File | Changes |
|------|---------|
| `bot/database/models/main.py` | Add `payment_receipt_photo` (String, file_id) to `Order` model. Add `promptpay_account` to `BotSettings` defaults. |
| `bot/config/env.py` | Add `PROMPTPAY_ID` (phone or national ID), `PROMPTPAY_ACCOUNT_NAME` env vars |
| `bot/handlers/user/order_handler.py` | Add `promptpay` as third payment method option in checkout. After selection: generate QR → send to user → transition to receipt upload state. |
| `bot/states/payment_state.py` | Add `waiting_receipt_photo` state |
| `bot/handlers/admin/main.py` | Add "✅ Verify Payment" inline button on order view |
| `bot_cli.py` | Add `--verify-payment` flag to `order` command. Add `promptpay` subcommand for account config. |
| `bot/payments/notifications.py` | Add `notify_payment_received()` for admin alert when receipt uploaded |
| `bot/i18n/strings.py` | Add promptpay-related strings (en/ru/th) |
| `bot/keyboards/inline.py` | Add promptpay payment button, verify payment button |
| `requirements.txt` | Add `promptpay>=1.1`, `qrcode[pil]>=7.4` |

**Implementation Details:**

1. **QR Generation Flow:**
   ```
   User selects PromptPay → bot generates QR with:
     - PromptPay ID (from config)
     - Amount (order total in THB)
     - Note: order_code
   → QR sent as photo message to user
   → User pays via bank app
   → User uploads screenshot/receipt photo
   → Bot saves file_id to Order.payment_receipt_photo
   → Admin notified with receipt photo + order details
   → Admin clicks "✅ Verified" → order status → confirmed
   ```

2. **PromptPay QR Payload:**
   - Use EMVCo standard (same as all Thai banks)
   - `promptpay` Python lib handles payload encoding
   - `qrcode` lib renders to PNG
   - Send via `bot.send_photo()` with caption showing amount + instructions

3. **Receipt Verification:**
   - **MVP:** Admin manual verification via inline button
   - **Future (optional):** OCR auto-check using Google Vision or OpenAI to match amount + reference

4. **Config:**
   ```env
   PROMPTPAY_ID=0812345678          # Phone number or national ID
   PROMPTPAY_ACCOUNT_NAME=ร้านอาหาร  # Display name for receipt
   ```

**Order Model Changes:**
```python
# Add to Order class
payment_receipt_photo = Column(String(255), nullable=True)  # Telegram file_id
payment_verified_by = Column(BigInteger, nullable=True)     # Admin who verified
payment_verified_at = Column(DateTime, nullable=True)
```

**Dependencies:** `promptpay>=1.1`, `qrcode[pil]>=7.4`, `Pillow>=10.0`

**Effort:** Medium (1–2 days)

**Acceptance Criteria:**
- [ ] User can select PromptPay at checkout
- [ ] QR code with correct amount is generated and sent
- [ ] User can upload receipt photo
- [ ] Admin receives notification with receipt
- [ ] Admin can verify payment via bot button or CLI
- [ ] Order transitions to confirmed after verification
- [ ] PromptPay account configurable via env vars and CLI

**Test Plan:**
| Test File | Tests | What to Assert |
|-----------|-------|----------------|
| `tests/unit/payments/test_promptpay.py` | `test_generate_qr_payload` | QR payload contains correct PromptPay ID + amount in EMVCo format |
| | `test_generate_qr_image` | Returns valid PNG bytes, correct dimensions |
| | `test_qr_with_zero_amount` | Raises ValueError — amount must be > 0 |
| | `test_qr_with_invalid_promptpay_id` | Raises ValueError for malformed phone/ID |
| `tests/unit/database/test_models.py` | `test_order_payment_receipt_fields` | `payment_receipt_photo`, `payment_verified_by`, `payment_verified_at` nullable, default None |
| | `test_order_promptpay_payment_method` | Order with `payment_method="promptpay"` persists correctly |
| `tests/unit/database/test_crud.py` | `test_verify_payment` | Sets `payment_verified_by` + `payment_verified_at`, transitions order to confirmed |
| | `test_save_receipt_photo` | Updates `payment_receipt_photo` with file_id string |
| `tests/integration/test_order_lifecycle.py` | `test_promptpay_order_full_flow` | Create order → select promptpay → upload receipt → admin verify → confirmed → delivered |
| | `test_promptpay_order_without_receipt` | Cannot verify without receipt photo |

---

### Card 2: GPS-Enabled Delivery Address + Live Location — DONE

**Why:** Bangkok addresses are notoriously messy (soi numbers, moo, unnamed roads, condos with identical names). Grab/LINE MAN/Robinhood all use GPS pin + live location. This is table stakes for Thai delivery.

**Scope:**
- User can share Telegram location (GPS pin) during checkout
- User can optionally share live location for rider tracking
- Store lat/lng and generate Google Maps link
- Display location on admin order view and CLI
- Keep text address as fallback

**Files to Modify:**
| File | Changes |
|------|---------|
| `bot/database/models/main.py` | Add `latitude` (Float), `longitude` (Float), `google_maps_link` (String 255) to `Order` and `CustomerInfo` models |
| `bot/handlers/user/order_handler.py` | After address text entry: offer "📍 Share Location" button. Handle `message.location` and `message.venue`. Generate Google Maps link. Store coordinates. Allow skip if text address provided. |
| `bot/states/user_state.py` | Add `waiting_location` state to `OrderStates` |
| `bot/keyboards/inline.py` | Add location-sharing request button (KeyboardButton with `request_location=True`) |
| `bot_cli.py` | Display lat/lng + Maps link in order details view |
| `bot/handlers/admin/main.py` | Show Google Maps link in admin order notification |
| `bot/payments/notifications.py` | Include Maps link in order confirmation/notification messages |
| `bot/i18n/strings.py` | Add location-related strings |

**Implementation Details:**

1. **Checkout Flow Change:**
   ```
   Current:  Address (text) → Phone → Note → Payment
   New:      Address (text) → "📍 Share Location" (optional) → Phone → Note → Payment
   ```

2. **Location Handling:**
   ```python
   # In order_handler.py
   @router.message(OrderStates.waiting_location)
   async def process_location(message: Message, state: FSMContext):
       if message.location:
           lat = message.location.latitude
           lng = message.location.longitude
           maps_link = f"https://www.google.com/maps?q={lat},{lng}"
           await state.update_data(latitude=lat, longitude=lng, google_maps_link=maps_link)
       # Also handle message.venue for named locations
   ```

3. **Telegram Location Button:**
   ```python
   # Use ReplyKeyboardMarkup (not inline) for location sharing
   location_kb = ReplyKeyboardMarkup(
       keyboard=[[KeyboardButton(text="📍 Share My Location", request_location=True)]],
       resize_keyboard=True, one_time_keyboard=True
   )
   ```

4. **Live Location (bonus):**
   - Telegram supports `live_period` in location messages
   - Bot can receive location updates for 1–8 hours
   - Store latest location for rider reference
   - Implementation: listen for `edited_message` with location updates

**Model Changes:**
```python
# Add to Order class
latitude = Column(Float, nullable=True)
longitude = Column(Float, nullable=True)
google_maps_link = Column(String(255), nullable=True)

# Add to CustomerInfo class (save for reuse)
latitude = Column(Float, nullable=True)
longitude = Column(Float, nullable=True)
```

**Effort:** Low (half day)

**Acceptance Criteria:**
- [ ] User can share GPS location during checkout
- [ ] Location is optional (text address still works alone)
- [ ] Google Maps link auto-generated from coordinates
- [ ] Admin sees Maps link in order view
- [ ] CLI displays coordinates and Maps link
- [ ] Saved to CustomerInfo for future orders
- [ ] Live location updates handled (if shared)

**Test Plan:**
| Test File | Tests | What to Assert |
|-----------|-------|----------------|
| `tests/unit/database/test_models.py` | `test_order_gps_fields` | `latitude`, `longitude`, `google_maps_link` nullable, stored as Float/String |
| | `test_customer_info_gps_fields` | CustomerInfo stores lat/lng for reuse |
| `tests/unit/database/test_crud.py` | `test_save_order_location` | GPS coordinates + maps link persist on order |
| | `test_order_without_location` | Order valid with text address only (no GPS) |
| `tests/unit/utils/test_validators.py` | `test_validate_latitude_range` | Reject lat outside -90 to 90 |
| | `test_validate_longitude_range` | Reject lng outside -180 to 180 |
| | `test_generate_maps_link` | Returns `https://www.google.com/maps?q={lat},{lng}` |

---

### Card 3: Dead Drop Option + Custom Delivery Instructions — DONE

**Why:** Condos with security guards, offices with reception desks, gated communities — Bangkok customers frequently need "leave with guard", "put at door", "lobby shelf". This is standard in Thai delivery apps (Grab calls it "Leave at Door").

**Scope:**
- New delivery type selection: Door delivery / Dead drop / Self-pickup
- Dead drop: collect specific instructions + optional photo of drop location
- Photo of drop location stored for rider reference
- Update order status to require photo confirmation before "delivered"

**Files to Modify:**
| File | Changes |
|------|---------|
| `bot/database/models/main.py` | Add `delivery_type` (String, enum: door/dead_drop/pickup) to `Order`. Add `drop_location_photo` (String, file_id) to `Order`. |
| `bot/handlers/user/order_handler.py` | New step after address/location: select delivery type. If dead_drop: collect instructions text + optional photo of drop location. If pickup: skip address entirely. |
| `bot/states/user_state.py` | Add `waiting_delivery_type`, `waiting_drop_instructions`, `waiting_drop_photo` states |
| `bot/keyboards/inline.py` | Add delivery type selection buttons (🚪 Door / 📦 Dead Drop / 🏪 Pickup) |
| `bot_cli.py` | Display delivery type + drop instructions in order view |
| `bot/payments/notifications.py` | Include delivery type and drop instructions in admin notifications |
| `bot/i18n/strings.py` | Add delivery type strings |

**Implementation Details:**

1. **Updated Checkout Flow:**
   ```
   Address → Location (opt) → Delivery Type Selection → [Dead Drop Instructions + Photo] → Phone → Note → Payment
   ```

2. **Delivery Type Enum:**
   ```python
   # Not a SQLAlchemy enum — use string column with validation
   DELIVERY_TYPES = {
       "door": "🚪 Deliver to Door",
       "dead_drop": "📦 Dead Drop / Leave at Location",
       "pickup": "🏪 Self Pickup"
   }
   ```

3. **Dead Drop Flow:**
   ```
   User selects "📦 Dead Drop"
   → Bot: "Please describe where to leave your order (e.g., 'with security guard at lobby', 'under the mat at room 405')"
   → User types instructions
   → Bot: "📸 Want to send a photo of the drop location? (optional)"
   → User sends photo or skips
   → Instructions + photo saved to Order
   ```

4. **Pickup Flow:**
   ```
   User selects "🏪 Self Pickup"
   → Skip address/location collection
   → Bot shows restaurant address + operating hours
   → Continue to payment
   ```

**Model Changes:**
```python
# Add to Order class
delivery_type = Column(String(20), default="door")  # door | dead_drop | pickup
drop_location_photo = Column(String(255), nullable=True)  # Telegram file_id
drop_instructions = Column(Text, nullable=True)
```

**Effort:** Low (half day)

**Acceptance Criteria:**
- [ ] User can select delivery type (door/dead drop/pickup)
- [ ] Dead drop collects text instructions
- [ ] Dead drop optionally accepts photo of location
- [ ] Pickup skips address collection
- [ ] Admin sees delivery type + instructions in order view
- [ ] CLI shows delivery type details

**Test Plan:**
| Test File | Tests | What to Assert |
|-----------|-------|----------------|
| `tests/unit/database/test_models.py` | `test_order_delivery_type_default` | Default is `"door"` |
| | `test_order_delivery_type_values` | Accepts `door`, `dead_drop`, `pickup` |
| | `test_order_drop_fields` | `drop_instructions` (Text) + `drop_location_photo` (String) nullable |
| `tests/unit/database/test_crud.py` | `test_create_dead_drop_order` | Order with delivery_type=dead_drop, instructions, and photo persists |
| | `test_create_pickup_order` | Order with delivery_type=pickup, no address required |
| `tests/integration/test_order_lifecycle.py` | `test_dead_drop_order_flow` | Full flow with dead drop type + instructions + photo |
| | `test_pickup_order_flow` | Pickup order skips address, completes successfully |

---

### Card 4: Photo Proof of Delivery — DONE

**Why:** Standard in Grab/Foodpanda/LINE MAN — rider takes photo of food at door/dead drop as proof. Prevents disputes ("I never received it") and builds trust. Critical for dead drop orders.

**Scope:**
- After order status = `confirmed`, admin/rider must upload delivery photo before marking `delivered`
- Photo sent automatically to customer as confirmation
- Audit trail: photo stored with order
- Required for dead_drop orders, optional for door delivery

**Files to Modify:**
| File | Changes |
|------|---------|
| `bot/database/models/main.py` | Add `delivery_photo` (String, file_id), `delivery_photo_at` (DateTime) to `Order` |
| `bot/handlers/admin/main.py` | Add "📸 Upload Delivery Photo" button on confirmed orders. Handle photo upload. Auto-transition to delivered after photo for dead_drop orders. |
| `bot/states/user_state.py` or new `bot/states/admin_state.py` | Add `waiting_delivery_photo` admin state |
| `bot_cli.py` | Add `--delivery-photo` flag (accepts file path) to `order --status-delivered`. Block delivery without photo for dead_drop orders. |
| `bot/payments/notifications.py` | Add `notify_delivery_with_photo()`: send delivery photo to customer with "Your order has been delivered!" message |
| `bot/keyboards/inline.py` | Add upload photo button for admin order view |
| `bot/i18n/strings.py` | Add delivery photo strings |

**Implementation Details:**

1. **Admin Delivery Flow:**
   ```
   Current:  Admin clicks "Mark Delivered" → done
   New:      Admin clicks "📸 Upload Delivery Photo" → sends photo →
             Bot saves file_id → auto-marks delivered →
             Photo sent to customer with delivery confirmation
   ```

2. **Enforcement Rules:**
   ```python
   # In delivery completion logic
   if order.delivery_type == "dead_drop" and not order.delivery_photo:
       raise ValueError("Dead drop orders require delivery photo proof")
   # Door delivery: photo recommended but not required
   # Pickup: no photo needed
   ```

3. **Customer Notification:**
   ```python
   async def notify_delivery_with_photo(bot, order):
       caption = f"✅ Order {order.order_code} delivered!\n"
       if order.delivery_type == "dead_drop":
           caption += f"📦 Left at: {order.drop_instructions}\n"
       caption += "Thank you for your order!"
       await bot.send_photo(order.buyer_id, order.delivery_photo, caption=caption)
   ```

4. **Audit Trail:**
   - Photo file_id stored permanently in Order record
   - Timestamp of photo upload
   - Admin who uploaded (from message sender)
   - Visible in CLI export and order details

**Model Changes:**
```python
# Add to Order class
delivery_photo = Column(String(255), nullable=True)    # Telegram file_id
delivery_photo_at = Column(DateTime, nullable=True)
delivery_photo_by = Column(BigInteger, nullable=True)  # Admin/rider who took photo
```

**Effort:** Medium (1 day — integrates with Telegram media handling)

**Acceptance Criteria:**
- [ ] Admin can upload delivery photo via bot
- [ ] Photo auto-sent to customer on delivery
- [ ] Dead drop orders require photo before marking delivered
- [ ] Door delivery orders allow optional photo
- [ ] Pickup orders skip photo requirement
- [ ] Photo stored in Order record with timestamp
- [ ] CLI supports delivery photo workflow
- [ ] Customer receives photo with delivery confirmation message

**Test Plan:**
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

---

## Phase 2: Thailand Localization (Cards 5–7) — DONE

These cards adapt the bot's language, currency, and address format for Thailand.

---

### Card 5: Full Thai Language (i18n) — DONE

**Why:** Most Bangkok customers prefer Thai. The bot currently supports Russian and English. Thai is essential for mass adoption.

**Scope:**
- Add `th` locale with full translation of all strings
- Update locale loading to support Thai
- Thai as default locale in config

**Files to Create:**
| File | Purpose |
|------|---------|
| (none — translations are in `bot/i18n/strings.py` as dicts) | |

**Files to Modify:**
| File | Changes |
|------|---------|
| `bot/i18n/strings.py` | Add `th` key to every translation dict (~80 strings). Full Thai translations for all UI text, buttons, messages, errors, admin panels. |
| `bot/config/env.py` | Change `BOT_LOCALE` default to `"th"` |
| `bot/i18n/main.py` | Ensure locale manager handles `th` (likely works already since it's dict-based) |

**Key Translation Groups:**
```python
# Buttons
"btn.shop": "🛒 ร้านค้า"
"btn.profile": "👤 โปรไฟล์"
"btn.rules": "📜 กฎ"
"btn.support": "☎ ติดต่อเรา"
"btn.referral": "👥 แนะนำเพื่อน"

# Order flow
"order.select_payment": "เลือกวิธีชำระเงิน"
"order.enter_address": "กรุณาใส่ที่อยู่จัดส่ง"
"order.enter_phone": "กรุณาใส่หมายเลขโทรศัพท์"
"order.confirmed": "✅ คำสั่งซื้อได้รับการยืนยัน"
"order.delivered": "🎉 คำสั่งซื้อจัดส่งแล้ว"

# PromptPay (new)
"payment.promptpay.scan": "สแกน QR เพื่อชำระเงิน"
"payment.promptpay.upload_receipt": "📸 อัปโหลดสลิปการโอนเงิน"
```

**Effort:** Low (half day — mostly translation work)

**Acceptance Criteria:**
- [ ] All UI strings available in Thai
- [ ] Bot displays Thai when `BOT_LOCALE=th`
- [ ] All new Phase 1 features have Thai translations
- [ ] Admin panel strings translated
- [ ] Error messages in Thai

**Test Plan:**
| Test File | Tests | What to Assert |
|-----------|-------|----------------|
| `tests/unit/i18n/test_strings.py` | `test_all_keys_have_th_translation` | Every key in strings dict has `th` entry |
| | `test_th_strings_not_empty` | No empty Thai translations |
| | `test_th_format_placeholders_match` | Thai strings have same `{placeholders}` as English |
| | `test_locale_switch_to_th` | `localize(key)` returns Thai when `BOT_LOCALE=th` |

---

### Card 6: THB Currency + Thai Number Formatting — DONE

**Why:** Default currency is RUB. Thailand uses Thai Baht (THB/฿). All prices, totals, receipts, and admin stats must display in THB.

**Scope:**
- Set THB as default currency
- Update all price display formatting
- Thai number formatting (comma separators)
- Baht symbol (฿) in all displays

**Files to Modify:**
| File | Changes |
|------|---------|
| `bot/config/env.py` | Change `PAY_CURRENCY` default to `"THB"` |
| `.env.example` | Update example to `PAY_CURRENCY=THB` |
| `bot/i18n/strings.py` | Update currency format strings. Add `฿` symbol. Format: `฿1,234.00` |
| `bot/handlers/user/order_handler.py` | Ensure price displays use THB format |
| `bot/handlers/user/cart_handler.py` | Cart total in THB |
| `bot/handlers/user/shop_and_goods.py` | Product prices in THB |
| `bot/handlers/user/referral_system.py` | Bonus amounts in THB |
| `bot_cli.py` | All CLI price outputs in THB |
| `bot/export/customer_csv.py` | Export headers/values in THB |

**Implementation Details:**

1. **Currency Formatting Helper:**
   ```python
   def format_thb(amount: Decimal) -> str:
       """Format amount as Thai Baht: ฿1,234.00"""
       return f"฿{amount:,.2f}"
   ```

2. **Config Change:**
   ```env
   PAY_CURRENCY=THB
   ```

**Effort:** Low (2–3 hours)

**Acceptance Criteria:**
- [ ] All prices display with ฿ symbol
- [ ] Comma-separated thousands (฿1,234.00)
- [ ] Cart totals, order summaries, receipts all in THB
- [ ] Admin stats and CLI in THB
- [ ] CSV exports show THB

**Test Plan:**
| Test File | Tests | What to Assert |
|-----------|-------|----------------|
| `tests/unit/utils/test_currency.py` | `test_format_thb_basic` | `format_thb(Decimal("1234.5"))` → `"฿1,234.50"` |
| | `test_format_thb_zero` | `format_thb(Decimal("0"))` → `"฿0.00"` |
| | `test_format_thb_large` | `format_thb(Decimal("1000000"))` → `"฿1,000,000.00"` |
| | `test_format_thb_decimal_rounding` | Two decimal places always shown |

---

### Card 7: Thai Address Format Fields — DONE

**Why:** Thai addresses follow a specific format: House no. → Soi → Road → Sub-district (Khwaeng) → District (Khet) → Province → Postal code. While GPS (Card 2) is primary, structured address fields help riders and create proper receipts.

**Scope:**
- Extend CustomerInfo with structured Thai address fields
- Optional structured input during checkout (GPS is primary)
- Display formatted Thai address in orders

**Files to Modify:**
| File | Changes |
|------|---------|
| `bot/database/models/main.py` | Add `address_structured` (JSON) column to `CustomerInfo` and `Order` — stores `{house, soi, road, subdistrict, district, province, postal_code}` |
| `bot/handlers/user/order_handler.py` | After free-text address: optionally parse or ask for structured fields. Keep simple — don't force structured input. |
| `bot_cli.py` | Format Thai address in order display |
| `bot/i18n/strings.py` | Thai address field labels |

**Implementation Details:**

1. **Approach: JSON column, not separate columns** — simpler migration, flexible:
   ```python
   address_structured = Column(JSON, nullable=True)
   # Example value:
   # {
   #   "house": "123/45",
   #   "soi": "สุขุมวิท 23",
   #   "road": "ถ.สุขุมวิท",
   #   "subdistrict": "คลองเตยเหนือ",
   #   "district": "วัฒนา",
   #   "province": "กรุงเทพมหานคร",
   #   "postal_code": "10110"
   # }
   ```

2. **Checkout Flow (simple approach):**
   - Keep single text field for address (current behavior)
   - GPS location is primary (Card 2)
   - Structured fields are optional enhancement for receipt formatting
   - Can be populated from Google Maps reverse geocoding (future)

**Effort:** Low (2–3 hours)

**Acceptance Criteria:**
- [ ] JSON address field available on Order and CustomerInfo
- [ ] Free-text address still works (backward compatible)
- [ ] Structured address displayed in formatted Thai style
- [ ] GPS coordinates remain primary delivery method

**Test Plan:**
| Test File | Tests | What to Assert |
|-----------|-------|----------------|
| `tests/unit/database/test_models.py` | `test_order_address_structured_json` | JSON column stores/retrieves Thai address dict correctly |
| | `test_customer_info_address_structured` | CustomerInfo saves structured address for reuse |
| `tests/unit/utils/test_validators.py` | `test_validate_thai_address_schema` | Validate required keys: house, soi, road, subdistrict, district, province, postal_code |
| | `test_validate_postal_code_format` | Thai postal codes are 5 digits |

---

## Phase 3: Restaurant Flow Polish (Cards 8–12) — DONE

These cards transform the generic shop into a restaurant-specific delivery operation.

---

### Card 8: Restaurant Menu Enhancers (Modifiers + Categories) — DONE

**Why:** Restaurant orders need customization: spice level, toppings, protein choice, "no onion", "extra rice". The current `Goods` model has no modifier support. Categories exist but need restaurant-style grouping.

**Scope:**
- Add modifier system to products (spice level, extras, removals)
- Restaurant-style category ordering (Starters → Mains → Drinks → Desserts)
- Modifier selection during add-to-cart
- Modifiers stored with cart items and order items

**Files to Modify:**
| File | Changes |
|------|---------|
| `bot/database/models/main.py` | Add `modifiers` (JSON) to `Goods` — defines available modifiers. Add `selected_modifiers` (JSON) to `ShoppingCart` and `OrderItem`. Add `sort_order` (Integer) to `Categories`. |
| `bot/handlers/user/shop_and_goods.py` | Show modifiers on product view. After "Add to Cart": present modifier selection (inline buttons). |
| `bot/handlers/user/cart_handler.py` | Display selected modifiers in cart view. Include modifiers in order summary. |
| `bot/handlers/user/order_handler.py` | Pass modifiers through to OrderItem creation |
| `bot/handlers/admin/adding_position_states.py` | Add modifier configuration step when adding product |
| `bot/handlers/admin/update_position_states.py` | Edit modifiers for existing products |
| `bot_cli.py` | Display modifiers in order details. Add modifier management commands. |
| `bot/keyboards/inline.py` | Modifier selection buttons (multi-select with checkmarks) |
| `bot/i18n/strings.py` | Modifier-related strings |

**Implementation Details:**

1. **Modifier Schema (JSON on Goods):**
   ```python
   # Goods.modifiers example:
   {
       "spice_level": {
           "label": "🌶 Spice Level",
           "type": "single",        # single choice
           "required": true,
           "options": [
               {"id": "mild", "label": "Mild", "price": 0},
               {"id": "medium", "label": "Medium", "price": 0},
               {"id": "hot", "label": "Hot 🔥", "price": 0},
               {"id": "thai_hot", "label": "Thai Hot 🔥🔥🔥", "price": 0}
           ]
       },
       "extras": {
           "label": "➕ Extras",
           "type": "multi",          # multiple choices
           "required": false,
           "options": [
               {"id": "extra_rice", "label": "Extra Rice", "price": 20},
               {"id": "egg", "label": "Fried Egg", "price": 15},
               {"id": "extra_meat", "label": "Extra Meat", "price": 40}
           ]
       },
       "removals": {
           "label": "❌ Remove",
           "type": "multi",
           "required": false,
           "options": [
               {"id": "no_onion", "label": "No Onion", "price": 0},
               {"id": "no_cilantro", "label": "No Cilantro", "price": 0},
               {"id": "no_peanut", "label": "No Peanuts", "price": 0}
           ]
       }
   }
   ```

2. **Selected Modifiers (stored on CartItem / OrderItem):**
   ```python
   # ShoppingCart.selected_modifiers / OrderItem.selected_modifiers example:
   {
       "spice_level": "thai_hot",
       "extras": ["extra_rice", "egg"],
       "removals": ["no_onion"]
   }
   ```

3. **Price Calculation:**
   ```python
   def calculate_item_price(goods, selected_modifiers):
       base_price = goods.price
       modifier_total = Decimal(0)
       for group_key, selection in selected_modifiers.items():
           group = goods.modifiers[group_key]
           if isinstance(selection, list):  # multi
               for opt_id in selection:
                   opt = next(o for o in group["options"] if o["id"] == opt_id)
                   modifier_total += Decimal(str(opt["price"]))
           else:  # single
               opt = next(o for o in group["options"] if o["id"] == selection)
               modifier_total += Decimal(str(opt["price"]))
       return base_price + modifier_total
   ```

4. **Category Sort Order:**
   ```python
   # Categories model addition
   sort_order = Column(Integer, default=0)
   # Admin sets: Starters=1, Mains=2, Drinks=3, Desserts=4
   # Query: order_by(Categories.sort_order)
   ```

**Effort:** Medium (1–2 days)

**Acceptance Criteria:**
- [ ] Products can have configurable modifiers (single/multi choice)
- [ ] Modifiers with price adjustments calculate correctly
- [ ] User selects modifiers when adding to cart
- [ ] Cart displays items with selected modifiers
- [ ] Order items store selected modifiers
- [ ] Admin can configure modifiers per product
- [ ] Categories have sort order for restaurant-style menu
- [ ] CLI shows modifier details in orders

**Test Plan:**
| Test File | Tests | What to Assert |
|-----------|-------|----------------|
| `tests/unit/database/test_models.py` | `test_goods_modifiers_json` | Goods stores/retrieves modifier schema JSON |
| | `test_order_item_selected_modifiers` | OrderItem stores selected modifier choices |
| | `test_cart_item_selected_modifiers` | ShoppingCart stores selected modifiers |
| | `test_categories_sort_order` | Categories have `sort_order` integer, default 0 |
| `tests/unit/utils/test_modifiers.py` | `test_calculate_item_price_no_modifiers` | Base price unchanged when no modifiers |
| | `test_calculate_item_price_single_choice` | Single-choice modifier with price adds correctly |
| | `test_calculate_item_price_multi_extras` | Multiple extras sum correctly |
| | `test_calculate_item_price_free_removals` | Removals with price=0 don't change total |
| | `test_calculate_item_price_combined` | Single + multi + removals all together |
| | `test_validate_modifier_selection_required` | Required modifier group raises error if missing |
| | `test_validate_modifier_selection_invalid_id` | Invalid option ID raises error |
| `tests/unit/database/test_cart.py` | `test_add_to_cart_with_modifiers` | Cart stores item + selected modifiers |
| | `test_cart_total_with_modifier_prices` | Cart total includes modifier price adjustments |
| `tests/integration/test_order_lifecycle.py` | `test_order_with_modifiers_flow` | Add item with modifiers → checkout → order items have correct modifiers + prices |

---

### Card 9: Kitchen & Delivery Status Workflow + Group Notifications — DONE

**Why:** Restaurant orders need real-time status updates: kitchen prep, ready for pickup, out for delivery. The current flow (pending→reserved→confirmed→delivered) doesn't distinguish kitchen and delivery stages. Kitchen staff and riders need separate Telegram group notifications.

**Scope:**
- Extended order statuses: `pending → reserved → confirmed → preparing → ready → out_for_delivery → delivered`
- Auto-forward new confirmed orders to kitchen Telegram group
- Notify rider group when order is ready
- Customer receives status updates at each stage
- Admin/kitchen/rider can update status via bot buttons

**Files to Modify:**
| File | Changes |
|------|---------|
| `bot/database/models/main.py` | Extend `order_status` allowed values. Add `kitchen_group_message_id` and `rider_group_message_id` to `Order` for tracking forwarded messages. |
| `bot/config/env.py` | Add `KITCHEN_GROUP_ID`, `RIDER_GROUP_ID` env vars |
| `bot/handlers/admin/main.py` | Add status transition buttons per current state. Kitchen: "🍳 Preparing" → "✅ Ready". Rider: "🛵 Out for Delivery" → "📸 Delivered". |
| `bot/payments/notifications.py` | Add `notify_kitchen_group()`, `notify_rider_group()`, `notify_customer_status_update()`. Format order details for each audience (kitchen sees items+modifiers, rider sees address+GPS). |
| `bot_cli.py` | Add `--status-preparing`, `--status-ready`, `--status-out-for-delivery` flags to order command |
| `bot/keyboards/inline.py` | Status transition buttons for kitchen/rider groups |
| `bot/i18n/strings.py` | Status labels in Thai/English |
| `bot/tasks/reservation_cleaner.py` | Update expired check to handle new statuses (only expire `reserved` orders, not `preparing`/`ready`) |

**Implementation Details:**

1. **Extended Status Flow:**
   ```
   pending → reserved → confirmed → preparing → ready → out_for_delivery → delivered
                      ↘ cancelled                                        ↘ cancelled
                      ↘ expired
   ```

2. **Group Notification Flow:**
   ```
   Order Confirmed (admin verifies payment)
     → Forward to Kitchen Group: "🆕 Order ABCDEF\n🍜 Pad Thai (hot, no onion) x2\n🍚 Fried Rice x1"
     → Kitchen clicks "🍳 Start Preparing"
     → Customer notified: "Your order is being prepared! 🍳"

   Kitchen clicks "✅ Ready"
     → Forward to Rider Group: "📦 Order ABCDEF READY\n📍 [Google Maps Link]\n🚪 Door delivery\n📞 0812345678"
     → Customer notified: "Your order is ready and waiting for pickup! 📦"

   Rider clicks "🛵 Picked Up"
     → Customer notified: "Your order is on the way! 🛵"

   Rider uploads delivery photo
     → Auto-delivered (Card 4 flow)
     → Customer notified with photo: "Delivered! ✅"
   ```

3. **Kitchen Group Message Format:**
   ```
   🆕 New Order: ABCDEF
   ⏰ 14:30

   1x Pad Thai 🌶🌶🌶 (no onion)
   2x Fried Rice + Egg
   1x Thai Iced Tea

   📝 Note: Extra spicy please

   [🍳 Start Preparing]
   ```

4. **Rider Group Message Format:**
   ```
   📦 Order ABCDEF — READY FOR PICKUP

   🚪 Door Delivery
   📍 Google Maps: [link]
   📞 081-234-5678
   📝 Gate code: 1234, building B

   💰 COD: ฿450

   [🛵 Mark Picked Up]
   ```

5. **Config:**
   ```env
   KITCHEN_GROUP_ID=-1001234567890    # Telegram group for kitchen staff
   RIDER_GROUP_ID=-1001234567891      # Telegram group for riders
   ```

**Effort:** Medium (1–2 days)

**Acceptance Criteria:**
- [ ] Order flows through all extended statuses
- [ ] Kitchen group receives formatted order on confirmation
- [ ] Rider group notified when order is ready
- [ ] Customer receives status updates at each stage
- [ ] Kitchen can mark "preparing" and "ready" via buttons
- [ ] Rider can mark "picked up" via button
- [ ] CLI supports all new status transitions
- [ ] Reservation cleaner only expires `reserved` orders

**Test Plan:**
| Test File | Tests | What to Assert |
|-----------|-------|----------------|
| `tests/unit/database/test_models.py` | `test_order_extended_statuses` | All statuses valid: pending, reserved, confirmed, preparing, ready, out_for_delivery, delivered, cancelled, expired |
| | `test_order_group_message_ids` | `kitchen_group_message_id`, `rider_group_message_id` nullable |
| `tests/unit/database/test_crud.py` | `test_update_order_status_preparing` | confirmed → preparing transition works |
| | `test_update_order_status_ready` | preparing → ready transition works |
| | `test_update_order_status_out_for_delivery` | ready → out_for_delivery transition works |
| | `test_invalid_status_transition` | Cannot skip statuses (e.g., confirmed → delivered directly) |
| `tests/unit/notifications/test_group_notifications.py` | `test_format_kitchen_message` | Kitchen message contains items, modifiers, order code |
| | `test_format_rider_message` | Rider message contains address, GPS link, phone, COD amount |
| `tests/integration/test_order_lifecycle.py` | `test_full_kitchen_to_delivery_flow` | confirmed → preparing → ready → out_for_delivery → delivered |
| | `test_reservation_cleaner_ignores_preparing` | Only `reserved` orders get expired, not `preparing`/`ready` |

---

### Card 10: Delivery Time Slots + Bangkok Zone Pricing — DONE

**Why:** Bangkok traffic makes delivery timing critical. Peak hours (11:30–13:00, 17:30–19:30) need longer slots. Different zones (Sukhumvit, Silom, outskirts) have different delivery fees. This is standard for Thai delivery apps.

**Scope:**
- Configurable delivery time slots
- User selects preferred delivery slot at checkout
- Zone-based delivery fee calculation
- Admin configures zones and fees via CLI

**Files to Create:**
| File | Purpose |
|------|---------|
| `bot/config/delivery_zones.py` | Zone definitions, fee calculation, time slot management |

**Files to Modify:**
| File | Changes |
|------|---------|
| `bot/database/models/main.py` | Add `delivery_zone` (String), `delivery_fee` (Numeric), `preferred_time_slot` (String) to `Order`. Add `DeliveryZone` model (name, fee, boundaries). Add `TimeSlot` to `BotSettings` or separate config. |
| `bot/config/env.py` | Add `DELIVERY_ZONES_ENABLED`, `TIME_SLOTS_ENABLED` feature flags |
| `bot/handlers/user/order_handler.py` | After address/location: auto-detect zone from GPS coordinates (simple polygon check or distance). Show time slot picker. Add delivery fee to order total. |
| `bot/keyboards/inline.py` | Time slot selection buttons, zone display |
| `bot_cli.py` | Add zone management commands: `zone add/edit/remove`. Time slot configuration. |
| `bot/i18n/strings.py` | Time slot and zone strings |

**Implementation Details:**

1. **Time Slot System:**
   ```python
   DEFAULT_TIME_SLOTS = [
       {"id": "lunch_early", "label": "11:00–12:00", "available": True},
       {"id": "lunch_peak",  "label": "12:00–13:00", "available": True},
       {"id": "lunch_late",  "label": "13:00–14:00", "available": True},
       {"id": "afternoon",   "label": "14:00–17:00", "available": True},
       {"id": "dinner_early","label": "17:00–18:30", "available": True},
       {"id": "dinner_peak", "label": "18:30–20:00", "available": True},
       {"id": "dinner_late", "label": "20:00–21:30", "available": True},
       {"id": "asap",        "label": "🔥 ASAP",     "available": True},
   ]
   ```

2. **Zone Pricing (simple distance-based):**
   ```python
   DELIVERY_ZONES = [
       {"name": "Zone 1 - Central", "max_km": 3, "fee": 0},      # Free delivery nearby
       {"name": "Zone 2 - Inner",   "max_km": 7, "fee": 30},     # ฿30
       {"name": "Zone 3 - Mid",     "max_km": 12, "fee": 50},    # ฿50
       {"name": "Zone 4 - Outer",   "max_km": 20, "fee": 80},    # ฿80
       {"name": "Zone 5 - Far",     "max_km": 99, "fee": 120},   # ฿120
   ]
   ```

3. **Zone Detection (from GPS):**
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
       return DELIVERY_ZONES[-1]  # Furthest zone
   ```

4. **Checkout Flow Addition:**
   ```
   ... → Location → Delivery Type → [Time Slot Selection] → [Zone + Fee Display] → Phone → Payment
   ```

**Model Changes:**
```python
# Add to Order
delivery_zone = Column(String(50), nullable=True)
delivery_fee = Column(Numeric(12, 2), default=0)
preferred_time_slot = Column(String(50), nullable=True)

# New model (or store in BotSettings as JSON)
class DeliveryZone(Base):
    __tablename__ = "delivery_zones"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    max_distance_km = Column(Float, nullable=False)
    fee = Column(Numeric(12, 2), default=0)
    is_active = Column(Boolean, default=True)
```

**Effort:** Low-Medium (1 day)

**Acceptance Criteria:**
- [ ] Time slots configurable and displayed at checkout
- [ ] Zone auto-detected from GPS coordinates
- [ ] Delivery fee calculated and added to order total
- [ ] User sees zone + fee before confirming order
- [ ] Admin can manage zones via CLI
- [ ] Time slots can be enabled/disabled
- [ ] Order stores selected slot and zone

**Test Plan:**
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

---

### Card 11: Cash on Delivery — Thai Localization — DONE

**Why:** COD already exists in the repo. This card just relocalizes it for Thailand (Thai labels, rider cash collection flow).

**Scope:**
- Rename COD labels to Thai
- Add "waiting for cash" status indicator
- Rider confirms cash collected before marking delivered

**Files to Modify:**
| File | Changes |
|------|---------|
| `bot/i18n/strings.py` | Add Thai COD strings: `"💵 เก็บเงินปลายทาง"` (Cash on Delivery), `"รอเก็บเงิน"` (Waiting for Cash) |
| `bot/handlers/user/order_handler.py` | Update COD payment method label to Thai |
| `bot/payments/notifications.py` | Rider notification includes COD amount: `"💰 เก็บเงิน ฿450"` |
| `bot_cli.py` | Show COD indicator in order details |

**Implementation Details:**
- Minimal changes — COD flow already works
- Main addition: rider sees cash amount prominently in their notification
- Cash amount = order total + delivery fee (from Card 10)

**Effort:** Very Low (1–2 hours)

**Acceptance Criteria:**
- [ ] COD labels in Thai
- [ ] Rider notification shows cash amount to collect
- [ ] COD includes delivery fee in total

**Test Plan:**
| Test File | Tests | What to Assert |
|-----------|-------|----------------|
| `tests/unit/i18n/test_strings.py` | `test_cod_thai_label` | COD string key returns `"💵 เก็บเงินปลายทาง"` in th locale |
| `tests/unit/notifications/test_group_notifications.py` | `test_rider_cod_amount_includes_delivery_fee` | COD amount = order total + delivery fee |

---

### Card 12: Timezone + Background Tasks (ICT +07) — DONE

**Why:** Thailand is UTC+7 (ICT). All timestamps, reservation expiry, time slots, and scheduled tasks must use Bangkok time. The repo has timezone support but defaults to UTC.

**Scope:**
- Set default timezone to Asia/Bangkok
- Verify all timestamp operations use configured timezone
- Ensure reservation_cleaner respects timezone

**Files to Modify:**
| File | Changes |
|------|---------|
| `bot/config/timezone.py` | Set default to `"Asia/Bangkok"` |
| `.env.example` | Update timezone example |
| `bot/tasks/reservation_cleaner.py` | Verify timezone-aware datetime comparisons |
| `bot_cli.py` | Ensure CLI time displays in Bangkok time |
| `bot/database/models/main.py` | Verify all `DateTime` columns use timezone-aware defaults |

**Implementation Details:**

1. **Config Change:**
   ```python
   # bot/config/timezone.py
   DEFAULT_TIMEZONE = "Asia/Bangkok"
   ```

2. **Verification Checklist:**
   - `Order.created_at` — uses timezone-aware `func.now()`?
   - `Order.reserved_until` — calculated with correct TZ?
   - `reservation_cleaner.py` — compares with TZ-aware `now()`?
   - CLI time displays — formatted in Bangkok time?
   - Time slot labels (Card 10) — match Bangkok time?

**Effort:** Very Low (1–2 hours)

**Acceptance Criteria:**
- [ ] Default timezone is Asia/Bangkok
- [ ] All displayed times in ICT (+07)
- [ ] Reservation expiry works correctly in Bangkok timezone
- [ ] CLI shows Bangkok time
- [ ] No UTC/ICT mismatch bugs

**Test Plan:**
| Test File | Tests | What to Assert |
|-----------|-------|----------------|
| `tests/unit/config/test_timezone.py` | `test_default_timezone_bangkok` | Default is `"Asia/Bangkok"` |
| | `test_timezone_aware_now` | `get_now()` returns UTC+7 aware datetime |
| | `test_reservation_expiry_timezone` | `reserved_until` calculated in correct TZ |
| `tests/unit/tasks/test_reservation_cleaner.py` | `test_cleaner_uses_timezone_aware_comparison` | Expired check uses TZ-aware now(), not naive UTC |
| | `test_cleaner_does_not_expire_future_orders` | Order with `reserved_until` in future (ICT) not expired |

---

## Implementation Roadmap

### Week 1: Core Thailand Experience (Phase 1)
| Day | Cards | Focus |
|-----|-------|-------|
| Day 1 | Card 12, Card 6 | Timezone + Currency (quick wins, foundational) |
| Day 2 | Card 2, Card 3 | GPS Location + Dead Drop (low effort, high impact) |
| Day 3–4 | Card 1 | PromptPay QR Payment (most complex) |
| Day 5 | Card 4 | Photo Proof of Delivery |

### Week 2: Localization + Restaurant Flow (Phase 2–3)
| Day | Cards | Focus |
|-----|-------|-------|
| Day 6 | Card 5, Card 7, Card 11 | Thai Language + Address Format + COD labels |
| Day 7–8 | Card 8 | Menu Modifiers + Category Ordering |
| Day 9–10 | Card 9 | Kitchen & Delivery Workflow + Group Notifications |

### Week 3: Polish
| Day | Cards | Focus |
|-----|-------|-------|
| Day 11 | Card 10 | Delivery Time Slots + Zone Pricing |
| Day 12–14 | All | Integration testing, edge cases, Thai UX review |

---

## Database Migration Summary

All model changes in one view (apply together or incrementally):

```python
# Order model additions
payment_receipt_photo = Column(String(255), nullable=True)
payment_verified_by = Column(BigInteger, nullable=True)
payment_verified_at = Column(DateTime, nullable=True)
latitude = Column(Float, nullable=True)
longitude = Column(Float, nullable=True)
google_maps_link = Column(String(255), nullable=True)
delivery_type = Column(String(20), default="door")
drop_location_photo = Column(String(255), nullable=True)
drop_instructions = Column(Text, nullable=True)
delivery_photo = Column(String(255), nullable=True)
delivery_photo_at = Column(DateTime, nullable=True)
delivery_photo_by = Column(BigInteger, nullable=True)
delivery_zone = Column(String(50), nullable=True)
delivery_fee = Column(Numeric(12, 2), default=0)
preferred_time_slot = Column(String(50), nullable=True)
address_structured = Column(JSON, nullable=True)

# CustomerInfo model additions
latitude = Column(Float, nullable=True)
longitude = Column(Float, nullable=True)
address_structured = Column(JSON, nullable=True)

# Goods model additions
modifiers = Column(JSON, nullable=True)

# ShoppingCart model additions
selected_modifiers = Column(JSON, nullable=True)

# OrderItem model additions
selected_modifiers = Column(JSON, nullable=True)

# Categories model additions
sort_order = Column(Integer, default=0)

# New model: DeliveryZone
```

---

## New Dependencies

```
promptpay>=1.1
qrcode[pil]>=7.4
Pillow>=10.0
```

---

## New Environment Variables

```env
# PromptPay (Card 1)
PROMPTPAY_ID=0812345678
PROMPTPAY_ACCOUNT_NAME=Restaurant Name

# Groups (Card 9)
KITCHEN_GROUP_ID=-1001234567890
RIDER_GROUP_ID=-1001234567891

# Restaurant Location (Card 10)
RESTAURANT_LAT=13.7563
RESTAURANT_LNG=100.5018

# Feature Flags
DELIVERY_ZONES_ENABLED=true
TIME_SLOTS_ENABLED=true

# Timezone (Card 12)
TIMEZONE=Asia/Bangkok

# Currency (Card 6)
PAY_CURRENCY=THB

# Locale (Card 5)
BOT_LOCALE=th
```

---

## Files Created (New)

| File | Card | Purpose |
|------|------|---------|
| `bot/payments/promptpay.py` | 1 | PromptPay QR generation |
| `bot/handlers/user/payment_promptpay_handler.py` | 1 | Receipt upload flow |
| `bot/config/delivery_zones.py` | 10 | Zone definitions + time slots |

## Files Modified (Existing)

| File | Cards | Changes |
|------|-------|---------|
| `bot/database/models/main.py` | 1,2,3,4,7,8,9,10 | All model additions |
| `bot/handlers/user/order_handler.py` | 1,2,3,7,10 | Checkout flow expansion |
| `bot/handlers/user/cart_handler.py` | 6,8 | THB formatting, modifiers display |
| `bot/handlers/user/shop_and_goods.py` | 6,8 | THB prices, modifiers, category sort |
| `bot/handlers/admin/main.py` | 1,4,9 | Payment verify, delivery photo, status buttons |
| `bot/config/env.py` | 1,5,6,9,10,12 | New env vars |
| `bot/states/user_state.py` | 2,3,4 | New FSM states |
| `bot/keyboards/inline.py` | 1,2,3,4,8,9,10 | All new buttons |
| `bot/i18n/strings.py` | 1–12 | All translations |
| `bot/payments/notifications.py` | 1,2,3,4,9,11 | All notification changes |
| `bot_cli.py` | 1,2,3,4,8,9,10,11,12 | CLI commands for all features |
| `bot/tasks/reservation_cleaner.py` | 9,12 | New statuses, timezone |
| `requirements.txt` | 1 | New dependencies |
| `.env.example` | 1,6,9,10,12 | New env var examples |

---

## Backlog Detail

### Card 21: Persistent Cart Stub + Brand/Store Switch Guards — 0%

> See full card: [`docs/CARD-21-persistent-cart-stub.md`](docs/CARD-21-persistent-cart-stub.md)

**Phase:** UX Polish | **Priority:** High (next up) | **Effort:** Medium (3–5 days)

**Summary:** Adds a single-line cart banner (`🛒 Brand · Store · ฿Total`) on every menu refresh, flash animation on add-to-cart, brand-switch save/delete/stay prompt with new `SavedCart` model, same-brand store switch with availability check, and `ShoppingCart.expires_at` TTL (default 2h) with lazy cleanup. Prereq for smoother multi-brand UX in CARD-19.

### Card 19: Multi-Brand / Multi-Store Telegram Bot Coordination Platform — 15% (DB models only)

> See full card: [`docs/CARD-19-multi-brand-bot-coordination.md`](docs/CARD-19-multi-brand-bot-coordination.md)

**Phase:** 3 — Platform Scale | **Priority:** High | **Effort:** Very High (10–14 days)

**Summary:** One backend process manages N independent Telegram bots, each representing a brand. Adds `BotConfig` model, `BotPool` multi-bot runtime, `BrandContextMiddleware` for automatic brand context injection, store selector UI, brand-scoped queries, per-brand rate limiting, encrypted token storage, and CLI-based bot management. Backward-compatible: single-bot deployments work unchanged with `MULTI_BOT_ENABLED=false`.

### Card 17: Grok AI Admin Assistant — 0%

> See full card: [`docs/CARD-17-grok-admin-assistant.md`](docs/CARD-17-grok-admin-assistant.md)

**Phase:** 5 — Admin Intelligence | **Priority:** Medium | **Effort:** High (5–7 days)

**Summary:** Natural-language admin interface powered by Grok (xAI). Pydantic schemas constrain AI output to validated, structured actions (price updates, bulk menu edits, order lookups, data import). Admins describe intent in plain language instead of navigating rigid button UIs.

### Card 16: Parallel Line Messaging API Integration — 0%

> See full card: [`docs/CARD-16-line-api-integration.md`](docs/CARD-16-line-api-integration.md)

**Phase:** 5 — Multi-Platform | **Priority:** Medium-High | **Effort:** High (5–8 days)

**Summary:** Add Line (53M Thai users) as a parallel messaging channel alongside Telegram. Requires transport-layer abstraction across handlers, keyboards, and message_utils — currently tightly coupled to aiogram. Shared business logic, database, and admin tools. Defer until CARD-19 brand context is stable.

---

## Restaurant Core Cards

# Feature Cards - Prioritized Implementation — ALL DONE

> All cards below (RC1–RC7, FC1–FC9) are fully implemented and verified in the codebase.

> See [MENU-SYSTEM.md](MENU-SYSTEM.md) for complete menu schema, modifier format, media handling, import/export, and multi-currency docs.

## P0 - Restaurant Core (Menu Optimization) — DONE

### CARD-RC1: Multi-Media Menu Items
- **Status**: IMPLEMENTED
- **Files**: `bot/database/models/main.py` (Goods.image_file_id, Goods.media), `bot/handlers/user/shop_and_goods.py`, `bot/handlers/admin/adding_position_states.py`
- **What**: Items support a primary display photo + gallery of multiple photos/videos. Item detail shows photo via `answer_photo()`. Gallery button sends MediaGroup.
- **Admin Flow**: During item creation, send photos/videos one at a time -> first becomes primary -> all stored in media JSON array

### CARD-RC2: Prep Time + Kitchen Prep Tracking
- **Status**: IMPLEMENTED
- **Files**: `bot/database/models/main.py` (Goods.prep_time_minutes, Order.estimated_ready_at), `bot/handlers/admin/order_management.py`
- **What**: Each item has a prep time in minutes. Kitchen notifications show total prep time and estimated ready time. Orders track `estimated_ready_at`.
- **Calculation**: `max(item.prep_time * quantity)` across all order items (parallel kitchen work)

### CARD-RC3: Allergen Management
- **Status**: IMPLEMENTED
- **Files**: `bot/database/models/main.py` (Goods.allergens), `bot/handlers/admin/adding_position_states.py`
- **What**: 8 standard allergens (gluten, dairy, eggs, nuts, shellfish, soy, fish, sesame) as toggleable buttons during item creation. Shown on item detail page.
- **Storage**: Comma-separated string: `"gluten,dairy,nuts"`

### CARD-RC4: Availability Windows + Daily Limits
- **Status**: IMPLEMENTED
- **Files**: `bot/database/models/main.py`, `bot/database/methods/create.py` (add_to_cart), `bot/tasks/reservation_cleaner.py`
- **What**: Items and categories can have time windows (breakfast 06:00-11:00). Items can have daily kitchen limits. `sold_out_today` flag for instant 86-ing.
- **Daily reset**: Midnight scheduler resets `daily_sold_count` and `sold_out_today`

### CARD-RC5: Multi-Currency
- **Status**: IMPLEMENTED
- **Files**: `bot/handlers/admin/settings_management.py`, `bot/keyboards/inline.py`
- **What**: Admin can select from 13 currencies (THB default). Stored in `bot_settings` table.
- **Currencies**: THB, USD, EUR, GBP, JPY, RUB, AED, SAR, IRR, AFN, MYR, SGD, BTC

### CARD-RC6: Menu Import/Export
- **Status**: IMPLEMENTED
- **Files**: `bot/utils/menu_io.py`
- **What**: Export entire menu as JSON + images folder. Import into another store. Validates structure, handles image upload/download via Telegram API.
- **Modes**: merge (add/update) or replace (wipe and reimport)

### CARD-RC7: Interactive Modifier Builder
- **Status**: IMPLEMENTED
- **Files**: `bot/handlers/admin/adding_position_states.py`
- **What**: Step-by-step modifier group creation instead of raw JSON paste. Group name -> type (single/multi) -> required? -> options (label + price). Power users can still paste raw JSON.

---

## P0 - Critical User Experience — DONE

### CARD-FC1: Product Search
- **Status**: IMPLEMENTED
- **Files**: `bot/handlers/user/search_handler.py`
- **What**: Text search for products by name and description (ILIKE query)
- **User Flow**: Main menu -> Search -> Enter keywords -> See results -> Tap to view item
- **Integration**: Results link to existing item detail handler (`item_{name}_{category}_goods-page_...`)

### CARD-FC2: Reorder Button
- **Status**: IMPLEMENTED
- **Files**: `bot/handlers/user/orders_view_handler.py` (reorder_handler)
- **What**: One-tap reorder from order history - copies all items from a delivered order into cart
- **User Flow**: My Orders -> View Order -> Reorder -> Items added to cart
- **Handles**: Out-of-stock items skipped with notification

---

## P1 - Revenue & Trust — DONE

### CARD-FC3: Coupon / Promo Codes
- **Status**: IMPLEMENTED
- **Files**:
  - Model: `bot/database/models/main.py` (Coupon, CouponUsage)
  - Admin: `bot/handlers/admin/coupon_management.py`
  - Utils: `bot/utils/coupon_utils.py`
- **What**: Full coupon system with percent/fixed discounts, min order, max uses, per-user limits, expiry
- **Admin Flow**: Console -> Coupons -> Create (code/auto, type, value, min order, max uses, expiry)
- **User Flow**: During checkout, enter coupon code -> validate -> apply discount to order
- **Validation**: Active, not expired, not over-used, min order met, per-user limit

### CARD-FC4: Review / Rating System
- **Status**: IMPLEMENTED
- **Files**:
  - Model: `bot/database/models/main.py` (Review)
  - Handler: `bot/handlers/user/review_handler.py`
- **What**: 1-5 star ratings with optional comments, post-delivery
- **User Flow**: Order delivered -> "Leave Review" button -> Select 1-5 stars -> Optional comment
- **Constraints**: One review per order per user (UniqueConstraint)
- **Product View**: Average rating shown on product cards via `get_item_rating()`

---

## P2 - Professional Operations — DONE

### CARD-FC5: Invoice / Receipt Generation
- **Status**: IMPLEMENTED
- **Files**: `bot/utils/invoice.py`
- **What**: Text-based receipt with itemized breakdown, fees, discounts, totals
- **User Flow**: View Order -> Receipt button -> Formatted receipt in `<pre>` block
- **Includes**: Items, subtotal, delivery fee, coupon discount, bonus, total, delivery info

### CARD-FC6: Support Ticketing
- **Status**: IMPLEMENTED
- **Files**:
  - Models: `bot/database/models/main.py` (SupportTicket, TicketMessage)
  - User: `bot/handlers/user/ticket_handler.py`
  - Admin: `bot/handlers/admin/ticket_management.py`
- **What**: Full ticket lifecycle with IDs, status tracking, message history
- **User Flow**: Support -> New Ticket -> Subject -> Description -> Ticket #ABC12345 created
- **Admin Flow**: Console -> Tickets -> View -> Reply -> Resolve (notifies user)
- **Statuses**: open -> in_progress -> resolved -> closed
- **Priorities**: low, normal, high, urgent
- **Features**: Link ticket to order, user/admin replies, close ticket

### CARD-FC7: Accounting / Revenue Export
- **Status**: IMPLEMENTED
- **Files**:
  - Export: `bot/export/sales_report.py`
  - Admin: `bot/handlers/admin/accounting_handler.py`
- **What**: Sales reports, revenue by product, payment reconciliation
- **Admin Flow**: Console -> Accounting -> Summary (today/week/month/all) or Export CSV
- **Reports**:
  - Revenue summary: total, orders, avg, by payment method, top 5 products
  - Sales CSV: order code, date, items, total, payment, delivery fee, discounts
  - Revenue by product CSV: product, category, units sold, revenue, avg price
  - Payment reconciliation CSV: method, count, total, avg value

---

## P3 - Growth & Scale — DONE

### CARD-FC8: Customer Segmentation
- **Status**: IMPLEMENTED
- **Files**: `bot/handlers/admin/segmented_broadcast.py`
- **What**: Targeted broadcasts to customer segments instead of all users
- **Admin Flow**: Console -> Targeted Broadcast -> Select segment -> Type message -> Send
- **Segments**:
  - High Spenders: total_spendings >= 2x average
  - Recent Buyers: ordered in last 7 days
  - Inactive Users: no order in 30+ days
  - New Users: registered in last 7 days
- **Integration**: Uses existing BroadcastManager for batch sending

### CARD-FC9: Multi-Store / Multi-Location
- **Status**: IMPLEMENTED
- **Files**:
  - Model: `bot/database/models/main.py` (Store)
  - Admin: `bot/handlers/admin/store_management.py`
  - Order: `bot/database/models/main.py` (Order.store_id)
- **What**: Multiple store/branch locations with GPS, active/inactive toggle, default store
- **Admin Flow**: Console -> Stores -> Add (name, address, GPS) / Toggle / Set Default
- **Order Integration**: Order.store_id FK to stores table for per-order store assignment
- **Features**: Store list, detail view, activate/deactivate, set default, GPS location

---

## Database Schema Additions

| Model | Table | Key Fields |
|-------|-------|------------|
| Coupon | coupons | code, discount_type, discount_value, min_order, max_discount, valid_until, max_uses |
| CouponUsage | coupon_usages | coupon_id, user_id, order_id, discount_applied |
| Review | reviews | order_id, user_id, item_name, rating (1-5), comment |
| SupportTicket | support_tickets | ticket_code, user_id, subject, status, priority, order_id |
| TicketMessage | ticket_messages | ticket_id, sender_id, sender_role, message_text |
| Store | stores | name, address, latitude, longitude, is_active, is_default |

Order model additions: `coupon_code`, `coupon_discount`, `store_id`
