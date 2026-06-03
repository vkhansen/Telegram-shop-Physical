# CARD-27: Input Validation & Error-Handling Hardening

## Status: ✅ Complete (verified 2026-06-02)

## Priority: P1 — Production Hardening
## Effort: Low (1–2d)
## Phase: Production Hardening

---

## Completion Note (2026-06-02 code audit)

Both weaknesses this card targeted are resolved in the working tree:

- **Phone validation — DONE.** `bot/utils/validators.py:81` defines `validate_and_normalize_phone()`, which accepts `0XXXXXXXXX`, `+66XXXXXXXXX`, and bare `66XXXXXXXXX`, normalizing all to E.164 (`+66…`) and raising `ValueError` on malformed input. It is wired into checkout at `bot/handlers/user/order_handler.py:482` (try/except → localized `order.delivery.phone_invalid` on failure). 15 cases in `tests/unit/utils/test_validators.py:242-296` cover Thai/E.164/formatting/rejection paths.
- **Silent failures — DONE.** A sweep of `bot/handlers/user/` found only **2** remaining bare `except Exception: pass` blocks (`order_handler.py:87`, `shop_and_goods.py:406`), both intentional idempotent `message.delete()` suppressions with explanatory comments. The ~23 swallows the card cited have already been replaced with typed handlers + logging.

> The dedicated test file the card proposed (`tests/unit/utils/test_phone_validator.py`) was folded into the existing `test_validators.py` instead — equivalent coverage, fewer files. No further work required.

---

## Why

Two recurring weaknesses across the user-facing handlers make production debugging and data quality worse than they need to be:

1. **No real phone validation.** Checkout uses a loose inline regex (`bot/handlers/user/order_handler.py:494`) with no country-code handling, Thai-format check, `+66` normalization, or E.164 storage. Riders get inconsistent numbers; some won't be callable.
2. **Silent failures.** There are ~23 bare `except Exception: pass` blocks across `bot/handlers/user/`. Errors vanish with no log, making field issues nearly impossible to diagnose.

## Scope

- Add a `phone_validator` in `bot/utils/validators.py`: accept `0XXXXXXXXX` and `+66XXXXXXXXX`, normalize to E.164 (`+66…`) before storage, reject malformed input with a clear message.
- Sweep `bot/handlers/user/` for bare `except Exception: pass`; replace with scoped exception types and `logger.warning/exception`. Where a swallow is intentional, comment why.
- Apply the bug-class rule from `CLAUDE.md`: fix every instance of each class, not just the first.

## Files to Modify

| File | Changes |
|------|---------|
| `bot/utils/validators.py` | New `phone_validator` (Thai + E.164 normalization) |
| `bot/handlers/user/order_handler.py` | Use `phone_validator` at line ~494; store normalized number |
| `bot/handlers/user/*.py` | Replace bare `except: pass` with typed handlers + logging |

## Acceptance Criteria

- [x] `0812345678` and `+66812345678` both normalize to `+66812345678`
- [x] Malformed phone numbers are rejected with a localized message
- [x] No bare `except Exception: pass` remains in `bot/handlers/user/` (intentional swallows are commented and logged)

## Test Plan

| Test File | Tests | Assert |
|-----------|-------|--------|
| `tests/unit/utils/test_phone_validator.py` | `test_local_normalizes_to_e164` | `0812345678` → `+66812345678` |
| | `test_already_e164_passthrough` | `+66812345678` unchanged |
| | `test_rejects_malformed` | Letters / wrong length raise |

## Links

P1 hardening in [`../MASTER-PLAN.md`](../MASTER-PLAN.md).
