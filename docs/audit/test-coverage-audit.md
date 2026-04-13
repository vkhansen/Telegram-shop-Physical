# Test Coverage & Code-Quality Audit

**Date:** 2026-04-13
**Scope:** `bot/` vs `tests/` — focus on gaps, e2e robustness, if/elif → state-machine refactors.

---

## Phase 1 — Coverage Gaps

### Well-covered (unit + e2e)
`database/*`, `utils/{order_status, order_helpers, order_codes, modifiers, validators, delivery_types, delivery_zones, coupon_utils, currency, invoice, message_utils, pagination, tracking, user_utils, constants}`, `payments/{bitcoin, chain_verify, crypto_addresses, price_feed, promptpay, slip_verify, payment_checker}`, `referrals`, `ai/*`, `i18n/*`, `config/timezone`.

### Untested (0 test files)
| Area | Module | Risk | Notes |
|---|---|---|---|
| **Handlers (user)** | `cart_handler`, `order_handler`, `orders_view_handler`, `delivery_chat_handler`, `shop_and_goods`, `store_selection`, `ticket_handler`, `review_handler`, `search_handler`, `referral_system`, `reference_code_handler`, `privacy_handler`, `help_handler`, `user/main` | **HIGH** | Critical paths tested only indirectly via e2e DB fixtures — no callback/FSM dispatch tests |
| **Handlers (admin)** | `order_management`, `goods_management_states`, `adding/update_position_states`, `categories_management_states`, `store_management`, `shop_management_states`, `settings_management`, `user_management_states`, `coupon_management`, `ticket_management`, `broadcast`, `segmented_broadcast`, `reference_code_management`, `accounting_handler`, `grok_assistant` | **HIGH** | Admin FSM handlers completely untested; order-status transitions, kitchen/rider buttons, permission filters |
| **Middleware** | `locale`, `rate_limit`, `security` | **MEDIUM** | Locale priority rules (explicit → ctxvar → env → default) is exactly the kind of rule that regresses silently |
| **Filters** | `filters/main` (`HasPermissionFilter`) | **HIGH** | Permission-bypass bugs already found (C3); need unit coverage |
| **Tasks** | `file_watcher`, `reservation_cleaner` | **MEDIUM** | `payment_checker` has tests, others don't |
| **Utils** | `menu_io`, `cart_stub`, `singleton` | **MEDIUM** | `menu_io` was source of H8 (photo IndexError) and M7 (Decimal float loss) |
| **Payments** | `notifications` | **MEDIUM** | Customer-facing messaging path |

### Thinly covered (regressions possible)
- `order_handler.py` (2098 LOC) — only exercised via DB fixtures; **no FSM state transition tests** covering the payment dispatch table, bonus precision round-trip (H2 regression), delivery_type validation (M1), GPS extraction (M10).
- `admin/order_management.py` — status transition race (H3) has no concurrency regression test; `with_for_update()` assertion only checks the SQL call exists.

---

## Phase 2 — E2E Robustness Issues

Looking at the existing `tests/e2e/`:

1. **No regression tests for `review-DRY.md` fixes.** Fixed bugs C1–C4, H1–H8, M1–M14 have no targeted e2e test. If a future refactor reintroduces any of them, nothing catches it.
2. **`test_full_order_flow.py` asserts happy-path only.** No test for:
   - Invalid status transition rejection (e.g., `pending → delivered`).
   - Expired reserved order cleanup.
   - Inventory race (two orders consuming last unit).
   - Bonus amount precision round-trip (`฿33.33` → FSM state → back to `Decimal`).
   - Unknown `payment_method` callback data fallback.
   - `_extract_coords_from_url()` returning `None`.
3. **Mocks hide real paths.** Several tests `patch()` the bot object wholesale; callback handlers never actually run. The existing e2e is really "DB integration" — not simulated user flow.
4. **No golden-path for admin FSM.** `order_status_change_handler` → `_send_status_notifications` dispatch is completely untested end-to-end.
5. **No test for `PAYMENT_PROCESSORS` dispatch table.** Adding a new method to `constants.py` without updating the dict would silently fall to the `.get()` fallback at runtime.

---

## Phase 3 — Good-Practice / DRY / State-Machine Refactor Candidates

Prior audits (`DRY-audit-report.md`, `review-DRY.md`) already landed D1–D6 helpers. Remaining structural `if/elif` smells:

### R1 — Kitchen/Rider status buttons are 4 near-duplicate handlers
**File:** `bot/handlers/admin/order_management.py:272–392`
Four handlers (`kitchen_start_preparing`, `kitchen_mark_ready`, `rider_picked_up`, `rider_mark_delivered`) differ only in `(callback_prefix, target_status, side_effects, confirm_text, suffix)`. Each repeats:
```python
order_id = int(call.data.replace(prefix, ""))  # with try/except
with Database().session() as session:
    order = ... .with_for_update().first()
    if not order or not is_valid_transition(...): ...
    order.order_status = target
    session.commit()
    await _notify_customer_status(...)
    await call.answer(label)
    await call.message.edit_text(... + suffix)
```
**Refactor:** Replace with a single handler driven by a transition table:
```python
QUICK_TRANSITIONS = {
    "kitchen_preparing": QuickTransition("preparing", label="Preparing", suffix="🍳 <b>PREPARING</b>"),
    "kitchen_ready":     QuickTransition("ready",     label="Ready",     suffix="📦 <b>READY</b>", post=_send_rider_notification),
    "rider_picked":      QuickTransition("out_for_delivery", label="Out for Delivery", suffix="🚗 <b>OUT FOR DELIVERY</b>", post=_assign_driver_and_prompt_gps),
    "rider_delivered":   QuickTransition("delivered", label="Delivered", suffix="✅ <b>DELIVERED</b>", post=_finalize_delivery),
}
```
Lines saved: ~100. Removes 4 duplicated try/except blocks, unifies error handling, and new transitions become one dict entry.

### R2 — `_send_status_notifications` if/elif chain
**File:** `bot/handlers/admin/order_management.py:397–414`
```python
if new_status == "confirmed":   await _send_kitchen_notification(...)
elif new_status == "ready":     await _send_rider_notification(...)
elif new_status == "out_for_delivery": ...
elif new_status == "delivered" or new_status in ("preparing", "ready"): ...
```
Note the last branch has a latent bug: `"ready"` is already handled above, so the `or` is dead. A dict-of-callbacks replaces the chain and forces explicit coverage.
```python
STATUS_NOTIFIERS: dict[str, list[Callable]] = {
    "confirmed":        [_send_kitchen_notification],
    "preparing":        [_notify_customer_status],
    "ready":            [_send_rider_notification, _notify_customer_status],
    "out_for_delivery": [_notify_customer_status, _prompt_customer_gps],
    "delivered":        [_notify_customer_status],
}
```

### R3 — `_notify_customer_status` hardcoded branch
**File:** `bot/handlers/admin/order_management.py:558–568`
```python
status_key = f"order.status.{order.order_status}"
if order.order_status == "delivered":
    status_key = "order.status.delivered_notify"
```
Trivial but it's the start of a pattern. Move to a `STATUS_MESSAGE_KEY` dict beside `VALID_TRANSITIONS`.

### R4 — `order_handler.py` per-method payment flows (D2 revisited)
Prior audit flagged 3× ~100-line blocks for BTC/Cash/PromptPay finalization. `order_helpers.create_order_from_customer()` now exists, but the three `process_*_payment_new_message` functions still duplicate the pre-order glue. Worth a second pass *with* tests first (see R5 dependency).

### R5 — Before refactoring, add regression tests
R1/R2 are behavior-preserving but non-trivial. Required e2e before touching them:
- Each `QUICK_TRANSITIONS` key drives the correct final `order_status` + side effects.
- Invalid transitions (e.g. `kitchen_preparing` on an already-delivered order) return a user alert and do not mutate state.
- `_send_status_notifications` fires the exact expected set of notifications for each status.
- Concurrency: two simultaneous `kitchen_preparing` clicks on the same order — second must lose cleanly (exercises `with_for_update()`).

---

## Recommended Next Steps (in order)

1. **Add regression tests** for the fixed bugs in `review-DRY.md` that don't yet have one: H2 (bonus precision), H3 (status race), M1 (delivery_type validation), M10 (Maps URL extract). → new `tests/unit/test_review_dry_regressions.py`.
2. **Add admin FSM tests** for `order_status_change_handler` and the 4 quick-transition handlers (callback simulation, not DB-only).
3. **Implement R1 refactor** (quick-transition table) with the new tests in place.
4. **Implement R2/R3** dict dispatches.
5. **Then** tackle R4 (order finalization helper extension) — highest risk, needs R1–R3 test coverage first.

---

## Open questions before proceeding
- Are handler-level tests acceptable given there's no existing callback-simulation harness, or prefer to extend the DB-only style?
- R1 touches 4 registered aiogram routes. OK to collapse into one `F.data.startswith(prefix)` handler, or keep 4 thin handler shells calling one body?
- Should bugs already marked FIXED in `review-DRY.md` be re-verified first? (Some "VERIFIED" items aren't test-backed.)
