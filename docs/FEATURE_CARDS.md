# Feature Cards — Status Board

> **Clear start (read first):** [`CLEAR-START.md`](CLEAR-START.md)  
> **Master archive (blurb · pitch · WIP · full doc index):** [`MASTER-DOCUMENT.md`](MASTER-DOCUMENT.md)  
> **Unified backend law:** [`Specifications/UNIFIED-BACKEND-CHANNEL-INTERFACE.md`](Specifications/UNIFIED-BACKEND-CHANNEL-INTERFACE.md)  
> **Multi-channel plan:** [`later/MULTI-CHANNEL-TIERED-PLAN.md`](later/MULTI-CHANNEL-TIERED-PLAN.md)  
> **Milestones:** [`MASTER-PLAN.md`](MASTER-PLAN.md) · **Growth narrative:** [`ROADMAP.md`](ROADMAP.md)  
> **Base repo:** multi-brand commerce + kitchen/delivery · Telegram = richest **adapter** today, not a special domain API  
> **North star:** White-label Brand + Branch sites + **one application service layer** for web, bots, forms, chatbox

Last board update: **2026-07-17** (post CARD-40 freeze · IG/LINE foundations · portal/funnel polish)

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

### BACKLOG (Open) — prioritized 2026-07-17

> **North star:** White-label Brand + Branch sites + one service layer (web, TG, LINE, IG, forms).  
> **Spine frozen:** CARD-40 A–F · adapters → services → domain.  
> **Do not** clone web leads into Telegram · **do not** put ops on IG/LINE.

#### P0 — Platform spine (near-complete; only leftovers)

| # | Card | Name | Progress | Effort left | Detail |
|---|------|------|----------|-------------|--------|
| — | **CARD-38** | White-Label Brand & Branch Sites | **~90%** A+B+C ✅ | polish | [later/CARD-38](later/CARD-38-white-label-brand-branch-sites.md) |
| — | **CARD-40** | Web↔TG Abstracted Parity | **~100% freeze** | none (law) | [CARD-40](later/CARD-40-web-telegram-abstracted-feature-parity.md) · [scorecard](later/CARD-40-parity-scorecard.md) |
| — | **CARD-32** | Customer Application Services | **~98%** | small leftovers | [later/CARD-32](later/CARD-32-customer-application-services.md) |
| — | CARD-29 / 30 / 31 | Messenger · Identities · Caps | **~95%** each | optional polish | later/CARD-29…31 |

#### P1 — Product surfaces (high value, mostly code-complete)

| # | Card | Name | Progress | Effort left | Detail |
|---|------|------|----------|-------------|--------|
| 1 | **CARD-39** | Web OAuth + Ticket Portal | **~90%** | **ops:** live Google OAuth env | [later/CARD-39](later/CARD-39-web-oauth-ticket-portal.md) |
| 2 | **CARD-36** | Web leads + meeting booking | **~90%** | optional CAPTCHA / TG opt-in | [later/CARD-36](later/CARD-36-instagram-web-telegram-funnel.md) |

#### P2 — Messaging channels (foundations landed; production depth open)

| # | Card | Name | Progress | Effort left | Detail |
|---|------|------|----------|-------------|--------|
| 3 | **CARD-33** | Instagram Messaging | **~55%** | QR host, slip, Redis, Meta review | [later/CARD-33](later/CARD-33-instagram-messaging-channel.md) · `bot/channels/instagram/` |
| 4 | **CARD-16** | LINE Messaging | **~55%** | Flex UI, QR host, Redis, multi-OA | [later/CARD-16](later/CARD-16-line-api-integration.md) · `bot/channels/line/` |
| 5 | CARD-34 | Conversation & Workflow Specs | 0% | 3–6d docs | [later/CARD-34](later/CARD-34-conversation-workflow-specifications.md) |
| 6 | CARD-35 | Storefront UI patterns | subsumed by 38C | — | [later/CARD-35](later/CARD-35-instagram-style-web-storefront.md) |

#### P3 — Parked / demo only

| # | Card | Name | Progress | Note | Detail |
|---|------|------|----------|------|--------|
| 7 | CARD-37 | SnusThai Hub Astro MVP | 0% | Vertical demo — **not** platform architecture | [later/CARD-37](later/CARD-37-snusthai-hub-astro-mvp.md) |

---

### Next Up (execute)

1. **Spine:** CARD-38/32/29–31/40 frozen or near-done.  
2. **Recommended next (pick one):**  
   - **A — Ship web auth:** live Google OAuth credentials + redirect (CARD-39 ops)  
   - **B — Finish one channel:** CARD-33 QR/slip/Redis **or** CARD-16 Flex/QR  
   - **C — Spec debt:** CARD-34 flow docs (gates clean multi-channel QA)  
3. IG + LINE stay **flag-off** until Meta/LINE credentials + depth polish.  
4. Smoke: `pytest tests/unit/channels/ tests/unit/platform/test_card40ef_nonparity.py -q --no-cov`

**Reject for “next PR”:** new business logic only in Telegram handlers · “parity” by cloning lead forms into Telegram · IG/LINE ops surfaces · skipping service + capability row for shared features.

---

### Restaurant Core & Feature suites (DONE)

Shipped as RC/FC suites (menu media, prep time, allergens, windows, multi-currency, import/export, modifier builder; search, reorder, coupons, reviews, invoice, tickets, accounting, segmentation, multi-store). Details historically in FEATURE_CARDS restaurant sections / done docs — treated as **done** for board purposes.

---

## Dependency graph (open work only)

```text
DONE: M0–M2 · CARD-19 · CARD-28 · CARD-38 A+B+C
        │
        ▼
UNIFIED BACKEND LAW + CARD-40 A–F freeze ✅
  (services · Messenger · identities · caps · parity scorecard)
        │
        ├─► CARD-39 live Google OAuth (ops)     ◄── recommended ship path
        ├─► CARD-36 optional CAPTCHA / opt-in
        │
        ├─► CARD-33 finish (QR · slip · Redis · Meta)
        ├─► CARD-16 finish (Flex · QR · Redis · multi-OA)
        └─► CARD-34 workflow specs (docs)
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
| [CARD-40-parity-scorecard.md](later/CARD-40-parity-scorecard.md) | **Parity freeze + PR gate** |
| [MULTI-CHANNEL-TIERED-PLAN.md](later/MULTI-CHANNEL-TIERED-PLAN.md) | Multi-channel tiers |
| [MASTER-PLAN.md](MASTER-PLAN.md) | Milestone history + M3 |
| [later/CARD-33-…](later/CARD-33-instagram-messaging-channel.md) | IG adapter |
| [later/CARD-16-…](later/CARD-16-line-api-integration.md) | LINE adapter |
| [later/CARD-39-…](later/CARD-39-web-oauth-ticket-portal.md) | Web ticket portal |
| [later/CARD-36-…](later/CARD-36-instagram-web-telegram-funnel.md) | Leads/booking funnel |
| [later/](later/) | Open cards |
| [done/](done/) | Completed cards |
| [Specifications/](Specifications/) | Deep specs |

---

## Historical note

Earlier M3 framing allowed Telegram handlers to call domain forever and prioritized IG DM first. **2026-07-16:** white-label web first. **2026-07-17:** unified application services are mandatory; Telegram is an adapter; frontends use capability masks. **FEATURE_CARDS + CLEAR-START + UNIFIED-BACKEND win on conflict.**
