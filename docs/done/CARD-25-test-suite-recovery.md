# CARD-25: Test Suite Recovery & Payment-Layer Coverage

## Status: ✅ DONE (2026-06-03) — `smoke` marker registered, marker drift reconciled, gate ratcheted 25→30

> **Closed 2026-06-03.** Registered the `smoke` marker in `pytest.ini` and `pyproject.toml`, reconciled the marker lists across both files (added `payments`, `e2e`, `smoke` to `pyproject.toml`), and raised `fail_under` 25→30. Verified: `pytest tests/` now collects 1584 tests with no collection error and runs **1434 passed, 150 skipped, 0 failures** at **46.98%** coverage.

## Priority: P0 — Launch Blocker
## Effort: Small (≤0.5d remaining)
## Phase: Launch Readiness — Quality Gate

---

## ⚠️ Re-scope (2026-06-02 fresh run on Linux)

The original "red suite" picture was based on `fail_output.txt`, a **stale Windows artifact** (`D:\GitHub\…`). A fresh run on this machine tells a very different story:

```
.venv/bin/python -m pytest tests/   # (strict-markers relaxed to get past collection)
→ 1426 passed, 150 skipped, 1 warning in 71.85s
→ Total coverage: 46.89%   (gate is 25; proposed ratchet is 30 — both already cleared)
```

Almost all of this card's original scope is **already done**:

- **The 3 named failures are all fixed in the current tree:**
  - `metrics.py:75` set-mutation crash → fixed (`bot/monitoring/metrics.py:88-90` snapshots with `list(step_set)[:to_remove]` then `difference_update`); regression test `test_prunes_when_max_exceeded` in `tests/unit/test_monitoring.py:170`.
  - `test_middleware.py` locale mock → fixed (mock now sets `from_user`, e.g. `test_middleware.py:534`).
  - `test_tasks.py` `Categories` PK → fixed (`test_resets_all_goods` uses `category_name=cat.name`, the real PK).
- **Payment-verification layer is covered, not 0%:** `tests/unit/payments/test_slip_verify.py` (~22 tests), `tests/unit/payments/test_chain_verify.py` (~37), `tests/unit/payments/test_payment_checker.py` (~7). Source files `slip_verify.py`, `chain_verify.py`, `verifiers/{btc,ltc,sol,usdt_sol}.py`, `tasks/payment_checker.py` all exist and are exercised.
- **Coverage is 46.89%**, already above both the 25% gate and the proposed 30% floor.

### The one thing actually still red

`pytest tests/` as configured **aborts at collection** because `tests/e2e/test_smoke.py:18` declares `pytestmark = [pytest.mark.e2e, pytest.mark.smoke]` but **`smoke` is not a registered marker**, and `--strict-markers` is on (`pytest.ini` / `pyproject.toml` addopts). Collection error → CI red, even though every test that runs passes. There is also **marker-config drift**: `pytest.ini` registers `e2e/payments/orders/models/crud/inventory/referrals/bitcoin`, but `[tool.pytest.ini_options]` in `pyproject.toml` is missing those — the two must be reconciled (pytest.ini currently wins, masking the gap).

## Remaining Scope (small)

- **Register the `smoke` marker** in `pytest.ini` (and reconcile the marker list with `pyproject.toml` so they don't drift). This alone turns `pytest tests/` green.
- **Ratchet `fail_under` 25 → 30** in `pyproject.toml:167` — current 46.89% clears it with margin.
- *(Optional, nice-to-have)* add the `tests/integration/test_checkout_payment.py` happy-path smoke test — the only originally-scoped file that doesn't yet exist. Not a launch blocker given the existing payment-layer unit coverage.

## Files to Modify

| File | Changes |
|------|---------|
| `pytest.ini` | Register `smoke` marker; reconcile marker list |
| `pyproject.toml` | Add missing markers to `[tool.pytest.ini_options]`; raise `fail_under` 25 → 30 |
| `tests/integration/test_checkout_payment.py` *(optional/new)* | Happy-path checkout → confirm smoke test |
| ~~`bot/monitoring/metrics.py`~~ | ✅ already fixed |
| ~~`tests/unit/test_middleware.py`~~ | ✅ already fixed |
| ~~`tests/unit/test_tasks.py`~~ | ✅ already fixed |
| ~~`tests/unit/payments/test_slip_verify.py`~~ | ✅ exists (~22 tests) |
| ~~`tests/unit/payments/test_chain_verify.py`~~ | ✅ exists (~37 tests) |
| ~~`tests/unit/payments/test_payment_checker.py`~~ | ✅ exists (~7 tests) |

## Acceptance Criteria

- [x] `pytest tests/` exits 0 with **0 failures and no collection error** (`smoke` registered) — 1434 passed, 150 skipped
- [x] `bot/monitoring/metrics.py` no longer crashes when the conversion set exceeds its cap (regression test added)
- [x] `slip_verify.py`, `chain_verify.py`, `verifiers/*`, and `payment_checker.py` each have meaningful coverage (no live network calls in tests)
- [x] Coverage ≥ 30% and `fail_under` raised to match (coverage 46.98%; gate raised 25→30)
- [x] CI `test` job is green on `master`

## Test Plan

This card *is* the test plan; success = the suite passes and the payment layer is exercised. Verify with:

```
docker compose -f docker-compose.test.yml up --abort-on-container-exit
# or locally:
pytest tests/ --cov=bot --cov-branch
```

## Links

Gate for go-live in [`../MASTER-PLAN.md`](../MASTER-PLAN.md). Directly validates [CARD-24](CARD-24-payment-integrity.md) and [CARD-23](CARD-23-payment-session-refactor.md).
