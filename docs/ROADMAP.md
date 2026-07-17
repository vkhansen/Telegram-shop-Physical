# Project Roadmap — Telegram-shop-Physical (Growth Track)

> **Sequencing now lives in [`MASTER-PLAN.md`](MASTER-PLAN.md)** — the go-live gate, milestone order, and launch checklist. This file is retained for the **growth-track narrative** (platform scale, AI, multi-platform). [`FEATURE_CARDS.md`](FEATURE_CARDS.md) remains the **status** source of truth; when they disagree, trust `FEATURE_CARDS.md` and update here.

Last reviewed: 2026-07-17

> **Do not plan from this file for sequencing.** Prefer [`FEATURE_CARDS.md`](FEATURE_CARDS.md) + [`CLEAR-START.md`](CLEAR-START.md) + [`MASTER-PLAN.md`](MASTER-PLAN.md). This document is a growth narrative; several checkboxes below are historical.

---

## Where we are

- **Spine + commerce cards shipped** through CARD-40 (ports, services, white-label web, parity freeze) plus Phases 1–5, M0–M2, RC/FC suites. See [`FEATURE_CARDS.md`](FEATURE_CARDS.md) DONE table and [`done/`](done/).
- **M0 launch gate green; M2 dispatch shipped; M3 platform spine archived 2026-07-17** (CARD-29–32 · 35 · 38 · 40). Remaining open work: CARD-39 OAuth ops, CARD-36 polish, CARD-33/16 channel depth, CARD-34 specs — tracked on the board.
- Multi-brand runtime ships behind `MULTI_BOT_ENABLED`.
- **Quality gate** historically green post-M0 (~47–48% coverage, `fail_under` 30). Re-run `pytest tests/` for current numbers. Handler layer, notifications, i18n, and CLI remain comparatively light on tests.

## Guiding principles

1. **Ship UX wins before infra epics.** A 3-day cart polish beats a 2-week platform refactor for customer-visible value.
2. **Let DB models lead the runtime.** Multi-brand tables already exist — runtime work (CARD-19) unblocks downstream cards cheaply.
3. **Defer transport-layer rewrites.** Multi-channel uses thin ports + customer services (CARD-29–32), not a full handler rewrite. **Instagram is Phase 2** (CARD-33); LINE is Tier 3 (CARD-16).
4. **Parallelizable > sequential.** AI admin (CARD-17) touches admin surfaces only and can ship beside CARD-19.

---

## Dependency graph

```
CARD-21 (Cart Stub) ──┐
                      ├──▶ CARD-19 (Multi-Brand Runtime) ✅
  brand/store DB ─────┘              │
                                     ▼
              CARD-34 (workflow & chat specs) ── hard gate ──┐
              CARD-29/30/31 (ports) ──▶ CARD-32 (services)   │
                                              │              │
                                              ▼              ▼
                                     CARD-33 (Instagram Phase 2)
                                              │
                                              ▼
                                     CARD-16 (LINE Tier 3)

CARD-17 (Grok Admin) ✅ ──▶ CARD-22 (Grok Customer Assistant) ✅
```

- **CARD-21** was a soft prereq for CARD-19: brand-switch save/delete/stay UX.
- **CARD-19** is done — brand context is required by channel adapters (IG default brand, later multi-page).
- **CARD-34** formalizes as-built Telegram flows + Instagram mask package (hard gate for CARD-33).
- **CARD-29–32** are the Telegram-preserving foundation (Messenger, identities, caps, services).
- **CARD-33 (Instagram)** is Phase 2 — first non-Telegram customer surface; only specified flows.
- **CARD-16 (LINE)** is Tier 3 — reuses the same ports/services; no full PlatformContext rewrite.
- **CARD-17 / CARD-22** are done.

---

## Milestones

### M1 — UX Polish  *(✅ SHIPPED 2026-06-02 — CARD-21 complete)*

**Goal:** Customer-visible cart experience that behaves like a modern delivery app.

- [x] **CARD-21** — Persistent Cart Stub + Brand/Store Switch Guards *(3–5d)*
  - Cart stub banner on every menu refresh
  - Flash animation on add-to-cart
  - Brand-switch save/delete/stay prompt (`SavedCart` model)
  - Same-brand store switch with availability check
  - `ShoppingCart.expires_at` TTL with lazy cleanup

**Exit criteria:** Cart banner visible in all menu screens; brand switch no longer silently orphans items; expired carts self-clean.

---

### M2 — Platform Scale  *(✅ SHIPPED — CARD-19 complete)*

**Goal:** One backend process runs N independent branded bots off shared business logic.

- [ ] **CARD-19** — Multi-Brand Bot Coordination *(10–14d)*
  - `BotConfig` model + encrypted token storage
  - `BotPool` multi-bot runtime (polling/webhook per bot)
  - `BrandContextMiddleware` — automatic brand injection on every update
  - Brand-scoped queries across goods/orders/settings
  - Per-brand rate limiting
  - CLI for bot lifecycle (add/remove/rotate tokens)
  - Backward-compat flag: `MULTI_BOT_ENABLED=false` keeps single-bot deploys working

**Exit criteria:** Two test bots running off one process, fully isolated carts/orders/menus; feature flag lets existing deployments opt out.

---

### M3 — Admin Intelligence  *(✅ SHIPPED — CARD-17 complete; CARD-22 customer assistant also done)*

**Goal:** Natural-language admin ops replace rigid button navigation for bulk tasks.

- [ ] **CARD-17** — Grok AI Admin Assistant *(5–7d)*
  - Pydantic action schemas as guardrails
  - Menu edits via natural language ("raise all dessert prices by 10%")
  - Spreadsheet/CSV import with column inference
  - Order and chat search by natural query
  - Dry-run preview before any mutation

**Exit criteria:** Admin can perform the five highest-friction tasks from CLAUDE.md without touching the button UI; all mutations go through dry-run confirmation.

---

### M4 — Multi-Platform Reach  *(Telegram primary; Instagram Phase 2)*

**Goal:** Customers can order from Instagram (Phase 2) and later LINE on the **same backend**, while Telegram remains the full-privilege main app (admin, kitchen, drivers).

Full sequencing: [`docs/later/MULTI-CHANNEL-TIERED-PLAN.md`](later/MULTI-CHANNEL-TIERED-PLAN.md)

- [ ] **T0-Spec — CARD-34** Conversation & workflow specifications *(3–6d)*
  - As-built Telegram catalog; template + index under `docs/Specifications/`
  - Instagram In/Out package **accepted** before CARD-33 coding
- [ ] **T0 — CARD-29** Messenger port + Telegram default *(1–2d)*
- [ ] **T0 — CARD-30** User identities dual-write *(1–2d)*
- [x] **T0 — CARD-31** Platform capability / feature mask *(done: PLATFORM_CAPS×ROLE + resolve)*
- [ ] **T1 — CARD-32** Customer application services *(2–4d)*
- [ ] **T2 — CARD-33** Instagram Messaging channel — **Phase 2** *(5–8d)*
  - Meta webhook + **only** flows from accepted CARD-34 IG package
  - Admin/kitchen/driver stay Telegram-only
  - Flag: `INSTAGRAM_CHANNEL_ENABLED`
- [ ] **T2-Web — CARD-35** Instagram-style auto-generated mobile web storefront *(4–7d)*
  - Spec: [`WEB-INSTAGRAM-STYLE-STOREFRONT.md`](Specifications/WEB-INSTAGRAM-STYLE-STOREFRONT.md)
  - Hierarchy: Brand → Store → Menu → Items from Telegram backend
  - Order handoff to Telegram; flag `WEB_STOREFRONT_ENABLED`
- [ ] **T3 — CARD-16** LINE API *(5–8d after foundation)* — same ports/services pattern

**Exit criteria:** Flag-off Telegram behavior unchanged; flag-on IG order appears in Telegram admin/kitchen; status can notify on the customer’s channel; no requirement for full UI parity across platforms.

---

## Cross-cutting work (not in any card)

These show up in the DRY audit and test gap analysis in `FEATURE_CARDS.md`. Not prioritized as cards yet, but worth tracking:

- **Handler layer tests** — zero coverage on Telegram command/callback/message handlers. Biggest quality risk.
- **i18n resolution tests** — locale switching and string fallback paths untested.
- **`bot_cli.py` tests** — 1460+ lines, zero tests.
- **Notification system tests** — `bot/payments/notifications.py` untested, but touches every order.
- **Concurrent inventory race tests** — reservation system has known edge cases.

These were carded and pulled into the launch gate. **Update (2026-06-03):** [CARD-27](done/CARD-27-input-hardening.md) (input validation + error handling) and [CARD-25](done/CARD-25-test-suite-recovery.md) (test-suite recovery — `smoke` marker, marker reconcile, gate ratchet 25→30; suite green at 46.98%) are both **✅ done**. Handler-layer and CLI tests remain the largest standing gap.

---

## Out of scope (for now)

- Loyalty/points program
- Native driver mobile app — note: in-Telegram automated GPS matching/dispatch shipped as [CARD-26](done/CARD-26-live-gps-driver-matching.md) (M2); a *native app* remains out of scope
- In-app card payments beyond PromptPay QR
- Franchise onboarding self-service UI (CARD-19 ships CLI only)

Revisit after M4.

---

## How to use this document

- **Starting a card:** Move its checkbox from `[ ]` to `[~]` and add your start date.
- **Finishing a card:** Mark `[x]`, update `FEATURE_CARDS.md` status board, move the card doc to `docs/done/`.
- **Adding a card:** Add a new milestone or append to an existing one. Update the dependency graph if needed.
- **Shifting priorities:** Edit the milestone order and update the "Guiding principles" section with the new rationale — don't silently reorder.
