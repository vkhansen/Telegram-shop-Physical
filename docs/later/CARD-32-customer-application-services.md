# Card 32: Customer Application Services

## Implementation Status

> **~95% Complete** | `███████████████████░` | **2026-07-17:** TG cart + payments + store_selection/bonus on cart service; web commerce API (CARD-40-B). Tickets polish still open.

**Tier:** T1 — Shared customer domain API (**hard gate for second channel**)  
**Phase:** M3 — Multi-Platform Growth  
**Priority:** **Critical** (unified backend directive 2026-07-17)  
**Effort:** Medium (2–4 days)  
**Dependencies:** Prefer [CARD-29](CARD-29-messenger-port.md) for notify DTOs; domain methods already exist. Prefer [CARD-34](CARD-34-conversation-workflow-specifications.md) customer core flow IDs (soft gate).  
**Law:** [UNIFIED-BACKEND-CHANNEL-INTERFACE](../Specifications/UNIFIED-BACKEND-CHANNEL-INTERFACE.md)  
**Plan:** [`MULTI-CHANNEL-TIERED-PLAN.md`](MULTI-CHANNEL-TIERED-PLAN.md)

---

## Why

Customer flows still mix **business rules** with **Telegram I/O** inside handlers (`order_handler.py`, `cart_handler.py`, …). Web already uses services for catalog/leads/tickets. **Every frontend** (Telegram, LINE, web, forms, chatbox) must call the **same** cart/checkout/order services.

Extract **thin application services** that:

- Call existing `database/methods` and `payments/*`
- Return **DTOs** (no `Message`, no `CallbackQuery`, no HTTP request objects)
- Preserve CARD-23 rules: no DB session held across awaits

Telegram handlers become **adapters only**; they call services and render UI. **No new business logic in handlers.**

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

- [x] Web catalog / leads / tickets already service-shaped (do not re-fork)  
- [x] `cart` + `checkout` + `order_query` modules landed  
- [x] Telegram **PromptPay** path uses checkout service (`process_promptpay_payment`)  
- [x] Telegram **cash** path uses checkout service (`process_cash_payment_new_message` → `start_cash_order`)  
- [x] Telegram **crypto** paths use checkout (`start_crypto_order`: legacy BTC + multi-coin + CryptoPayment)  
- [x] `cart_handler` uses cart service only (list/add/remove/clear)  
- [x] Inventory reservation and order status transitions unchanged (parity via service tests + CARD-23 cash)  
- [x] Optional: store_selection / leftover `get_cart_items` call sites (CARD-40-B)  
- [x] Suite green on touched paths; no new session-across-await patterns  
- [ ] PR checklist: reject new handler→domain commerce code

---

## Effort

| Task | Days |
|------|------|
| DTOs + cart service | 0.5–1 |
| Checkout (cash + PromptPay + crypto) | 1–2 |
| order_query + tickets | 0.5–1 |
| Telegram path migration + tests | 0.5–1 |
| **Total** | **2–4** |
