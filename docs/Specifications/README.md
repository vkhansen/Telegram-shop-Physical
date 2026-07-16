# Conversation & Workflow Specifications

> **Source of truth for chat interactions and workflows.**  
> Owned by **[CARD-34](../later/CARD-34-conversation-workflow-specifications.md)**.  
> Multi-channel plan: [MULTI-CHANNEL-TIERED-PLAN.md](../later/MULTI-CHANNEL-TIERED-PLAN.md).  
> **Backend law (all surfaces):** [UNIFIED-BACKEND-CHANNEL-INTERFACE.md](UNIFIED-BACKEND-CHANNEL-INTERFACE.md).

**Default mode:** document **as-built** flows against **application services** where they exist; note adapter (Telegram/web) only for I/O. Capability masks define LINE / IG / web subsets.

| Resource | Path |
|----------|------|
| **Unified backend interface** | [UNIFIED-BACKEND-CHANNEL-INTERFACE.md](UNIFIED-BACKEND-CHANNEL-INTERFACE.md) |
| Flow template | [`_TEMPLATE-FLOW.md`](_TEMPLATE-FLOW.md) |
| Flow docs | [`flows/`](flows/) (created as specs are written) |
| Cross-cutting | [`cross-cutting/`](cross-cutting/) |
| Existing deep specs | [AI-CUSTOMER-ASSISTANT.md](AI-CUSTOMER-ASSISTANT.md), [MENU-SYSTEM.md](MENU-SYSTEM.md), [WEB-INSTAGRAM-STYLE-STOREFRONT.md](WEB-INSTAGRAM-STYLE-STOREFRONT.md), [FUNNEL-INSTAGRAM-WEB-TELEGRAM.md](FUNNEL-INSTAGRAM-WEB-TELEGRAM.md), [SNUSTHAI-HUB-MVP.md](SNUSTHAI-HUB-MVP.md), [BRAND-BRANCH-WEB-CONTENT-MODEL.md](BRAND-BRANCH-WEB-CONTENT-MODEL.md), [WHITE-LABEL-SITE-MODES-COMPLIANCE-LEADS.md](WHITE-LABEL-SITE-MODES-COMPLIANCE-LEADS.md), [WHITE-LABEL-ASTRO-IMPLEMENTATION.md](WHITE-LABEL-ASTRO-IMPLEMENTATION.md), [WHITE-LABEL-OAUTH-TICKETS.md](WHITE-LABEL-OAUTH-TICKETS.md) |
| Gallery research | [research/GALLERY-JS-INSPIRATION.md](research/GALLERY-JS-INSPIRATION.md) |
| **Session start** | [../CLEAR-START.md](../CLEAR-START.md) |
| **Master archive (blurb · pitch · WIP · index)** | [../MASTER-DOCUMENT.md](../MASTER-DOCUMENT.md) |

---

## Status legend

| Status | Meaning |
|--------|---------|
| `missing` | Not written yet |
| `draft` | First pass exists |
| `reviewed` | Reviewed against code |
| `accepted` | Ready to gate implementation (esp. Instagram) |
| `linked` | Covered by an existing deep-spec doc |

---

## Customer flows

| ID | Name | Status | Spec path |
|----|------|--------|-----------|
| C-01 | Start / main menu / profile | missing | |
| C-02 | Language picker | missing | |
| C-03 | Privacy / PDPA | missing | |
| C-04 | Rules / help | missing | |
| C-05 | Store / brand selection + switch | missing | |
| C-06 | Browse shop | missing | (see also MENU-SYSTEM.md) |
| C-07 | Product search | missing | |
| C-08 | Cart + modifiers | missing | |
| C-09 | Saved carts | missing | |
| C-10 | Checkout — location methods | missing | |
| C-11 | Checkout — delivery type | missing | |
| C-12 | Checkout — phone / address / note | missing | |
| C-13 | Payment — cash | missing | |
| C-14 | Payment — PromptPay + slip | missing | |
| C-15 | Payment — crypto | missing | |
| C-16 | Bonus at checkout | missing | |
| C-17 | My orders / reorder | missing | |
| C-18 | Order status notifications | missing | |
| C-19 | Delivery chat + live location | missing | |
| C-20 | Reviews | missing | |
| C-21 | Referrals / reference codes | missing | |
| C-22 | Support tickets | missing | |
| C-23 | Customer AI assistant | linked | [AI-CUSTOMER-ASSISTANT.md](AI-CUSTOMER-ASSISTANT.md) |
| C-24 | Coupons / promo | missing | |

---

## Admin / ops flows (Telegram only)

| ID | Name | Status | Spec path |
|----|------|--------|-----------|
| A-01 | Admin console entry | missing | |
| A-02 | Shop / goods / categories CRUD | missing | |
| A-03 | Stock / modifiers admin | missing | |
| A-04 | Order management + status | missing | |
| A-05 | Kitchen group buttons | missing | |
| A-06 | Rider group / photo proof | missing | |
| A-07 | Users ban / role / bonus | missing | |
| A-08 | Broadcast | missing | |
| A-09 | Coupons / accounting / settings / stores | missing | |
| A-10 | Tickets admin | missing | |
| A-11 | Admin Grok assistant | missing | |
| A-12 | CLI ops vs in-bot | missing | |

---

## Driver flows (Telegram only)

| ID | Name | Status | Spec path |
|----|------|--------|-----------|
| D-01 | Registration / approval | missing | |
| D-02 | Online / offline + live location | missing | |
| D-03 | Job offer accept / decline | missing | |
| D-04 | Picked up / delivered | missing | |

---

## Web storefront flows (auto-generated mobile site)

| ID | Name | Status | Spec path |
|----|------|--------|-----------|
| W-01 | Browse Brand → Store → Menu → Item → Telegram handoff | draft | [WEB-INSTAGRAM-STYLE-STOREFRONT.md](WEB-INSTAGRAM-STYLE-STOREFRONT.md) §13 |
| W-02 | Shared item deep link | draft | same §13 |
| W-03 | Unavailable item display | draft | same §13 |

**Implementation card:** [CARD-35](../later/CARD-35-instagram-style-web-storefront.md)  
**Hierarchy:** Brand → Store → Menu (categories) → Items — data from Telegram backend; no separate CMS.

---

## Cross-cutting

| Doc | Status |
|-----|--------|
| identity-and-locale | missing |
| order-status-machine | missing |
| payment-methods | missing |
| error-and-back-navigation | missing |
| platform-masks | missing |

---

## Instagram Phase 2 package (CARD-33 gate)

Fill during CARD-34; until then treat as draft intent:

| Flow IDs | On Instagram? |
|----------|----------------|
| C-01, C-06–C-08, C-10–C-18, C-22 | **In** (simplified where noted in each flow) |
| C-19, C-23 (optional), all A-*, all D-* | **Out** |

**CARD-33 must not implement flows outside the accepted In list.**

---

## Writing order (recommended)

1. Cross-cutting: order-status-machine, payment-methods  
2. C-05 → C-18 (commerce core)  
3. C-01–C-04, C-20–C-24  
4. A-04–A-06, D-01–D-04  
5. Remaining admin inventory  
6. Accept Instagram package in this README  

Use [`_TEMPLATE-FLOW.md`](_TEMPLATE-FLOW.md) for every new flow file under `flows/`.
