# Card 34: Conversation & Workflow Specifications

## Implementation Status

> **0% Complete** | `░░░░░░░░░░░░░░░░░░░` | Card created 2026-07-16 — specs not yet written.

**Tier:** T0-Spec — Formal interaction specs (gates multi-channel UX)  
**Phase:** M3 — Multi-Platform Growth  
**Priority:** High (P1)  
**Effort:** Medium–High (3–6 days writing + review; no runtime code required)  
**Dependencies:** None to start (source of truth is live Telegram handlers); align with [CARD-31](CARD-31-platform-capabilities.md) for platform masks  
**Blocks / gates:**  
- Soft gate for [CARD-32](CARD-32-customer-application-services.md) (customer DTOs should match named flows)  
- **Hard gate** for [CARD-33](CARD-33-instagram-messaging-channel.md) Instagram Phase 2 (implement only specified masked flows)  
- Hard gate for [CARD-16](CARD-16-line-api-integration.md) LINE Tier 3  

**Plan:** [`MULTI-CHANNEL-TIERED-PLAN.md`](MULTI-CHANNEL-TIERED-PLAN.md)

---

## Why

Multi-channel work (ports, services, Instagram) risks reverse-engineering behavior from ~40 handler modules. Without formal specs:

- Instagram ships incomplete or wrong chat paths  
- Service extraction misses edge cases (bonus, stock, cancel, back)  
- “Masked subset” is undefined in practice  
- QA has no acceptance checklist independent of code  

This card produces a **written catalog of workflows and chat interactions** for the live Telegram product, plus **platform masks** for Instagram (and later LINE). It is documentation-first; code changes only if a gap is found and filed as a bug/follow-up.

Existing deep specs to **extend, not replace**:

- [`docs/Specifications/AI-CUSTOMER-ASSISTANT.md`](../Specifications/AI-CUSTOMER-ASSISTANT.md)  
- [`docs/Specifications/MENU-SYSTEM.md`](../Specifications/MENU-SYSTEM.md)  

---

## Deliverables

### 1. Index + template

| Path | Purpose |
|------|---------|
| `docs/Specifications/README.md` | Master index of all flows; status; platform coverage matrix |
| `docs/Specifications/_TEMPLATE-FLOW.md` | Required sections for every flow doc |
| `docs/Specifications/flows/` | One file per flow (or tight group) |

### 2. Flow inventory (must list every entry)

Group by actor. Each item becomes a flow file (or an explicit “deferred / out of scope” row in the index).

#### Customer (Telegram full)

| ID | Flow | Primary code anchors (starting point) |
|----|------|----------------------------------------|
| C-01 | Start / main menu / profile | `handlers/user/main.py` |
| C-02 | Language picker | language states |
| C-03 | Privacy / PDPA | `privacy_handler.py` |
| C-04 | Rules / help | `help_handler.py` |
| C-05 | Store / brand selection + switch | `store_selection.py`, cart stub |
| C-06 | Browse shop (categories → item) | `shop_and_goods.py` |
| C-07 | Product search | `search_handler.py` |
| C-08 | Cart (add/remove/clear, modifiers) | `cart_handler.py` |
| C-09 | Saved carts restore/discard | `saved_carts_handler.py` |
| C-10 | Checkout — location methods | `order_handler.py` + `OrderStates` |
| C-11 | Checkout — delivery type (door/drop/pickup) | same |
| C-12 | Checkout — phone / address / note | same |
| C-13 | Payment — cash | same |
| C-14 | Payment — PromptPay QR + slip | same + payments |
| C-15 | Payment — crypto (BTC/LTC/SOL/USDT) | same |
| C-16 | Bonus application at checkout | same |
| C-17 | My orders / detail / reorder | `orders_view_handler.py` |
| C-18 | Order status notifications (inbound push) | `payments/notifications.py` |
| C-19 | Delivery chat + live location | `delivery_chat_handler.py` |
| C-20 | Reviews | `review_handler.py` |
| C-21 | Referrals / reference codes | referral + refcode handlers |
| C-22 | Support tickets | `ticket_handler.py` |
| C-23 | Customer AI assistant | **link** existing AI-CUSTOMER-ASSISTANT.md |
| C-24 | Coupons / promo at cart or checkout | coupon utils + handlers |

#### Admin / ops (Telegram only — document for fidelity; not ported)

| ID | Flow | Notes |
|----|------|-------|
| A-01 | Admin console entry | permission gates |
| A-02 | Shop / goods / categories CRUD | FSM heavy |
| A-03 | Stock / sold-out / modifiers admin | |
| A-04 | Order management + status transitions | kitchen path trigger |
| A-05 | Kitchen group order buttons | group UX |
| A-06 | Rider group / assign / photo proof | |
| A-07 | Users ban/role/bonus | |
| A-08 | Broadcast / segmented broadcast | |
| A-09 | Coupons / accounting / settings / stores | |
| A-10 | Tickets admin | |
| A-11 | Admin Grok assistant | link or short pointer |
| A-12 | CLI ops (`bot_cli.py`) vs in-bot | note parity |

#### Driver (Telegram only)

| ID | Flow |
|----|------|
| D-01 | Driver registration / approval |
| D-02 | Online/offline + live location |
| D-03 | Job offer accept/decline + assignment |
| D-04 | Picked up / delivered actions |

#### Web storefront (auto-generated; Instagram-style)

| ID | Flow | Spec |
|----|------|------|
| W-01 | Brand → Store → Menu → Item → Telegram handoff | [WEB-INSTAGRAM-STYLE-STOREFRONT.md](../Specifications/WEB-INSTAGRAM-STYLE-STOREFRONT.md) |
| W-02 | Shared item link | same |
| W-03 | Unavailable item | same |

Implementation: [CARD-35](CARD-35-instagram-style-web-storefront.md).

### 3. Per-flow document requirements

Every flow file MUST use `_TEMPLATE-FLOW.md` and include:

1. **Metadata** — ID, name, actors, platforms (`telegram` / `instagram` / `line` / `none`), feature flags, related cards  
2. **Goal** — one paragraph success outcome  
3. **Preconditions** — auth, ban, cart, brand/store, capabilities  
4. **Entry points** — commands, `callback_data`, text patterns, media types, deep links  
5. **Conversation script** — ordered turns:
   - Bot message (i18n key + short English gloss)
   - User action (button label + callback / free text / photo / location)
   - System effects (DB, inventory, payment, notify)
6. **State machine** — FSM state names or channel-agnostic state IDs; transitions including Back/Cancel  
7. **Branch table** — success / validation fail / empty cart / stock fail / payment fail / banned  
8. **Side effects** — notifications (who, when), group messages, metrics  
9. **Platform mask** — for each non-Telegram platform: **Full / Simplified / Off** + notes  
10. **Acceptance checks** — testable bullets for QA / e2e  
11. **Code map** — handlers, states, keyboards, services (once CARD-32 lands)  

### 4. Cross-cutting specs (single files)

| Path | Content |
|------|---------|
| `docs/Specifications/cross-cutting/identity-and-locale.md` | Registration, ban, locale resolution |
| `docs/Specifications/cross-cutting/order-status-machine.md` | Status graph + who can transition + who is notified |
| `docs/Specifications/cross-cutting/payment-methods.md` | Cash / PromptPay / crypto shared rules |
| `docs/Specifications/cross-cutting/error-and-back-navigation.md` | Global back, cancel, “message not modified” |
| `docs/Specifications/cross-cutting/platform-masks.md` | Full matrix customer flows × telegram/instagram/line (from CARD-31) |

### 5. Instagram Phase 2 package (subset)

Explicit package listing **only** flows allowed on IG for CARD-33, e.g.:

- In: C-01 (simplified), C-06–C-08 (limited), C-10–C-16 (as applicable), C-17–C-18, C-22  
- Out: C-19 live chat/location, all A-*, all D-*, full modifiers if marked simplified  

Each “In” flow must have **Instagram script variant** (quick replies / text) in the same file or `flows/instagram/` overlay.

---

## Template sketch (`_TEMPLATE-FLOW.md`)

```markdown
# {ID}: {Name}

| Field | Value |
|-------|-------|
| Actors | customer / admin / driver |
| Platforms | telegram: full \| instagram: simplified \| line: off |
| Feature flags | … |
| FSM | … |
| Status | draft / reviewed / accepted |

## Goal
## Preconditions
## Entry points
## Conversation (Telegram)
| Step | Actor | Content / i18n key | Action / callback | Effects |
|------|-------|--------------------|-------------------|---------|
| 1 | bot | … | … | … |

## State machine
## Branches / errors
## Notifications
## Platform masks
## Acceptance criteria
## Code map
```

---

## Process

1. **Inventory pass** — complete index table; mark `missing` / `exists` / `linked`  
2. **Customer core first** — C-05…C-18 (shop through payment + status) before admin  
3. **Review** — at least one human review per flow group (customer / admin / driver)  
4. **Accept** — index status `accepted` for hard-gated flows before CARD-33 starts coding those paths  
5. **Drift policy** — when handlers change behavior, update the flow file in the same PR (note in CLAUDE.md optional follow-up)

**Out of scope for this card:** implementing services or Instagram; rewriting handlers to match idealized specs (file bugs if code is wrong; specs document **as-built** first, then `desired` deltas if any).

---

## As-built vs desired

Default mode: **as-built** (document what production Telegram does today).

Optional section per flow:

```markdown
## Desired deltas (optional)
- …
```

Instagram variants may be **desired** by design (simplified) without changing Telegram.

---

## Exit criteria

- [ ] `docs/Specifications/README.md` indexes all C-*, A-*, D-* IDs with status  
- [ ] `_TEMPLATE-FLOW.md` exists and is used by all new flow files  
- [ ] All **customer** flows C-01–C-24 either fully specified or explicitly deferred with reason  
- [ ] Cross-cutting order-status + payment specs written  
- [ ] Platform mask matrix complete for Instagram Phase 2 set  
- [ ] Instagram package list accepted (In/Out) — **hard gate for CARD-33**  
- [ ] Admin + driver flows at least inventoried; core A-04/A-05/A-06 and D-01–D-04 specified (as-built)  
- [ ] Linked from MULTI-CHANNEL-TIERED-PLAN and FEATURE_CARDS  

**Not required for exit:** perfect prose for every admin FSM leaf (e.g. every modifier-builder substep) if inventory + main paths are covered and remaining leaves listed as “admin detail — as-built in handler X”.

---

## Effort

| Task | Days |
|------|------|
| Template + index + inventory | 0.5–1 |
| Customer core flows (shop → pay → status) | 1.5–2.5 |
| Support / AI / referrals / reviews | 0.5–1 |
| Admin + kitchen/rider as-built | 0.5–1 |
| Driver as-built | 0.5 |
| Instagram mask package + review | 0.5–1 |
| **Total** | **3–6** |

---

## Related

- Capabilities: [CARD-31](CARD-31-platform-capabilities.md)  
- Services: [CARD-32](CARD-32-customer-application-services.md)  
- Instagram: [CARD-33](CARD-33-instagram-messaging-channel.md)  
- Tier plan: [MULTI-CHANNEL-TIERED-PLAN.md](MULTI-CHANNEL-TIERED-PLAN.md)  
