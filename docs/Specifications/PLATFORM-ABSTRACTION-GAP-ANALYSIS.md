# Platform Abstraction — Gap Analysis & Enforcement

> **Status:** binding for new work · remediation landed 2026-07-18  
> **Law:** [`UNIFIED-BACKEND-CHANNEL-INTERFACE.md`](UNIFIED-BACKEND-CHANNEL-INTERFACE.md)  
> **Goal:** Chat, leads, and checkout depend on **internal `user_id` + brand/domain DB state** — never on transport usernames, Telegram types, or channel-only business rules.

---

## 1. Target contract (enforced)

```text
adapter edge (TG | web | IG | LINE | forms)
  1. authenticate / map (platform, external_id) → user_id
  2. capability mask (channel × role × brand)
  3. normalize channel input → DTOs (incl. location)
  4. call application services only
  5. render ServiceResult / events natively
```

| Must not appear in services | Allowed only in adapters |
|-----------------------------|---------------------------|
| aiogram `Message` / `CallbackQuery` | Parse webhook / bot update |
| Graph / LINE SDK types | HTTP to Meta / LINE |
| “username is identity” | Optional `display_name` for staff CSV |
| Free-text-only delivery for dispatch | Channel UI for pin / maps / geo |
| `get_shared_bot()` for customer DM | Telegram `Messenger` implementation |

**Identity key:** internal `user_id` (= physical column `users.telegram_id` — **legacy name**, not “Telegram-only”).  
**Not** `@username`, not PSID as order FK, not OAuth email as cart key.

**Leads:** brand-scoped rows; `user_id` optional. No chat identity required.

---

## 2. Gap inventory (pre-fix)

| ID | Gap | Severity | Where |
|----|-----|----------|--------|
| G1 | Maps/GPS parse lived only in Telegram `order_handler` | High | TH delivery reliability |
| G2 | IG/LINE checkout: text address only; no lat/lng | High | `channels/*/adapter.py` |
| G3 | Web checkout UI never sent `latitude`/`longitude` | High | `checkout.astro` |
| G4 | `ensure_delivery_profile` wrote phone/address then lat/lng in a **second** session; API used `telegram_id=` | Medium | `checkout.py` + `customer_csv` |
| G5 | Channel display strings hardcoded (`ig:…`, `line:…`) | Low | adapters |
| G6 | Services/docs still say “Telegram ID” for internal user | Medium | export, comments |
| G7 | Telegram handlers still ORM-bypass services (R7 debt) | Medium | cart modifiers, delivery chat |
| G8 | Physical PK column still named `telegram_id` | Low* | schema (rename = big migration) |
| G9 | In-flight FSM/session is channel-local (not shared DB workflow) | Accepted | IG/LINE/TG sessions |
| G10 | Ops surfaces (admin/kitchen/driver) Telegram-only by mask | Accepted | capability design |

\*G8: **do not rename columns in this pass** — map as `user_id` at every service boundary; document ORM column as internal id.

---

## 3. Final changes (this remediation)

### 3.1 Shared location (G1–G3)

| Artifact | Role |
|----------|------|
| `bot/utils/location.py` | Extract coords from Maps URLs / `lat,lng`; normalize delivery payload |
| TG `order_handler` | Call shared util (no private `_extract_coords_from_url`) |
| IG + LINE adapters | Address step → `normalize_delivery_input` → profile lat/lng |
| Web `commerce_api` + storefront | Accept `maps_url` / lat/lng; UI geolocation + Maps paste |

**Policy:** coordinates are source of truth for dispatch. Free-text address is landmark / note when GPS present.

### 3.2 Delivery profile single writer (G4, G6)

| Artifact | Role |
|----------|------|
| `create_or_update_customer_info` | Primary arg `user_id` (`telegram_id=` deprecated alias); optional lat/lng |
| `checkout.ensure_delivery_profile` | One write path; `display_name` preferred over “username” |

### 3.3 Identity display (G5)

| Artifact | Role |
|----------|------|
| `bot/platform/identity.display_name(platform, external_id)` | Stable staff-facing label |
| Adapters | Use helper; never invent identity from username |

### 3.4 Boundary tests

| Test | Asserts |
|------|---------|
| `tests/unit/utils/test_location.py` | Maps URL, plain coords, free-text |
| `tests/unit/platform/test_abstraction_boundaries.py` | Services must not import aiogram; location util is pure |
| Channel tests | IG profile receives lat/lng when Maps URL pasted |

### 3.5 Explicit non-goals (this pass)

- Alembic rename `users.telegram_id` → `users.id`
- Full TG handler → service migration (G7 tracked; no new shortcuts)
- Shared durable multi-channel checkout FSM in Redis/Postgres
- Live location on IG/LINE (mask out)

---

## 4. Acceptance checklist

- [x] One location normalizer used by TG + IG + LINE + web body path  
- [x] Delivery profile service API uses `user_id` / `display_name`  
- [x] IG/LINE store lat/lng when customer sends Maps link or `lat,lng`  
- [x] Web checkout can submit geolocation or Maps URL  
- [x] Unit tests for location + abstraction boundary  
- [ ] G7 remaining: migrate cart modifier + delivery_chat ORM to services (follow-up)  
- [ ] Optional: DB column rename migration (follow-up epic)

---

## 5. Adapter checklist (copy into PR reviews)

```text
[ ] No new business rule only in handlers/**
[ ] resolve (platform, external_id) → user_id before services
[ ] can(channel, feature) / brand caps before mutation
[ ] location via bot.utils.location (not ad-hoc regex)
[ ] outbound customer notify via messenger_router / Messenger port
[ ] leads/bookings only via leads_bookings service
```
