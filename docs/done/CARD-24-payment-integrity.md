# CARD-24: Payment Integrity — Duplicate Slips, Refunds & Crypto Reconciliation

## Status: ✅ DONE (2026-06-03) — all adversarial paths closed; see Completion Note

## Priority: P0 — Launch Blocker
## Effort: Medium (2–3d)
## Phase: Launch Readiness — Money Safety

---

## Verification Audit (2026-06-02)

Recent DB-hardening commits landed two pieces of this card; the rest is genuinely open:

| Scope item | State | Evidence |
|------------|-------|----------|
| 1a. UNIQUE on `slip_transaction_id` | ✅ DONE | `main.py:553` (`uq_orders_slip_transaction_id`); migration `616a5683e747_unique_slip_transaction_id_card_24.py` |
| 1b. Pre-confirm dup query + user/admin messaging | ❌ NOT STARTED | `order_handler.py:1916` sets the id then commits (1932); duplicates only fail at the constraint and fall into the generic except at 1934 — no friendly rejection or admin alert |
| 2. Bonus restored on cancel/expire | ✅ DONE (partial) | `bot_cli.py:279-292` and `inventory.py:403-430` restore `bonus_applied` → `bonus_balance` |
| 2. `Refund` model + `refunds.py::reverse_payment()` | ❌ NOT STARTED | no `bot/payments/refunds.py`, no `Refund` model, no `refund_status` column |
| 3. `overpaid_amount` on `CryptoPayment` | ❌ NOT STARTED | not present on model (`main.py:697-725`) |
| 3. `release_address()` + `address_reclaimer.py` | ❌ NOT STARTED | no release/reclaim code in `crypto_addresses.py`; no such task file |
| 4. Receiver-name hardening | ❌ NOT STARTED | `slip_verify.py:426` still a loose `in` substring check |
| 5. CLI `refund` / `--reclaim-addresses` | ❌ NOT STARTED | absent from `bot_cli.py` subcommands |

**Net:** the *structural guarantee* (one slip → one order) exists at the DB layer and bonus is no longer silently lost on cancel, but the **user-facing dedup handling, the refund record/audit trail, and all crypto reconciliation remain to be built.** Remaining effort is still ~2–3d.

---

## Why

The payment **happy path** is solid (PromptPay EMVCo QR is correct; SlipOK/EasySlip/RDCW and the BTC/LTC/SOL/USDT verifiers are real API integrations; auto-confirm only fires on a genuine `VerifyStatus.VERIFIED` — see `bot/handlers/user/order_handler.py:1919-1923`). The **adversarial path** is not. Before taking real money these three holes can each be exploited or cause silent loss:

1. **No application-level duplicate-slip protection.** `Order.slip_transaction_id` is stored (`order_handler.py:1913`) but nothing prevents the *same* bank slip from confirming two different orders. Only EasySlip flags duplicates server-side (`slip_verify.py:205`); SlipOK and RDCW do not. A customer can reuse one ฿200 slip across several orders.
2. **No refund / reversal path.** Cancelling a paid order does not restore `bonus_balance`, reverse a crypto payment, or flag a PromptPay refund. Bonus is deducted at order creation (`order_handler.py:829-832`) and never returned on cancel.
3. **Crypto reconciliation gaps.** Verifiers accept `amount >= expected` with no overpayment tracking/refund, and used addresses are never reclaimed when an order expires unpaid — the pool only depletes (you can see the live `Bitcoin address pool running low` warning today).

## Scope

- **Duplicate-slip guard:** add a `UNIQUE` constraint on `(slip_transaction_id)` (nullable) and, before auto-confirm, query for an existing order with the same transaction id → reject with a clear user message and an admin alert.
- **Refund/reversal flow:** introduce a `Refund` record + a single `reverse_payment(order)` path invoked on cancellation that (a) restores `bonus_applied` to `bonus_balance`, (b) marks crypto/PromptPay payments `refund_required` for admin action, and (c) audit-logs the reversal.
- **Crypto reconciliation:** record overpayment delta on the payment row; add a `reclaim_expired_addresses` task that releases `is_used` addresses whose order is `expired`/`cancelled` after a TTL (default 24h) back to the pool.
- **Receiver-name match hardening:** tighten the substring compare at `slip_verify.py:426` to a normalized exact/whitelist match.

## Files to Modify

| File | Changes |
|------|---------|
| `bot/database/models/main.py` | `UNIQUE` on `Order.slip_transaction_id`; add `Refund` model; add `overpaid_amount` to `CryptoPayment`; add `refund_status` to `Order` |
| `bot/handlers/user/order_handler.py` | Pre-confirm duplicate-slip query (~line 1918); call `reverse_payment` on cancel paths |
| `bot/payments/slip_verify.py` | Normalize receiver-name comparison (line ~426); surface `DUPLICATE` consistently across providers |
| `bot/payments/refunds.py` *(new)* | `reverse_payment()`, bonus restoration, refund record creation |
| `bot/payments/crypto_addresses.py` | `release_address()`; record overpayment delta |
| `bot/tasks/address_reclaimer.py` *(new)* | Periodic task: reclaim used addresses for expired/cancelled orders past TTL |
| `bot_cli.py` | `refund` subcommand; `--reclaim-addresses` maintenance flag |

## Acceptance Criteria

- [x] Same `slip_transaction_id` cannot confirm two orders (DB constraint + pre-check), with a user-facing rejection and admin alert
- [x] Cancelling a paid order restores bonus balance and creates a `Refund` record
- [x] Crypto overpayment delta is recorded on the payment row
- [x] Expired/cancelled crypto orders return their address to the pool after TTL
- [x] Receiver-name verification uses a normalized exact match, not loose substring
- [x] `bot_cli.py refund <order>` reverses a payment and is audit-logged

---

## Completion Note (2026-06-03)

All six acceptance criteria met; full suite green (**1447 passed**, 150 skipped, 47.67% coverage).

### What shipped

| Scope item | Implementation |
|------------|----------------|
| **Duplicate-slip guard** | `order_handler.py` `process_receipt_photo` now runs a pre-confirm query for any *other* order owning the same `slip_transaction_id` before auto-confirming. On a hit it refuses to confirm, sets `slip_verify_status='duplicate'`, sends the customer `order.payment.promptpay.duplicate_slip` (added to all 7 locales) and a 🚫 admin alert naming the original order. Also constraint-safe: a duplicate txn id is never copied onto a second row, so `uq_orders_slip_transaction_id` can't trip the broad except. |
| **Refund / reversal** | New `bot/payments/refunds.py::reverse_payment(order, session)` — the single reversal path: restores `bonus_applied`→`bonus_balance`, writes an auditable `Refund` row (new model), flags external (crypto/PromptPay/cash) payments as `pending_manual` with `order.refund_status='pending'`, and logs `ORDER_REFUND`. **Idempotent** (existing-row check → no double credit). `cancel_order_by_code` and `cleanup_expired_reservations` were both refactored to route through it. |
| **Crypto overpayment** | `crypto_payments.overpaid_amount` column; `payment_checker` records `received − expected` when positive. |
| **Address reclaim** | `crypto_addresses.release_address()` (+`readd_address_to_file`); new `bot/tasks/address_reclaimer.py` releases `is_used` addresses for `expired`/`cancelled` orders past a 24h TTL, started from `bot.main` and exposed as `bot_cli.py reclaim-addresses`. |
| **Receiver-name hardening** | `slip_verify.py` substring compare replaced with `_receiver_matches()` — normalized, title/whitespace tolerant, order-independent token match; a single shared word no longer validates (e.g. "Bangkok" ✗ "Bank of Bangkok"). |
| **CLI** | `bot_cli.py refund <order_code> [--reason]` and `reclaim-addresses [--ttl-hours]`. |
| **Schema** | New `Refund` model + `Order.refund_status` + `CryptoPayment.overpaid_amount`; Alembic migration `0aff8ed12a0d` (now head). |

### Bug-class fix found while wiring (per CLAUDE.md)

`bot_cli.py` wrote invalid `order_status` literals that violate `ck_orders_order_status`: `cancel_order_by_code` set `'canceled'` (one L) and `complete_order_by_code` set `'completed'` (not in the allowed set). Both would fail the CHECK constraint on Postgres. Fixed the whole class → `'cancelled'` / `'delivered'`, including the dead `=='canceled'`/`=='completed'` status guards.

### Tests

- `tests/unit/payments/test_slip_dedup.py` — duplicate txn rejected (pre-check + DB constraint); normalized receiver match.
- `tests/unit/payments/test_refunds.py` — bonus restored on reversal; `Refund` row created + audit-logged + idempotent; paid order flagged `pending_manual` for the cash delta.
- `tests/unit/payments/test_address_reclaim.py` — expired order releases address; within-TTL/active order kept; overpayment delta recorded via `check_pending_payments`.

## Test Plan

| Test File | Tests | Assert |
|-----------|-------|--------|
| `tests/unit/payments/test_slip_dedup.py` | `test_duplicate_txn_rejected` | Second order with same txn id is blocked |
| | `test_receiver_name_normalized_match` | "Bangkok" slip does not satisfy "Bank of Bangkok" |
| `tests/unit/payments/test_refunds.py` | `test_cancel_restores_bonus` | Cancelled order returns `bonus_applied` to balance |
| | `test_refund_record_created` | Refund row written + audit-logged |
| `tests/unit/payments/test_address_reclaim.py` | `test_expired_order_releases_address` | Address `is_used` flips back after TTL |
| | `test_overpayment_recorded` | `overpaid_amount` set when amount > expected |

## Links

Surfaces the money-safety gaps behind the go-live gate in [`../MASTER-PLAN.md`](../MASTER-PLAN.md). Pairs with [CARD-25](CARD-25-test-suite-recovery.md) (which adds the missing verification-layer coverage) and [CARD-23](CARD-23-payment-session-refactor.md) (concurrency under load).
