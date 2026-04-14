# CARD-23: Payment Handler DB-Session Refactor

## Status: Not Started

## Priority: High
## Effort: Medium (2–3d)
## Phase: Reliability — Infrastructure Hardening

---

## Problem

Two order-creation handlers hold a single `with Database().session()` context open
across many `await` calls, keeping a PostgreSQL connection checked out from the pool
for the entire duration of Telegram API I/O, Redis state updates, and admin
notifications.  Under load this exhausts the pool (size 20 + overflow 40) and causes
`TimeoutError: QueuePool limit of size 20 overflow 40 reached` for all other
concurrent users.

### Affected functions

| File | Function | Line | `await` calls inside session |
|------|----------|------|------------------------------|
| `bot/handlers/user/order_handler.py` | `process_bitcoin_payment_new_message` | ~1235 | 6+ |
| `bot/handlers/user/order_handler.py` | `process_crypto_payment` | ~769 | 5+ |

### Pattern (current — bad)

```python
with Database().session() as session:
    customer_info = session.query(CustomerInfo)...first()
    if not customer_info:
        await message.answer(...)          # ← connection held during Telegram I/O
        return
    if bonus_applied > ...customer_info.bonus_balance:
        await message.answer(...)          # ← connection held during Telegram I/O
        return

    order = Order(...)
    session.add(order)
    session.flush()
    ...
    reserve_inventory(..., session=session)
    session.commit()

    await message.answer(payment_text)     # ← connection held after commit
    await notify_admin_new_order(...)      # ← connection held during admin send
    await state.clear()                    # ← connection held during Redis write
```

### Root cause

The `with Database().session()` block is one monolithic unit.  All outbound I/O
(Telegram sends, Redis writes) happens inside the same block that owns the DB
connection, even after `session.commit()` when the connection is no longer needed.

---

## Solution

Split each handler into three phases, closing the DB connection between phases:

**Phase 1 — Pre-flight read** (short session, no awaits)
- Query `CustomerInfo` for all scalar values needed: `bonus_balance`, `delivery_address`,
  `phone_number`, `latitude`, `longitude`, etc.
- Close session immediately.
- Run all early-exit checks on the extracted scalars.

**Phase 2 — Write transaction** (short session, no awaits except `reserve_inventory` which is sync)
- Open a new session.
- Create `Order`, `OrderItem`, reserve inventory, mark address used, create
  `CryptoPayment`/`BitcoinPayment` record, delete `ShoppingCart` rows.
- `session.commit()`.
- Extract `order.id`, `order.order_code` as scalars.
- Close session.

**Phase 3 — Outbound I/O** (no DB session open)
- `await message.answer(payment_text, ...)`
- `await notify_admin_new_order(...)`
- `await state.clear()`
- `sync_customer_to_csv(...)` (sync, but no DB connection held)

### Pattern (target — correct)

```python
# Phase 1: pre-flight reads
customer_bonus = None
customer_address = None
with Database().session() as session:
    ci = session.query(CustomerInfo).filter_by(telegram_id=user_id).first()
    if not ci:
        await message.answer(localize("order.payment.customer_not_found"), ...)
        return
    customer_bonus = ci.bonus_balance
    customer_address = ci.delivery_address
    # ... extract all needed scalars
# Session closed here

if bonus_applied > 0 and customer_bonus < bonus_applied:
    await message.answer(localize("order.bonus.insufficient"), ...)
    return

# Phase 2: write transaction (all sync — no awaits inside)
order_id = None
order_code = None
with Database().session() as session:
    # Deduct bonus, create Order + OrderItems, reserve, commit
    ...
    session.commit()
    order_id = order.id
    order_code = order.order_code
# Session closed here

# Phase 3: outbound I/O (no connection held)
await message.answer(payment_text, ...)
await notify_admin_new_order(order_id, ...)
await state.clear()
```

---

## Scope

### `process_bitcoin_payment_new_message` (~line 1235)

- ~190-line function.
- **Early exits to move before session open**: `customer_not_found` check,
  `bonus.insufficient` check.
- **Post-commit awaits to move after `with` block**: `await message.answer(payment_text)`,
  `await notify_admin_new_order(...)`, `await state.clear()`.
- `reserve_inventory` is synchronous — stays inside the write transaction.
- `generate_unique_order_code` needs the session — stays inside the write transaction.

### `process_crypto_payment` (~line 769)

- ~190-line function, same structure.
- Same three early-exit awaits: `customer_not_found`, `bonus.insufficient`,
  `unable_to_reserve`.
- Post-commit awaits to move out: `await message.answer(payment_text)`,
  `await state.clear()`.
- `get_available_address` and `mark_address_used` — verify whether these need the
  session or can be called independently; `mark_address_used` currently accepts an
  optional `session=` kwarg and must stay in the write transaction.

---

## Testing Requirements

Before implementing, capture the current behaviour with integration tests:

1. **Happy path** — order created, payment message sent, state cleared.
2. **`customer_not_found`** — handler exits early, no order row created.
3. **`bonus_insufficient`** — handler exits early, bonus balance unchanged.
4. **`reserve_inventory` failure** — handler exits early, no order row, no
   `CryptoPayment` row, address not marked used.
5. **Post-commit Telegram failure** — order IS committed (idempotent), but
   `await message.answer` raises `TelegramAPIError` — confirm the order survives
   and the user can recover (check order status).

After refactor all five scenarios must produce identical outcomes.

---

## Acceptance Criteria

- [ ] `process_bitcoin_payment_new_message`: no `await` inside any `with Database().session()` block.
- [ ] `process_crypto_payment`: no `await` inside any `with Database().session()` block.
- [ ] All existing payment-flow tests green.
- [ ] New tests covering the 5 scenarios above.
- [ ] Pool exhaustion smoke test: 20 concurrent payment submissions do not raise `QueuePool` timeout.

---

## Related

- This is the same DB-session-across-awaits pattern fixed in CARD-23's predecessor
  work (2026-04-14):
  - `check_and_ask_about_bonus` — already fixed (scalar extraction pattern).
  - `checkout_cart_handler` / `confirm_delivery_info_handler` — already fixed.
- `bot/database/main.py` pool config: `pool_size=20`, `max_overflow=40`,
  `pool_timeout=30`, `statement_timeout=30000ms`.
- `reserve_inventory` in `bot/database/methods/inventory.py` is synchronous and
  accepts an optional `session=` kwarg — it must remain inside the write transaction.
