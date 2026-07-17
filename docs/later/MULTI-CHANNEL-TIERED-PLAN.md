# Multi-Channel Tiered Plan — Unified Backend First

> **⚠️ Priority source of truth:** [`CLEAR-START.md`](../CLEAR-START.md) + [`FEATURE_CARDS.md`](../FEATURE_CARDS.md)  
> **Binding interface law:** [`Specifications/UNIFIED-BACKEND-CHANNEL-INTERFACE.md`](../Specifications/UNIFIED-BACKEND-CHANNEL-INTERFACE.md)  
> **Last updated:** 2026-07-17

---

## 0. Directive (2026-07-17) — read first

### What changed

Older drafts said *“Telegram handlers may call domain directly forever.”*  
**That is revoked for all new work.**

| Principle | Meaning |
|-----------|---------|
| **Unified backend** | Catalog, cart, checkout, orders, tickets, leads, booking, media, notify, identity are **standardized application services** |
| **Adapters only at edges** | Telegram · LINE · WhatsApp · Instagram DM · web storefront · web forms · chatbox — all call the **same** services |
| **Masks, not forks** | Each frontend implements a **subset** of capabilities; it must not invent parallel business logic |
| **No TG-only feature paths** | A capability is not “done” until it has a channel-agnostic service entry (even if only Telegram adapter uses it today) |
| **Legacy debt** | Existing handler→domain paths may remain until CARD-32 migrates them; **do not add new ones** |

### North star diagram

```text
   Telegram   LINE   Web UI   Web forms   Chatbox/AI
       \        \      |         |            /
        \        \     |         |           /
         ▼        ▼    ▼         ▼          ▼
              ┌────────────────────────────┐
              │  Application services      │  ← single contract
              │  + platform capabilities   │
              └─────────────┬──────────────┘
                            ▼
              ┌────────────────────────────┐
              │  Domain (DB, payments, …)  │
              └────────────────────────────┘
```

Full rules: [UNIFIED-BACKEND-CHANNEL-INTERFACE.md](../Specifications/UNIFIED-BACKEND-CHANNEL-INTERFACE.md).

---

## 1. Goals

| Goal | Meaning |
|------|---------|
| Shared backend | Same DB, inventory, payments, order state machine, multi-brand context |
| Clean seams | Services + ports (`Messenger`, identity, media, capabilities) — not a full UI framework |
| Surface freedom | Any frontend may expose a **mask** of features; backend feature set is complete and standard |
| Telegram as adapter | Telegram remains the richest **ops + customer** adapter today — not a special-case domain API |
| Privilege levels | Elevated roles (admin/kitchen/driver) stay on ops adapters (Telegram groups/UI) until an ops web exists; still no duplicate order math |

---

## 2. Architecture (unified)

```
┌──────────────────────────────────────────────────────────────────┐
│ ADAPTERS (I/O only — no business ownership)                        │
│  Telegram handlers · Web /api/public · Astro SSR · forms · AI tools│
│  (future: LINE / IG / WA webhooks)                                 │
└────────────────────────────┬─────────────────────────────────────┘
                             │ DTOs + capability check
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│ APPLICATION SERVICES (standardized)                                │
│  catalog_public · leads_bookings · tickets_web · web_auth          │
│  + CARD-32: cart · checkout · order_query · tickets                │
│  platform: capabilities · media_ref · messaging                    │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│ DOMAIN                                                             │
│  database/methods · payments · inventory · matching · AI core      │
└──────────────────────────────────────────────────────────────────┘
```

**Rule:** Adapters call services. Services call domain.  
**Forbidden for new code:** Adapter → domain business methods with channel-specific rules.

**Landed (partial):**

| Piece | Status |
|-------|--------|
| `bot/platform/capabilities.py` | ✅ brand + channel masks; public brand DTO |
| `bot/platform/media_ref.py` | ✅ local / tg / https schemes |
| `bot/platform/messaging.py` | ✅ protocol + registry (adapters TBD) |
| Public web catalog / media / leads / tickets | ✅ service-shaped |
| Storefront BrandShell + capability gating | ✅ |
| Messenger wire into notifications | ❌ CARD-29 |
| Identities dual-write complete | ◐ CARD-30 / 39 partial |
| Platform×role matrix full | ◐ CARD-31 (extend platform) |
| Cart/checkout services + TG migration | ❌ CARD-32 |

---

## 3. Tier overview

| Tier | Theme | Cards | Effort |
|------|--------|-------|--------|
| **T0-Spec** | Formal flow IDs | CARD-34 | 3–6d |
| **T0** | Ports under unified law | CARD-29, 30, 31 | 2–4d |
| **T1** | Customer application services (kill TG-only paths) | **CARD-32** | 2–4d |
| **T1.5** | Web↔Telegram **abstracted** feature parity (masks) | **[CARD-40](../done/CARD-40-web-telegram-abstracted-feature-parity.md)** | tiered ~7–13d |
| **T-Web** | White-label web as first-class adapter | CARD-38 ✅ · 39 · 36 | — |
| **T2** | Second messaging channel (masked) | CARD-33 IG | 5–8d |
| **T3** | LINE / more | CARD-16 | 5–8d each |

```
T-Web  CARD-38/39/36  public web already on services  ─────────┐
                                                                │
T0     CARD-29 Messenger · 30 Identities · 31 Caps ─────────────┤
                                                                │
T1     CARD-32 Customer services  ◀── HARD for second channel   │
       (migrate Telegram handlers onto services)                │
                                                                │
T1.5   CARD-40 Web↔TG abstracted parity                         │
       shared services + intentional non-parity                 │
       (leads / Google booking = web-only by mask)              │
                                                                ▼
T2     CARD-33 / 16  only if T1 + T1.5 spine + masks green
```

**Hard gate:** No second messaging channel ships until CARD-32 has checkout + order_query services and at least one Telegram payment path uses them.

---

## 4. Capability masks (product policy)

Frontends **do not** need parity. Backend **does** need a complete service map.

| Feature | Telegram adapter | Web storefront | Web forms | IG/LINE (later) |
|---------|------------------|----------------|-----------|-----------------|
| Catalog browse | Full | Full | — | Limited |
| Cart + modifiers | Full | Optional mask | — | Simplified |
| Checkout / payments | Full | Per `commerce_mode` | — | Masked |
| Live GPS / rider chat | Full | Off (default) | — | Off |
| Leads / inquire | Optional | Full (portfolio) | Full | Optional |
| Booking | Optional | Full | Full | Optional |
| Tickets | Full | Full (OAuth) | — | Text |
| Age gate / disclaimers | Soft | Full | Footer | Policy text |
| Admin / kitchen / driver | Full ops | Off | Off | Off |

Machine form: `resolve_capabilities(brand, channel)` + CARD-31 platform×role intersection.

---

## 5. Tier 0 — Foundation ports

**Exit criteria:** outbound notify via Messenger; identities dual-write; capability matrix tested; **no new handler→domain business paths**.

| Card | Deliverable |
|------|-------------|
| **CARD-29** | `Messenger` / align with `bot/platform/messaging.py`; wire `notifications.py` |
| **CARD-30** | `user_identities` dual-write + resolve (extend web OAuth rows) |
| **CARD-31** | Full platform×role matrix merged into `bot/platform/capabilities` |

---

## 6. Tier 1 — Customer application services (critical)

**Exit criteria:** cart/checkout/order_query/tickets are pure services; **Telegram payment paths call services**; inventory reserve identical; suite green.

| Card | Deliverable |
|------|-------------|
| **CARD-32** | `bot/services/{cart,checkout,order_query,tickets,dto}.py` |

This is the **main anti-Telegram-coupling** milestone. Until done, multi-channel remains incomplete by law of §0.

---

## 7. Web adapter (already in flight)

Web is not a second-class “brochure”:

- Public API + media + leads/booking + OAuth tickets already service-shaped  
- Storefront uses capability mask from API  
- Must keep calling **only** public/services APIs (never invent domain rules in Astro)

---

## 8. Tier 2+ messaging channels

Instagram / LINE / WhatsApp:

1. Webhook adapter  
2. Identity resolve  
3. `can(channel, feature)`  
4. Call CARD-32 services  
5. Outbound via Messenger multi-backend  

**Hard-gated** by accepted flow specs (CARD-34) + T1 services.

---

## 9. Implementation order (execution checklist)

### Now (directive + web)

1. [x] Document unified interface law  
2. [x] `bot/platform` capabilities / media_ref / messaging protocol  
3. [x] CARD-38 public catalog + storefront capability gating  
4. [ ] Keep all new web/form features on services only  

### Sprint A — T0 ports

5. [ ] CARD-29 Messenger + notifications  
6. [ ] CARD-30 identity dual-write + resolve helpers  
7. [ ] CARD-31 complete matrix + tests  

### Sprint B — T1 services (mandatory)

8. [ ] CARD-32 cart + checkout DTOs  
9. [ ] Migrate Telegram PromptPay (then cash/crypto) onto services  
10. [ ] order_query + tickets services; deprecate duplicate handler logic  

### Sprint C — second channel (optional)

11. [ ] CARD-34 IG package accepted  
12. [ ] CARD-33 or CARD-16 using **only** services  

---

## 10. Config / ops (preview)

```bash
TOKEN=...
OWNER_ID=...
# Brand web_profile.channels + modules control masks (DB)
# INSTAGRAM_CHANNEL_ENABLED=false  # later
```

---

## 11. Risks

| Risk | Mitigation |
|------|------------|
| Scope creep “full parity every channel” | Capability matrix + PR checklist |
| Handler rewrite pressure | Incremental CARD-32 migration; reject new dual paths |
| Identity collision | user_identities + explicit link flows |
| Half-migrated payments | Parity tests service vs legacy until cutover |

---

## 12. Success metrics

| Milestone | Done when |
|-----------|-----------|
| Directive | Spec linked from CLEAR-START / FEATURE_CARDS; team uses R1–R8 |
| T0 | Messenger + identities + caps tests green |
| T1 | ≥1 TG checkout path uses services; no new handler domain logic in review |
| Multi-channel ready | Web + TG share services; second adapter can ship on masks only |

---

## 13. Related docs

| Doc | Role |
|-----|------|
| [UNIFIED-BACKEND-CHANNEL-INTERFACE](../Specifications/UNIFIED-BACKEND-CHANNEL-INTERFACE.md) | **Binding law** |
| [CARD-29](../done/CARD-29-messenger-port.md) · [30](../done/CARD-30-user-identities.md) · [31](../done/CARD-31-platform-capabilities.md) · [32](../done/CARD-32-customer-application-services.md) | Execution |
| [CARD-38](../done/CARD-38-white-label-brand-branch-sites.md) | Web adapter |
| [CARD-16](../done/CARD-16-line-api-integration.md) | LINE channel (code done) |
| [CARD-34](../done/CARD-34-conversation-workflow-specifications.md) | Flow specs + packages |
| [FEATURE_CARDS](../FEATURE_CARDS.md) | Status board |
| [MASTER-PLAN](../MASTER-PLAN.md) | Milestones |
