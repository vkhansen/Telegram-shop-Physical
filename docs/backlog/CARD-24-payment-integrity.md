# CARD-24: Payment Integrity — Duplicate Slips, Refunds & Crypto Reconciliation

## Status: Not Started

## Priority: P0 — Launch Blocker
## Effort: Medium (2–3d)
## Phase: Launch Readiness — Money Safety

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

- [ ] Same `slip_transaction_id` cannot confirm two orders (DB constraint + pre-check), with a user-facing rejection and admin alert
- [ ] Cancelling a paid order restores bonus balance and creates a `Refund` record
- [ ] Crypto overpayment delta is recorded on the payment row
- [ ] Expired/cancelled crypto orders return their address to the pool after TTL
- [ ] Receiver-name verification uses a normalized exact match, not loose substring
- [ ] `bot_cli.py refund <order>` reverses a payment and is audit-logged

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
