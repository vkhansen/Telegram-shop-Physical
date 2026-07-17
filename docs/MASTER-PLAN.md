# Master Plan — Telegram Shop (Physical / Thailand Restaurant Delivery)

> **The single source of truth for sequencing.** This file answers one question: *what stands between us and a safe go-live, and in what order do we close it?*
>
> - **Master archive** (blurb · pitch · WIP · full doc index): [`MASTER-DOCUMENT.md`](MASTER-DOCUMENT.md)
> - **Clear start / next work:** [`CLEAR-START.md`](CLEAR-START.md)
> - **Status board** (what shipped + prioritized backlog): [`FEATURE_CARDS.md`](FEATURE_CARDS.md)
> - **Card details:** `docs/done/`, `docs/later/`
> - This plan supersedes the milestone ordering in [`ROADMAP.md`](ROADMAP.md), which is retained for the growth-track narrative. On conflict with older multi-channel notes, **CLEAR-START + FEATURE_CARDS win**.

Last reviewed: 2026-07-17 (M3 spine archived to `done/` — CARD-29–32 · 35 · 38 · 40; open work = 39/36/33/16/34)

---

## 1. Where we actually are

The bot **runs** and a customer can complete a happy-path order end to end (verified live: PromptPay QR is correct, slip/crypto verification call real APIs, the order state machine and rider-group workflow work). **M0–M2 + M3 spine shipped** (CARD-01–19, 21–32, 35, 38, 40 + RC/FC). See FEATURE_CARDS DONE table. Historical M0 close: 2026-06-03.

**The M0 launch gate is fully green and M2 (live delivery dispatch) is shipped** — quality, concurrency, money-safety, and now automated GPS driver dispatch are all closed. The table below reflects the 2026-06-03 state:

| Area | Reality (2026-06-02) | Evidence |
|------|---------|----------|
| Quality gate | ✅ **Green** — 1434 passed / 150 skipped at **46.98%** coverage; `smoke` marker registered, marker drift reconciled, gate ratcheted 25→30. No collection error. | [CARD-25](done/CARD-25-test-suite-recovery.md) ✅ |
| Concurrency | ✅ **Green** — all 6 payment/order handlers refactored to release the DB session before any Telegram/network I/O (AST-guarded). Also fixed a latent `get_metrics` `NameError`. | [CARD-23](done/CARD-23-payment-session-refactor.md) ✅ |
| Money safety | ✅ **Green** — dup-slip pre-confirm rejection + admin alert; `reverse_payment()`/`Refund` audit trail wired into cancel + expiry (idempotent); crypto overpayment recorded + expired-address reclaim (24h TTL); receiver-name normalized match. Also fixed an invalid-`order_status` bug class in `bot_cli.py`. | [CARD-24](done/CARD-24-payment-integrity.md) ✅ |
| Input safety | ✅ **Done** — phone validator (Thai+E.164) wired into checkout; bare-`except` sweep complete (only 2 intentional swallows left) | [CARD-27](done/CARD-27-input-hardening.md) ✅ |
| Cart UX | ✅ **Done** — all 6 phases incl. brand-switch save/delete/stay and store-switch availability | [CARD-21](done/CARD-21-persistent-cart-stub.md) ✅ |
| Driver dispatch | ✅ **Done** — driver model/onboarding, online/offline + live-location trail, nearest-driver offer/accept/escalate with manual fallback, live ETA; all flag-gated (`AUTO_DISPATCH_ENABLED`) | [CARD-26](done/CARD-26-live-gps-driver-matching.md) ✅ |

## 2. Guiding principles

1. **Money safety and the quality gate come before everything.** You cannot launch payments you can't trust or certify.
2. **Reuse what's built.** The GPS / live-location / chat / state-machine foundation is solid — new work is the missing *layer*, not a rewrite.
3. **Flag-gate new runtime behavior** (`AUTO_DISPATCH_ENABLED`, etc.) so existing single-bot, manual-dispatch deployments keep working.
4. **One bug → fix the whole class** (per `CLAUDE.md`).

---

## 3. The plan — sequenced by milestone

### M0 — Launch Readiness *(Go-Live Gate)* — **✅ COMPLETE (2026-06-03)**

All three gate cards are green; nothing blocks taking real customers/money. *(Re-scoped 2026-06-02; CARD-25, CARD-23, and CARD-24 all closed 2026-06-03.)*

| Order | Card | Outcome | Effort left |
|-------|------|------|--------|
| ✅ | [CARD-25](done/CARD-25-test-suite-recovery.md) **DONE** | `smoke` marker registered, `pytest.ini`↔`pyproject.toml` drift reconciled, `fail_under` ratcheted 25→30. | done |
| ✅ | [CARD-23](done/CARD-23-payment-session-refactor.md) **DONE** | Whole-class fix: all **6** payment/order handlers release the DB session before I/O; AST-guarded. Fixed a latent `get_metrics` `NameError`. | done |
| ✅ | [CARD-24](done/CARD-24-payment-integrity.md) **DONE** | Dup-slip pre-confirm rejection + admin alert; `Refund` model + idempotent `reverse_payment()` audit trail wired into cancel + expiry; crypto overpayment + 24h expired-address reclaim; receiver-name normalized match; `bot_cli.py refund`/`reclaim-addresses`. Also fixed an invalid-`order_status` bug class. Suite: 1447 passed, 47.67%. | done |

> **The M0 launch gate is closed.** CI is green, the payment path no longer holds connections across I/O, the same slip can't pay twice, and reversals leave an auditable `Refund` trail.

**Exit criteria — all met:** CI green at ≥30% coverage (47.67%); the same slip can't pay twice *(friendly rejection + admin alert, not just a DB error)*; cancelling/expiring a paid order reverses funds via a `Refund` record; the payment handlers release the session before I/O (CARD-23, AST-guarded).

---

### M1 — Production Hardening — **✅ COMPLETE (2026-06-02)**

| Card | What | Status |
|------|------|--------|
| [CARD-27](done/CARD-27-input-hardening.md) | Phone validation (Thai + E.164); kill silent `except: pass` | ✅ Done |
| [CARD-21](done/CARD-21-persistent-cart-stub.md) | Cart polish — all 6 phases incl. brand-switch prompt & store-switch availability | ✅ Done |

**Exit criteria met:** rider-callable normalized phone numbers; no silent error swallowing in user handlers (2 intentional swallows commented); cart no longer orphaned on brand/store switch.

---

### M2 — Live Delivery Dispatch — **✅ SHIPPED 2026-06-03**

The differentiator that turns a kitchen-notification tool into a delivery platform.

| Card | What | Status |
|------|------|--------|
| [CARD-26](done/CARD-26-live-gps-driver-matching.md) | Driver model + availability + nearest-driver matching + offer/accept + live ETA (4 shippable phases A–D) | ✅ Done |

**Exit criteria met:** a `ready` order auto-offers to the nearest online driver, escalates on decline/timeout, falls back to manual rider-group; customer sees a live, position-driven ETA. Flag-gated behind `AUTO_DISPATCH_ENABLED` (default off).

---

### M3 — White-label + multi-channel

> **Session bootstrap:** [`CLEAR-START.md`](CLEAR-START.md)  
> **Unified backend law:** [`Specifications/UNIFIED-BACKEND-CHANNEL-INTERFACE.md`](Specifications/UNIFIED-BACKEND-CHANNEL-INTERFACE.md)  
> **Plan:** [`later/MULTI-CHANNEL-TIERED-PLAN.md`](later/MULTI-CHANNEL-TIERED-PLAN.md) · **Board:** [`FEATURE_CARDS.md`](FEATURE_CARDS.md)  
> **North star:** One domain · many adapters · capability masks · **no new Telegram-only business paths**.

#### M3 spine — DONE (archived 2026-07-17)

| Card | What | Detail |
|------|------|--------|
| [CARD-38](done/CARD-38-white-label-brand-branch-sites.md) | White-label sites A+B+C | done |
| [CARD-32](done/CARD-32-customer-application-services.md) | Customer services (cart/checkout/orders/tickets) | done |
| [CARD-29](done/CARD-29-messenger-port.md) | Messenger port | done |
| [CARD-30](done/CARD-30-user-identities.md) | Identities dual-write + resolve | done |
| [CARD-31](done/CARD-31-platform-capabilities.md) | Platform x role caps | done |
| [CARD-40](done/CARD-40-web-telegram-abstracted-feature-parity.md) | Web↔TG abstracted parity A–F | freeze done |
| [CARD-35](done/CARD-35-instagram-style-web-storefront.md) | Storefront patterns | superseded by 38C |

**Spine exit criteria met:** service entrypoints for customer commerce; TG payments/cart/tickets call services; capability masks + parity scorecard; web adapter shipped.

#### M3 open — channels & product polish

| Priority | Card | What | Effort left |
|----------|------|------|-------------|
| **P1** | [CARD-39](later/CARD-39-web-oauth-ticket-portal.md) | Live Google OAuth env (portal code ~90%) | ops |
| P1 | [CARD-36](later/CARD-36-instagram-web-telegram-funnel.md) | CAPTCHA / signed TG opt-in (optional) | polish |
| P2 | [CARD-33](later/CARD-33-instagram-messaging-channel.md) | IG depth (QR/slip/Redis/Meta) | ~45% left |
| ops | [CARD-16](done/CARD-16-line-api-integration.md) | LINE go-live (tokens + HTTPS media) | ops only — code done |
| — | [CARD-34](done/CARD-34-conversation-workflow-specifications.md) | Flow specs | done |
| P3 | [CARD-37](later/CARD-37-snusthai-hub-astro-mvp.md) | Vertical demo only | parked |

**Already shipped (earlier):** multi-brand ([CARD-19](done/CARD-19-multi-brand-bot-coordination.md)), public web catalog/media/storefront.

---

## 4. Dependency graph

```
M0 done · M1 done · M2 done · M3 spine done (29–32 · 35 · 38 · 40)
        |
        v
M3 open  product + channels
        |- P1  CARD-39 OAuth ops · CARD-36 optional polish
        |- P2  CARD-33 · 16 · 34  (adapters only on services)
        +- P3  CARD-37 demo (parked)
```

## 5. Launch checklist (M0 exit)

Code gate closed with CARD-23/24/25. Residual items are **ops / deploy hygiene**, not open engineering cards.

- [x] `pytest tests/` passes with 0 failures **and no collection error** (`smoke` marker registered); coverage >= 30% *(46.98%; `fail_under` raised 25->30)* — done 2026-06-03
- [x] Payment flow no longer holds a DB connection across `await` — all 6 handlers refactored, AST-guarded (CARD-23 done 2026-06-03)
- [x] Duplicate slip rejected with user-facing message; refund/cancel reverses bonus + writes a `Refund` record — CARD-24
- [x] Crypto address pool self-reclaims expired orders — CARD-24
- [ ] **Ops:** `.env` reviewed; bot token rotated if exposed; PromptPay/slip keys set or auto-verify intentionally off
- [x] Decision recorded: v1 could launch with **manual rider dispatch**; CARD-26 auto-dispatch shipped flag-gated (`AUTO_DISPATCH_ENABLED`)

## 6. How to use this document

- **Starting a card:** flip its status to `In Progress` and add a start date in the card file.
- **Finishing a card:** set `100% Complete`, move the file to `docs/done/`, and update the [status board](FEATURE_CARDS.md).
- **Re-prioritizing:** edit the milestone tables here *and* note the rationale — don't silently reorder.
