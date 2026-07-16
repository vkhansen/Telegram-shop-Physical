# Card 29: Messenger Port (Telegram Default)

## Implementation Status

> **~90% Complete** | `██████████████████░░` | **2026-07-17:** `Messenger` + `TelegramMessenger` + `notifications.py` wired. Optional: broadcast/dispatch still direct Bot.

**Tier:** T0 — Multi-Channel Foundation  
**Phase:** M3 — Multi-Platform Growth  
**Priority:** High (blocks multi-channel outbound)  
**Effort:** Low–Medium (1–2 days)  
**Dependencies:** Align with [UNIFIED-BACKEND-CHANNEL-INTERFACE](../Specifications/UNIFIED-BACKEND-CHANNEL-INTERFACE.md) §6  
**Plan:** [`MULTI-CHANNEL-TIERED-PLAN.md`](MULTI-CHANNEL-TIERED-PLAN.md)  
**Code (partial):** `bot/platform/messaging.py`

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
bot/platform/messaging.py            # Messenger protocol + get/set_messenger + RecordingMessenger
bot/platform/telegram_messenger.py   # TelegramMessenger + shared Bot session
bot/payments/notifications.py        # all sends via get_messenger()
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

- [x] `Messenger` protocol + `TelegramMessenger` in tree  
- [x] All functions in `notifications.py` use Messenger (no direct `get_shared_bot` for sends; re-export only)  
- [x] Unit tests: `tests/unit/platform/test_messaging_card29.py`  
- [ ] Optional: `broadcast_system` / dispatch DMs via Messenger  
- [x] Suite green on platform tests; no Telegram UX regression (signatures preserved)  

---

## Effort

| Task | Days |
|------|------|
| Port + Telegram adapter | 0.5 |
| Wire notifications | 0.5 |
| Optional broadcast/dispatch | 0.5 |
| Tests | 0.5 |
| **Total** | **1–2** |
