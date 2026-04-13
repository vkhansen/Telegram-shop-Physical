# Testing Guide

## Running Tests

### Quick commands (Docker-based)

```powershell
# Full suite: spin up deps → run all tests → tear down
.\scripts\test\all.ps1

# Only unit tests (no Docker deps needed)
.\scripts\test\run.ps1 -Suite unit

# Integration tests with live db+redis
.\scripts\test\up.ps1
.\scripts\test\run.ps1 -Suite integration
.\scripts\test\down.ps1

# E2E / smoke tests
.\scripts\test\run.ps1 -Suite e2e

# Filter by keyword
.\scripts\test\run.ps1 -Suite unit -K "test_cart"

# Skip coverage collection
.\scripts\test\run.ps1 -Suite all -NoCov
```

### Direct pytest (local venv, no Docker)

```bash
# Unit tests only
pytest tests/unit/

# All tests except e2e
pytest tests/

# Include e2e
pytest tests/ --run-e2e

# Specific marker
pytest -m "cart and not integration"
```

## E2E Gate

E2E tests are **skipped by default**. They require live database and Redis containers.

- Tests are gated by the `--run-e2e` flag (defined in root `conftest.py`)
- Items are skipped if they carry `@pytest.mark.e2e` **or** reside under `tests/e2e/`
- `scripts\test\run.ps1` passes `--run-e2e` automatically for `-Suite e2e` and `-Suite all`

## Marker Taxonomy

| Marker | Scope | Requires |
|---|---|---|
| `unit` | Pure logic, no I/O | nothing |
| `integration` | DB / Redis calls | live containers |
| `e2e` | Full bot flow | live containers + `--run-e2e` |
| `smoke` | Fast sanity subset of e2e | live containers + `--run-e2e` |
| `asyncio` | Async test functions | nothing extra |
| `database` | ORM / schema tests | SQLite in-memory or live db |
| `models` | SQLAlchemy model tests | SQLite in-memory |
| `crud` | Repository layer | SQLite in-memory |
| `orders` | Order domain | SQLite in-memory |
| `cart` | Cart domain | SQLite in-memory |
| `payments` | Payment flow | SQLite in-memory |
| `bitcoin` | BTC payment path | SQLite in-memory |
| `inventory` | Stock tracking | SQLite in-memory |
| `referrals` | Referral system | SQLite in-memory |
| `validators` | Input validation | nothing |

All markers are declared in `pytest.ini`. Add new markers there to avoid `PytestUnknownMarkWarning`.

## Adding a New Marker

1. Add to `pytest.ini` under `markers =`:
   ```ini
   mymarker: short description
   ```
2. Decorate tests: `@pytest.mark.mymarker`
3. Update the table above.

## Test Layout

```
tests/
  conftest.py          # shared fixtures: env vars, db_engine (SQLite in-memory)
  unit/                # no external deps
  integration/         # requires db + redis containers
  e2e/
    test_smoke.py      # smoke suite (4 fast sanity tests)
    test_full_order_flow.py
    test_scenarios.py
    test_smart_navigation_flow.py
    test_coverage_gaps.py
    menu_loader.py
    sample_menu.json
    run_e2e.py
```

Root `conftest.py` owns the `--run-e2e` CLI option only. Do not add fixtures there.

## Coverage Output

| Artifact | Location |
|---|---|
| HTML report | `htmlcov/index.html` |
| XML (CI) | `coverage.xml` |

Coverage is collected automatically by `scripts\test\run.ps1` unless `-NoCov` is passed.
Threshold and omit rules are in `pyproject.toml` (`[tool.coverage.*]`).

## Local vs Docker Deps

| Suite | db container | redis container |
|---|---|---|
| unit | no | no |
| integration | yes (`telegram_shop_db_test`) | yes (`telegram_shop_redis_test`) |
| e2e | yes | yes |

`scripts\test\up.ps1` starts `telegram_shop_db_test` and `telegram_shop_redis_test` from `docker-compose.test.yml` and waits for the db healthcheck before returning.
