# Multi-Channel Tiered Plan — Telegram Primary (historical + detail)

> **⚠️ Priority source of truth (2026-07-16):** [`CLEAR-START.md`](../CLEAR-START.md) + [`FEATURE_CARDS.md`](../FEATURE_CARDS.md).  
> **Next epic:** [CARD-38 white-label brand/branch sites](CARD-38-white-label-brand-branch-sites.md) — **before** Instagram DM (CARD-33) or vertical demos (CARD-37).  
> This file retains multi-channel design detail; **do not** use its old “IG Phase 2 first” order when starting work.

Last updated: 2026-07-16

---

## 1. Goals

| Goal | Meaning |
|------|---------|
| Preserve Telegram | Handlers, FSM, keyboards, kitchen/rider groups, admin, dispatch stay first-class |
| Shared backend | Same DB, inventory, payments, order state machine, multi-brand context |
| Clean seams | Small ports (`Messenger`, identity, media, capabilities) — not a full UI framework |
| Instagram = Phase 2 | First *customer* channel after foundation; **masked** feature set |
| Privilege levels | Elevated roles (admin/kitchen/driver) stay Telegram until a deliberate ops UI exists |

---

## 2. Architecture (Telegram-first)

```
┌──────────────────────────────────────────────────────────────┐
│  TELEGRAM (primary app — never demoted)                       │
│  handlers · keyboards · FSM · middleware · BotPool · admin    │
└───────────────┬────────────────────────────┬─────────────────┘
                │ optional extract           │ always
                ▼                            ▼
┌───────────────────────────┐    ┌────────────────────────────┐
│ Application services      │───▶│ Domain (unchanged APIs)    │
│ cart · checkout · orders  │    │ methods · payments ·       │
│ tickets (customer)        │    │ inventory · matching · AI  │
└─────────────┬─────────────┘    └─────────────▲──────────────┘
              │                                │
              ▼                                │
┌───────────────────────────┐                  │
│ Ports                     │                  │
│ Messenger · UserDirectory │                  │
│ MediaRef · Capabilities   │                  │
└───────┬───────────────────┘                  │
        │                                      │
   ┌────┴─────┬────────────┐                   │
   ▼          ▼            ▼                   │
Telegram   Instagram    LINE / Web             │
Messenger  (Phase 2)    (later tiers) ─────────┘
```

**Rule:** Telegram handlers may call domain directly forever. Services are shared paths for multi-channel reuse, not a mandatory choke point for Telegram.

---

## 3. Tier overview

| Tier | Milestone | Theme | Second channel? | Cards | Effort (est.) |
|------|-----------|--------|-----------------|-------|----------------|
| **T0-Spec** | M3-Specs | Formal workflow & chat specs | No | [CARD-34](CARD-34-conversation-workflow-specifications.md) | 3–6d |
| **T0** | M3-Foundation | Ports under Telegram only | No | [CARD-29](CARD-29-messenger-port.md), [CARD-30](CARD-30-user-identities.md), [CARD-31](CARD-31-platform-capabilities.md) | 2–4d |
| **T1** | M3-Services | Customer application services | No | [CARD-32](CARD-32-customer-application-services.md) | 2–4d |
| **T2** | M3-Instagram | Instagram Messaging (masked customer) | **Yes — Instagram DM** | [CARD-33](CARD-33-instagram-messaging-channel.md) | 5–8d |
| **T2-Web** | M3-Web | Instagram-style web + **SnusThai Hub** Astro MVP | **Yes — Web** | [CARD-35](CARD-35-instagram-style-web-storefront.md), [CARD-37](CARD-37-snusthai-hub-astro-mvp.md) | 5–8d |
| **T2-Funnel** | M3-Funnel | IG → web forms → private bot/staff | **Bridge** | [CARD-36](CARD-36-instagram-web-telegram-funnel.md) | 3–5d |
| **T3** | M3-Expand | Additional channels | LINE | [CARD-16](CARD-16-line-api-integration.md) (re-scoped) | 5–8d each |

```
T0-Spec  CARD-34 Conversation & workflow specifications
         (as-built Telegram catalog + Instagram mask package)
              │ can parallel T0 ports
              ▼
T0  CARD-29 Messenger ──┬──▶ CARD-30 Identities
                        └──▶ CARD-31 Capabilities
                                      │
                                      ▼
T1  CARD-32 Customer services  ◀── soft-gated by CARD-34 customer core
                                      │
                                      ▼
T2  CARD-33 Instagram Messaging  ◀── Phase 2 DM; HARD-gated by CARD-34 IG package
T2-Web  CARD-35 Instagram-style web storefront
        Brand → Store → Menu → Items (auto from Telegram backend)
        Spec: docs/Specifications/WEB-INSTAGRAM-STYLE-STOREFRONT.md
                                      │
                                      ▼
T3  CARD-16 LINE (optional) · full web checkout (later)
```

---

## 3b. Tier 0-Spec — Conversation & workflow specifications

**Card:** [CARD-34](CARD-34-conversation-workflow-specifications.md)  
**Index:** [`docs/Specifications/README.md`](../Specifications/README.md)

**Exit criteria:** Customer flows inventoried and core commerce paths specified as-built; Instagram In/Out package **accepted**; template + index live.

| Gate | Effect |
|------|--------|
| Soft | CARD-32 service boundaries should match named flow IDs |
| **Hard** | CARD-33 / CARD-16 must not invent chat paths outside accepted specs |

Can run **in parallel** with T0 ports (29–31). Prefer finishing **customer core + IG package** before T2 coding starts.

---

## 4. Tier 0 — Foundation ports (Telegram-only behavior)

**Exit criteria:** all outbound order/status/kitchen/rider notifies go through `Messenger`; users dual-write a Telegram identity row; capability matrix exists and is unit-tested; **zero customer-visible Telegram UX change**.

| Card | Deliverable | Risk if skipped |
|------|-------------|-----------------|
| **CARD-29** | `Messenger` protocol + `TelegramMessenger`; wire `notifications.py` (broadcast/dispatch optional same PR series) | Every channel reimplements send |
| **CARD-30** | `user_identities` table; dual-write on Telegram user create/login; resolve API | Cannot map IG PSID → internal user |
| **CARD-31** | `PLATFORM_CAPS` + `features_for(platform, role)`; docs for masks | Feature creep / unsupported IG flows |

**Telegram compatibility:** `get_shared_bot()` may remain as an implementation detail of `TelegramMessenger`. Public helpers (`notify_order_confirmed`, etc.) keep signatures.

---

## 5. Tier 1 — Customer application services

**Exit criteria:** PromptPay/cash/crypto order creation and cart ops usable as pure functions returning DTOs; at least one Telegram payment path calls the service without behavior change; tests cover service success/failure paths.

| Card | Deliverable |
|------|-------------|
| **CARD-32** | `bot/services/{cart,checkout,order_query,tickets}.py` — thin over existing methods |

**Does not include:** admin goods FSM, kitchen/rider UI, driver live location, full keyboard abstraction.

---

## 6. Tier 2 — Instagram (Phase 2 channel)

**Exit criteria:** Meta Instagram Messaging webhook live (flag-gated); customer can complete a **masked** journey on IG that shares the same orders/payments backend; elevated roles remain Telegram-only; Telegram regression suite green.

| Card | Deliverable |
|------|-------------|
| **CARD-33** | Instagram adapter + webhook + masked customer flows + outbound via Messenger router |

### Instagram capability mask (by design)

| Feature | Telegram | Instagram (T2) |
|---------|----------|----------------|
| Browse menu / search | Full | Limited (carousel / text list) |
| Cart + modifiers | Full | Simplified (core modifiers only or text) |
| Checkout address + phone | Full | Full (text + optional location) |
| Live GPS / rider ETA stream | Full | **Off** |
| Delivery chat live location | Full | **Off** (text status only) |
| PromptPay QR + slip photo | Full | QR image + slip image (Meta media) |
| Crypto payment instructions | Full | Text + copyable address |
| Order status / history | Full | Full (text + quick replies) |
| Support tickets | Full | Open + reply text |
| Customer AI assistant | Full | Optional short-turn |
| Admin / kitchen / driver | Full | **Off** |
| Broadcasts | Full | Template/policy constrained (opt-in later) |

### Privilege policy

| Actor | Surface |
|-------|---------|
| Customer | Telegram (full) + Instagram (mask) |
| Admin / Owner / Superadmin | **Telegram only** |
| Kitchen / Rider staff | **Telegram groups only** |
| Driver dispatch | **Telegram only** |

---

## 7. Tier 3 — Later channels (not Phase 2)

| Channel | Card | When |
|---------|------|------|
| LINE | CARD-16 (re-scoped: ports + services first, no full handler rewrite) | After T2 stable |
| Webchat | Future card | When product wants full map/UI control |

LINE remains valuable for Thailand reach but is **not** Phase 2 in this plan.

---

## 8. Implementation order (execution checklist)

### Sprint A0 — T0-Spec (can parallel A)

1. [ ] CARD-34 template + index + inventory  
2. [ ] Customer core flows C-05…C-18 + cross-cutting order/payment  
3. [ ] Accept Instagram Phase 2 In/Out package in Specs README  

### Sprint A — T0 (ports)

4. [ ] CARD-29 Messenger + Telegram adapter + notifications wiring  
5. [ ] CARD-30 `user_identities` migration + dual-write  
6. [ ] CARD-31 capabilities module + unit tests  
7. [ ] Flag: none required (behavior-preserving)

### Sprint B — T1 (services)

8. [ ] CARD-32 cart + checkout DTOs; migrate one Telegram payment path  
9. [ ] Migrate remaining customer payment paths when stable  
10. [ ] order_query + tickets services for IG reuse  

### Sprint C — T2 (Instagram DM) — requires CARD-34 IG package accepted

11. [ ] Meta app, Instagram Business + Page, webhooks, secrets in env  
12. [ ] CARD-33 inbound adapter → identity resolve → services  
13. [ ] Outbound Messenger multi-backend (`telegram` default, `instagram` if linked)  
14. [ ] Implement **only** flows in accepted IG package  
15. [ ] `INSTAGRAM_CHANNEL_ENABLED` flag (default off)  
16. [ ] E2E: IG happy path + Telegram regression  

### Sprint C-Web — T2-Web / SnusThai Hub (can parallel C; does not need Meta)

17. [ ] **CARD-37 SnusThai Hub** Astro setup + age gate + hero + social (LINE/WA/IG)  
18. [ ] Product gallery (MD content Mode A) + filters + PhotoSwipe + inquire CTA  
19. [ ] Lead form + Resend (+ optional CARD-36 webhook)  
20. [ ] Blog MDX + sitemap/SEO  
21. [ ] CARD-35 Mode B later: catalog API from Telegram backend  
22. [ ] Spec acceptance: SNUSTHAI-HUB-MVP §10

### Sprint D — T3 (optional)

21. [ ] CARD-16 LINE using same ports/services + LINE flow masks in specs  
22. [ ] In-web checkout (CARD-32) if product wants full web ordering  

---

## 9. Config / ops (preview)

```bash
# Existing Telegram (unchanged)
TOKEN=...
OWNER_ID=...
MULTI_BOT_ENABLED=false

# Instagram (CARD-33)
INSTAGRAM_CHANNEL_ENABLED=false
INSTAGRAM_PAGE_ACCESS_TOKEN=
INSTAGRAM_APP_SECRET=
INSTAGRAM_VERIFY_TOKEN=
INSTAGRAM_WEBHOOK_PATH=/webhooks/instagram
# Optional: default brand for IG entry
INSTAGRAM_DEFAULT_BRAND_ID=1
```

Webhook hosting: HTTPS endpoint co-located with bot process (aiohttp/FastAPI) or reverse-proxied — same deployment unit preferred.

---

## 10. Risks

| Risk | Mitigation |
|------|------------|
| Meta app review / messaging permissions | Start with test IG account; feature-flag production |
| 24h messaging window / policy | Prefer user-initiated threads; status push within window |
| Limited interactive UI on IG | Masked flows; deep-link to Telegram for full UX when needed |
| Identity collision (same person on TG + IG) | Manual or code-based account link later; dual identity rows OK |
| Scope creep to “full parity” | Capability matrix + PR checklist against mask |
| Handler rewrite pressure | Reject PRs that force PlatformContext on all Telegram handlers |

---

## 11. Success metrics

| Tier | Done when |
|------|-----------|
| T0-Spec | Spec index complete for customer core; IG package accepted; template in use |
| T0 | Notify path uses Messenger; identities dual-written; caps tested; Telegram UX identical |
| T1 | Checkout service creates same order rows as legacy path; inventory reserve identical |
| T2 | Flag-on: IG user places PromptPay (or cash) order visible in Telegram admin; status notifies on IG |
| T3 | Second non-TG channel reuses ≥80% of services without new domain logic |

---

## 12. Related docs

| Doc | Role |
|-----|------|
| [CARD-34](CARD-34-conversation-workflow-specifications.md) | Formal workflow & chat specs |
| [Specifications/README.md](../Specifications/README.md) | Spec index |
| [CARD-29](CARD-29-messenger-port.md) | Messenger port |
| [CARD-30](CARD-30-user-identities.md) | Identity dual-write |
| [CARD-31](CARD-31-platform-capabilities.md) | Feature masks |
| [CARD-32](CARD-32-customer-application-services.md) | Services |
| [CARD-33](CARD-33-instagram-messaging-channel.md) | Instagram Phase 2 DMs |
| [CARD-35](CARD-35-instagram-style-web-storefront.md) | Auto web storefront |
| [WEB-INSTAGRAM-STYLE-STOREFRONT.md](../Specifications/WEB-INSTAGRAM-STYLE-STOREFRONT.md) | Web storefront full spec |
| [CARD-16](CARD-16-line-api-integration.md) | LINE Tier 3 (re-scoped) |
| [FEATURE_CARDS.md](../FEATURE_CARDS.md) | Status board |
| [MASTER-PLAN.md](../MASTER-PLAN.md) | Milestone sequencing |
