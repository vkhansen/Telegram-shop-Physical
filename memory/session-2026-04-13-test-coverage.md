---
name: Test coverage + DRY audit session (2026-04-13)
description: R1 refactor landed, Docker e2e parity achieved at 1203 tests / 40.9% coverage, coverage-gap roadmap for next sessions
type: project
---

# Session snapshot — 2026-04-13

## Current status

- **Local venv:** 1203 passed, 0 skipped, 0 xfail, 0 xpass
- **Docker full-suite:** 1203 passed in 165s, coverage **40.85%** (gate=25%)
- **Working tree state:** `docker-compose.test.yml` + `requirements.txt` are modified locally and **not yet committed**. `.env` is local-only (gitignored).
- **Git:** master at `03900f8` (`Create session-2026-04-13-test-coverage.md`), pushed.

## What landed earlier in this session (already committed + pushed)

1. **`test-coverage-audit.md`** — gap report mapping `bot/` modules to test coverage; lists R1–R4 refactor targets with file:line pointers.
2. **`tests/unit/test_review_dry_regressions.py`** (~280 LOC, 36 tests) — pins bugs fixed in `review-DRY.md` that had no test coverage:
   - H1 PAYMENT_PROCESSORS `.get()` fallback + dict completeness
   - H2 bonus Decimal↔str round-trip precision
   - H3 row-lock on `_execute_quick_transition` (structural `inspect.getsource` check)
   - H4/H5 price_feed missing-key + zero-price guards (mocked httpx)
   - M1 VALID_DELIVERY_TYPES frozenset + extract_delivery_fields
   - M3 build_google_maps_link co-validation
   - M10 `_extract_coords_from_url` None on garbage/out-of-range
   - State-machine invariants (terminal states, can't skip, cancel-from-any-non-terminal, happy path connectivity)
   - R2 dead-branch current-behavior pin (so refactoring R2 later is comparable)
3. **R1 refactor** in `bot/handlers/admin/order_management.py`:
   - 4 near-duplicate kitchen/rider handlers collapsed into `QUICK_TRANSITIONS` dict + `_execute_quick_transition` shared body
   - `QuickTransition` frozen dataclass with `pre_commit` / `post_commit` hook tuples
   - Hooks: `_assign_driver_hook`, `_mark_completed_hook`, `_notify_customer_hook`, `_notify_rider_hook`, `_prompt_gps_hook`
   - Notification ordering preserved exactly (kitchen_ready: rider→customer; rider_picked: customer→prompt_gps)
   - Row lock (`with_for_update()`) + `is_valid_transition()` guard kept in the shared body
4. **`tests/unit/test_quick_transitions.py`** (~180 LOC, 12 tests) — R1 structural + dispatch tests.
5. **Skip/xfail cleanup**:
   - `bot/database/methods/update.py::update_category` — removed redundant manual bulk UPDATE of `Goods.category_name`; relies on declared `ForeignKey(..., onupdate="CASCADE")`. Fixed SQLite FK-ordering crash.
   - `tests/unit/database/test_crud.py::test_update_category` — `@pytest.mark.skip` removed.
   - `tests/unit/ai/test_executor.py` — two `@pytest.mark.xfail` markers removed (underlying C4 inventory bug was already fixed).

## Docker e2e parity — debugging chain (uncommitted local changes)

Ran through 5 attempts to get Docker matching the local venv. Every issue and fix:

| # | Task id | Failure | Fix |
|---|---|---|---|
| 1 | `b1phv18b8` | `.env` missing → compose bailed with exit 0 (silently) | Created local `.env` from `.env.example` |
| 2 | `b7hzivh0l` | Redis crashed: `FATAL CONFIG FILE ERROR >>> 'requirepass' wrong number of arguments` — main compose uses `--requirepass ${REDIS_PASSWORD}`, which became `--requirepass ` with empty env | Set `REDIS_PASSWORD=testredispass` in `.env`; changed `docker-compose.test.yml` to `REDIS_PASSWORD: ${REDIS_PASSWORD}` instead of hardcoded `""` |
| 3 | `bnzd3dih1` | `pytest: unrecognized arguments: --timeout=120` — `pytest-timeout` package missing | Added `pytest-timeout~=2.3.1` to `requirements.txt` |
| 4 | `bvdn6pp7d` | `fail_under=25` coverage gate (22.95% running only `tests/e2e/`) — e2e alone doesn't exercise enough code | Changed compose command `tests/e2e/` → `tests/` (full suite), dropped `-x` so one failure doesn't mask others |
| 5 | `bk93iy8aj` | ✅ **1203 passed in 165s, 40.90% coverage** | — |

### Uncommitted local changes to commit on resume

- `requirements.txt` — `pytest-timeout~=2.3.1` added
- `docker-compose.test.yml` — `REDIS_PASSWORD` passthrough; command runs `tests/` not `tests/e2e/`; dropped `-x`
- `.env` — local-only, gitignored (has `REDIS_PASSWORD=testredispass`, test DB/user values)

Suggested commit message:
```
Fix Docker test harness: env passthrough, full suite, pytest-timeout

- Add pytest-timeout (docker-compose command passes --timeout=120)
- docker-compose.test.yml: inherit REDIS_PASSWORD from env instead of
  hardcoding empty string (main compose uses --requirepass which broke
  on empty value)
- Run tests/ (full suite) not tests/e2e/ — e2e alone misses the
  fail_under=25 coverage gate (22.95%); full suite hits 40.9%
- Drop -x so all failures are visible in one run
```

Also consider gitignoring `docker-e2e.log` and `coverage.xml`/`htmlcov/` if not already.

## Coverage map — where to focus next

Total **40.85%** / **6,858 missed lines**. Top 10 modules by missed-line count:

| # | Module | Cov | Missed | Character |
|---|---|---|---|---|
| 1 | `handlers/user/order_handler.py` | 15% | 708 | FSM payment flows; biggest single module |
| 2 | `handlers/admin/user_management_states.py` | 15% | 309 | Admin FSM |
| 3 | `utils/menu_io.py` | **0%** | 296 | Pure-function JSON import/export — **easy win** |
| 4 | `handlers/admin/adding_position_states.py` | 24% | 267 | Admin FSM |
| 5 | `ai/executor.py` | 55% | 247 | Partially tested already |
| 6 | `handlers/user/shop_and_goods.py` | 13% | 223 | Browse/cart |
| 7 | `handlers/user/ticket_handler.py` | 23% | 219 | Support tickets |
| 8 | `handlers/user/delivery_chat_handler.py` | 28% | 197 | Card 15 chat |
| 9 | `handlers/user/cart_handler.py` | 17% | 194 | Cart ops |
| 10 | `handlers/admin/order_management.py` | 33% | 187 | 33% post-R1; was much lower |

### Three categories of gap (attack differently)

**A. Pure functions at 0% or near — quick wins, no harness needed**
- `utils/menu_io.py` 0% / 296 lines — was source of bugs M7 (Decimal→float loss) and H8 (photo IndexError). Highest ROI.
- `utils/cart_stub.py` 0% / 70 lines — check first if it's a real stub or dead code.
- `export/customer_csv.py` 16% / 133 missed — pure CSV generation.
- `keyboards/inline.py` 16% / 162 missed — keyboard builders.

**B. Low-level infra (silent bugs live here)**
- `filters/main` (`HasPermissionFilter`) — had C3 permission-bypass bug, still untested
- `middleware/security.py` 17%, `rate_limit.py` 19%, `locale.py` 27%
- `monitoring/metrics.py` 14%, `recovery.py` 13%
- `tasks/file_watcher.py` 24%, `reservation_cleaner.py` 26%

**C. Handler FSM flows — biggest LOC, hardest without a harness**
- User: order, cart, shop_and_goods, ticket, delivery_chat, orders_view, referral_system, review, store_selection, main
- Admin: user/goods/adding_position/coupon/settings/store/ticket/reference_code/shop_management_states, grok_assistant
- All 10–35%. Each needs ~500 lines of mocks without a harness.

### Recommended session plan

1. **Session A (quick wins):** `utils/menu_io.py`, `utils/cart_stub.py` (check first), `export/customer_csv.py`, `keyboards/inline.py`. Pure functions; ~700 covered lines added. Total should jump to ~47%.
2. **Session B (infra):** `filters/main` (`HasPermissionFilter`), `middleware/{locale,security,rate_limit}`. Closes the C3-style security gap. ~300 lines.
3. **Session C (harness):** Build `tests/helpers/fake_telegram.py` — `FakeCallbackQuery`, `FakeMessage`, `FakeFSMContext`, `FakeBot`. ~200 LOC. Prereq for everything below.
4. **Session D+:** With harness, tackle `order_handler.py` in slices (one `process_*_payment` at a time), then admin FSM states.

## Refactors still pending (tests are in place for R2/R3)

- **R2** `_send_status_notifications` if/elif → dict dispatch (`order_management.py:397`). Dead branch pinned by `TestR2SendStatusNotificationsDeadBranch`. Safe to refactor.
- **R3** `_notify_customer_status` hardcoded `delivered` branch → `STATUS_MESSAGE_KEY` dict (`order_management.py:558`).
- **R4** `order_handler.py` payment-flow pre-order glue — three `process_*_payment_new_message` functions duplicate ~100 lines each. Needs harness first (Session C).

## Local test environment

- **Venv:** `D:/GitHub/Telegram-shop-Physical/.venv` using Python 3.13 (`py -3.13 -m venv .venv`)
  - Why not 3.14: pydantic-core Rust build fails (`ForwardRef._evaluate` signature change)
  - Why not 3.11 (Dockerfile version): not installed locally
  - Dep override: `pydantic>=2.9` instead of pinned `~=2.5.0` (needed for 3.13)
  - Skipped: `pyzbar` (needs zbar system lib; no test imports it)
- **Run local tests:** `.venv/Scripts/python.exe -m pytest tests/ --no-cov -q`
- **Run docker tests:**
  ```
  docker compose -f docker-compose.yml -f docker-compose.test.yml down -v
  docker compose -f docker-compose.yml -f docker-compose.test.yml up --build --abort-on-container-exit bot 2>&1 | tee docker-e2e.log
  ```

## How to resume (checklist)

1. `git status` — expect `docker-compose.test.yml` + `requirements.txt` modified. `.env` present (gitignored).
2. Commit + push those two with the message in "Uncommitted local changes" above.
3. Read `test-coverage-audit.md` and this file for context — don't re-audit.
4. Pick a session from "Recommended session plan" above. Default: **Session A** (quick wins on pure functions — `utils/menu_io.py` first, it's 0% and 296 lines).
5. To track progress: rerun `.venv/Scripts/python.exe -m pytest tests/ --cov=bot --cov-report=term -q | tail -90` after each session — watch total climb from 40.9%.

## Open questions queued for next session

1. `utils/cart_stub.py` — is it a legit stub/interface or dead code? Check imports before writing tests for it.
2. Dockerfile/requirements pydantic version gap — worth bumping `pydantic~=2.9` in requirements.txt to unify local (3.13) and Docker (3.11)? Current Docker build works with pinned 2.5.3 (saw it install successfully), so not urgent.
3. Should `docker-e2e.log`, `coverage.xml`, `htmlcov/` be gitignored? Not currently.
