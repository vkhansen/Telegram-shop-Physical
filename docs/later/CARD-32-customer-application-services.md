# Card 32: Customer Application Services

## Implementation Status

> **0% Complete** | `░░░░░░░░░░░░░░░░░░░` | Design only — not started.

**Tier:** T1 — Shared customer domain API  
**Phase:** M3 — Multi-Platform Growth  
**Priority:** High  
**Effort:** Medium (2–4 days)  
**Dependencies:** Prefer [CARD-29](CARD-29-messenger-port.md) for notify DTOs; domain methods already exist. Prefer [CARD-34](CARD-34-conversation-workflow-specifications.md) customer core flow IDs so service boundaries match named workflows (soft gate).
**Plan:** [`MULTI-CHANNEL-TIERED-PLAN.md`](MULTI-CHANNEL-TIERED-PLAN.md)

---

## Why

Customer flows today mix **business rules** with **Telegram I/O** inside handlers (`order_handler.py`, `cart_handler.py`, …). Instagram (CARD-33) must not copy that logic.

Extract **thin application services** that:

- Call existing `database/methods` and `payments/*`
- Return **DTOs** (no `Message`, no `CallbackQuery`)
- Preserve CARD-23 rules: no DB session held across awaits

Telegram handlers stay; they gradually call services and render the same UI.

---

## Modules

```
bot/services/
  __init__.py
  cart.py
  checkout.py
  order_query.py
  tickets.py
  dto.py            # shared result types
```

### cart.py

Wrap: `add_to_cart`, `remove_from_cart`, `clear_cart`, `get_cart_items`, `calculate_cart_total`, modifier validation helpers.

### checkout.py

| Method | Behavior |
|--------|----------|
| `start_cash(...)` | Create order + reserve; return order_code / errors |
| `start_promptpay(...)` | Create order + reserve + QR bytes + amount |
| `start_crypto(...)` | Address assignment + amount |
| `apply_bonus / set_delivery_fields` | Pure state prep as needed |

Reuse: `create_order_from_customer`, `reserve_inventory`, `generate_promptpay_qr`, crypto address pool, slip verify remains handler- or adapter-triggered with image bytes.

### order_query.py

List/detail/status for a user; reorder snapshot data.

### tickets.py

Open ticket, append message, list open — for IG support without admin UI.

### DTO example

```python
@dataclass
class ServiceResult:
    ok: bool
    error_key: str | None = None  # i18n key for any channel
    data: dict | None = None
```

---

## Telegram migration strategy

1. Extract service methods by **copying logic out** of handlers (behavior-preserving).  
2. Point **one** payment path (e.g. PromptPay) at the service; compare outcomes in tests.  
3. Migrate cash/crypto next.  
4. **Do not** rewrite FSM or keyboards.

Admin/driver handlers: **out of scope**.

---

## Tests

- Unit tests with SQLite fixtures: empty cart, insufficient stock, bonus, PromptPay order row shape  
- Parity test: service-created order matches fields produced by legacy helper paths where still dual-path  

---

## Exit criteria

- [ ] Services package exists and is imported by at least one Telegram payment path  
- [ ] Inventory reservation and order status transitions unchanged  
- [ ] Suite green; no new session-across-await patterns  

---

## Effort

| Task | Days |
|------|------|
| DTOs + cart service | 0.5–1 |
| Checkout (cash + PromptPay + crypto) | 1–2 |
| order_query + tickets | 0.5–1 |
| Telegram path migration + tests | 0.5–1 |
| **Total** | **2–4** |
