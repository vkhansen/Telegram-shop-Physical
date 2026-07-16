# Feature Cards — Status Board

> **Clear start (read first):** [`CLEAR-START.md`](CLEAR-START.md)  
> **Master archive (blurb · pitch · WIP · full doc index):** [`MASTER-DOCUMENT.md`](MASTER-DOCUMENT.md)  
> **Unified backend law:** [`Specifications/UNIFIED-BACKEND-CHANNEL-INTERFACE.md`](Specifications/UNIFIED-BACKEND-CHANNEL-INTERFACE.md)  
> **Multi-channel plan:** [`later/MULTI-CHANNEL-TIERED-PLAN.md`](later/MULTI-CHANNEL-TIERED-PLAN.md)  
> **Milestones:** [`MASTER-PLAN.md`](MASTER-PLAN.md) · **Growth narrative:** [`ROADMAP.md`](ROADMAP.md)  
> **Base repo:** multi-brand commerce + kitchen/delivery · Telegram = richest **adapter** today, not a special domain API  
> **North star:** White-label Brand + Branch sites + **one application service layer** for web, bots, forms, chatbox

Last board update: **2026-07-17**

---

## Status Board

### DONE

All of the following live under [`docs/done/`](done/). Do not re-open unless regression.

| Card | Name | Phase | Detail |
|------|------|-------|--------|
| CARD-01 | PromptPay QR Payment | Phase 1 | [done/CARD-01](done/CARD-01-promptpay-qr-payment.md) |
| CARD-02 | GPS Delivery Address | Phase 1 | [done/CARD-02](done/CARD-02-gps-delivery-address.md) |
| CARD-03 | Dead Drop Delivery | Phase 1 | [done/CARD-03](done/CARD-03-dead-drop-delivery.md) |
| CARD-04 | Photo Proof of Delivery | Phase 1 | [done/CARD-04](done/CARD-04-photo-proof-delivery.md) |
| CARD-05 | Thai Language i18n | Phase 2 | [done/CARD-05](done/CARD-05-thai-language-i18n.md) |
| CARD-06 | THB Currency | Phase 2 | [done/CARD-06](done/CARD-06-thb-currency.md) |
| CARD-07 | Thai Address Format | Phase 2 | [done/CARD-07](done/CARD-07-thai-address-format.md) |
| CARD-08 | Menu Modifiers | Phase 3 | [done/CARD-08](done/CARD-08-menu-modifiers.md) |
| CARD-09 | Kitchen & Delivery Workflow | Phase 3 | [done/CARD-09](done/CARD-09-kitchen-delivery-workflow.md) |
| CARD-10 | Delivery Zones & Timeslots | Phase 3 | [done/CARD-10](done/CARD-10-delivery-zones-timeslots.md) |
| CARD-11 | COD Thai Localization | Phase 3 | [done/CARD-11](done/CARD-11-cod-thai-localization.md) |
| CARD-12 | Timezone Bangkok | Phase 3 | [done/CARD-12](done/CARD-12-timezone-bangkok.md) |
| CARD-13 | Driver Chat + Live Location | Phase 3 | [done/CARD-13](done/CARD-13-driver-chat-live-location.md) |
| CARD-14 | Language Picker | Phase 3 | [done/CARD-14](done/CARD-14-language-picker.md) |
| CARD-15 | GPS Live Tracking & Delivery Chat | Phase 3 | [done/CARD-15](done/CARD-15-gps-live-tracking-delivery-chat.md) |
| CARD-17 | Grok AI Admin Assistant | Phase 5 | [done/CARD-17](done/CARD-17-grok-admin-assistant.md) |
| CARD-18 | Multi-Crypto Payments | Phase 2 | [done/CARD-18](done/CARD-18-crypto-payment-verification.md) |
| CARD-19 | Multi-Brand Bot Coordination | Phase 4 | [done/CARD-19](done/CARD-19-multi-brand-bot-coordination.md) |
| CARD-21 | Persistent Cart Stub + Brand/Store Switch | M1 | [done/CARD-21](done/CARD-21-persistent-cart-stub.md) |
| CARD-22 | Grok AI Customer Assistant | Phase 5 | [done/CARD-22](done/CARD-22-grok-customer-assistant.md) |
| CARD-23 | Payment Session Refactor | M0 | [done/CARD-23](done/CARD-23-payment-session-refactor.md) |
| CARD-24 | Payment Integrity | M0 | [done/CARD-24](done/CARD-24-payment-integrity.md) |
| CARD-25 | Test Suite Recovery | M0 | [done/CARD-25](done/CARD-25-test-suite-recovery.md) |
| CARD-26 | Live GPS Driver Matching | M2 | [done/CARD-26](done/CARD-26-live-gps-driver-matching.md) |
| CARD-27 | Input Validation Hardening | M1 | [done/CARD-27](done/CARD-27-input-hardening.md) |
| CARD-28 | Per-Store Menu Image + Payment QR | Feature | [done/CARD-28](done/CARD-28-per-store-menu-image-and-payment-qr.md) |
| CARD-RC1–RC7 | Restaurant Core suite | RC | [see below](#restaurant-core--feature-suites-done) |
| CARD-FC1–FC9 | Feature suite | FC | [see below](#restaurant-core--feature-suites-done) |

**Milestones closed:** M0 Launch Gate ✅ · M1 Hardening ✅ · M2 Live Dispatch ✅  

---

### BACKLOG (Open) — prioritized 2026-07-16

> **North star:** White-label Brand + Branch auto-sites from backend (any vertical).  
> **Do not start** with single-vertical marketing sites (CARD-37) or IG DMs (CARD-33) as the main path.

#### P0 — Next (start here)

| # | Card | Name | Progress | Effort | Detail |
|---|------|------|----------|--------|--------|
| **1** | **CARD-38** | **White-Label Brand & Branch Auto-Sites** | ~90% (A+B+C done) | High | [later/CARD-38](later/CARD-38-white-label-brand-branch-sites.md) · `apps/storefront` |

Phases: **A ✅** API · **B ✅** media proxy · **C ✅** Astro shell (desktop+mobile). Forms API → CARD-36.
**Build contract:** [WHITE-LABEL-ASTRO-IMPLEMENTATION.md](Specifications/WHITE-LABEL-ASTRO-IMPLEMENTATION.md) · **Bootstrap:** [CLEAR-START.md](CLEAR-START.md)

#### P1 — Unified backend foundation (**priority after 38**)

> **Law:** adapters → services → domain. No new Telegram→domain business paths.  
> Frontends implement **masks**; backend features are **standard services**.

| # | Card | Name | Progress | Effort | Detail |
|---|------|------|----------|--------|--------|
| 2 | **CARD-39** | **Web OAuth + Ticket Portal** | ~50% | Med–High | [later/CARD-39](later/CARD-39-web-oauth-ticket-portal.md) · [spec](Specifications/WHITE-LABEL-OAUTH-TICKETS.md) |
| 3 | **CARD-32** | **Customer Application Services** | **~95%** (TG + web commerce on services; tickets polish optional) | 2–4d | [later/CARD-32](later/CARD-32-customer-application-services.md) · **critical** |
| 4 | CARD-29 | Messenger Port | ~90% (TelegramMessenger + notifications wired; optional broadcast/dispatch) | 1–2d | [later/CARD-29](later/CARD-29-messenger-port.md) |
| 5 | CARD-30 | User Identities Dual-Write | ~90% (table + TG dual-write + backfill + resolve; link UI out) | 1–2d | [later/CARD-30](later/CARD-30-user-identities.md) |
| 6 | CARD-31 | Platform Capabilities & Feature Mask | **~95%** (`PLATFORM_CAPS`×`ROLE_FEATURES` + resolve + tests) | done-ish | [later/CARD-31](later/CARD-31-platform-capabilities.md) · code: `bot/platform/capabilities.py` |
| 7 | **CARD-40** | **Web ↔ Telegram Abstracted Feature Parity** | **~35%** (Tier A+B ✅; C–F open) | High / tiered | [later/CARD-40](later/CARD-40-web-telegram-abstracted-feature-parity.md) · [parity matrix](later/CARD-40-parity-matrix.md) |

#### P2 — Conversion & channels (after catalog tenants work)

| # | Card | Name | Progress | Effort | Detail |
|---|------|------|----------|--------|--------|
| 8 | CARD-35 | Web storefront UI patterns (gallery/theme) | subsumed by 38C | — | [later/CARD-35](later/CARD-35-instagram-style-web-storefront.md) |
| 9 | CARD-36 | Web leads + **meeting booking** | ~70% | polish | [later/CARD-36](later/CARD-36-instagram-web-telegram-funnel.md) |
| 10 | CARD-34 | Conversation & Workflow Specs | 0% | 3–6d | [later/CARD-34](later/CARD-34-conversation-workflow-specifications.md) |
| 11 | CARD-33 | Instagram Messaging Channel | 0% | 5–8d | [later/CARD-33](later/CARD-33-instagram-messaging-channel.md) |
| 12 | CARD-16 | LINE API Integration | 0% | 5–8d | [later/CARD-16](later/CARD-16-line-api-integration.md) |

#### P3 — Parked / demo only

| # | Card | Name | Progress | Note | Detail |
|---|------|------|----------|------|--------|
| 11 | CARD-37 | SnusThai Hub Astro MVP | 0% | Vertical demo theme — **not** platform architecture | [later/CARD-37](later/CARD-37-snusthai-hub-astro-mvp.md) |

---

### Next Up (execute)

1. **CARD-38 ✅** · **CARD-32 ~95%** · **CARD-29 ~90%** · **CARD-30 ~90%** · **CARD-31 ~95%** · **CARD-40 A+B ✅**.  
2. **Next:** **CARD-40 Tier C** — tickets unify + Messenger customer status + identity edge.  
3. CARD-40 = abstracted web↔TG parity; web-only leads/booking stay masked off Telegram by default.  
4. Run: `pytest tests/unit/services/test_commerce_parity_card40b.py tests/unit/platform/ -q --no-cov`  

**Reject for “next PR”:** new business logic only in Telegram handlers · second channel before CARD-40 C/D freeze · “parity” by cloning lead forms into Telegram.

---

### Restaurant Core & Feature suites (DONE)

Shipped as RC/FC suites (menu media, prep time, allergens, windows, multi-currency, import/export, modifier builder; search, reorder, coupons, reviews, invoice, tickets, accounting, segmentation, multi-store). Details historically in FEATURE_CARDS restaurant sections / done docs — treated as **done** for board purposes.

---

## Dependency graph (open work only)

```text
DONE: M0–M2 · CARD-19 · CARD-28 · CARD-38 A+B+C (web adapter)
        │
        ▼
   UNIFIED BACKEND LAW (Specifications/UNIFIED-BACKEND-CHANNEL-INTERFACE)
        │
        ▼
P1  CARD-32 Customer services  ◀── migrate TG handlers off domain
        │
        ├─ CARD-29 Messenger port
        ├─ CARD-30 Identities
        └─ CARD-31 Caps (extend bot/platform)
        │
        ▼
    CARD-40 Web↔TG abstracted parity (T1.5)
        │  shared services; leads/booking = web-only mask
        ▼
P2  CARD-36 polish · CARD-34 specs · CARD-33 IG · CARD-16 LINE
        │     (second channel only on services + masks + 40 spine)
P3  CARD-37 vertical demo (optional)
```

---

## Doc map

| Doc | Purpose |
|-----|---------|
| [MASTER-DOCUMENT.md](MASTER-DOCUMENT.md) | **Blurb · pitch · WIP archive · full index** |
| [CLEAR-START.md](CLEAR-START.md) | **Session bootstrap** |
| [UNIFIED-BACKEND-CHANNEL-INTERFACE.md](Specifications/UNIFIED-BACKEND-CHANNEL-INTERFACE.md) | **Backend law** |
| [MULTI-CHANNEL-TIERED-PLAN.md](later/MULTI-CHANNEL-TIERED-PLAN.md) | Multi-channel tiers |
| [MASTER-PLAN.md](MASTER-PLAN.md) | Milestone history + M3 |
| [later/CARD-38-…](later/CARD-38-white-label-brand-branch-sites.md) | Web epic |
| [later/CARD-32-…](later/CARD-32-customer-application-services.md) | Service extract |
| [later/CARD-40-…](later/CARD-40-web-telegram-abstracted-feature-parity.md) | Web↔TG abstracted parity |
| [later/](later/) | Open cards |
| [done/](done/) | Completed cards |
| [Specifications/](Specifications/) | Deep specs |

---

## Historical note

Earlier M3 framing allowed Telegram handlers to call domain forever and prioritized IG DM first. **2026-07-16:** white-label web first. **2026-07-17:** unified application services are mandatory; Telegram is an adapter; frontends use capability masks. **FEATURE_CARDS + CLEAR-START + UNIFIED-BACKEND win on conflict.**
