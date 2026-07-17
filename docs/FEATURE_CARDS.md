# Feature Cards — Status Board

> **Clear start (read first):** [`CLEAR-START.md`](CLEAR-START.md)  
> **Master archive (blurb · pitch · WIP · full doc index):** [`MASTER-DOCUMENT.md`](MASTER-DOCUMENT.md)  
> **Unified backend law:** [`Specifications/UNIFIED-BACKEND-CHANNEL-INTERFACE.md`](Specifications/UNIFIED-BACKEND-CHANNEL-INTERFACE.md)  
> **Multi-channel plan:** [`later/MULTI-CHANNEL-TIERED-PLAN.md`](later/MULTI-CHANNEL-TIERED-PLAN.md)  
> **Milestones:** [`MASTER-PLAN.md`](MASTER-PLAN.md) · **Growth narrative:** [`ROADMAP.md`](ROADMAP.md)  
> **Base repo:** multi-brand commerce + kitchen/delivery · Telegram = richest **adapter** today, not a special domain API  
> **North star:** White-label Brand + Branch sites + **one application service layer** for web, bots, forms, chatbox

Last board update: **2026-07-17** (CARD-42 Google OAuth credentials runbook · storefront commerce ship · CARD-39 ops wiring · open = CARD-39 live secrets / 33 / 36 / 37)

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
| **CARD-29** | Messenger Port | M3 spine | [done/CARD-29](done/CARD-29-messenger-port.md) |
| **CARD-30** | User Identities Dual-Write | M3 spine | [done/CARD-30](done/CARD-30-user-identities.md) |
| **CARD-31** | Platform Capabilities & Masks | M3 spine | [done/CARD-31](done/CARD-31-platform-capabilities.md) |
| **CARD-32** | Customer Application Services | M3 spine | [done/CARD-32](done/CARD-32-customer-application-services.md) |
| **CARD-35** | IG-style storefront (patterns) | M3 | [done/CARD-35](done/CARD-35-instagram-style-web-storefront.md) — **superseded by CARD-38C** |
| **CARD-38** | White-Label Brand & Branch Sites | M3 spine | [done/CARD-38](done/CARD-38-white-label-brand-branch-sites.md) — A+B+C ✅ |
| **CARD-40** | Web↔TG Abstracted Parity | M3 spine | [done/CARD-40](done/CARD-40-web-telegram-abstracted-feature-parity.md) · [scorecard](done/CARD-40-parity-scorecard.md) · [matrix](done/CARD-40-parity-matrix.md) |
| **CARD-16** | LINE Messaging | M3 channel | [done/CARD-16](done/CARD-16-line-api-integration.md) — code done; ops credentials residual |
| **CARD-34** | Conversation & Workflow Specs | M3 docs | [done/CARD-34](done/CARD-34-conversation-workflow-specifications.md) |
| **CARD-41** | Physical Invite Cards + Brand A4 PDF | Feature | [done/CARD-41](done/CARD-41-physical-invite-cards-brand-pdf.md) — tear-off #↔code registry, deep-link QR, brand sheet |
| **CARD-42** | Google OAuth Credentials Runbook | Ops docs | [done/CARD-42](done/CARD-42-google-oauth-credentials-runbook.md) — where to get Client ID/secret · `.env` · Funnel verify |
| CARD-RC1–RC7 | Restaurant Core suite | RC | [see below](#restaurant-core--feature-suites-done) |
| CARD-FC1–FC9 | Feature suite | FC | [see below](#restaurant-core--feature-suites-done) |

**Milestones closed:** M0 Launch Gate ✅ · M1 Hardening ✅ · M2 Live Dispatch ✅ · **M3 platform spine** ✅ · **CARD-16/34** ✅

---

### BACKLOG (Open) — prioritized 2026-07-17

> **North star:** White-label Brand + Branch sites + one service layer (web, TG, LINE, IG, forms).  
> **Spine frozen and archived in `done/`:** CARD-29–32 · 35 · 38 · 40.  
> **Do not** clone web leads into Telegram · **do not** put ops on IG/LINE.

#### P1 — Product surfaces (code mostly done; ship/polish)

| # | Card | Name | Progress | Effort left | Detail |
|---|------|------|----------|-------------|--------|
| 1 | **CARD-39** | Web OAuth + Ticket Portal | **~95%** | **ops only:** paste live Google secrets (follow [CARD-42](done/CARD-42-google-oauth-credentials-runbook.md)) | [later/CARD-39](later/CARD-39-web-oauth-ticket-portal.md) |
| 2 | **CARD-36** | Web leads + meeting booking | **~90%** | optional CAPTCHA / TG opt-in | [later/CARD-36](later/CARD-36-instagram-web-telegram-funnel.md) |

#### P2 — Messaging channels (production depth)

| # | Card | Name | Progress | Effort left | Detail |
|---|------|------|----------|-------------|--------|
| 3 | **CARD-33** | Instagram Messaging | **~55%** | QR host, slip, Redis, Meta review | [later/CARD-33](later/CARD-33-instagram-messaging-channel.md) · `bot/channels/instagram/` · package [PACKAGE-instagram](Specifications/flows/PACKAGE-instagram.md) |

#### P3 — Parked / demo only

| # | Card | Name | Progress | Note | Detail |
|---|------|------|----------|------|--------|
| 4 | CARD-37 | SnusThai Hub Astro MVP | 0% | Vertical demo — **not** platform architecture | [later/CARD-37](later/CARD-37-snusthai-hub-astro-mvp.md) |

---

### Next Up (execute)

1. **Spine + LINE code + workflow specs are done** — do not re-open unless regression.  
2. **Recommended next (pick one):**  
   - **A — Live Google login:** create OAuth client per [CARD-42](done/CARD-42-google-oauth-credentials-runbook.md) → fill `.env` → restart bot (closes CARD-39 residual)  
   - **B — Finish Instagram:** CARD-33 QR/slip/Redis/Meta (use [PACKAGE-instagram](Specifications/flows/PACKAGE-instagram.md))  
   - **C — LINE go-live ops:** credentials + `PUBLIC_MEDIA_BASE_URL` HTTPS (code already in [done/CARD-16](done/CARD-16-line-api-integration.md))  
3. IG + LINE stay **flag-off** until provider credentials + public HTTPS for media.  
4. Smoke: `pytest tests/unit/channels/ tests/unit/platform/test_card40ef_nonparity.py -q --no-cov`

**Reject for “next PR”:** new business logic only in Telegram handlers · “parity” by cloning lead forms into Telegram · IG/LINE ops surfaces · skipping service + capability row for shared features.

---

### Restaurant Core & Feature suites (DONE)

Shipped as RC/FC suites (menu media, prep time, allergens, windows, multi-currency, import/export, modifier builder; search, reorder, coupons, reviews, invoice, tickets, accounting, segmentation, multi-store). Details historically in FEATURE_CARDS restaurant sections / done docs — treated as **done** for board purposes.

---

## Dependency graph (open work only)

```text
DONE: M0–M2 · spine 29–32/38/40 · CARD-16 LINE code · CARD-34 specs
        │
        ▼
UNIFIED BACKEND LAW (adapters → services → domain)
        │
        ├─► CARD-39 live Google OAuth (ops)     ◄── recommended ship path
        ├─► CARD-36 optional CAPTCHA / opt-in
        ├─► CARD-33 finish (QR · slip · Redis · Meta)
        └─► CARD-16 ops: live LINE tokens + public HTTPS QR base
                │
P3              ▼
            CARD-37 vertical demo (optional)
```

---

## Doc map

| Doc | Purpose |
|-----|---------|
| [MASTER-DOCUMENT.md](MASTER-DOCUMENT.md) | **Blurb · pitch · WIP archive · full index** |
| [CLEAR-START.md](CLEAR-START.md) | **Session bootstrap** |
| [UNIFIED-BACKEND-CHANNEL-INTERFACE.md](Specifications/UNIFIED-BACKEND-CHANNEL-INTERFACE.md) | **Backend law** |
| [CARD-40-parity-scorecard.md](done/CARD-40-parity-scorecard.md) | **Parity freeze + PR gate** |
| [MULTI-CHANNEL-TIERED-PLAN.md](later/MULTI-CHANNEL-TIERED-PLAN.md) | Multi-channel tiers |
| [MASTER-PLAN.md](MASTER-PLAN.md) | Milestone history + M3 open work |
| [later/CARD-33-…](later/CARD-33-instagram-messaging-channel.md) | IG adapter |
| [done/CARD-16](done/CARD-16-line-api-integration.md) | LINE adapter |
| [done/CARD-34](done/CARD-34-conversation-workflow-specifications.md) | Workflow specs |
| [Specifications/README.md](Specifications/README.md) | Flow catalog index |
| [later/CARD-39-…](later/CARD-39-web-oauth-ticket-portal.md) | Web ticket portal |
| [later/CARD-36-…](later/CARD-36-instagram-web-telegram-funnel.md) | Leads/booking funnel |
| [later/](later/) | Open cards only |
| [done/](done/) | Completed cards |
| [Specifications/](Specifications/) | Deep specs |
| [backlog/](backlog/) | Ops notes (not the status board) |

---

## Historical note

Earlier M3 framing allowed Telegram handlers to call domain forever and prioritized IG DM first. **2026-07-16:** white-label web first. **2026-07-17:** unified application services mandatory; Telegram is an adapter; CARD-40 A–F freeze; spine cards archived to `docs/done/`. **FEATURE_CARDS + CLEAR-START + UNIFIED-BACKEND win on conflict.**
