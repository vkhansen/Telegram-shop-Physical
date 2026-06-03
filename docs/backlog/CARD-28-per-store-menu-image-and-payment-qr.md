# CARD-28: Per-Store Menu Image + Per-Store Payment QR

## Status: Not Started

## Priority: P2 — Multi-store ops polish
## Effort: Medium (3–5d)
## Phase: Multi-Store Polish

---

## Why

Multi-store brands (CARD-19) can pick a branch at checkout, but two branch-level needs are unmet:

1. **No branch-specific menu visual.** Store selection (`bot/handlers/user/store_selection.py:128/215` set `current_store_id`) drops the customer straight into the shared category list. There is no per-branch menu board / flyer image — restaurants routinely want to show "their" menu the moment a branch is chosen.
2. **All payments route to one account.** The PromptPay branch of checkout reads a **global** bot setting — `get_promptpay_id()` (`bot/handlers/user/order_handler.py:1971-1974`) — and ignores even the per-brand `Brand.promptpay_id`. A brand whose branches are independently owned/operated cannot collect to each branch's own account, and there is no way to use a branch's pre-printed static QR.

**Reuse (this card adds branch-level wiring on top of existing machinery):**
- Store model + store-selection flow (CARD-19).
- Telegram `file_id` image pattern + `answer_photo` rendering (CARD-RC1 multi-media items, e.g. `Goods.image_file_id`).
- Dynamic amount-embedded PromptPay QR generator (CARD-1) — `bot/payments/promptpay.py::generate_promptpay_qr`.
- Admin store-management FSM — `bot/handlers/admin/store_management.py`.

## Scope (phased — each phase shippable)

**Phase A — Per-store menu image**
- Add `Store.menu_image_file_id` (Telegram `file_id`).
- On store selection, if the store has a menu image, send it as a **simple photo** (`answer_photo`) with the store name as caption, before the category list. No image → today's behaviour unchanged.
- Admin: upload / replace / clear a store's menu image.

**Phase B — Per-store PromptPay (dynamic QR)**
- Add `Store.promptpay_id` + `Store.promptpay_name`.
- Payment-QR id resolution precedence: **`Store.promptpay_id` → `Brand.promptpay_id` → global `get_promptpay_id()`**. The order already carries `store_id`, so the order_handler PromptPay branch resolves from the order's store first and only falls back when unset.
- Admin: set / clear per-store PromptPay id + display name.

**Phase C — Static QR image fallback**
- Add `Store.payment_qr_file_id` (Telegram `file_id` of a pre-made static QR).
- When a store has a static QR image **and** no dynamic PromptPay id, send the stored image instead of a generated amount-embedded QR. A static QR can't embed the amount, so the amount must be shown clearly in the caption and the customer enters it manually.
- Admin: upload / clear a store's static QR.

> All three are independent and additive — a store with none of them behaves exactly as today (brand/global PromptPay, no menu image, dynamic QR).

## Files (modify unless noted)

| File | Purpose |
|------|---------|
| `bot/database/models/main.py` | `Store`: + `menu_image_file_id`, `promptpay_id`, `promptpay_name`, `payment_qr_file_id` |
| `migrations/versions/*_store_menu_qr_card_28.py` *(new)* | add the four nullable `stores` columns |
| `bot/handlers/user/store_selection.py` | send the menu image on store select |
| `bot/handlers/user/order_handler.py` | PromptPay id resolution precedence (store → brand → global); static-QR fallback path |
| `bot/payments/promptpay.py` *(maybe)* | small resolver helper if the precedence logic is shared |
| `bot/handlers/admin/store_management.py` | admin upload/set for menu image, PromptPay id/name, static QR |
| `bot/states/user_state.py` (or an admin states module) | FSM states for the new admin uploads |
| `bot/i18n/strings.py` | new keys across **all 7 locales** (parity test enforced) |

## Acceptance Criteria

- [ ] Selecting a store that has a menu image sends that image (simple photo + store-name caption) before the menu; stores without one are unchanged.
- [ ] An order placed in a store with its own PromptPay id generates the QR to **that** account; absent → brand id; absent → global id (existing behaviour preserved).
- [ ] A store with a static QR image and no dynamic id sends the stored QR with the order amount in the caption.
- [ ] Admin can set / replace / clear all three per-store assets from store management.
- [ ] Fully backward compatible: stores with none of the new fields behave exactly as before.

## Test Plan

| Test File | Tests | Assert |
|-----------|-------|--------|
| `tests/unit/handlers/test_store_assets.py` | `test_menu_image_sent_on_select` | photo sent with the store's `menu_image_file_id` when set; not sent when null |
| | `test_promptpay_resolution_precedence` | resolver returns store id → brand id → global, in that order |
| | `test_static_qr_fallback` | stored static QR sent (with amount in caption) when no dynamic id |
| `tests/integration/test_store_payment_routing.py` | `test_order_uses_store_promptpay` | order placed in a store with its own id → generated QR payload encodes **that** id |

## Links

Builds on [CARD-19](../done/CARD-19-multi-brand-bot-coordination.md) (multi-store), [CARD-01](../done/CARD-01-promptpay-qr-payment.md) (PromptPay QR), and CARD-RC1 (multi-media menu items). Multi-store polish; independent of the launch gate and M2 dispatch.
