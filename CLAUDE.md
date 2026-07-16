# CLAUDE.md

## Bug Hunting Rule
When you find a bug, always search for that **entire class of bug** across the full codebase before fixing. For example:
- Find one missing `query=` kwarg in `localize()` → grep every `localize(` call for missing kwargs
- Find one unchecked `None` return → grep every call to that function for null guards
- Find one `max([])` crash → grep every `max(` call on potentially empty collections
- Find one missing permission filter → check every admin FSM handler for the same gap

Fix all instances, not just the one you found.

## Project Commands
- **Deploy**: `docker compose build bot && docker compose up -d bot`
- **Logs**: `docker compose logs -f bot`
- **Load test data**: `docker compose exec bot python load_test_data.py`
- **Clean test data**: `docker compose exec bot python load_test_data.py --clean`
- **Run tests**: `pytest tests/`

## Architecture Notes
- Telegram is an **adapter** (aiogram 3.22), not a special domain API — SQLAlchemy 2.0, PostgreSQL 16, Redis 7
- **Unified backend law:** adapters (Telegram/web/LINE/forms/chatbox) → application services → domain. No new handler→domain business shortcuts. Spec: `docs/Specifications/UNIFIED-BACKEND-CHANNEL-INTERFACE.md`
- Platform contracts: `bot/platform/` (capabilities, media_ref, messaging)
- Capability masks: frontends implement subsets; backend features are standardized services
- `prepared` items have unlimited stock (stock_quantity=0 means unlimited)
- `product` items are inventory-tracked
- Locale priority: explicit param > request contextvar > BOT_LOCALE env > DEFAULT_LOCALE ("th")
- Session bootstrap: `docs/CLEAR-START.md`
