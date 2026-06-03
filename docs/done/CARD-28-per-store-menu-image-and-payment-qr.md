# CARD-28: Per-Store Menu Image + Per-Store Payment QR

## Status: ✅ DONE (2026-06-03) — all three phases shipped & tested; see Completion Note

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

---

## Completion Note (2026-06-03)

All three phases shipped, fully backward compatible, committed in stages. Full suite green: **1476 passed (+16 new), 150 skipped, 48.87% coverage**.

### What was built

**The critical path (Phase B + slip verification) — the user's priority.**
- `bot/payments/store_payment.py::resolve_payment_target` is the single source of truth, precedence **store → brand → global**, used by **both** QR generation and slip verification so the account paid and the account verified can never diverge (before this, the QR used a global id while verification used a global name — per-store would have silently mismatched).
- QR generation (`order_handler.process_promptpay_payment`): dynamic amount-embedded QR to the resolved id; **static-QR-image fallback** (Phase C, amount shown in caption) when a store has a static QR and no dynamic id; text fallback when nothing is configured.
- Slip verification (`order_handler.process_receipt_photo`): `expected_receiver` resolved from the order's own `store_id`/`brand_id`, so a customer pays the branch's QR and the uploaded slip auto-verifies against that same branch account.

**Phase A — per-store menu image.** `Store.menu_image_file_id`; `_show_categories` sends it as a simple photo (store-name caption) the moment a store is selected. No image → unchanged.

**Admin management.** Store management view shows the PromptPay / menu-image / static-QR state and lets an admin set, replace, or clear each: photo uploads for the menu image and static QR; PromptPay id (validated: 10-digit phone or 13-digit national id) followed by the account name; `-` clears.

### Schema & files
- `Store`: + `menu_image_file_id`, `promptpay_id`, `promptpay_name`, `payment_qr_file_id` (all nullable). Migration `b3f2c4e8a1d7` (head; `add_column` only — Postgres + SQLite safe).
- New `bot/payments/store_payment.py`; modified `order_handler.py`, `store_selection.py`, `store_management.py`; 11 i18n keys × 7 locales.

### Tests (16 new)
- `tests/unit/payments/test_store_payment_card28.py` (7): resolver precedence matrix (store/brand/global), static-QR-only, menu-image getter, and QR payload encodes the store's id.
- `tests/integration/test_store_payment_routing.py` (3): end-to-end `process_receipt_photo` verifying the slip against store / brand / global accounts with auto-confirm.
- `tests/unit/handlers/test_store_assets_card28.py` (6): menu image sent only when set; admin set menu image, set/validate/reject/clear PromptPay.

### Notes / follow-ups
- Brand-level PromptPay (`Brand.promptpay_id`) is now honoured by the resolver — previously the order flow ignored it and only used the global setting.
- Static QR can't embed the amount; the caption instructs the customer to enter it manually (`order.payment.promptpay.static_amount_note`).
- Admin-facing strings follow the repo convention (translated `ru`, English placeholders in other non-English locales).
