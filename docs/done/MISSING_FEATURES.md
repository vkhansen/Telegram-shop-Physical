# Missing Features, Bugs & Test Gaps

---

## CONFIRMED BUGS — ALL FIXED

### Slip Verify KeyError [CRITICAL] — FIXED 2026-03-23
- `bot/payments/slip_verify.py:126` — `slip_data["amount"]` changed to `.get("amount")`
- Lines 128-130: nested `.get("bank", {})` changed to `(x.get("bank") or {})` for null safety

### Unchecked None on User Lookup [HIGH] — FIXED 2026-03-23
- `bot/handlers/admin/shop_management_states.py:252` — added `if not user: return` guard
- `bot/handlers/admin/user_management_states.py:566,620` — added null guards on `get_role_id_by_name()` return

### Missing Permission Checks on Admin FSM Handlers [HIGH/SECURITY] — FIXED 2026-03-23
- `bot/handlers/admin/broadcast.py:36` — added `HasPermissionFilter(permission=Permission.BROADCAST)`
- `bot/handlers/admin/segmented_broadcast.py:139` — added `HasPermissionFilter(permission=Permission.BROADCAST)`
- `bot/handlers/admin/ticket_management.py:148` — added `HasPermissionFilter(permission=Permission.USERS_MANAGE)`
- `bot/handlers/admin/grok_assistant.py:105-107,123` — added `HasPermissionFilter(permission=16)` (SHOP_MANAGE)

### Localize Missing Kwargs [HIGH] — FIXED 2026-03-23
- `bot/handlers/user/ticket_handler.py:429,532` — `ticket_code=` changed to `code=` matching `{code}` placeholder
- `bot/handlers/user/review_handler.py:141` — added `rating=rating` for `{rating}` placeholder
- `bot/handlers/admin/accounting_handler.py:102` — rewrote to pass all 7 kwargs (period, total, currency, orders, avg, payments, products)
- `bot/handlers/user/search_handler.py:74` — added `query=query` for `{query}` placeholder

### Delivery Note Log Wrong Variable [LOW] — FIXED 2026-03-23
- `bot/handlers/user/order_handler.py:812` — changed `delivery_address` to `delivery_note`

### Telegram ID Validation Too Strict [LOW] — FIXED 2026-03-23
- `bot/utils/validators.py:81` — upper bound raised from 9999999999 to 99999999999 (11 digits)

### check_value Bug [FIXED 2026-03-23]
- `bot/database/methods/read.py:check_value()` always returned `False`
- Fixed to return `True` for prepared items with zero stock (unlimited)

### Locale Middleware [FIXED 2026-03-23]
- Created `bot/middleware/locale.py` — user's saved language now applied on every request

### Rate Limiter max([]) — NOT A BUG
- `bot/middleware/rate_limit.py:64,77` — `not reqs or now - max(reqs)` short-circuits safely; `max()` never called on empty list

---

## MISSING FEATURES (NOT YET IMPLEMENTED)

### Phone Number Validation [HIGH]
- No country code validation — accepts any 8-20 char string of digits/symbols
- No Thai number format check (should accept `0812345678` or `+66812345678`)
- No auto-prepend of `+66` for local Thai numbers
- No E.164 normalization before storage
- No phone validator in `bot/utils/validators.py`
- Validation is a loose inline regex in `bot/handlers/user/order_handler.py:494`

### Grok AI Vision [MEDIUM]
- Photo analysis not implemented — returns placeholder text
- Location: `bot/ai/data_parser.py:20`

### Thai Structured Address [LOW]
- DB model `address_structured` (JSON) exists on Order and CustomerInfo
- Not fully utilized in checkout flow

### Error Handling [MEDIUM]
- 23+ instances of bare `except Exception: pass` in user handlers
- Payment processing has overly broad exception catches

---

## TEST COVERAGE GAPS

### Handler Tests — ZERO Coverage (36 files, ~12,000 lines)

**User handlers (0% tested):**
- `order_handler.py` (1,904 lines) — most critical file, zero unit tests
- `cart_handler.py` (459 lines)
- `delivery_chat_handler.py` (727 lines)
- `shop_and_goods.py` (531 lines)
- `orders_view_handler.py` (426 lines)
- `referral_system.py` (309 lines)
- `review_handler.py` (261 lines)
- `ticket_handler.py` (558 lines)
- `search_handler.py` (77 lines)
- `store_selection.py` (174 lines)
- `reference_code_handler.py` (227 lines)

**Admin handlers (0% tested):**
- `order_management.py` — confirm/prepare/ready/dispatch/deliver
- `coupon_management.py` — coupon CRUD
- `goods_management_states.py` — item CRUD
- `user_management_states.py` — ban/unban/promote
- `broadcast.py`, `segmented_broadcast.py`
- `accounting_handler.py`
- `settings_management.py`
- `store_management.py`
- `ticket_management.py`

### Middleware — ZERO Tests
- `rate_limit.py` — rate limiting logic
- `security.py` — blocking, CSRF, suspicious patterns
- `locale.py` — per-request locale

### Missing E2E Scenarios

**Banned user flows:**
- Banned user trying to browse / add to cart / checkout / place order

**Payment failures:**
- Cash order timeout (24h with no payment)
- Bitcoin address never receives payment
- PromptPay receipt rejected by admin
- Double payment submission
- Concurrent payments from same user

**Inventory edge cases:**
- Item goes out of stock during checkout
- Item removed from menu while in cart
- Item price changes while in cart
- Reservation expires (24h timeout) — inventory release
- Concurrent reservations for last item in stock

**Order edge cases:**
- Same user places multiple concurrent orders
- Order with all items from different brands
- Order at delivery zone boundary (exact edge of zone)
- Order outside service area

**Coupon system (ZERO tests):**
- Apply coupon to order
- Expired coupon rejected
- Exhausted coupon (max uses hit)
- Coupon + referral bonus stacking
- Concurrent coupon usage

**Support ticket system (ZERO tests):**
- Create / assign / respond / resolve / close

**Review system (ZERO tests):**
- Post review after delivery
- Rating constraint enforcement (1-5)

**Search (ZERO tests):**
- SQL wildcard injection (%, _) — code escapes but no test
- Empty query handling
- Case sensitivity
- No results case

**Delivery:**
- Dead drop photo proof requirement
- Live location tracking updates
- Driver-customer chat window timing
- Post-delivery chat window expiry

**Referral:**
- Multi-level referral chains
- Circular referral prevention
- Bonus calculation accuracy
- Bonus depletion across orders

### Current Coverage Summary

| Area | Files | Coverage | Priority |
|------|-------|----------|----------|
| Database CRUD | 12 files | ~70% | OK |
| Payments | 3 files | ~60% | Needs work |
| Utilities | 14 files | ~80% | OK |
| E2E scenarios | 3 files | ~40% | Needs expansion |
| Handlers | 0 files | **0%** | **CRITICAL** |
| Middleware | 0 files | **0%** | **HIGH** |
| Coupons | 0 files | **0%** | HIGH |
| Tickets | 0 files | **0%** | MEDIUM |
| Reviews | 0 files | **0%** | MEDIUM |
| Overall | 41 files | **~45%** | — |
