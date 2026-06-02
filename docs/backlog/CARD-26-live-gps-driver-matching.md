# CARD-26: Live GPS Driver Matching & Dispatch

## Status: Not Started

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
