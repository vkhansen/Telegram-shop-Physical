# Master Plan — Telegram Shop (Physical / Thailand Restaurant Delivery)

> **The single source of truth for sequencing.** This file answers one question: *what stands between us and a safe go-live, and in what order do we close it?*
>
> - **Status board** (what shipped): [`FEATURE_CARDS.md`](FEATURE_CARDS.md)
> - **Card details:** `docs/done/`, `docs/backlog/`, `docs/later/`
> - This plan supersedes the milestone ordering in [`ROADMAP.md`](ROADMAP.md), which is retained for the growth-track narrative.

Last reviewed: 2026-06-02

---

## 1. Where we actually are

The bot **runs** and a customer can complete a happy-path order end to end (verified live: PromptPay QR is correct, slip/crypto verification call real APIs, the order state machine and rider-group workflow work). **22 cards are shipped.**

But "running" is not "launch-ready." A code-level audit found the gaps below are **not yet carded** — they are the real blockers:

| Area | Reality | Evidence |
|------|---------|----------|
| Concurrency | Payment handlers hold a DB session across 5–6 awaits → pool exhaustion under load | [CARD-23](backlog/CARD-23-payment-session-refactor.md) |
| Money safety | No duplicate-slip guard, no refund/reversal, no crypto reconciliation | [CARD-24](backlog/CARD-24-payment-integrity.md) |
| Quality gate | 3 failing tests; coverage 19.69% < 25% gate; payment-verification layer 0% covered | [CARD-25](backlog/CARD-25-test-suite-recovery.md) |
| Input safety | No real phone validation; ~23 silent `except: pass` blocks | [CARD-27](backlog/CARD-27-input-hardening.md) |
| Driver dispatch | **No automated GPS driver matching at all** — manual rider-group pickup only | [CARD-26](backlog/CARD-26-live-gps-driver-matching.md) |

## 2. Guiding principles

1. **Money safety and the quality gate come before everything.** You cannot launch payments you can't trust or certify.
2. **Reuse what's built.** The GPS / live-location / chat / state-machine foundation is solid — new work is the missing *layer*, not a rewrite.
3. **Flag-gate new runtime behavior** (`AUTO_DISPATCH_ENABLED`, etc.) so existing single-bot, manual-dispatch deployments keep working.
4. **One bug → fix the whole class** (per `CLAUDE.md`).

---

## 3. The plan — sequenced by milestone

### M0 — Launch Readiness *(Go-Live Gate)* — **P0, ~1.5–2 weeks**

Nothing ships to real customers/money until all three are green.

| Order | Card | What | Effort |
|-------|------|------|--------|
| 1 | [CARD-25](backlog/CARD-25-test-suite-recovery.md) | Fix 3 failing tests (incl. real `metrics.py:75` crash); cover payment-verification layer; restore + ratchet coverage gate | 3–5d |
| 2 | [CARD-23](backlog/CARD-23-payment-session-refactor.md) | Refactor payment handlers to 3-phase session pattern (no DB session held across I/O) | 2–3d |
| 3 | [CARD-24](backlog/CARD-24-payment-integrity.md) | Duplicate-slip guard, refund/reversal path, crypto overpayment + address reclaim | 2–3d |

> Sequence rationale: do **CARD-25 first** so the suite can actually verify 23 and 24 as they land. 23 and 24 can then proceed in parallel if staffed.

**Exit criteria:** CI green at ≥30% coverage; the same slip can't pay twice; cancelling a paid order reverses funds; payment handlers survive a concurrent-load test without pool exhaustion.

---

### M1 — Production Hardening — **P1, ~1 week**

| Card | What | Effort |
|------|------|--------|
| [CARD-27](backlog/CARD-27-input-hardening.md) | Phone validation (Thai + E.164); kill silent `except: pass` | 1–2d |
| [CARD-21](backlog/CARD-21-persistent-cart-stub.md) | Finish cart polish — Phases 4 (brand-switch prompt) & 5 (store-switch availability) | 2–3d |

**Exit criteria:** rider-callable normalized phone numbers; no silent error swallowing in user handlers; cart no longer orphaned on brand/store switch.

---

### M2 — Live Delivery Dispatch — **P2, ~2–3 weeks**

The differentiator that turns a kitchen-notification tool into a delivery platform.

| Card | What | Effort |
|------|------|--------|
| [CARD-26](backlog/CARD-26-live-gps-driver-matching.md) | Driver model + availability + nearest-driver matching + offer/accept + live ETA (4 shippable phases A–D) | 2–3wk |

**Exit criteria:** a `ready` order auto-offers to the nearest online driver, escalates on decline, falls back to manual; customer sees a live, position-driven ETA. Flag-gated.

---

### M3 — Multi-Platform Growth — *deferred, after M2 stable*

| Card | What | Effort |
|------|------|--------|
| [CARD-16](later/CARD-16-line-api-integration.md) | Line API integration (53M Thai users) atop a transport abstraction, inheriting the shipped multi-brand context | 5–8d |

**Already shipped on the growth track:** multi-brand runtime ([CARD-19](done/CARD-19-multi-brand-bot-coordination.md)), Grok admin ([CARD-17](done/CARD-17-grok-admin-assistant.md)) and customer ([CARD-22](done/CARD-22-grok-customer-assistant.md)) assistants.

---

## 4. Dependency graph

```
M0 (Go-Live Gate)
  CARD-25 (tests) ──┬─▶ CARD-23 (session refactor)
                    └─▶ CARD-24 (payment integrity)
        │
        ▼
M1  CARD-27 (input)   CARD-21 (cart polish)
        │
        ▼
M2  CARD-26 (GPS driver dispatch)        ◀── reuses CARD-02/13/15 GPS+chat foundation
        │
        ▼
M3  CARD-16 (Line)   ◀── inherits CARD-19 brand context (shipped)
```

## 5. Launch checklist (M0 exit)

- [ ] `pytest tests/` passes with 0 failures; coverage ≥ 30%
- [ ] Concurrent-load test on payment flow shows no pool exhaustion
- [ ] Duplicate slip rejected; refund/cancel reverses bonus + flags payment
- [ ] Crypto address pool self-reclaims expired orders
- [ ] `.env` reviewed; bot token rotated if exposed; PromptPay/slip keys set or auto-verify intentionally off
- [ ] Decision recorded: launch with **manual rider dispatch** (CARD-26 is post-launch) — confirmed acceptable for v1

## 6. How to use this document

- **Starting a card:** flip its status to `In Progress` and add a start date in the card file.
- **Finishing a card:** set `100% Complete`, move the file to `docs/done/`, and update the [status board](FEATURE_CARDS.md).
- **Re-prioritizing:** edit the milestone tables here *and* note the rationale — don't silently reorder.
