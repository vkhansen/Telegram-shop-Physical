# DRY & Bug Audit Report

**Date:** 2026-03-25
**Scope:** Full codebase scan of `bot/` — handlers, payments, utils, tasks, database, config
**Method:** Automated deep-read of 40+ Python files with line-level analysis

---

## Part 1: Bugs Found

### CRITICAL (will cause crashes or data corruption)

| # | File | Line(s) | Bug | Fix |
|---|------|---------|-----|-----|
| B1 | `database/methods/inventory.py` | 73-76, 152, 229, 314 | **Session context-manager misuse** — when `session is None`, code assigns `Database().session()` (a context manager) to `session` but never enters it with `with`. `__exit__` is never called → resource leaks, uncommitted transactions. | Wrap body in `with Database().session() as session:` when no external session provided. |
| B2 | `handlers/user/order_handler.py` | 721 | **KeyError on unknown payment method** — `PAYMENT_PROCESSORS[method]` crashes if method string not in dict (e.g. malformed callback data). | Use `.get(method)` with fallback error message. |

### HIGH (security, correctness, data integrity)

| # | File | Line(s) | Bug | Fix |
|---|------|---------|-----|-----|
| B3 | `handlers/admin/order_management.py` | 275-376 | **Race condition in order status transitions** — query → check → update → commit is not atomic. Two admins can change status simultaneously, skipping states. | Use `SELECT FOR UPDATE` row lock or optimistic locking with version column. |
| B4 | `handlers/user/order_handler.py` | 569, 614, 651, 787 | **Float ↔ Decimal precision loss** — bonus_applied stored as `float()` in FSM state, later converted back via `Decimal(str(...))`. Floating-point representation can lose precision on round-trip for amounts like ฿33.33. | Store as `str(bonus_amount)` in state, parse with `Decimal()`. |
| B5 | `payments/verifiers/btc.py` | 59 | **Unguarded `int()` parse** — `int(tip_resp.text.strip())` on block height response. If API returns non-numeric text, `ValueError` propagates and crashes the payment checker loop iteration. | Wrap in try/except, return `TxResult(found=False)`. |
| B6 | `payments/price_feed.py` | 56 | **Division by zero** — `fiat_amount / price_in_fiat` if CoinGecko returns price=0 (outage scenario). | Add `if price_in_fiat <= 0: raise ValueError(...)`. |
| B7 | `payments/verifiers/ltc.py`, `sol.py`, `usdt_sol.py` | various | **Raw `os.environ.get()` instead of `EnvKeys`** — bypasses centralized config, inconsistent with rest of codebase. | Use `EnvKeys.BLOCKCYPHER_API_KEY`, `EnvKeys.SOLANA_RPC_URL`. |

### MEDIUM (error handling, robustness)

| # | File | Line(s) | Bug | Fix |
|---|------|---------|-----|-----|
| B8 | `handlers/user/order_handler.py` | 789, 1065, 1245, 1533, 1701 | **Missing delivery_type validation** — `data.get('delivery_type', 'door')` is stored in Order without validating against allowed values. | Validate against `('door', 'dead_drop', 'pickup')`. |
| B9 | `payments/promptpay.py` | 235-238 | **Bare `except Exception: pass`** on Decimal parse — silently swallows errors, makes debugging impossible. | Catch `(ValueError, TypeError, InvalidOperation)`, log warning. |
| B10 | `tasks/payment_checker.py` | 140-180 | **SQLAlchemy lazy-load outside session** — `payment.order` accessed in notify functions may trigger lazy load after session scope ends. | Eagerly load `order` relationship or access within session scope. |
| B11 | `utils/menu_io.py` | 75 | **Decimal→float precision loss** — `float(item.price)` in JSON export loses precision. | Remove `float()`, rely on existing `DecimalEncoder`. |

### LOW (code quality, defensive coding)

| # | File | Line(s) | Bug | Fix |
|---|------|---------|-----|-----|
| B12 | `handlers/user/ticket_handler.py` | 72, 81 | Bare `except Exception: pass` in `_notify_maintainers()` — swallows all errors silently. | Catch specific Telegram exceptions, log. |
| B13 | `utils/delivery_types.py` | 5-8 | Missing `None` guard on `order` parameter in `needs_delivery_photo()`. | Add `if not order: return False`. |
| B14 | `tasks/file_watcher.py` | 38-70 | Non-atomic debounce check — `last_reload_time` read/write not protected in lock. | Move time comparison inside lock. |

---

## Part 2: DRY Violations

### Priority 1 — HIGH Impact (10+ occurrences or critical-path duplication)

#### D1: Callback Data Parsing — 34 occurrences across 20 files

Three repeated patterns not yet centralized:

**Pattern A: `int(call.data.replace("prefix_", ""))` — 20 sites**

| File | Line | Prefix |
|------|------|--------|
| `user/ticket_handler.py` | 299 | `create_ticket_for_order_` |
| `user/ticket_handler.py` | 441 | `view_ticket_` |
| `user/ticket_handler.py` | 491 | `reply_ticket_` |
| `user/ticket_handler.py` | 542 | `close_ticket_` |
| `user/store_selection.py` | 76 | `select_brand_` |
| `user/store_selection.py` | 140 | `select_branch_` |
| `user/orders_view_handler.py` | 170 | `view_order_` |
| `user/orders_view_handler.py` | 350 | `reorder_` |
| `user/orders_view_handler.py` | 406 | `invoice_` |
| `user/delivery_chat_handler.py` | 505 | `chat_with_driver_` |
| `admin/order_management.py` | 102 | `admin_order_` |
| `admin/order_management.py` | 275 | `kitchen_preparing_` |
| `admin/order_management.py` | 298 | `kitchen_ready_` |
| `admin/order_management.py` | 323 | `rider_picked_` |
| `admin/order_management.py` | 355 | `rider_delivered_` |
| `admin/coupon_management.py` | 313 | `admin_view_coupon_` |
| `admin/coupon_management.py` | 367 | `admin_toggle_coupon_` |
| `admin/ticket_management.py` | 82, 139, 209 | `admin_view/reply/resolve_ticket_` |

**Pattern B: `call.data.replace("prefix_", "")` (string) — 18 sites**

| File | Line | Prefix |
|------|------|--------|
| `admin/goods_management_states.py` | 132, 163, 178, 268, 283, 298, 436, 454 | various `edit_/set_/clear_/stock_/toggle_` |
| `admin/accounting_handler.py` | 82, 135 | `accounting_summary_`, `accounting_export_` |
| `admin/coupon_management.py` | 127 | `coupon_type_` |
| `admin/settings_management.py` | 614 | `currency_select_` |
| `admin/segmented_broadcast.py` | 119 | `segment_` |
| `user/orders_view_handler.py` | 81 | `view_orders_` |
| `user/main.py` | 117 | `set_locale_` |

**Pattern C: `int(call.data.split("_")[-1])` — 6 sites**

| File | Line |
|------|------|
| `user/referral_system.py` | 102, 144, 236 |
| `admin/user_management_states.py` | 167 |
| `admin/store_management.py` | 182, 225, 251 |
| `admin/shop_management_states.py` | 162 |

**Suggested extraction:**
```python
# bot/utils/callback_parser.py
def parse_callback_int(data: str, prefix: str) -> int:
def parse_callback_str(data: str, prefix: str) -> str:
def parse_callback_tail_int(data: str, sep: str = "_") -> int:
```

**Lines saved: ~50**

---

#### D2: Order Creation + Customer Validation — 3 occurrences × 90+ lines each

Near-identical blocks in:
- `order_handler.py:1264-1372` (Bitcoin flow)
- `order_handler.py:1499-1602` (Cash flow)
- `order_handler.py:1727-1838` (PromptPay flow)

Each does: CustomerInfo query → None check → bonus deduction → Order() creation → OrderItem loop → reserve_inventory → clear cart → commit → track metrics.

**Suggested extraction:** `_create_and_finalize_order(session, user_id, cart_items, payment_method, **payment_kwargs)` returning the created Order.

**Lines saved: ~180**

---

#### D3: Delivery State Extraction — 4 exact duplicates

Identical 5-line block in `order_handler.py` at lines 1065, 1245, 1489, 1720:
```python
dd_type = data.get('delivery_type', 'door')
dd_instructions = data.get('drop_instructions')
dd_lat = data.get('drop_latitude')
dd_lng = data.get('drop_longitude')
dd_media = data.get('drop_media')
```

**Suggested extraction:** `extract_delivery_fields(state_data: dict) -> dict`

**Lines saved: ~20**

---

### Priority 2 — MEDIUM Impact (3-9 occurrences)

#### D4: `get_metrics()` None-check pattern — 38 remaining sites

`tracking.py` wrappers were applied to `cart_handler.py` and `order_handler.py` (partially), but **38 call sites** still use raw `get_metrics()`:

| File | Count |
|------|-------|
| `monitoring/dashboard.py` | 10 |
| `middleware/security.py` | 4 |
| `admin/user_management_states.py` | 5 |
| `handlers/user/order_handler.py` | 2 |
| `handlers/user/reference_code_handler.py` | 2 |
| `caching/cache.py` | 3 |
| `admin/broadcast.py` | 2 |
| `database/methods/inventory.py` | 2 |
| Others | 8 |

**Lines saved: ~40**

---

#### D5: Payment Error Handling — 8 occurrences in order_handler.py

Repeated pattern at lines 800, 830, 1022, 1138, 1352, 1580, 1838:
```python
logger.error("...: %s", e)
await message.answer(localize("...error..."), reply_markup=back("view_cart"))
return
```

**Suggested extraction:** `_payment_error(message, log_msg, error, i18n_key)`

**Lines saved: ~15**

---

#### D6: Pagination Setup Boilerplate — 6+ occurrences

Repeated LazyPaginator setup in:
- `user/referral_system.py:62-93, 114-135`
- `user/shop_and_goods.py` (category pagination)
- `admin/user_management_states.py` (user list)
- `admin/shop_management_states.py` (shop list)
- `admin/coupon_management.py` (coupon list)

**Lines saved: ~30**

---

### Priority 3 — LOW Impact (2 occurrences)

#### D7: CustomerInfo Query — 12 occurrences
`session.query(CustomerInfo).filter_by(telegram_id=user_id).first()` repeated across 6 files. Already partially centralized in `database/methods/`.

#### D8: Shopping Cart Clear — 5 occurrences
`session.query(ShoppingCart).filter_by(user_id=user_id).delete()` — could consistently use existing `clear_cart()` function.

#### D9: Address File Line Parsing — 2 occurrences
Same `[line.strip() for line in f if line.strip() and not line.strip().startswith('#')]` pattern in both `bitcoin.py` and `crypto_addresses.py`.

---

## Part 3: Summary

### Bugs by Severity

| Severity | Count | Action |
|----------|-------|--------|
| CRITICAL | 2 | Fix immediately |
| HIGH | 5 | Fix before next deploy |
| MEDIUM | 4 | Fix in next sprint |
| LOW | 3 | Backlog |
| **Total** | **14** | |

### DRY Violations by Impact

| Priority | Category | Sites | Lines Saved |
|----------|----------|-------|-------------|
| HIGH | Callback data parsing | 34 | ~50 |
| HIGH | Order creation duplication | 3 | ~180 |
| HIGH | Delivery state extraction | 4 | ~20 |
| MEDIUM | get_metrics() None-checks | 38 | ~40 |
| MEDIUM | Payment error handling | 8 | ~15 |
| MEDIUM | Pagination boilerplate | 6 | ~30 |
| LOW | CustomerInfo queries | 12 | ~5 |
| LOW | Cart clear | 5 | ~3 |
| LOW | Address file parsing | 2 | ~3 |
| **Total** | | **112** | **~346** |

### Recommended Fix Order

1. **B1** — inventory.py session management (CRITICAL, affects all order flows)
2. **B2** — PAYMENT_PROCESSORS KeyError guard (CRITICAL, easy 1-line fix)
3. **D1** — Callback parser module (34 sites, highest DRY ROI)
4. **D2** — Order creation helper (180 lines saved, biggest block)
5. **B4** — Float→Decimal bonus precision fix
6. **B5+B6** — Verifier error guards (division by zero, int parse)
7. **D3** — Delivery state extraction helper
8. **D4** — Migrate remaining get_metrics() to tracking.py
9. **B7** — Verifier env var consistency (EnvKeys)
10. **D5** — Payment error handler
