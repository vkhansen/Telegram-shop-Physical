# Card 40: Web ↔ Telegram Abstracted Feature Parity

## Implementation Status

> **~100% Complete** | `████████████████████` | Tier A–F done 2026-07-17 (masks · commerce · tickets · Grok · non-parity harden · scorecard/PR gate). Builds on CARD-29–32; does **not** require pixel-identical UX.

**Tier:** T1.5 — Cross-surface parity epic (after T0 ports + T1 services spine)  
**Phase:** M3 — Multi-Platform Growth  
**Priority:** **Critical** (definition of “one backend, two first-class adapters”)  
**Effort:** High (phased; ~2–4 weeks calendar if sequential, less if parallelized by tier)  
**Dependencies (hard):**  
- [CARD-29](CARD-29-messenger-port.md) Messenger (outbound)  
- [CARD-30](CARD-30-user-identities.md) Identities resolve/dual-write  
- [CARD-31](CARD-31-platform-capabilities.md) Capability / mask matrix (complete enforcement)  
- [CARD-32](CARD-32-customer-application-services.md) Customer services (cart/checkout/order_query; finish leftovers)  
**Soft / related:** CARD-17/22 Grok tools → services · CARD-36 leads/booking · CARD-39 web auth/tickets · [UNIFIED-BACKEND law](../Specifications/UNIFIED-BACKEND-CHANNEL-INTERFACE.md)  
**Plan:** [`MULTI-CHANNEL-TIERED-PLAN.md`](MULTI-CHANNEL-TIERED-PLAN.md)

---

## 1. Aim

**Total abstracted feature parity** between **web** and **Telegram** for every capability that is *meant* to exist on both surfaces:

> Same application services · same DTOs · same business rules · same identity spine · same capability keys  

**Not** the same UI, copy layout, or interaction model.  
**Not** forcing web-only product surfaces into Telegram (or vice versa).

### Parity definition (pass/fail)

| Rule | Meaning |
|------|---------|
| **P1 — Single entry** | For a shared capability, both adapters call the **same** `bot/services/*` (or platform) method — no TG-only / web-only business fork |
| **P2 — Same outcomes** | Given the same brand, user, cart, and payment method, order/ticket/lead **domain state** matches (status, stock, prices, bonuses) |
| **P3 — Mask honesty** | If a surface **disables** a capability, the adapter **hides/refuses** it via `resolve_capabilities` / `cap_enabled` — no silent alternate path |
| **P4 — No adapter domain** | No new inventory math, payment create, or ticket policy inside handlers or Astro |
| **P5 — Identity** | Services receive **internal `user_id`**; adapters resolve via `user_identities` / TG dual-write / web OAuth |

**Parity is measured at the service boundary**, not at pixel level.

---

## 2. Why masks ≠ incomplete product

**Feature parity ≠ feature identity.**

Some capabilities are **first-class on web only** (or ops-only on Telegram). That is **by design**, expressed as capability masks — not as missing backend work.

| Capability | Backend service (exists or target) | Web | Telegram | Notes |
|------------|-------------------------------------|-----|----------|--------|
| `leads` / inquire forms | `leads_bookings` | ✅ | ❌ default off | Landing / funnel; no need for TG form clone |
| `booking` / Google scheduling / slots | `leads_bookings` (+ calendar later) | ✅ | ❌ default off | Web widgets + OAuth calendar; TG can deep-link later if desired |
| `age_gate` | profile / compliance | ✅ typical | ❌ rare | Regulatory UX for public web |
| `about` / `faq` / `benefits` / `ticker` | content DTOs / `web_profile` | ✅ | ❌ or thin link | Marketing shell |
| `auth` (OAuth) | `web_auth` | ✅ | N/A (implicit TG identity) | Different auth **adapter**, same user spine |
| `portfolio` (inquiry-first commerce) | catalog + leads | ✅ | mask | Mode-driven; TG may still shop if `checkout` on |
| `catalog` / `item_detail` / `media` | `catalog_public` + media_ref | ✅ | ✅ | **Parity required** |
| `cart` / `checkout` / payments | `cart` · `checkout` | ✅ when mode allows | ✅ | **Parity required** (web cart may lag UI; service must exist) |
| `order_status` | `order_query` | ✅ | ✅ | **Parity required** |
| `tickets` | `tickets_web` → unify TG tickets | ✅ | ✅ | **Parity required** |
| `ai_customer` (Grok tools) | tools → services (CARD-40-C) | optional chatbox | ✅ today | **Parity of tools that hit shared caps** |
| `admin_console` / kitchen / driver | ops domain (later ops services) | ❌ default | ✅ ops adapter | **Not** web customer parity |
| Live GPS / delivery chat | domain + Messenger | optional web track | ✅ | Channel-native I/O; service for status/events |

**Law:** Web-only features still live as **standardized services** so forms, Astro, and future chatbox share them. Telegram simply **does not enable the mask**.

---

## 3. Architecture (unchanged law)

```text
        Web storefront / forms / OAuth          Telegram handlers / FSM
                    \                              /
                     \     capability mask        /
                      ▼                          ▼
                 ┌────────────────────────────────────┐
                 │  Application services + platform   │
                 │  catalog · cart · checkout · orders│
                 │  tickets · leads · booking · auth  │
                 │  identity · media · messenger · AI │
                 └────────────────┬───────────────────┘
                                  ▼
                              Domain (DB / payments)
```

```text
effective_caps(brand, channel, role) =
    PLATFORM_CAPS[channel]
  ∩ ROLE_FEATURES[role]
  ∩ brand_channel_mask(web_profile)
  ∩ commerce_mode_rules
```

Adapters **must** gate UI and mutations on `effective_caps`.  
Services **may** re-check dangerous mutations (checkout, ticket open) with the same keys.

---

## 4. Tiered delivery (this epic)

Work is ordered so each tier leaves both surfaces **more equal on the service bus**, without blocking on web-only chrome.

### Tier A — Contract freeze (masks + inventory) · ~0.5–1 d

**Goal:** One shared vocabulary so “parity” is testable.

| Deliverable | Detail |
|-------------|--------|
| **A1** Capability catalog | ✅ Merge CARD-31 keys with current `CAPABILITY_KEYS` into one documented table (this card §2 + [matrix](CARD-40-parity-matrix.md)) |
| **A2** Default masks | ✅ `web` vs `telegram` defaults: web includes `leads`, `booking`, marketing modules; telegram **excludes** them unless brand explicitly enables (`CHANNEL_DEFAULT_OFF`) |
| **A3** Parity matrix doc | ✅ Rows = capabilities; columns = service module, web adapter, TG adapter, status — [CARD-40-parity-matrix.md](CARD-40-parity-matrix.md) |
| **A4** Tests | ✅ Unit: default masks; brand override can turn `leads` on for TG (`test_capabilities_media.py`) |

**Exit A:** Engineers can answer “is X shared, web-only, or TG-ops?” without reading handlers.

**Tier A status (2026-07-17):** ✅  
- Code: `PLATFORM_CAPS` / `ROLE_FEATURES` / `CHANNEL_DEFAULT_OFF` in `bot/platform/capabilities.py`  
- Doc: [`CARD-40-parity-matrix.md`](CARD-40-parity-matrix.md)  
- Tests: `tests/unit/platform/test_capabilities_media.py`

---

### Tier B — Shared commerce spine parity · ~2–4 d

**Goal:** Catalog, cart, checkout, order status behave the same **through services** on both surfaces (where `checkout` / `catalog` masks allow).

| Deliverable | Detail |
|-------------|--------|
| **B1** Finish CARD-32 leftovers | ✅ `store_selection` + bonus/`calculate_cart_total` paths → cart service |
| **B2** Web cart/checkout path | ✅ `bot/web/commerce_api.py` — cart/checkout via same services (storefront UI optional) |
| **B3** Order status | ✅ `GET /api/public/orders` + `order_query` |
| **B4** Payments | ✅ cash + PromptPay via checkout service; QR via `build_promptpay_qr_payload` |
| **B5** Parity tests | ✅ `tests/unit/services/test_commerce_parity_card40b.py` |

**Exit B:** Commerce is **abstracted-parity**. Web may still lack a pretty cart UI, but **must not** invent a second order writer.

**Tier B status (2026-07-17):** ✅  
- Adapter: `bot/web/commerce_api.py` (session-auth cart/checkout/orders)  
- Helpers: `checkout.ensure_delivery_profile`, `catalog_public.resolve_brand_store` / `resolve_goods_name`  
- TG leftovers: `store_selection` + `order_handler` bonus totals on cart service

**Non-goals for B:** Lead forms, Google Calendar UI, age gate, marketing pages.

---

### Tier C — Shared support & identity · ~1–2 d

**Goal:** Tickets + identity + outbound notify use platform ports on both sides.

| Deliverable | Detail |
|-------------|--------|
| **C1** Tickets service unify | ✅ `bot/services/tickets.py` single writer; TG `ticket_handler` + `tickets_web` facade |
| **C2** Identity at adapter edge | ✅ Web OAuth session uid / TG dual-write; resolve API only — no link UI |
| **C3** Messenger for customer status | ✅ order_management, payment_checker, inventory expire, admin ticket reply → `get_messenger()` |
| **C4** Auth mask | ✅ Web OAuth ON; TG `auth` OFF in platform ceiling + CHANNEL_DEFAULT_OFF |

**Exit C:** Support + identity + notify are shared; only auth **adapter** differs.

**Tier C status (2026-07-17):** ✅  
- Service: `bot/services/tickets.py` · facade: `tickets_web.py`  
- TG adapter: `bot/handlers/user/ticket_handler.py`  
- Tests: `tests/unit/services/test_tickets_parity_card40c.py`

---

### Tier D — Grok / chatbox as a masked adapter · ~2–3 d

**Goal:** Customer AI is not a third business stack.

| Deliverable | Detail |
|-------------|--------|
| **D1** Tool → service | Customer Grok tools call `catalog_public` / `order_query` / tickets / cart services — not raw ORM for shared features |
| **D2** Tool list from mask | `ai_customer` + per-tool caps (`catalog`, `order_status`, `tickets`, …); never expose lead/booking tools on TG if mask off |
| **D3** Assistant session (optional slice) | Move history off pure FSM toward channel-agnostic session store if web chatbox is in scope |
| **D4** Notify via Messenger | Ticket / maintainer pings from AI path use Messenger where possible |

**Exit D:** Grok is an **adapter** (or tool host) on the same bus. Web chatbox can reuse tools later without forking.

**Non-goals for D:** Admin Grok full service extract (ops surface; lower priority for web customer parity).

**Tier D status (2026-07-17):** ✅  
- Service: `bot/services/customer_catalog.py` · tickets/order_query reused  
- Tools mask: `bot/ai/customer_tool_defs.py` (`tools_for_channel` / `TOOL_REQUIRED_CAP`)  
- Executor: `bot/ai/customer_executor.py` (no raw SupportTicket ORM)  
- Adapter: `bot/handlers/user/grok_customer.py`  
- Tests: `tests/unit/ai/test_customer_card40d.py`  
- D3 session store: deferred (FSM history remains)

---

### Tier E — Web-only & TG-ops hardening (explicit non-parity) · ~1–2 d

**Goal:** Document and enforce **intentional asymmetry** so it never looks like “debt.”

| Deliverable | Detail |
|-------------|--------|
| **E1** Web-only pack | `leads`, `booking` (+ Google scheduling), `age_gate`, marketing modules — services + web adapters only; TG mask **off** by default |
| **E2** Deep-link policy (optional) | TG may send a **URL button** to web lead/book pages without implementing forms in-bot |
| **E3** TG-ops pack | Admin / kitchen / driver / broadcast remain Telegram (or future ops web) — **out of** customer web parity |
| **E4** Enforcement tests | TG adapter never registers lead/book FSM; public API rejects TG-impersonation for ops features |

**Exit E:** Product can ship “full web funnel + full TG shop” without anyone re-adding lead forms to Telegram “for parity.”

**Tier E status (2026-07-17):** ✅  
- Packs: `WEB_ONLY_CAPS` · `TG_OPS_CAPS` · `SHARED_PARITY_CAPS` in `capabilities.py`  
- Deep links: `bot/platform/deep_links.py` (`storefront_url` / `funnel_url_button`)  
- API: `auth_api` gates `leads`/`booking` via mask; rejects ops impersonation  
- Tests: `tests/unit/platform/test_card40ef_nonparity.py`

---

### Tier F — Proof & freeze · ~1 d

| Deliverable | Detail |
|-------------|--------|
| **F1** Parity scorecard | Checklist §6 green for shared caps; web-only/tg-ops marked N/A |
| **F2** PR gate | CI or review checklist: new feature needs service + mask row + adapter notes |
| **F3** CLEAR-START / FEATURE_CARDS | Board reflects CARD-40 status |

**Tier F status (2026-07-17):** ✅  
- Scorecard: [`CARD-40-parity-scorecard.md`](CARD-40-parity-scorecard.md)  
- PR gate: [`.github/PULL_REQUEST_TEMPLATE.md`](../../.github/PULL_REQUEST_TEMPLATE.md)  
- Machine freeze: `test_card40ef_nonparity.py` (F suite)

---

## 5. Suggested default masks (customer role)

### Telegram (customer)

```text
ON:  catalog, item_detail, media, cart, checkout, payment_*, order_status,
     tickets, ai_customer, referrals, reviews (as product already has),
     location_*, delivery_chat (channel-native)
OFF: leads, booking, age_gate, about, faq, benefits, ticker, portfolio-only UX,
     auth(OAuth), admin_console, kitchen_ops, driver_dispatch
```

### Web (customer / anonymous + OAuth)

```text
ON:  catalog, item_detail, media, about, faq, benefits, ticker, contact,
     leads, booking, age_gate (if brand), tickets, auth,
     cart+checkout IFF commerce_mode allows, order_status (authed),
     portfolio IFF mode allows, social_links
OFF: admin_console, kitchen_ops, driver_dispatch, location_live (unless product adds),
     delivery_chat (unless product adds)
OPTIONAL: ai_customer chatbox widget later
```

Brand `web_profile.channels.telegram.mask` / `.web.mask` may tighten further; they must not invent new business rules.

---

## 6. Exit criteria (epic done)

- [x] **Tier A** capability + parity matrix published and tested  
- [x] **Tier B** shared commerce only through `cart` / `checkout` / `order_query` / catalog services on **both** adapters (where masks allow)  
- [x] **Tier C** tickets + identity + customer notify on platform ports  
- [x] **Tier D** customer Grok tools use services + masks (no parallel commerce rules)  
- [x] **Tier E** web-only (`leads`, `booking`/Google scheduling, marketing) and TG-ops explicitly **masked off** the other surface  
- [x] **Tier F** scorecard + PR gate  
- [x] No new handler→domain commerce shortcuts (R1) for shared commerce/support  
- [x] Web lead/book **not** reimplemented as Telegram FSM “for parity”

---

## 7. Out of scope

- Pixel-perfect UI matching  
- Second messaging channel (IG/LINE) — uses this epic’s services **after** freeze (CARD-33/16)  
- Full ops web admin  
- Changing `users.telegram_id` PK  
- Forcing Google Calendar or lead forms into Telegram

---

## 8. Dependency graph

```text
CARD-29 Messenger ──┐
CARD-30 Identities ─┼──► CARD-31 Caps (complete) ──┐
CARD-32 Services ───┘                              │
CARD-36/39 web leads·auth·tickets ─────────────────┤
                                                   ▼
                                            CARD-40 tiers A→F
                                                   │
                                                   ▼
                                     CARD-33 / 16 second channel (masked)
```

---

## 9. Effort (indicative)

| Tier | Days |
|------|------|
| A Contract freeze | 0.5–1 |
| B Commerce spine parity | 2–4 |
| C Support + identity + notify | 1–2 |
| D Grok on services | 2–3 |
| E Explicit non-parity | 1–2 |
| F Proof + freeze | 0.5–1 |
| **Total** | **~7–13** |

Parallelism: A blocks language; B/C can partially overlap after A; D after B/C for tools that need services; E anytime after A.

---

## 10. One-sentence law for this card

> **Web and Telegram share every business capability that both should have; masks deliberately omit the rest — especially web lead forms and Google scheduling on Telegram, and ops consoles on web customers.**
