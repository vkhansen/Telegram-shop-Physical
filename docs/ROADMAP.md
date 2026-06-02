# Project Roadmap — Telegram-shop-Physical (Growth Track)

> **Sequencing now lives in [`MASTER-PLAN.md`](MASTER-PLAN.md)** — the go-live gate, milestone order, and launch checklist. This file is retained for the **growth-track narrative** (platform scale, AI, multi-platform). [`FEATURE_CARDS.md`](FEATURE_CARDS.md) remains the **status** source of truth; when they disagree, trust `FEATURE_CARDS.md` and update here.

Last reviewed: 2026-06-02

---

## Where we are

- **22 numbered cards shipped** (Phases 1–5) plus the RC/FC menu & feature suites — including the multi-brand runtime (CARD-19) and both Grok assistants (CARD-17 admin, CARD-22 customer), which are now **done**, not backlog.
- **Open work is reorganized around go-live.** The launch gate (CARD-23/24/25) and driver dispatch (CARD-26) are tracked in [`MASTER-PLAN.md`](MASTER-PLAN.md).
- Codebase is single-bot, single-brand in runtime but has the multi-brand runtime shipped behind `MULTI_BOT_ENABLED`.
- **Quality gate is currently red** (3 failing tests; 19.69% < 25% coverage; payment-verification layer 0% covered) — see [CARD-25](backlog/CARD-25-test-suite-recovery.md). Handler layer, notifications, i18n, and CLI remain largely untested.

## Guiding principles

1. **Ship UX wins before infra epics.** A 3-day cart polish beats a 2-week platform refactor for customer-visible value.
2. **Let DB models lead the runtime.** Multi-brand tables already exist — runtime work (CARD-19) unblocks downstream cards cheaply.
3. **Defer transport-layer rewrites.** CARD-16 (Line) forces a handler abstraction across the whole codebase; do it once, after brand context is stable.
4. **Parallelizable > sequential.** AI admin (CARD-17) touches admin surfaces only and can ship beside CARD-19.

---

## Dependency graph

```
CARD-21 (Cart Stub) ──┐
                      ├──▶ CARD-19 (Multi-Brand Runtime) ──▶ CARD-16 (Line API)
  brand/store DB ─────┘
  models (merged)

CARD-17 (Grok Admin) ✅ ──▶ CARD-22 (Grok Customer Assistant)
                              reuses: grok_client, rate limiter,
                              tool-call loop, Pydantic schema pattern
```

- **CARD-21** is a soft prereq for CARD-19: its brand-switch save/delete/stay flow is the UX primitive CARD-19's multi-brand runtime needs.
- **CARD-16** is a hard dependency on CARD-19: Line integration should inherit brand context, not add a second dimension of coupling.
- **CARD-17** is done — its Grok client, rate-limit helper, and tool-call executor pattern are directly reusable by CARD-22.
- **CARD-22** is independent of CARD-19/21 — it only touches user handlers and can ship in parallel.

---

## Milestones

### M1 — UX Polish  *(target: 1 week after start)*

**Goal:** Customer-visible cart experience that behaves like a modern delivery app.

- [ ] **CARD-21** — Persistent Cart Stub + Brand/Store Switch Guards *(3–5d)*
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

### M4 — Multi-Platform Reach  *(target: after M2 stable)*

**Goal:** Line users (53M in Thailand, 3.5× Telegram's Thai base) can order from the same backend.

- [ ] **CARD-16** — Line API Integration *(5–8d)*
  - Transport-layer abstraction: `MessagingPlatform` interface over aiogram + Line SDK
  - Shared handler registry emits platform-neutral intents
  - Keyboard builder emits both inline keyboards and Line Flex messages
  - Shared DB, shared brand context (inherited from CARD-19)
  - Per-platform delivery tracking for metrics

**Exit criteria:** Same menu, same orders, same admin tooling across Telegram and Line; one order shows up identically regardless of which platform created it.

---

## Cross-cutting work (not in any card)

These show up in the DRY audit and test gap analysis in `FEATURE_CARDS.md`. Not prioritized as cards yet, but worth tracking:

- **Handler layer tests** — zero coverage on Telegram command/callback/message handlers. Biggest quality risk.
- **i18n resolution tests** — locale switching and string fallback paths untested.
- **`bot_cli.py` tests** — 1460+ lines, zero tests.
- **Notification system tests** — `bot/payments/notifications.py` untested, but touches every order.
- **Concurrent inventory race tests** — reservation system has known edge cases.

These are now carded and pulled forward into the launch gate: see [CARD-25](backlog/CARD-25-test-suite-recovery.md) (test recovery + payment-layer coverage) and [CARD-27](backlog/CARD-27-input-hardening.md) (input validation + error handling). They are **P0/P1 in [`MASTER-PLAN.md`](MASTER-PLAN.md)**, not background work.

---

## Out of scope (for now)

- Loyalty/points program
- Native driver mobile app — note: in-Telegram automated GPS matching/dispatch is now carded as [CARD-26](backlog/CARD-26-live-gps-driver-matching.md) (M2 in the master plan); a *native app* remains out of scope
- In-app card payments beyond PromptPay QR
- Franchise onboarding self-service UI (CARD-19 ships CLI only)

Revisit after M4.

---

## How to use this document

- **Starting a card:** Move its checkbox from `[ ]` to `[~]` and add your start date.
- **Finishing a card:** Mark `[x]`, update `FEATURE_CARDS.md` status board, move the card doc to `docs/done/`.
- **Adding a card:** Add a new milestone or append to an existing one. Update the dependency graph if needed.
- **Shifting priorities:** Edit the milestone order and update the "Guiding principles" section with the new rationale — don't silently reorder.
