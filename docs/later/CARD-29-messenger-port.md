# Card 29: Messenger Port (Telegram Default)

## Implementation Status

> **0% Complete** | `░░░░░░░░░░░░░░░░░░░` | Design only — not started.

**Tier:** T0 — Multi-Channel Foundation  
**Phase:** M3 — Multi-Platform Growth  
**Priority:** High (blocks Instagram / LINE outbound)  
**Effort:** Low–Medium (1–2 days)  
**Dependencies:** None (uses existing `notifications.py` / Bot)  
**Plan:** [`MULTI-CHANNEL-TIERED-PLAN.md`](MULTI-CHANNEL-TIERED-PLAN.md)

---

## Why

Outbound messaging is hard-wired to `get_shared_bot().send_message(telegram_id, …)`. A single **Messenger** port lets:

- Telegram keep current behavior via `TelegramMessenger`
- Instagram (CARD-33) and LINE (CARD-16) plug in without forking notify helpers
- Kitchen/rider/customer status APIs stay stable

Telegram remains the only implementation in this card.

---

## Scope

### In

```
bot/ports/
  __init__.py
  messenger.py          # Protocol + types
  telegram_messenger.py # TelegramMessenger (or same file)
```

```python
class Messenger(Protocol):
    async def send_text(
        self, user_ref: int | UserRef, text: str, *, buttons: ButtonSpec | None = None
    ) -> bool: ...
    async def send_photo(
        self, user_ref: int | UserRef, photo: MediaRef, *, caption: str | None = None
    ) -> bool: ...
    async def send_group(
        self, group_key: str, text: str, *, buttons: ButtonSpec | None = None
    ) -> str | None: ...  # platform message id
```

- Wire `bot/payments/notifications.py` through the port (`notify_order_*`, kitchen/rider, delivery photo).
- Optional same series: `broadcast_system.py`, dispatch customer/driver DMs.
- Module-level `get_messenger()` defaulting to `TelegramMessenger` (lazy Bot session, same as today).
- Preserve public function signatures used by handlers/CLI.

### Out

- Multi-backend router (CARD-33)
- Handler rewrites
- Identity table (CARD-30)
- Non-Telegram SDKs

---

## Telegram compatibility

| Constraint | Requirement |
|------------|-------------|
| UX | No customer/admin visible change |
| API | `notify_order_confirmed`, `notify_kitchen_group`, etc. keep signatures |
| Multi-bot | v1 may still use `EnvKeys.TOKEN`; note follow-up to inject brand bot |
| HTML parse mode | Unchanged for Telegram adapter |

---

## Tests

- Unit: fake Messenger records calls; notification helpers invoke it with expected user/group.
- Smoke: existing order-status notify tests still pass (or add thin tests if missing).

---

## Exit criteria

- [ ] `Messenger` protocol + `TelegramMessenger` in tree  
- [ ] All functions in `notifications.py` use Messenger (no direct `get_shared_bot` outside adapter)  
- [ ] Suite green; no Telegram UX regression  

---

## Effort

| Task | Days |
|------|------|
| Port + Telegram adapter | 0.5 |
| Wire notifications | 0.5 |
| Optional broadcast/dispatch | 0.5 |
| Tests | 0.5 |
| **Total** | **1–2** |
