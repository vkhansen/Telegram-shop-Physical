# Master Document — Product, Pitch, WIP & Docs Index

> **This is the archive hub for product positioning, work-in-progress status, and the full documentation map.**  
> **Session bootstrap (day-to-day code work):** [`CLEAR-START.md`](CLEAR-START.md)  
> **Live status board:** [`FEATURE_CARDS.md`](FEATURE_CARDS.md)  
> **Sequencing / milestones:** [`MASTER-PLAN.md`](MASTER-PLAN.md)  
> **Backend law:** [`Specifications/UNIFIED-BACKEND-CHANNEL-INTERFACE.md`](Specifications/UNIFIED-BACKEND-CHANNEL-INTERFACE.md)

**Last archived:** 2026-07-17  
**Repo:** Telegram-shop-Physical (multi-brand conversational commerce + kitchen/delivery)

---

## Table of contents

1. [Blurb](#1-blurb)
2. [Pitch](#2-pitch)
3. [Product positioning (accurate scope)](#3-product-positioning-accurate-scope)
4. [Work-in-progress summary](#4-work-in-progress-summary)
5. [Architecture snapshot](#5-architecture-snapshot)
6. [Documentation index](#6-documentation-index)
7. [How to use this archive](#7-how-to-use-this-archive)

---

## 1. Blurb

### One-liner

A multi-channel, LLM-powered commerce platform: brands sell and operate through chat (Telegram first, web and social next), with Grok agents for natural-language shopping and ops—all on one multi-brand backend.

### Elevator (≈25 words)

Chat-native commerce OS for food and physical goods. Customers and staff talk to the business; dual Grok assistants turn language into actions; one backend powers Telegram, Instagram-style web, and future messengers.

### Short (≈50 words)

**[Platform]** is a multi-tenant conversational commerce system. Customers discover brands on social-style web storefronts or messaging apps, then complete menu, cart, payment, GPS delivery, and support in conversation. Grok customer and admin assistants sit on shared services. Telegram is the high-fidelity ops channel; web and social attach as capability-masked adapters—not forked business logic.

### Taglines (pick one)

| Use | Line |
|-----|------|
| Product | **One backend. Many chat surfaces. Zero commission apps.** |
| AI | **Order and operate by conversation—Grok handles the rest.** |
| Multi-channel | **Telegram-primary commerce. Social web. Same brain.** |
| Merchant | **Your brand. Your bot. Your site. Your orders.** |

---

## 2. Pitch

### Investor / partner (medium)

**[Platform]** is a chat-native, multi-channel social commerce system for physical goods and food delivery.

Customers discover brands on Instagram-style multi-tenant web storefronts or in messaging apps, then finish the journey in conversation: catalog, cart, local and crypto payments, GPS delivery, and rider chat. Dual **Grok** assistants form the LLM layer—a **customer agent** for discovery, order status, deals, and support escalation, and an **admin agent** for menu and ops via guarded tool calls.

A single multi-tenant core (brands, stores, inventory, payments, kitchen, dispatch) powers every surface. **Telegram** remains the richest adapter for customers and for elevated roles (admin, kitchen, driver). **Web** is a first-class projection and lead funnel. **Instagram DM** and **LINE** attach next on the same ports—capability masks, not rewrites.

**Why now:** Merchants want owned channels without app-store friction or marketplace commissions. Messaging is where customers already are. LLMs make button-only bots feel broken. This stack ships money-safe commerce, live dispatch, and AI on a path to multi-channel without forking domain logic.

### Merchant pitch (short)

No app store. No download tax. Customers open Telegram (or your brand site), order in their language, pay with PromptPay, COD, or crypto, and track the rider live. You run kitchen, riders, and admin in chat—or ask the AI assistant to change prices and import menus. One platform, many brands and branches, zero marketplace commission.

### Technical pitch (short)

Multi-channel conversational commerce OS:

```text
Adapters (Telegram · Web · forms · LINE/IG later)
        → identity + capability masks
        → application services (cart · checkout · orders · tickets · leads)
        → domain (inventory · payments · dispatch)
        + dual LLM agents (customer tools · admin structured actions)
```

**Law:** adapters are thin; services own business rules; no new Telegram-only domain shortcuts.

### Differentiators

| Traditional apps / marketplaces | This platform |
|---------------------------------|---------------|
| Download + account friction | Chat and web where customers already are |
| 15–30% commission | Merchant-owned channel |
| Separate kitchen / rider dashboards | Ops in Telegram groups + live dispatch |
| Static FAQ bots | Grok tools over real catalog, orders, support |
| One surface | Multi-brand bot pool + white-label sites + channel roadmap |
| Channel = rewrite | Ports, services, capability masks |

### Target audiences

- Restaurant and physical-goods brands in Thailand (PromptPay, Thai address, multi-language)
- Multi-location / multi-brand operators who want one ops core
- Teams that want AI-assisted admin without exposing raw DB access
- Builders extending to Instagram DM / LINE without forking checkout

---

## 3. Product positioning (accurate scope)

| Claim | Status (2026-07-17) |
|-------|---------------------|
| Chat-first commerce | **Live** — full Telegram customer + kitchen + rider + admin |
| LLM-based (customer + admin Grok) | **Live** — tool-calling assistants with schema guardrails |
| Multi-brand / multi-bot | **Live** — CARD-19 (`MULTI_BOT_ENABLED`) |
| White-label Instagram-style web | **~90%** — CARD-38 A+B+C (API, media, Astro shell) |
| Unified multi-channel backend | **Spine frozen** — law + services + ports + CARD-40 A–F parity freeze |
| Instagram DM / LINE | **IG ~55%** (CARD-33) · **LINE ~55%** (CARD-16 foundation) |
| Web-only leads / booking | **~90%** — services + forms + staff Messenger notify; not forced into Telegram |

**Best one-sentence truth today:**

> Telegram-primary conversational commerce with dual LLM agents, multi-brand ops, white-label web projection, and a multi-channel expansion underway on a unified service layer.

---

## 4. Work-in-progress summary

### Closed milestones

| Milestone | Status | Notes |
|-----------|--------|--------|
| **M0** Launch gate | ✅ | Payment session refactor, payment integrity, test suite recovery |
| **M1** Hardening | ✅ | Input validation, persistent cart + brand/store switch |
| **M2** Live dispatch | ✅ | GPS driver matching, offer/accept/escalate (`AUTO_DISPATCH_ENABLED`) |

**Shipped cards (numbered):** CARD-01–15, 17–19, 21–28 + Restaurant Core (RC) and Feature (FC) suites. Details: [`FEATURE_CARDS.md`](FEATURE_CARDS.md) · [`done/`](done/).

**Quality (historical checkpoint):** suite green post-M0; coverage ~47–48% with gate ≥30%. Re-run locally for current numbers.

### Active epic: M3 — white-label + unified multi-channel

**North star**

```text
One domain · many adapters (Telegram, web, forms, LINE, chatbox)
Frontends implement capability MASKS
Backend features are STANDARDIZED services
No new handler → domain business shortcuts
```

| Card | Name | Progress | Role |
|------|------|----------|------|
| **CARD-38** | White-label brand/branch sites | **~90%** (A+B+C ✅) | Web adapter: catalog API, media, Astro |
| **CARD-32** | Customer application services | **~95%** | cart / checkout / order_query shared |
| **CARD-29** | Messenger port | **~90%** | Outbound notify via `TelegramMessenger` |
| **CARD-30** | User identities | **~90%** | Dual-write, resolve, link helpers |
| **CARD-31** | Platform capabilities | **~95%** | Masks: platform × role |
| **CARD-40** | Web ↔ TG abstracted parity | **~35%** | Tier A+B ✅; **C–F open** |
| **CARD-39** | Web OAuth + ticket portal | **~50%** | Auth + tickets on web |
| **CARD-36** | Leads + meeting booking | **~70%** | Funnel polish / staff notify |
| CARD-34 | Conversation workflow specs | 0% | Spec gate for second chat channels |
| CARD-33 | Instagram Messaging | 0% | Phase 2 customer channel |
| CARD-16 | LINE | 0% | Tier 3 |
| CARD-37 | SnusThai Hub demo | 0% | **Parked** — vertical theme only |

### Next slice (do this)

1. **CARD-40 Tier C** — unify tickets (web + Telegram) · Messenger for customer status · identity edge cases  
2. Keep **CARD-40** as abstracted parity (same services, honest masks)—not pixel clones or “put lead forms in Telegram”  
3. **Reject** PRs that add business logic only in Telegram handlers or open a second chat channel before CARD-40 C/D freeze  

**Verify:**

```bash
pytest tests/unit/services/test_commerce_parity_card40b.py tests/unit/platform/ -q --no-cov
```

### Local demo (web + API)

```bash
python scripts/run_public_api.py          # → :9090
cd apps/storefront && npm run dev -- --host 127.0.0.1 --port 4321
# → http://127.0.0.1:4321/snus-demo
```

### Dependency graph (open work)

```text
DONE: M0–M2 · CARD-19 · CARD-28 · CARD-38 A+B+C
        │
        ▼
   UNIFIED BACKEND LAW
        │
        ▼
P1  CARD-32 services · CARD-29/30/31 ports   (~90–95%)
        │
        ▼
    CARD-40 Web↔TG parity   (A+B ✅ → Tier C next)
        │
        ▼
P2  CARD-36 · 34 · 33 · 16
P3  CARD-37 demo (parked)
```

### Honest channel map

| Surface | Customer commerce | Ops (admin/kitchen/driver) | LLM |
|---------|-------------------|----------------------------|-----|
| Telegram | Full | Full (primary) | Customer + admin Grok |
| Web storefront | Catalog + commerce API (UI may lag) | Off by design | Optional later |
| Web leads/booking | Forms → services | Staff notify (partial) | — |
| Instagram DM | Planned (masked) | Off | Optional short-turn |
| LINE | Planned (masked) | Off | Later |

---

## 5. Architecture snapshot

```text
                    PostgreSQL (source of truth)
         Brand · Store · Goods · Orders · web_profile · identities
                              │
                              ▼
                   Application services
         catalog · cart · checkout · order_query
         tickets · leads_bookings · web_auth
         platform: capabilities · messaging · identity · media_ref
                              │
           ┌──────────────────┼──────────────────┐
           ▼                  ▼                  ▼
     Public API +        Telegram            (LINE / IG later)
     Astro storefront    handlers (thin)     webhooks
```

### Key code paths

| Path | Role |
|------|------|
| `bot/services/*` | Application services (DTO / `ServiceResult`) |
| `bot/platform/capabilities.py` | Capability keys, masks, resolve |
| `bot/platform/messaging.py` | Messenger port |
| `bot/platform/identity.py` | Resolve / link / ensure Telegram identity |
| `bot/web/public_api.py` | Catalog + media + mounts |
| `bot/web/commerce_api.py` | Web cart/checkout/orders |
| `bot/web/auth_api.py` | OAuth session + tickets/leads HTTP |
| `bot/ai/*` | Grok client, admin + customer tools/executors |
| `bot/multibot/*` | Multi-brand bot pool |
| `apps/storefront` | Multi-tenant Astro shell |

### Stack

| Component | Technology |
|-----------|------------|
| Bot framework | Python · aiogram 3.22 |
| DB / cache | PostgreSQL 16 · Redis 7 |
| LLM | xAI Grok (function calling + Pydantic schemas) |
| Web | Astro + Tailwind · public HTTP API |
| Deploy | Docker Compose |

---

## 6. Documentation index

> Prefer links from this table over hunting the tree. On conflict: **CLEAR-START + FEATURE_CARDS + UNIFIED-BACKEND win.**

### 6.1 Entry points (start here)

| Doc | Purpose |
|-----|---------|
| **[MASTER-DOCUMENT.md](MASTER-DOCUMENT.md)** | **This file** — blurb, pitch, WIP archive, full index |
| [CLEAR-START.md](CLEAR-START.md) | Session bootstrap: north star, code map, local run, next slice |
| [FEATURE_CARDS.md](FEATURE_CARDS.md) | Live status board (done / backlog / next up) |
| [MASTER-PLAN.md](MASTER-PLAN.md) | Milestone sequencing & launch history |
| [ROADMAP.md](ROADMAP.md) | Growth-track narrative (secondary to MASTER-PLAN) |
| [MARKETING.md](MARKETING.md) | Merchant-facing restaurant product story (Telegram-era) |
| [TESTING.md](TESTING.md) | How to run and structure tests |

### 6.2 Architecture & multi-channel

| Doc | Purpose |
|-----|---------|
| [Specifications/UNIFIED-BACKEND-CHANNEL-INTERFACE.md](Specifications/UNIFIED-BACKEND-CHANNEL-INTERFACE.md) | **Binding law** — adapters → services → domain (R1–R8) |
| [later/MULTI-CHANNEL-TIERED-PLAN.md](later/MULTI-CHANNEL-TIERED-PLAN.md) | Tier plan T0–T3 (ports, services, IG, LINE, web) |
| [later/CARD-40-web-telegram-abstracted-feature-parity.md](later/CARD-40-web-telegram-abstracted-feature-parity.md) | Web↔TG parity epic |
| [later/CARD-40-parity-matrix.md](later/CARD-40-parity-matrix.md) | Shared vs web-only vs TG-ops capability matrix |
| [Specifications/README.md](Specifications/README.md) | Spec index + customer flow inventory (CARD-34) |

### 6.3 Specifications (deep)

| Doc | Purpose |
|-----|---------|
| [AI-CUSTOMER-ASSISTANT.md](Specifications/AI-CUSTOMER-ASSISTANT.md) | Customer Grok tools, FSM, scope rules |
| [MENU-SYSTEM.md](Specifications/MENU-SYSTEM.md) | Menu / modifiers / catalog model |
| [WEB-INSTAGRAM-STYLE-STOREFRONT.md](Specifications/WEB-INSTAGRAM-STYLE-STOREFRONT.md) | IG-like storefront product spec |
| [WHITE-LABEL-ASTRO-IMPLEMENTATION.md](Specifications/WHITE-LABEL-ASTRO-IMPLEMENTATION.md) | Astro multi-tenant build contract |
| [BRAND-BRANCH-WEB-CONTENT-MODEL.md](Specifications/BRAND-BRANCH-WEB-CONTENT-MODEL.md) | Hybrid content model (columns + JSON) |
| [WHITE-LABEL-SITE-MODES-COMPLIANCE-LEADS.md](Specifications/WHITE-LABEL-SITE-MODES-COMPLIANCE-LEADS.md) | full_store / portfolio / hybrid · age gate · leads |
| [WHITE-LABEL-OAUTH-TICKETS.md](Specifications/WHITE-LABEL-OAUTH-TICKETS.md) | Web OAuth + tickets |
| [FUNNEL-INSTAGRAM-WEB-TELEGRAM.md](Specifications/FUNNEL-INSTAGRAM-WEB-TELEGRAM.md) | IG → web → Telegram funnel |
| [SNUSTHAI-HUB-MVP.md](Specifications/SNUSTHAI-HUB-MVP.md) | Vertical demo theme (not platform architecture) |
| [research/GALLERY-JS-INSPIRATION.md](Specifications/research/GALLERY-JS-INSPIRATION.md) | Gallery UX research |
| [_TEMPLATE-FLOW.md](Specifications/_TEMPLATE-FLOW.md) | Flow-spec template for CARD-34 |

### 6.4 Open cards (`docs/later/`)

| Card | File |
|------|------|
| CARD-16 | [LINE API](later/CARD-16-line-api-integration.md) |
| CARD-29 | [Messenger port](later/CARD-29-messenger-port.md) |
| CARD-30 | [User identities](later/CARD-30-user-identities.md) |
| CARD-31 | [Platform capabilities](later/CARD-31-platform-capabilities.md) |
| CARD-32 | [Customer application services](later/CARD-32-customer-application-services.md) |
| CARD-33 | [Instagram messaging](later/CARD-33-instagram-messaging-channel.md) |
| CARD-34 | [Conversation workflow specs](later/CARD-34-conversation-workflow-specifications.md) |
| CARD-35 | [IG-style web storefront](later/CARD-35-instagram-style-web-storefront.md) *(subsumed by 38C)* |
| CARD-36 | [Web leads + booking funnel](later/CARD-36-instagram-web-telegram-funnel.md) |
| CARD-37 | [SnusThai Hub Astro MVP](later/CARD-37-snusthai-hub-astro-mvp.md) *(parked)* |
| CARD-38 | [White-label brand/branch sites](later/CARD-38-white-label-brand-branch-sites.md) |
| CARD-39 | [Web OAuth + ticket portal](later/CARD-39-web-oauth-ticket-portal.md) |
| CARD-40 | [Web↔TG abstracted parity](later/CARD-40-web-telegram-abstracted-feature-parity.md) |
| Plan | [MULTI-CHANNEL-TIERED-PLAN.md](later/MULTI-CHANNEL-TIERED-PLAN.md) |

### 6.5 Done cards (`docs/done/`)

| Card | Name |
|------|------|
| [CARD-01](done/CARD-01-promptpay-qr-payment.md) | PromptPay QR payment |
| [CARD-02](done/CARD-02-gps-delivery-address.md) | GPS delivery address |
| [CARD-03](done/CARD-03-dead-drop-delivery.md) | Dead drop delivery |
| [CARD-04](done/CARD-04-photo-proof-delivery.md) | Photo proof of delivery |
| [CARD-05](done/CARD-05-thai-language-i18n.md) | Thai language i18n |
| [CARD-06](done/CARD-06-thb-currency.md) | THB currency |
| [CARD-07](done/CARD-07-thai-address-format.md) | Thai address format |
| [CARD-08](done/CARD-08-menu-modifiers.md) | Menu modifiers |
| [CARD-09](done/CARD-09-kitchen-delivery-workflow.md) | Kitchen & delivery workflow |
| [CARD-10](done/CARD-10-delivery-zones-timeslots.md) | Delivery zones & timeslots |
| [CARD-11](done/CARD-11-cod-thai-localization.md) | COD Thai localization |
| [CARD-12](done/CARD-12-timezone-bangkok.md) | Timezone Bangkok |
| [CARD-13](done/CARD-13-driver-chat-live-location.md) | Driver chat + live location |
| [CARD-14](done/CARD-14-language-picker.md) | Language picker |
| [CARD-15](done/CARD-15-gps-live-tracking-delivery-chat.md) | GPS live tracking & delivery chat |
| [CARD-17](done/CARD-17-grok-admin-assistant.md) | Grok AI admin assistant |
| [CARD-18](done/CARD-18-crypto-payment-verification.md) | Multi-crypto payments |
| [CARD-19](done/CARD-19-multi-brand-bot-coordination.md) | Multi-brand bot coordination |
| [CARD-21](done/CARD-21-persistent-cart-stub.md) | Persistent cart + brand/store switch |
| [CARD-22](done/CARD-22-grok-customer-assistant.md) | Grok AI customer assistant |
| [CARD-23](done/CARD-23-payment-session-refactor.md) | Payment session refactor |
| [CARD-24](done/CARD-24-payment-integrity.md) | Payment integrity |
| [CARD-25](done/CARD-25-test-suite-recovery.md) | Test suite recovery |
| [CARD-26](done/CARD-26-live-gps-driver-matching.md) | Live GPS driver matching |
| [CARD-27](done/CARD-27-input-hardening.md) | Input validation hardening |
| [CARD-28](done/CARD-28-per-store-menu-image-and-payment-qr.md) | Per-store menu image + payment QR |

Plus **RC1–RC7** (restaurant core) and **FC1–FC9** (feature suite)—board-closed; see FEATURE_CARDS.

### 6.6 Audits, backlog, ops notes

| Doc | Purpose |
|-----|---------|
| [audit/Codebase-DRY-report.md](audit/Codebase-DRY-report.md) | DRY analysis |
| [audit/DRY-audit-report.md](audit/DRY-audit-report.md) | DRY audit |
| [audit/review-DRY.md](audit/review-DRY.md) | DRY review notes |
| [audit/MISSING_FEATURES.md](audit/MISSING_FEATURES.md) | Feature gap list |
| [audit/test-coverage-audit.md](audit/test-coverage-audit.md) | Coverage audit |
| [backlog/SLIP-VERIFICATION-SETUP.md](backlog/SLIP-VERIFICATION-SETUP.md) | SlipOK / EasySlip / RDCW setup |

### 6.7 Code & project roots (non-`docs/`)

| Path | Purpose |
|------|---------|
| [README.md](../README.md) | Install, deploy, feature guide (physical shop bot) |
| [CLAUDE.md](../CLAUDE.md) | Agent rules: bug classes, deploy/test commands, architecture notes |
| [apps/storefront/](../apps/storefront/) | White-label Astro multi-tenant storefront |
| [apps/snusthai-hub/](../apps/snusthai-hub/) | Vertical demo app (optional) |
| [bot/](../bot/) | Bot, services, platform, AI, payments, web API |
| [tests/](../tests/) | Unit, integration, e2e |
| [.env.example](../.env.example) | Environment reference |

---

## 7. How to use this archive

| Goal | Open |
|------|------|
| Copy-paste pitch / blurb | **§1–2** of this file |
| Start a coding session | [CLEAR-START.md](CLEAR-START.md) |
| See what’s done vs open | [FEATURE_CARDS.md](FEATURE_CARDS.md) |
| Order of work / milestones | [MASTER-PLAN.md](MASTER-PLAN.md) |
| “Can I put logic in the handler?” | [UNIFIED-BACKEND…](Specifications/UNIFIED-BACKEND-CHANNEL-INTERFACE.md) |
| Merchant brochure (restaurant Telegram) | [MARKETING.md](MARKETING.md) |
| Full doc tree | **§6** of this file |

### Update policy

When product story or M3 status changes:

1. Update **FEATURE_CARDS** (board) and **CLEAR-START** (handoff).  
2. Refresh **§1–4** of this master document (blurb/pitch if positioning shifts; WIP table if progress moves).  
3. Add new card/spec links under **§6** when files appear.  
4. Bump **Last archived** date at the top.

---

*Archived from live docs and codebase status as of 2026-07-17. Operational truth may move faster—prefer FEATURE_CARDS for card % and CLEAR-START for “next slice.”*
