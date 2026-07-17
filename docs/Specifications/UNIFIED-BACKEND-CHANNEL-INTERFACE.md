# Unified Backend · Channel-Agnostic Interface

> **Status:** Binding architecture directive (2026-07-17)  
> **Supersedes:** any note that “Telegram handlers may call domain forever” for *new* work  
> **Plan home:** [`docs/later/MULTI-CHANNEL-TIERED-PLAN.md`](../later/MULTI-CHANNEL-TIERED-PLAN.md)  
> **Code spine:** `bot/platform/` · public services · (target) `bot/services/{cart,checkout,…}` · adapters only at edges  

---

## 1. North star

```text
One domain · many surfaces · zero channel-specific business rules in handlers
```

| Surface (frontend / adapter) | Examples | Must implement full feature set? |
|------------------------------|----------|----------------------------------|
| Messaging bots | Telegram, LINE, WhatsApp, Instagram DM | **No** — mask only |
| Web storefront | Astro multi-tenant sites | **No** — mask only |
| Web forms | Lead, book, contact, ticket forms | **No** — subset |
| Chatbox / AI | Customer Grok tools, widget chat | **No** — subset |
| Ops (elevated) | Admin / kitchen / rider | Prefer Telegram **ops adapter** today; still calls same domain where applicable |

**Frontends differ. Backend feature contracts do not.**

Every customer-facing capability (catalog, cart, checkout, tickets, leads, booking, status, media, identity) is owned by a **channel-agnostic application service**. Adapters only:

1. Authenticate / resolve identity for their channel  
2. Check **capability mask** for `(brand, channel, role)`  
3. Call the **same service method** with DTOs  
4. Render / send results in channel-native UI  

---

## 2. Hard rules (PR / design checklist)

| # | Rule |
|---|------|
| **R1** | **No new Telegram → domain shortcuts.** New business logic must not live only in `handlers/**` calling `database/methods` or `payments/*` without a service entry. |
| **R2** | **Adapters are thin.** Handlers / web routes / webhooks: parse input → `resolve_user` → `can(channel, feature)` → `services.*` → map DTO to UI. |
| **R3** | **DTOs only across the boundary.** Services return `ServiceResult` / plain dicts — never `Message`, `CallbackQuery`, aiogram types, LINE events, or HTTP `Request`. |
| **R4** | **Public APIs never leak transport IDs as business keys.** Prefer internal `user_id` + `user_identities`; media as **media refs** → public URLs only. |
| **R5** | **Capability mask is mandatory** at every adapter boundary (`bot/platform/capabilities` + brand `web_profile.channels`). |
| **R6** | **Outbound notify** goes through **Messenger / MessageTransport**, not `get_shared_bot()` outside the Telegram adapter. |
| **R7** | **Legacy exception (temporary):** Existing Telegram handlers may still call domain directly until migrated (CARD-32). **No new code paths** may expand that pattern. Track debt; each migration removes one path. |
| **R8** | **Session rule (CARD-23):** Services must not hold a DB session across awaits / network I/O. |

If a PR adds a feature only reachable from Telegram handlers without a service, **reject or extract first**.

---

## 3. Target architecture

```text
                         ┌─────────────────────────────────────┐
                         │     Domain (DB + payments + AI)      │
                         │  methods · models · inventory · etc  │
                         └──────────────────▲──────────────────┘
                                            │
                         ┌──────────────────┴──────────────────┐
                         │   Application services (standardized)│
                         │  catalog · cart · checkout · orders  │
                         │  tickets · leads · bookings · media  │
                         │  identity · capabilities · notify    │
                         └──────────────────▲──────────────────┘
                                            │  DTOs only
              ┌──────────────┬──────────────┼──────────────┬─────────────┐
              ▼              ▼              ▼              ▼             ▼
        Telegram         Web public     Web forms      LINE/IG/WA    Chatbox
        adapter          API/SSR        (leads/book)   webhooks      AI tools
        (handlers)       storefront     OAuth tickets
```

### Layers (directories)

| Layer | Location | Responsibility |
|-------|----------|----------------|
| **Platform contracts** | `bot/platform/` | Channels, capabilities, media_ref, messaging protocol |
| **Application services** | `bot/services/*` | Business use-cases, DTOs, orchestration |
| **Domain** | `bot/database/**`, `bot/payments/**`, … | Persistence, money, inventory |
| **Adapters** | `bot/handlers/**`, `bot/web/**`, future webhooks | I/O only |
| **Storefront** | `apps/storefront` | Presentation of public DTOs; capability-gated UI |

---

## 4. Standard feature catalog (backend contracts)

Each feature is a **named capability** + **service surface**. Channels enable a **subset** via mask; the contract stays identical.

| Capability key | Service (target module) | Used by (examples) |
|----------------|-------------------------|---------------------|
| `catalog` | `catalog_public` | Web, TG shop, LINE browse |
| `item_detail` | `catalog_public` | Web item page, bot product card |
| `age_gate` | profile / compliance in `web_profile` | Web only typically |
| `cart` | `services/cart` (CARD-32) | TG full, web if checkout on |
| `checkout` | `services/checkout` (CARD-32) | TG; web when mode allows |
| `portfolio` / `leads` | `leads_bookings` | Web inquire, funnel forms |
| `booking` | `leads_bookings` | Web book; optional messaging |
| `order_status` | `services/order_query` (CARD-32) | All customer surfaces |
| `tickets` | `tickets_web` + future `services/tickets` | Web portal, TG tickets |
| `auth` | `web_auth` + identities | Web OAuth; TG is implicit identity |
| `media` | `media_proxy` + `media_ref` | All catalog UIs |
| `payment_*` | checkout services | Per channel mask |
| `admin_console` / `kitchen_ops` / `driver_dispatch` | **ops** services later | Default: Telegram ops adapter only |

**Machine-readable masks:**

- Brand: `web_profile.modules`, `web_profile.capabilities`, `web_profile.channels.<id>.mask`  
- Global platform defaults: CARD-31 matrix (platform × role) — merge with brand mask:  
  `effective = platform_role_caps ∩ brand_channel_caps`

Already partially landed:

- `bot/platform/capabilities.py` — brand + channel resolution  
- `bot/platform/media_ref.py` — `local:` / `tg:` / `https:`  
- `bot/platform/messaging.py` — `MessageTransport` protocol  
- Public brand DTO includes `capabilities` + `channels`  

---

## 5. Identity (all channels)

```text
users (internal spine)
    └── user_identities (platform, external_id) → user_id
```

| Channel | `platform` | `external_id` |
|---------|------------|---------------|
| Telegram | `telegram` | str(telegram_id) |
| Web OAuth | `web` / `google` | provider subject |
| LINE | `line` | LINE user id |
| Instagram | `instagram` | PSID |
| WhatsApp | `whatsapp` | wa id |

**Rule:** Services take **internal user_id** (or anonymous lead DTOs). Adapters resolve identity before calling commerce services.

CARD-30 dual-write + resolve API is required before second messaging channel goes live.

---

## 6. Messaging (outbound)

```text
notify_* helpers  →  MessageTransport / Messenger  →  TelegramMessenger | LineMessenger | …
```

- Payload: `OutboundMessage` (text, media_refs, metadata)  
- Target: `DeliveryTarget(channel, external_id, brand_id)`  
- **No** order-status business logic inside adapters  

CARD-29 wires existing `notifications.py` through the port (Telegram adapter first).

---

## 7. Media

| Stored as | Public sees |
|-----------|-------------|
| Media ref (`local:…`, `tg:…`, URL) | `/media/...` or absolute HTTPS URL |

Catalog DTOs expose **only** `logo_url` / `image_url` / `media_urls` — never raw Bot API file ids to browsers or third-party webhooks.

---

## 8. Frontend obligations (by type)

### Messaging adapter (Telegram / LINE / …)

- Map updates → service calls  
- Enforce capability mask before offering a flow  
- Render keyboards/templates from service DTOs + i18n  
- Must **not** implement inventory math, payment creation, or ticket policy in the adapter  

### Web storefront / SSR

- Read public catalog + capabilities  
- Hide nav/CTAs with `can(cap)`  
- Mutations via public REST that call the **same** services as bots  

### Web form / funnel

- Lead / book / contact: POST → `leads_bookings` (already service-shaped)  
- Same DTOs whether form is Astro, embedded widget, or Meta lead ad later  

### Chatbox / AI tools

- Tool executors call application services with `user_id` from auth context  
- Tools listed per capability mask (no “admin” tools on web customer mask)  

---

## 9. Migration plan (Telegram debt)

Legacy: most customer commerce still lives in `bot/handlers/user/*` with direct DB access.

| Wave | Work | Card |
|------|------|------|
| **W0** | Platform contracts + public web path (catalog, leads, tickets, caps) | Partial ✅ `bot/platform`, CARD-38/39 |
| **W1** | Messenger port; all *new* notifies via port | CARD-29 |
| **W2** | Identities dual-write + resolve | CARD-30 |
| **W3** | Align capability module with full platform×role matrix | CARD-31 (extend `bot/platform/capabilities`) |
| **W4** | Extract cart / checkout / order_query / tickets services; migrate TG paths one by one | CARD-32 |
| **W5** | Second channel (IG/LINE) **only** on services + masks | CARD-33 / 16 |

**Definition of done for “standardized backend”:**

- [ ] Every customer capability in §4 has a service entrypoint  
- [ ] No `handlers/**` contains payment/order creation logic not delegated to services  
- [ ] Web + at least one messaging adapter share ≥80% of service call sites  
- [ ] Capability mask unit tests for web / telegram / line / instagram  
- [ ] Messenger used for outbound customer/kitchen/rider customer-facing status  

---

## 10. Anti-patterns (forbidden for new code)

| Anti-pattern | Do instead |
|--------------|------------|
| `handler` → `create_order_from_customer` only | `handler` → `checkout.start_*` → domain |
| Copy-paste order logic into LINE webhook | Call same `checkout` service |
| Storefront invents stock rules in Astro | Trust API availability DTOs |
| Public JSON with Telegram `file_id` | Media proxy URL |
| Feature exists only as Telegram FSM | Extract service first, then thin FSM |
| `if platform == "telegram": special price` | Brand/store config or capability — never channel branching in domain |

---

## 11. Related documents

| Doc | Role |
|-----|------|
| [MULTI-CHANNEL-TIERED-PLAN](../later/MULTI-CHANNEL-TIERED-PLAN.md) | Execution tiers (updated to this directive) |
| [CARD-29](../done/CARD-29-messenger-port.md) | Messenger port |
| [CARD-30](../done/CARD-30-user-identities.md) | Identities |
| [CARD-31](../done/CARD-31-platform-capabilities.md) | Platform×role matrix |
| [CARD-32](../done/CARD-32-customer-application-services.md) | Customer services extract |
| [CARD-38](../done/CARD-38-white-label-brand-branch-sites.md) | Web as first-class surface |
| [WHITE-LABEL-SITE-MODES…](WHITE-LABEL-SITE-MODES-COMPLIANCE-LEADS.md) | Commerce modes + compliance |
| [CLEAR-START](../CLEAR-START.md) | Session entry |

---

## 12. One-sentence law

> **Adapters speak channels; services speak business; domain speaks data — and no adapter owns a business rule alone.**
