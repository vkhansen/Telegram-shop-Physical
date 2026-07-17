# Clear Start — Session Bootstrap

> **Open this file first in any new session.**  
> **Product blurb · pitch · full WIP archive · docs index:** [`MASTER-DOCUMENT.md`](MASTER-DOCUMENT.md)  
> **Last updated:** 2026-07-17 **SESSION SIGN-OFF**  
> **Resume file:** [`memory/session-2026-07-17-storefront-commerce-signoff.md`](../memory/session-2026-07-17-storefront-commerce-signoff.md)

---

## 0. Where we are (handoff)

| Area | Status |
|------|--------|
| **M0–M2** | Done (payments integrity, cart stub, dispatch) |
| **M3 spine** | **Archived in `docs/done/`** — CARD-29 · 30 · 31 · 32 · 35 · 38 · 40 |
| **CARD-38** white-label web | ✅ A+B+C — Astro storefront + public API + media |
| **Unified backend law** | Documented — adapters → services → domain |
| **CARD-32 services** | ✅ commerce + tickets + customer Grok tools on services |
| **CARD-29 Messenger** | ✅ customer status + crypto + inventory expire + ticket/AI pings via port |
| **CARD-30 Identities** | ✅ edge resolve; no TG↔web link UI (out of scope) |
| **CARD-31 Caps** | ✅ platform×role + default masks (`bot/platform/capabilities.py`) |
| **CARD-40 Web↔TG parity** | ✅ Tier A–F freeze — [scorecard](done/CARD-40-parity-scorecard.md) |
| **CARD-39 OAuth/tickets** | **~95%** — code + preflight done; **paste Google secrets** per [CARD-42](done/CARD-42-google-oauth-credentials-runbook.md) |
| **CARD-42 Google secrets** | **✅ runbook done** — where to get Client ID/secret · env · verify · [done/CARD-42](done/CARD-42-google-oauth-credentials-runbook.md) |
| **Storefront commerce** | **✅** cart/checkout/orders = TG C-08–C-17 via `commerce_api` · Playwright e2e |
| **CARD-36 funnel** | **~90% open** — leads/bookings + staff notify; optional CAPTCHA / TG opt-in |
| **CARD-33 Instagram** | **~55% open** — foundation in `bot/channels/instagram/`; Meta + slip polish · [PACKAGE-instagram](Specifications/flows/PACKAGE-instagram.md) |
| **CARD-16 LINE** | **✅ code done** — Flex/QR host/Redis/multi-OA; **ops:** live tokens + HTTPS media base · [done/CARD-16](done/CARD-16-line-api-integration.md) |
| **CARD-34 specs** | **✅ done** — flows C-01–C-24 + cross-cutting + IG/LINE packages · [done/CARD-34](done/CARD-34-conversation-workflow-specifications.md) |
| **Next slice** | **Paste Google secrets** ([CARD-42](done/CARD-42-google-oauth-credentials-runbook.md)) · or CARD-33 · or LINE go-live |
| **Git** | `master` @ `0d6fe8e` pushed to `origin` |
| **Runtime** | **Docker + Tailscale Funnel only** — not local :9090/:4321 |
| **Funnel URL** | https://telegram-shop-1.tail31319c.ts.net/ · demo `/snus-demo` |

**Do not re-litigate:** hybrid content model, commerce modes, age gate from DB, Telegram-as-adapter (not special domain), web lead forms into Telegram “for parity,” reopening spine cards without a regression.

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
**Parity freeze:** [`done/CARD-40-parity-scorecard.md`](done/CARD-40-parity-scorecard.md)

---

## 2. Architecture (current)

```text
PostgreSQL  Brand · Store · Goods · Orders · web_profile · identities
                    │
                    ▼
         Application services
    catalog_public · leads_bookings · web_auth
    cart · checkout · order_query · tickets · customer_catalog
    tickets_web = thin facade → tickets
    platform: capabilities · deep_links · media_ref · messaging · messenger_router · identity
    Grok tools = masked adapter → same services
                    │
     ┌──────────────┼──────────────┬────────────────┐
     ▼              ▼              ▼                ▼
 Public API    Telegram     Instagram DM         (LINE later)
 storefront    handlers     channels/instagram   webhooks
               + Grok AI    (flag-gated)
```

### Code map (know these paths)

| Path | Role |
|------|------|
| `bot/services/dto.py` | `ServiceResult` |
| `bot/services/cart.py` | Cart list/add/remove/clear |
| `bot/services/checkout.py` | `create_pending_order`, cash/PromptPay/crypto, QR, `ensure_delivery_profile` |
| `bot/services/order_query.py` | List/get orders as DTOs |
| `bot/services/tickets.py` | **Single ticket writer** — list/get/create/reply/close/append |
| `bot/services/tickets_web.py` | HTTP facade → `tickets` (legacy dict API for auth_api) |
| `bot/services/customer_catalog.py` | Grok/assistant catalog browse, specials, deals, nearby, coupon check |
| `bot/ai/customer_executor.py` | Tool dispatch → services (not raw ticket/order ORM) |
| `bot/ai/customer_tool_defs.py` | `tools_for_channel` / `tools_for_capabilities` (mask filter) |
| `bot/platform/capabilities.py` | Caps + `WEB_ONLY_CAPS` / `TG_OPS_CAPS` / `SHARED_PARITY_CAPS` |
| `bot/platform/deep_links.py` | TG → web funnel URL buttons (no form FSM) |
| `bot/platform/messenger_router.py` | Multi-channel customer `notify_user` |
| `bot/channels/instagram/` | CARD-33 IG webhook + adapter + Messenger |
| `bot/channels/line/` | CARD-16 LINE webhook + adapter + Messenger |
| `bot/web/commerce_api.py` | **Web commerce adapter** — cart/checkout/orders (session cookie) |
| `bot/web/auth_api.py` | OAuth session + tickets/leads/bookings (cap-gated) |
| `bot/web/public_api.py` | Catalog + media + mounts auth + commerce |
| `bot/handlers/user/cart_handler.py` | TG cart → **cart service** |
| `bot/handlers/user/order_handler.py` | TG payments → **checkout service** |
| `bot/handlers/user/ticket_handler.py` | TG tickets → **tickets service** (FSM UI only) |
| `bot/handlers/user/grok_customer.py` | Customer AI adapter — masked tools + Messenger |
| `bot/platform/messaging.py` | `Messenger` / `get_messenger` |
| `bot/platform/identity.py` | `resolve_user_id` / `link_identity` / `ensure_telegram_identity` |
| `apps/storefront` | BrandShell + cart/checkout/orders (parity with TG C-08–C-17 via commerce_api) |
| `docs/done/CARD-40-parity-matrix.md` | Shared vs web-only vs tg-ops table |
| `docs/done/CARD-40-parity-scorecard.md` | **F freeze** checklist + PR gate |
| `docs/Specifications/UNIFIED-BACKEND-CHANNEL-INTERFACE.md` | Law R1–R8 |

---

## 3. Run (Docker preferred)

```powershell
# Production-like stack (Funnel)
docker compose up -d --build
docker compose ps
docker compose logs -f bot

# Full stop
docker compose down
```

**Live site (when up):** https://telegram-shop-1.tail31319c.ts.net/snus-demo  

```powershell
# Local dev only (do not mix with Docker on same ports)
# python scripts/run_public_api.py   → :9090
# cd apps/storefront && npm run dev  → :4321/snus-demo
# SEED_SNUS_COMMERCE_MODE=full_store for cart/checkout on snus-demo
```

```powershell
# Tests
.\.venv\Scripts\python.exe -m pytest tests/unit/services/test_order_flow_parity.py tests/unit/services/test_commerce_http_parity.py -q --no-cov
.\.venv\Scripts\python.exe -m pytest tests/unit/platform/test_card40ef_nonparity.py tests/unit/services/test_commerce_parity_card40b.py -q --no-cov
# Playwright (API + storefront must be up): cd apps/storefront && npm run test:e2e
```

### Web commerce auth (any frontend)

- Session cookie: `wl_session` (from Google OAuth or `POST /api/public/auth/dev-login` when enabled)
- Cart/checkout/orders require cookie + credentials; gated by brand `capabilities` (`checkout` off → 403)
- **Not** a second order writer — same `cart` / `checkout` / `order_query` as Telegram
- Tickets: same `services.tickets` as TG; session `uid` is internal user_id
- Leads/bookings: cap-gated (`leads` / `booking`); ops role claims → 403

---

## 4. Migration checklist (CARD-32 / CARD-40)

### Done (commerce + support + AI + freeze)

- [x] `ServiceResult` DTO  
- [x] `cart` / `checkout` / `order_query` services  
- [x] Telegram payments + cart → services  
- [x] Web commerce API (CARD-40 B)  
- [x] **CARD-40 Tier C** — `services/tickets` single writer; TG `ticket_handler` + `tickets_web` facade  
- [x] Customer order-status / crypto / inventory-expire / ticket reply pings → `get_messenger()`  
- [x] Auth mask: web OAuth ON, TG `auth` OFF (no fake OAuth in bot)  
- [x] Tests: `test_tickets_parity_card40c.py`  
- [x] **CARD-40 Tier D** — Grok tools → services + capability masks + Messenger  
- [x] Tests: `test_customer_card40d.py`  
- [x] **CARD-40 Tier E** — web-only + TG-ops packs + deep_links + API enforcement  
- [x] **CARD-40 Tier F** — scorecard + PR template + machine freeze tests  
- [x] Tests: `test_card40ef_nonparity.py`  

### Next migration slices (pick one per session)

1. **CARD-39 ops** — live Google OAuth client + redirect on deploy (portal already polished)  
2. **CARD-33 or CARD-16 finish** — hosted QR / Flex UI / Redis sessions / multi-brand map  
3. **CARD-34** conversation workflow specs (docs; QA independence)  
4. Optional: CARD-36 CAPTCHA / signed TG opt-in  

**Hard gates (met):** TG + web commerce + tickets on services; Grok as masked adapter; Messenger; identities; CARD-31; **CARD-40 A–F freeze**; IG + LINE foundations (flag-off).

### Tier E+F exit (done)

- [x] **E1** Web-only pack off TG by default (`WEB_ONLY_CAPS` + `CHANNEL_DEFAULT_OFF`)  
- [x] **E2** Deep-link policy (`bot/platform/deep_links.py`) — URL buttons only  
- [x] **E3** TG-ops pack documented (`TG_OPS_CAPS`); web ceiling excludes ops  
- [x] **E4** No TG lead/book FSM; API rejects ops impersonation; leads/booking cap-gated  
- [x] **F** Scorecard + PR gate freeze  

---

## 5. Session checklist

- [ ] Read this file + UNIFIED-BACKEND law + [parity scorecard](done/CARD-40-parity-scorecard.md)  
- [ ] Prefer ship path (OAuth ops / one channel finish / specs) — not re-opening parity  
- [ ] New code: adapter → service only; new caps need matrix row  
- [ ] Run targeted pytest for touched services  
- [ ] Keep Telegram UX unchanged when migrating  
- [ ] Local run: `docker compose up -d` only when needed; stop when done  

---

## 6. Doc index

| Doc | Role |
|-----|------|
| **This file** | Bootstrap / handoff |
| [FEATURE_CARDS](FEATURE_CARDS.md) | **Status board** |
| [MASTER-DOCUMENT](MASTER-DOCUMENT.md) | Blurb · pitch · WIP archive · full index |
| [UNIFIED-BACKEND-CHANNEL-INTERFACE](Specifications/UNIFIED-BACKEND-CHANNEL-INTERFACE.md) | Backend law |
| [MULTI-CHANNEL-TIERED-PLAN](later/MULTI-CHANNEL-TIERED-PLAN.md) | Tiers |
| [CARD-40](done/CARD-40-web-telegram-abstracted-feature-parity.md) | Web↔TG abstracted parity ✅ |
| [CARD-40 scorecard](done/CARD-40-parity-scorecard.md) | **F freeze** + PR gate |
| [CARD-40 matrix](done/CARD-40-parity-matrix.md) | Capability × adapter table |
| [CARD-32](done/CARD-32-customer-application-services.md) | Customer services epic ✅ |
| [CARD-38](done/CARD-38-white-label-brand-branch-sites.md) | Web shell ✅ |
| [CARD-33](later/CARD-33-instagram-messaging-channel.md) | IG adapter (open) |
| [CARD-16](done/CARD-16-line-api-integration.md) | LINE adapter ✅ (ops residual) |
| [CARD-34](done/CARD-34-conversation-workflow-specifications.md) | Workflow specs ✅ |
| [Spec flows index](Specifications/README.md) | CARD-34 flow catalog |
| [CARD-39](later/CARD-39-web-oauth-ticket-portal.md) | Web ticket portal (open) |
| [CARD-36](later/CARD-36-instagram-web-telegram-funnel.md) | Leads/booking funnel (open) |
| [MASTER-PLAN](MASTER-PLAN.md) | Milestones |
| Claude.md | Commands + architecture notes |

---

## 7. Ready statement

**Session signed off. Spine frozen. CARD-16 code + CARD-34 specs archived. Board is truth.**

| Flag (default off) | Webhook |
|--------------------|---------|
| `INSTAGRAM_CHANNEL_ENABLED` | `/webhooks/instagram` |
| `LINE_CHANNEL_ENABLED` | `/webhooks/line` |

Smoke:

```bash
pytest tests/unit/channels/test_line_card16.py tests/unit/platform/test_card40ef_nonparity.py -q --no-cov
```

Say next (recommended order):

1. *“Live Google OAuth deploy (CARD-39 ops).”*  
2. *“CARD-33 finish QR/slip/Redis/Meta.”* (use PACKAGE-instagram)  
3. *“LINE go-live ops”* (tokens + `PUBLIC_MEDIA_BASE_URL` HTTPS — code already done)
