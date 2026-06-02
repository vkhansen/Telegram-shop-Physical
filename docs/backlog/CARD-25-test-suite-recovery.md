# CARD-25: Test Suite Recovery & Payment-Layer Coverage

## Status: Not Started

## Priority: P0 — Launch Blocker
## Effort: Medium (3–5d)
## Phase: Launch Readiness — Quality Gate

---

## Why

The repo's own quality gate is **currently red**, and the least-tested code is the code that moves money:

- `fail_output.txt`: **3 failing tests** and total coverage **19.69%**, below the configured `fail_under = 25` gate (`pyproject.toml:167`) → CI reports `FAIL Required test coverage`.
- The entire **payment-verification layer is 0% covered**: `bot/payments/slip_verify.py`, `bot/payments/chain_verify.py`, every `bot/payments/verifiers/*.py`, and `bot/tasks/payment_checker.py` (the cron that auto-confirms crypto). The riskiest paths have no tests.
- At least one failure is a **real production bug**, not a test artifact: `Set changed size during iteration` in `bot/monitoring/metrics.py:75`, which fires once conversion tracking exceeds its cap.

You cannot trust "go-live" while the suite that's supposed to certify it does not pass.

## Scope

- **Fix the 3 failures** and the underlying bugs they expose:
  - `bot/monitoring/metrics.py:75` — iterate over a snapshot (`list(...)`) before pruning.
  - `tests/unit/test_middleware.py:550` — mock spec missing `from_user`; fix the locale-middleware test.
  - `tests/unit/test_tasks.py` — `Categories` primary-key mismatch in the daily-counter reset test.
- **Cover the payment-verification layer** with provider responses mocked (no live API calls): SlipOK/EasySlip/RDCW happy/duplicate/amount-mismatch/no-key paths; BTC/LTC/SOL/USDT verifier parsing and confirmation thresholds; `payment_checker` state transitions (awaiting → detected → confirmed → expired).
- **Restore and ratchet the gate:** get green at ≥25%, then raise `fail_under` to 30% as the new floor.
- **Smoke-cover the highest-traffic handler path** (checkout → payment selection → confirm) at the integration level, since `order_handler.py` (~1,900 lines) is currently untested.

## Files to Modify

| File | Changes |
|------|---------|
| `bot/monitoring/metrics.py` | Fix set-mutation-during-iteration at line 75 |
| `tests/unit/test_middleware.py` | Correct mock spec (`from_user`) |
| `tests/unit/test_tasks.py` | Fix `Categories` PK assumption |
| `tests/unit/payments/test_slip_verify.py` *(new/expand)* | Mock all three providers across outcomes |
| `tests/unit/payments/test_chain_verify.py` *(new)* | Verifier parsing + confirmation thresholds |
| `tests/unit/tasks/test_payment_checker.py` *(new)* | Crypto payment state machine |
| `tests/integration/test_checkout_payment.py` *(new)* | Happy-path checkout → confirm |
| `pyproject.toml` | Raise `fail_under` 25 → 30 once green |

## Acceptance Criteria

- [ ] `pytest tests/` exits 0 with **0 failures**
- [ ] `bot/monitoring/metrics.py` no longer crashes when the conversion set exceeds its cap (regression test added)
- [ ] `slip_verify.py`, `chain_verify.py`, `verifiers/*`, and `payment_checker.py` each have meaningful coverage (no live network calls in tests)
- [ ] Coverage ≥ 30% and `fail_under` raised to match
- [ ] CI `test` job is green on `master`

## Test Plan

This card *is* the test plan; success = the suite passes and the payment layer is exercised. Verify with:

```
docker compose -f docker-compose.test.yml up --abort-on-container-exit
# or locally:
pytest tests/ --cov=bot --cov-branch
```

## Links

Gate for go-live in [`../MASTER-PLAN.md`](../MASTER-PLAN.md). Directly validates [CARD-24](CARD-24-payment-integrity.md) and [CARD-23](CARD-23-payment-session-refactor.md).
