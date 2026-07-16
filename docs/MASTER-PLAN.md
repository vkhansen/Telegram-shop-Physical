# Master Plan — Telegram Shop (Physical / Thailand Restaurant Delivery)

> **The single source of truth for sequencing.** This file answers one question: *what stands between us and a safe go-live, and in what order do we close it?*
>
> - **Clear start / next work:** [`CLEAR-START.md`](CLEAR-START.md)
> - **Status board** (what shipped + prioritized backlog): [`FEATURE_CARDS.md`](FEATURE_CARDS.md)
> - **Card details:** `docs/done/`, `docs/later/`
> - This plan supersedes the milestone ordering in [`ROADMAP.md`](ROADMAP.md), which is retained for the growth-track narrative. On conflict with older multi-channel notes, **CLEAR-START + FEATURE_CARDS win**.

Last reviewed: 2026-07-16 (backlog reprioritized: white-label sites CARD-38 first — see CLEAR-START.md)

---

## 1. Where we actually are

The bot **runs** and a customer can complete a happy-path order end to end (verified live: PromptPay QR is correct, slip/crypto verification call real APIs, the order state machine and rider-group workflow work). **28 cards are shipped** (CARD-21 and CARD-27 closed in the 2026-06-02 audit; CARD-25, CARD-23, CARD-24, CARD-26, and CARD-28 closed 2026-06-03).

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

### M3 — White-label public surfaces + multi-channel — *active*

> **Session bootstrap:** [`CLEAR-START.md`](CLEAR-START.md) · **Astro contract:** [`Specifications/WHITE-LABEL-ASTRO-IMPLEMENTATION.md`](Specifications/WHITE-LABEL-ASTRO-IMPLEMENTATION.md) · **Board:** [`FEATURE_CARDS.md`](FEATURE_CARDS.md)  
> **North star:** Auto-generated Brand + Branch sites from backend (any vertical), **Astro Instagram-like UI on desktop and mobile**. Telegram stays primary for orders/ops.  
> **Next epic:** [CARD-38](later/CARD-38-white-label-brand-branch-sites.md)

| Priority | Card | What | Effort |
|----------|------|------|--------|
| **P0** | [CARD-38](later/CARD-38-white-label-brand-branch-sites.md) | White-label brand/branch auto-sites (API → media → web shell) | 6–10d phased |
| P1 | [CARD-29](later/CARD-29-messenger-port.md) | Messenger port | 1–2d |
| P1 | [CARD-30](later/CARD-30-user-identities.md) | User identities dual-write | 1–2d |
| P1 | [CARD-31](later/CARD-31-platform-capabilities.md) | Capability masks | 0.5–1d |
| P1 | [CARD-32](later/CARD-32-customer-application-services.md) | Customer services DTOs | 2–4d |
| P2 | [CARD-36](later/CARD-36-instagram-web-telegram-funnel.md) | Leads/forms bridge | 3–5d |
| P2 | [CARD-34](later/CARD-34-conversation-workflow-specifications.md) | Chat/workflow specs | 3–6d |
| P2 | [CARD-33](later/CARD-33-instagram-messaging-channel.md) | Instagram DM | 5–8d |
| P2 | [CARD-16](later/CARD-16-line-api-integration.md) | LINE | 5–8d |
| P3 | [CARD-37](later/CARD-37-snusthai-hub-astro-mvp.md) | Vertical demo only | parked |

**Exit criteria (CARD-38):** Two brands expose distinct brand+branch pages from one deploy; menu/inventory updates without redeploy; flag-off safe.  
**Already shipped on growth track:** multi-brand runtime ([CARD-19](done/CARD-19-multi-brand-bot-coordination.md)), Grok admin/customer ([CARD-17](done/CARD-17-grok-admin-assistant.md), [CARD-22](done/CARD-22-grok-customer-assistant.md)).

---

## 4. Dependency graph

```
M0 ✅ Launch gate (CARD-25, 23, 24)
M1 ✅ Hardening (CARD-27, 21)
M2 ✅ Dispatch (CARD-26)
        │
        ▼
M3  White-label + multi-channel
        │
        ├─ P0  CARD-38 Brand/Branch auto-sites
        │         A Catalog API → B Media → C Web shell
        ├─ P1  CARD-29 / 30 / 31 / 32
        ├─ P2  CARD-36 leads · 34 specs · 33 IG · 16 LINE
        └─ P3  CARD-37 vertical demo (parked)
```

## 5. Launch checklist (M0 exit)

- [x] `pytest tests/` passes with 0 failures **and no collection error** (`smoke` marker registered); coverage ≥ 30% *(46.98%; `fail_under` raised 25→30)* — ✅ 2026-06-03
- [x] Payment flow no longer holds a DB connection across `await` — all 6 handlers refactored, AST-guarded (CARD-23 ✅ 2026-06-03). *(A live concurrent-load test remains a nice-to-have but is no longer the structural risk.)*
- [ ] Duplicate slip rejected with a user-facing message; refund/cancel reverses bonus + writes a `Refund` record
- [ ] Crypto address pool self-reclaims expired orders
- [ ] `.env` reviewed; bot token rotated if exposed; PromptPay/slip keys set or auto-verify intentionally off
- [ ] Decision recorded: launch with **manual rider dispatch** (CARD-26 is post-launch) — confirmed acceptable for v1

## 6. How to use this document

- **Starting a card:** flip its status to `In Progress` and add a start date in the card file.
- **Finishing a card:** set `100% Complete`, move the file to `docs/done/`, and update the [status board](FEATURE_CARDS.md).
- **Re-prioritizing:** edit the milestone tables here *and* note the rationale — don't silently reorder.
