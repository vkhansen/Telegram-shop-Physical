# Clear Start — Session Bootstrap

> **Open this file first in any new session.**  
> **Product blurb · pitch · full WIP archive · docs index:** [`MASTER-DOCUMENT.md`](MASTER-DOCUMENT.md)  
> **Last updated:** 2026-07-17 (CARD-40 Tier B commerce spine)

---

## 0. Where we are (handoff)

| Area | Status |
|------|--------|
| **M0–M2** | Done (payments integrity, cart stub, dispatch) |
| **CARD-38** white-label web | A+B+C done — Astro storefront + public API + media |
| **Unified backend law** | Documented — adapters → services → domain |
| **CARD-32 migration** | **~95%** — TG + web commerce on cart/checkout/order_query |
| **CARD-29 Messenger** | **~90%** — `TelegramMessenger` + notifications via port |
| **CARD-30 Identities** | **~90%** — TG dual-write + backfill + resolve/link helpers |
| **CARD-31 Caps** | **~95%** — platform×role + default masks (`bot/platform/capabilities.py`) |
| **CARD-40 Web↔TG parity** | **~35%** — Tier A+B ✅ (matrix + web commerce API); C–F open |
| **Next slice** | **CARD-40 Tier C** — tickets unify + Messenger status + identity edge |

**Do not re-litigate:** hybrid content model, commerce modes, age gate from DB, Telegram-as-adapter (not special domain).

---

## 1. North star

```text
One domain · many adapters (Telegram, web, forms, LINE, chatbox)
Frontends implement capability MASKS
Backend features are STANDARDIZED services
No new handler → domain business shortcuts
```

**Binding law:** [`Specifications/UNIFIED-BACKEND-CHANNEL-INTERFACE.md`](Specifications/UNIFIED-BACKEND-CHANNEL-INTERFACE.md)  
**Plan:** [`later/MULTI-CHANNEL-TIERED-PLAN.md`](later/MULTI-CHANNEL-TIERED-PLAN.md)  
**Board:** [`FEATURE_CARDS.md`](FEATURE_CARDS.md)

---

## 2. Architecture (current)

```text
PostgreSQL  Brand · Store · Goods · Orders · web_profile · identities
                    │
                    ▼
         Application services
    catalog_public · leads_bookings · tickets_web · web_auth
    cart · checkout · order_query          ◄── CARD-32 (new)
    platform: capabilities · media_ref · messaging
                    │
     ┌──────────────┼──────────────┐
     ▼              ▼              ▼
 Public API    Telegram        (LINE/IG later)
 storefront    handlers        webhooks
               (thin adapters)
```

### Code map (know these paths)

| Path | Role |
|------|------|
| `bot/services/dto.py` | `ServiceResult` |
| `bot/services/cart.py` | Cart list/add/remove/clear |
| `bot/services/checkout.py` | `create_pending_order`, cash/PromptPay/crypto, QR, `ensure_delivery_profile` |
| `bot/services/order_query.py` | List/get orders as DTOs |
| `bot/services/tickets_web.py` | Web tickets (Tier C: unify with TG `ticket_handler`) |
| `bot/platform/capabilities.py` | `CAPABILITY_KEYS`, `PLATFORM_CAPS`×role, `CHANNEL_DEFAULT_OFF`, `resolve_capabilities` / `can` |
| `bot/web/commerce_api.py` | **Web commerce adapter** — cart/checkout/orders (session cookie) |
| `bot/web/auth_api.py` | OAuth session + tickets/leads HTTP |
| `bot/web/public_api.py` | Catalog + media + mounts auth + commerce |
| `bot/handlers/user/cart_handler.py` | TG cart → **cart service** |
| `bot/handlers/user/order_handler.py` | TG payments → **checkout service** |
| `bot/handlers/user/ticket_handler.py` | TG tickets still domain-heavy → **Tier C target** |
| `bot/handlers/user/grok_customer.py` | Customer AI → **Tier D target** |
| `bot/platform/messaging.py` | `Messenger` / `get_messenger` |
| `bot/platform/identity.py` | `resolve_user_id` / `link_identity` / `ensure_telegram_identity` |
| `apps/storefront` | BrandShell + capability-gated UI (cart UI may lag API) |
| `docs/later/CARD-40-parity-matrix.md` | Shared vs web-only vs tg-ops table |
| `docs/Specifications/UNIFIED-BACKEND-CHANNEL-INTERFACE.md` | Law R1–R8 |

---

## 3. Local run

```bash
# API (SQLite demo + snus seed)
# SEED_SNUS_FORCE=1 optional
python scripts/run_public_api.py
# → http://127.0.0.1:9090

cd apps/storefront
# PUBLIC_API_BASE=http://127.0.0.1:9090
npm run dev -- --host 127.0.0.1 --port 4321
# → http://127.0.0.1:4321/snus-demo
```

```bash
# Prefer venv on Windows
.\.venv\Scripts\python.exe -m pytest tests/unit/services/test_commerce_parity_card40b.py tests/unit/services/test_checkout_service.py tests/unit/platform/ -q --no-cov
.\.venv\Scripts\python.exe -m pytest tests/unit/services/ -q --no-cov
```

### Web commerce auth (any frontend)

- Session cookie: `wl_session` (from Google OAuth or `POST /api/public/auth/dev-login` when enabled)
- Cart/checkout/orders require cookie + credentials; gated by brand `capabilities` (`checkout` off → 403)
- **Not** a second order writer — same `cart` / `checkout` / `order_query` as Telegram

---

## 4. Migration checklist (CARD-32)

### Done this wave

- [x] `ServiceResult` DTO  
- [x] `cart` / `checkout` / `order_query` services  
- [x] Telegram **PromptPay** → `checkout.start_promptpay_order`  
- [x] Telegram **cash** → `checkout.start_cash_order`  
- [x] Telegram **crypto** → `checkout.start_crypto_order` (legacy BTC + LTC/SOL/USDT + CryptoPayment)  
- [x] Telegram **cart_handler** → `cart` service (list/add/remove/clear; no domain cart methods)  
- [x] Unit tests: `tests/unit/services/test_checkout_service.py` (cart + checkout)  
- [x] Unified interface + multi-channel plan docs  
- [x] **CARD-32 TG commerce hard paths cleared** (cart + all payments)  

### Next migration slices (pick one per session)

1. **CARD-40 Tier C** (~1–2d) — tickets unify + Messenger customer status + identity edge  
2. **CARD-40 Tier D** (~2–3d) — customer Grok tools → services + masks  
3. **CARD-40 Tier E+F** (~2–3d) — intentional non-parity harden + scorecard/PR gate  
4. **Only then** CARD-33 / CARD-16 (second channel)  

**Hard gates (met):** TG + web commerce on services; Messenger; identities; CARD-31; CARD-40 A+B.  
**Next gates:** CARD-40 C (tickets/notify) then D (Grok) before second channel.

### Tier C task checklist (next session)

- [ ] **C1** Extract/share tickets application service; TG `ticket_handler` → service (web already `tickets_web`)  
- [ ] **C2** Document/identity edge only — web OAuth + TG dual-write; no fake OAuth in bot  
- [ ] **C3** Grep remaining customer order-status pings → `get_messenger()`  
- [ ] **C4** Auth mask honesty (web OAuth vs TG identity)  
- [ ] Tests: ticket create/list parity for same `user_id`; no dual ticket writers

---

## 5. Session checklist

- [ ] Read this file + UNIFIED-BACKEND law  
- [ ] Prefer **CARD-40 Tier C tickets + Messenger** next  
- [ ] New code: adapter → service only  
- [ ] Run targeted pytest for touched services  
- [ ] Keep Telegram UX unchanged when migrating  

---

## 6. Doc index

| Doc | Role |
|-----|------|
| **This file** | Bootstrap / handoff |
| [UNIFIED-BACKEND-CHANNEL-INTERFACE](Specifications/UNIFIED-BACKEND-CHANNEL-INTERFACE.md) | Backend law |
| [MULTI-CHANNEL-TIERED-PLAN](later/MULTI-CHANNEL-TIERED-PLAN.md) | Tiers |
| [CARD-32](later/CARD-32-customer-application-services.md) | Customer services epic |
| [CARD-40](later/CARD-40-web-telegram-abstracted-feature-parity.md) | Web↔TG abstracted parity (masks) |
| [CARD-40 parity matrix](later/CARD-40-parity-matrix.md) | Tier A capability × adapter table |
| [CARD-29](later/CARD-29-messenger-port.md) | Messenger |
| [CARD-38](later/CARD-38-white-label-brand-branch-sites.md) | Web shell (done) |
| [FEATURE_CARDS](FEATURE_CARDS.md) | Status board |
| [MASTER-PLAN](MASTER-PLAN.md) | Milestones |
| Claude.md | Commands + architecture notes |

---

## 7. Ready statement

**Context is clear for a clean continue.**

Say next: *“CARD-40 Tier C tickets and Messenger.”*
