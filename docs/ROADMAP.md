# Project Roadmap — Telegram-shop-Physical

> Master plan for the Bangkok restaurant delivery bot. This file is the **planning** source of truth; [`FEATURE_CARDS.md`](../FEATURE_CARDS.md) is the **status** source of truth (what shipped, what's in flight). When they disagree, trust `FEATURE_CARDS.md` for status and update this file.

Last reviewed: 2026-04-13

---

## Where we are

- **32 cards shipped** across Phases 1–3 (Thailand core, localization, restaurant flow, multi-crypto payments, restaurant-core menu, revenue/trust, ops).
- **4 cards open** in the backlog. One (CARD-19) has database models already merged.
- Codebase is single-bot, single-brand in runtime but has brand/store DB models ready for multi-brand scale.
- Test coverage ~40% after CARD-18 expansion. Handler layer, notifications, i18n, and CLI remain untested.

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

### M2 — Platform Scale  *(target: 3 weeks after M1)*

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

### M3 — Admin Intelligence  *(can run in parallel with M2)*

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

Recommendation: bundle into a single "Test Hardening" card (CARD-22) and slot it between M1 and M2, or treat it as background work during M2.

---

## Out of scope (for now)

- Loyalty/points program
- Driver mobile app (vs. current driver chat handler)
- In-app card payments beyond PromptPay QR
- Franchise onboarding self-service UI (CARD-19 ships CLI only)

Revisit after M4.

---

## How to use this document

- **Starting a card:** Move its checkbox from `[ ]` to `[~]` and add your start date.
- **Finishing a card:** Mark `[x]`, update `FEATURE_CARDS.md` status board, move the card doc to `docs/done/`.
- **Adding a card:** Add a new milestone or append to an existing one. Update the dependency graph if needed.
- **Shifting priorities:** Edit the milestone order and update the "Guiding principles" section with the new rationale — don't silently reorder.
