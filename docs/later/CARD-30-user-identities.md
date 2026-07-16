# Card 30: User Identities Dual-Write

## Implementation Status

> **0% Complete** | `░░░░░░░░░░░░░░░░░░░` | Design only — not started.

**Tier:** T0 — Multi-Channel Foundation  
**Phase:** M3 — Multi-Platform Growth  
**Priority:** High  
**Effort:** Medium (1–2 days)  
**Dependencies:** None hard; pairs with [CARD-29](CARD-29-messenger-port.md)  
**Plan:** [`MULTI-CHANNEL-TIERED-PLAN.md`](MULTI-CHANNEL-TIERED-PLAN.md)

---

## Why

`User.telegram_id` (BigInteger PK) is the identity spine for orders, carts, tickets, drivers, and staff. Changing the PK for multi-channel is a high-risk rewrite.

**Dual-write** adds a side table so Instagram (and later LINE) can resolve external string IDs to the same internal user without breaking Telegram.

---

## Schema

```sql
CREATE TABLE user_identities (
    id            SERIAL PRIMARY KEY,
    user_id       BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    platform      VARCHAR(20) NOT NULL,  -- 'telegram' | 'instagram' | 'line' | 'whatsapp' | 'web'
    external_id   VARCHAR(128) NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (platform, external_id)
);
CREATE INDEX ix_user_identities_user ON user_identities(user_id);
```

**Phase T0 policy:**

- Keep `users.telegram_id` as PK and all existing FKs.
- On Telegram user create (and optional login path): upsert `(platform='telegram', external_id=str(telegram_id))`.
- Backfill migration for existing users.

**Instagram (CARD-33):** create or link rows with `platform='instagram'`. New IG-only users need a stable `users` row strategy (see below).

### IG-only user strategy (document in migration notes)

Preferred for max Telegram compatibility:

1. **Synthetic Telegram-space id** reserved range **or**  
2. Introduce nullable-safe path later with internal surrogate PK (out of scope for T0).

**T0 recommendation:** backfill + dual-write for Telegram only. CARD-33 defines how IG-only users get a `users` row (e.g. negative synthetic IDs or separate sequence) **without** altering existing positive Telegram IDs.

Safer CARD-33 approach:

- Add `users` with a generated BigInteger from a dedicated sequence / hash of `instagram:{id}` that does not collide with real Telegram IDs (document collision check).
- Or require “link code” from Telegram before full ordering (stricter; better identity).

CARD-33 chooses one; CARD-30 only ships table + Telegram dual-write + resolve helpers.

---

## Code

```
bot/ports/identity.py
bot/database/models/main.py   # UserIdentity model
migrations/versions/..._user_identities.py
```

```python
def resolve_user_id(platform: str, external_id: str) -> int | None: ...
def link_identity(user_id: int, platform: str, external_id: str) -> None: ...
def ensure_telegram_identity(telegram_id: int) -> None: ...
```

Wire `ensure_telegram_identity` into `create_user` / auth middleware first-seen path.

---

## Out of scope

- Account linking UI (Telegram ↔ Instagram)
- Changing FK columns off `telegram_id`
- Multi-platform Messenger routing (CARD-33)

---

## Tests

- Unique constraint `(platform, external_id)`
- Dual-write on create_user
- Backfill creates one telegram identity per user
- resolve returns correct user_id

---

## Exit criteria

- [ ] Table + model + Alembic migration  
- [ ] Backfill of existing users  
- [ ] Dual-write on new Telegram users  
- [ ] Resolve/link helpers unit-tested  
- [ ] No change to order/cart FK behavior  

---

## Effort

| Task | Days |
|------|------|
| Model + migration + backfill | 0.5–1 |
| create_user / auth dual-write | 0.5 |
| Tests | 0.5 |
| **Total** | **1–2** |
