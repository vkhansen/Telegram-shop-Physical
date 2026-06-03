# CARD-26: Live GPS Driver Matching & Dispatch

## Status: ✅ DONE (2026-06-03) — all four phases (A–D) shipped & flag-gated; see Completion Note

## Priority: P2 — Growth (post-launch differentiator)
## Effort: Very High (2–3 weeks)
## Phase: Delivery Dispatch

---

## Why

Today the bot is, on the delivery side, a **kitchen-workflow tool with group notifications** — not a dispatch platform. There is **no automated driver matching**. The supporting infrastructure is genuinely good (this card builds the matching *layer*, not the foundation):

**Already present (reuse):**
- Customer GPS capture + Google Maps links (CARD-02) and customer live-location (CARD-15).
- Order state machine through `out_for_delivery → delivered` (CARD-09).
- Rider-group notifications + driver↔customer chat relay (CARD-13).
- `Order.driver_id` field and an `AssignDriverAction` for manual/AI assignment (`bot/ai/schemas.py:242`).
- A working Haversine implementation — but only for **store** selection (`bot/handlers/user/store_selection.py:34`), not drivers.

**Missing entirely (build):**
- No `Driver` model, registration/onboarding, or availability/online status.
- No proximity matching, no dispatch queue, no offer→accept→escalate loop.
- No driver-position trail or live ETA (driver "live location" is only a relayed Telegram message, never stored or used for distance).

> Note: `docs/ROADMAP.md` previously listed a "driver mobile app" as out of scope. This card deliberately stays **inside Telegram** (driver bot/handlers + live location), not a native app.

## Scope (phased — each phase shippable)

**Phase A — Driver model & onboarding**
- `Driver` model: telegram id, name, phone, vehicle type, service zones, `is_online`, `is_available`, rating, active-order count.
- Driver registration flow (invite/approval by admin), reusing the existing reference-code pattern.
- Promote `BrandStaff.role='rider'` (already defined, currently unused) into a real driver record.

**Phase B — Availability & location trail**
- Driver toggles online/offline; shares Telegram live location while online.
- `DriverLocationTrail` (driver_id, lat, lng, ts) updated from `edited_message` live-location events.
- `get_available_drivers(lat, lng, zone)` query: online + available + within zone, ranked by distance.

**Phase C — Matching & dispatch**
- On order `ready`, rank nearest available drivers (Haversine, generalized from store_selection).
- Offer to top-N drivers with accept/decline buttons; 60s timeout → escalate to next; fall back to manual rider-group assignment after N rounds.
- Load-balance by active-order count.

**Phase D — Live ETA**
- Compute ETA from current driver position → customer; push ETA updates to the customer on each live-location update, reusing the CARD-15 chat surface.

## Files (new unless noted)

| File | Purpose |
|------|---------|
| `bot/database/models/driver.py` | `Driver`, `DriverLocationTrail` models |
| `bot/handlers/driver/registration.py` | Onboarding/approval |
| `bot/handlers/driver/availability.py` | Online/offline + live-location intake |
| `bot/handlers/driver/job_offer.py` | Offer / accept / decline / timeout |
| `bot/dispatch/matching.py` | `get_available_drivers`, nearest-driver ranking, load balancing |
| `bot/dispatch/eta.py` | Distance→ETA estimation |
| `bot/tasks/dispatcher.py` | Auto-dispatch on `ready`; escalation timeouts |
| `bot/handlers/admin/order_management.py` *(modify)* | Replace `_assign_driver_hook` testing fallback with dispatch trigger |
| `bot/handlers/user/delivery_chat_handler.py` *(modify)* | Feed live ETA into customer updates |

## Acceptance Criteria

- [ ] Drivers can register, be approved, and toggle online/offline
- [ ] Online drivers' live location is stored as a trail
- [ ] `ready` orders auto-offer to the nearest available driver(s) with accept/decline
- [ ] Declines/timeouts escalate, then fall back to manual rider-group assignment
- [ ] Customer sees a live ETA that updates with the driver's position
- [ ] Feature is flag-gated (`AUTO_DISPATCH_ENABLED`) so manual rider-group flow still works

## Test Plan

| Test File | Tests | Assert |
|-----------|-------|--------|
| `tests/unit/dispatch/test_matching.py` | `test_nearest_available_ranked` | Closest online+available driver ranks first |
| | `test_excludes_offline_and_busy` | Offline/at-capacity drivers excluded |
| `tests/unit/dispatch/test_eta.py` | `test_eta_from_distance` | ETA monotonic with distance |
| `tests/unit/handlers/test_job_offer.py` | `test_decline_escalates` | Decline offers to next driver |
| | `test_timeout_falls_back_to_manual` | N timeouts → manual assignment path |
| `tests/integration/test_dispatch_flow.py` | `test_ready_to_delivered_auto` | ready → offer → accept → en route → delivered |

## Links

The growth-track centerpiece in [`../MASTER-PLAN.md`](../MASTER-PLAN.md). Depends on nothing in the launch gate, but should not start until the P0 cards (23/24/25) are closed.

---

## Completion Note (2026-06-03)

All four phases shipped and gated behind `AUTO_DISPATCH_ENABLED` (default off → the manual rider-group flow is untouched). Full suite green: **1460 passed (+13 new), 150 skipped, 48.19% coverage**.

### What was built, by phase

**Phase A — Driver model & onboarding**
- `Driver` + `DriverLocationTrail` models (in `bot/database/models/main.py` alongside the other models — the codebase keeps all models in one module; the card's separate-file suggestion was dropped to guarantee `create_all`/test registration). `Driver` carries telegram id, brand scope (NULL = platform-wide), name/phone/vehicle, `service_zones`, approval `status`, `is_online`/`is_available`, `active_order_count`, rating, and last-known position.
- `/driver` onboarding FSM (`bot/handlers/driver/registration.py`): name → phone → vehicle, lands as `pending`, pings the owner with inline **Approve/Reject** buttons. Approval promotes to a real driver record.

**Phase B — Availability & location trail**
- Online/offline toggle (`bot/handlers/driver/availability.py`); going offline clears availability.
- Driver live location (initial `message` + `edited_message` pin moves) is appended to `DriverLocationTrail` and updates the driver's last position. Location handlers are gated by an approved-driver DB filter and the driver router is registered **before** the user router, so a non-driver's private location edits fall through to the CARD-15 customer handlers.
- `get_available_drivers(lat, lng, zone, brand_id)` + `list_dispatchable_drivers` (`bot/dispatch/matching.py`, `bot/database/methods/driver.py`): online + available + under capacity + in-zone + in-radius, ranked nearest-first with active-order count as a load-balancing tiebreaker.

**Phase C — Matching & dispatch**
- On order `ready`, `bot/dispatch/dispatcher.py` offers to the nearest driver(s) with **Accept/Decline**, escalates on decline/timeout (`AUTO_DISPATCH_OFFER_TIMEOUT`, `AUTO_DISPATCH_MAX_ROUNDS`, `AUTO_DISPATCH_BATCH_SIZE`), and falls back to the manual rider-group notification when exhausted. Assignment is single-threaded (`SELECT … FOR UPDATE`) so two drivers can't claim one order; the winner gets the pickup/delivered action buttons and the customer is notified.
- Wired in at the two `ready` trigger points (`_notify_rider_hook` and `_send_status_notifications`) via `on_order_ready`, which routes to auto-dispatch or the legacy path by flag.

**Phase D — Live ETA**
- `bot/dispatch/eta.py::estimate_eta_minutes` (monotonic in distance). Each driver location update for an `out_for_delivery` order pushes a live ETA to the customer, throttled to only fire when the minute value changes.

### Supporting changes
- Feature flags in `bot/config/env.py`: `AUTO_DISPATCH_ENABLED`, `AUTO_DISPATCH_RADIUS_KM`, `AUTO_DISPATCH_OFFER_TIMEOUT`, `AUTO_DISPATCH_BATCH_SIZE`, `AUTO_DISPATCH_MAX_ROUNDS`, `DRIVER_MAX_ACTIVE_ORDERS`, `DRIVER_AVG_SPEED_KMH`.
- `edited_message` added to `allowed_updates` in `bot/main.py` (live-location pin moves were previously not delivered in polling — also fixes CARD-15's edited-location handlers).
- Driver capacity freed + ETA cache cleared on delivery (`_mark_completed_hook`).
- i18n: 42 new keys added to **all 7 locales** (parity test green).
- Alembic migration `c7e1a2d9f0b3_driver_dispatch_card_26` (head): creates `drivers` + `driver_location_trail`. Uses only `create_table`/`create_index` (Postgres- and SQLite-safe); reuses the existing `Order.driver_id` for the assignment link.

### Tests (13 new)
- `tests/unit/dispatch/test_eta.py` — monotonicity, speed sensitivity, bad-input safety.
- `tests/unit/dispatch/test_matching.py` — nearest-ranked, radius exclusion, zone filter, load-balance tiebreak, Haversine, and the DB query excluding offline/at-capacity/unapproved drivers.
- `tests/unit/handlers/test_job_offer.py` — decline-escalates, timeout→manual-fallback, no-GPS→immediate manual.
- `tests/integration/test_dispatch_flow.py` — full ready → offer → accept → en-route ETA → delivered.

### Notes / follow-ups
- The full Alembic chain can't be applied on SQLite because a pre-existing CARD-24 migration uses `ALTER`-constraint ops SQLite doesn't support; production is Postgres where the chain is clean. This card's own migration upgrades/downgrades cleanly in isolation, and the model definitions are exercised by the 13 tests via `create_all`.
- Dispatch offer state is in-process; a bot restart mid-offer drops in-flight offers (the order simply stays `ready` for manual handling). A durable offer table is a reasonable future hardening if dispatch volume grows.
