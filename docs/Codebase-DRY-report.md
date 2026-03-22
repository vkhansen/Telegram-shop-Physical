# Codebase Quality Report — Logic, DRY, Performance & Security

**Generated:** 2026-03-22
**Scope:** Full Python codebase (~49,000 lines)
**Categories:** Logical Issues, DRY Violations, Performance, Security

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 13 |
| HIGH | 19 |
| MEDIUM | 31 |
| LOW | 17 |
| **Total** | **80** |

---

## CRITICAL Issues

### SEC-01: Unsafe Pickle Deserialization — Remote Code Execution
- **File:** `bot/caching/cache.py:43-44`
- `pickle.loads(value)` is called on data from Redis. If an attacker gains Redis write access, they achieve arbitrary code execution via crafted pickle payloads.
- **Fix:** Replace pickle with `json` or `msgpack` for serialization.

### SEC-02: Hardcoded Database Credentials
- **File:** `bot/config/env.py:82`
- `DATABASE_URL: Final = "postgresql+psycopg2://user:password@localhost:5432/db_name"` is committed to source control as a fallback. This is a credential leak vector.
- **Fix:** Remove hardcoded credentials; require env var or fail loudly.

### SEC-03: Unauthenticated Monitoring Dashboard
- **File:** `bot/monitoring/dashboard.py:22-33`
- All monitoring endpoints (`/health`, `/metrics`, `/dashboard`, `/business-metrics`) are served over HTTP with zero authentication. Anyone who can reach the port gets full access to business data, revenue, error details, and Prometheus metrics.
- **Fix:** Add basic auth or API key middleware to the dashboard routes.

### SEC-04: Bitcoin Address Race Condition — Double Assignment
- **File:** `bot/payments/bitcoin.py:62-68`
- `get_available_bitcoin_address()` reads an address without locking. Two concurrent users receive the same address. No `SELECT ... FOR UPDATE` or atomic claim; `mark_bitcoin_address_used()` is called later in a separate transaction.
- **Fix:** Use `SELECT ... FOR UPDATE SKIP LOCKED` for atomic address claim.

### SEC-05: SQL Wildcard Injection in AI Search
- **File:** `bot/ai/executor.py:193`
- `q.filter(DeliveryChatMessage.message_text.ilike(f"%{action.keyword}%"))` — special characters `%` and `_` in user input alter query behavior. Searching `%` matches everything.
- **Fix:** Escape LIKE wildcards before interpolation.

### LOGIC-01: Race Condition in `add_to_cart` — Overselling
- **File:** `bot/database/methods/create.py:89-152`
- Stock check (line 117) and cart quantity check (lines 118-123) have no row-level locking (`with_for_update()`). Concurrent requests can reserve the same stock, leading to overselling.
- **Fix:** Add `with_for_update()` to the stock query or use a DB-level constraint.

### LOGIC-02: Race Conditions in `create_brand` — Check-Then-Insert
- **File:** `bot/database/methods/create.py:159-181`
- Two separate existence checks followed by an insert without locking. Concurrent requests both pass checks and attempt to insert, causing uncaught `IntegrityError`.
- **Fix:** Use `INSERT ... ON CONFLICT` or catch `IntegrityError`.

### LOGIC-03: `cleanup_expired_reservations` Holds DB Session Across Network I/O
- **File:** `bot/database/methods/inventory.py:372-472`
- The function calls `await bot.send_message(...)` (line 436) while inside a synchronous `with Database().session()` block. The DB connection is held open during a Telegram API call, blocking the connection pool and risking deadlocks under load.
- **Fix:** Collect data inside the session, close it, then send notifications.

### LOGIC-04: `log_inventory_change` Broken When Called Standalone
- **File:** `bot/database/methods/inventory.py:35-58`
- When `session is None`, `session = Database().session()` assigns a context manager object (not a session). Subsequent `session.add(log_entry)` raises `AttributeError`. This code path is broken.
- **Fix:** Use `with Database().session() as session:` when no session is provided.

### LOGIC-05: `update_item` Rename Silently Destroys Data
- **File:** `bot/database/methods/update.py:47-68`
- When renaming, a new `Goods` is created copying only `stock_quantity` and `reserved_quantity`. All other fields (`image_file_id`, `media`, `modifiers`, `prep_time_minutes`, `allergens`, `is_active`, `sold_out_today`, `daily_limit`, `calories`, `brand_id`, `item_type`, etc.) are lost.
- **Fix:** Copy all fields or use a SQL `UPDATE` on the PK.

### LOGIC-06: `NameError` on `Permission` Import
- **File:** `bot/database/methods/read.py:621, 670`
- `Permission` is used but never imported. This raises `NameError` at runtime in `can_manage_brand` and `is_superadmin`.
- **Fix:** Add `from bot.database.models.main import Permission` (or equivalent).

### LOGIC-07: `shop_management_states.py` — `.exists()` on String Crashes
- **File:** `bot/handlers/admin/shop_management_states.py:67-68`
- `.exists()` and `.stat()` are called on plain string literals (`"logs/audit.log"`) instead of `Path` objects. `str.exists()` does not exist — crashes with `AttributeError`.
- **Fix:** Wrap in `Path(...)`.

### LOGIC-08: `daily_cleanup` Crashes at Month Boundaries
- **File:** `bot/caching/scheduler.py:37`
- `next_run.replace(day=next_run.day + 1)` raises `ValueError` on the last day of any month (e.g., Jan 31 → day=32).
- **Fix:** Use `next_run + timedelta(days=1)`.

---

## HIGH Issues

### SEC-06: Missing Permission Checks on Reference Code FSM States
- **File:** `bot/handlers/admin/reference_code_management.py:69, 102, 134`
- FSM message handlers for `waiting_refcode_expires`, `waiting_refcode_max_uses`, and `waiting_refcode_note` have **no permission check**. Any user who enters these FSM states can create admin reference codes.

### SEC-07: CSRF Token System Defined But Never Enforced
- **File:** `bot/middleware/security.py:59-100`
- `generate_token()` and `verify_token()` are defined, but `verify_token()` is never called in the middleware's `__call__` method. CSRF protection is entirely dead code.

### LOGIC-09: `Order.status` vs `Order.order_status` Mismatch in Sales Reports
- **File:** `bot/export/sales_report.py:39, 87-88, 131-138, 179`
- Uses `Order.status == "delivered"` throughout, but the model and all other code uses `Order.order_status`. This silently returns empty results for all sales reports.

### LOGIC-10: `_request_locale` Is a Global Variable — Not Async-Safe
- **File:** `bot/i18n/main.py:10-11`
- `_request_locale` is module-level global. In async code, concurrent request handlers share this variable. Setting it for one user affects another user's response language.
- **Fix:** Use `contextvars.ContextVar` instead.

### LOGIC-11: `deduct_inventory` — Stock Can Go Negative Before Check
- **File:** `bot/database/methods/inventory.py:244-250`
- `goods.stock_quantity -= order_item.quantity` happens before the negative check. While rollback handles it, `reserved_quantity` was already decremented and rollback behavior is fragile.
- **Fix:** Check before mutation.

### LOGIC-12: `update_category` Calls `s.begin()` Inside Auto-Managed Session
- **File:** `bot/database/methods/update.py:84`
- The `Database().session()` context manager already manages transactions. Explicit `s.begin()` starts a nested transaction or raises an error depending on SQLAlchemy version.

### LOGIC-13: `delete_category` Cascade-Deletes Audit Trail
- **File:** `bot/database/methods/delete.py:16-19`
- Deleting a category cascades to goods, which cascades to `InventoryLog`, losing the audit trail entirely.
- **Fix:** Use soft deletes or detach inventory logs before deletion.

### LOGIC-14: Double Shutdown in `main.py`
- **File:** `bot/main.py:278-285`
- `__on_shutdown` runs in both `except` and `finally` blocks, causing double resource cleanup on error.

### LOGIC-15: `order_status` Split Truncates Multi-Word Statuses
- **File:** `bot/handlers/admin/order_management.py:168`
- `parts = call.data.split("_", 3)` on `"order_status_42_out_for_delivery"` yields `parts[3] = "out"` instead of `"out_for_delivery"`.

### LOGIC-16: Global `broadcast_manager` Shared Across Concurrent Admins
- **File:** `bot/handlers/admin/broadcast.py:23, 39, 80, 147`
- A single global `broadcast_manager` means concurrent broadcasts overwrite each other.

### LOGIC-17: `complete_order_by_code` Uses Wrong Status Values
- **File:** `bot_cli.py:122-128`
- Checks for `'completed'` and `'canceled'`, but valid values are `'delivered'` and `'cancelled'`. Guards never trigger.

### LOGIC-18: Ticket Reply Handler Crashes on Non-Text Messages
- **File:** `bot/handlers/user/ticket_handler.py:500-503`
- `message.text.strip()` raises `AttributeError` when users send photos/stickers since there's no `F.text` filter.

### LOGIC-19: `check_user` Returns `__dict__` — Leaks SQLAlchemy Internal State
- **File:** `bot/database/methods/read.py:68, 131, 138, 149, 177, 294`
- `__dict__` includes `_sa_instance_state`. Fragile and leaks ORM internals to callers.

### PERF-01: `_item_button_text` Opens a DB Session Per Item
- **File:** `bot/handlers/user/shop_and_goods.py:30-37`
- Called once per item in category. 20 items = 20 separate DB round-trips. Should batch-query.

### LOGIC-20: `datetime.utcnow()` Mixed with Timezone-Aware Datetimes
- **File:** `bot/handlers/admin/segmented_broadcast.py:70, 80, 101`
- Uses deprecated `datetime.utcnow()` (naive) while other code uses `datetime.now(timezone.utc)` (aware). Comparison between them fails or gives wrong results.

### LOGIC-21: Duplicate Message Sent in `order_handler`
- **File:** `bot/handlers/user/order_handler.py:80-83`
- Both `call.message.edit_text(prompt)` and `call.message.answer(prompt)` fire, sending the same prompt twice. Repeated at lines 318-322, 342-346.

### LOGIC-22: Price Validation Rejects Decimal Prices
- **File:** `bot/handlers/admin/adding_position_states.py:236`
- `price_text.isdigit()` rejects `"9.99"`. Same at `update_position_states.py:88`. For a shop, this is a significant limitation.

---

## MEDIUM Issues

### DRY-01: Brand Dict Serialization Repeated 4 Times
- **File:** `bot/database/methods/read.py:554-561, 571-576, 585-590, 650-657`
- Same `{id, name, slug, ...}` mapping copy-pasted in `get_all_brands`, `get_brand`, `get_brand_by_slug`, and `get_user_brands`.
- **Fix:** Extract `_brand_to_dict(b)` helper.

### DRY-02: User Profile Building Duplicated ~80 Lines
- **File:** `bot/handlers/admin/user_management_states.py:47-134` vs `143-231`
- `check_user_data` and `user_profile_view` contain near-identical code for building user profile text and action buttons.

### DRY-03: Referral/Earnings Pagination — 200+ Lines Duplicated
- **Files:** `bot/handlers/user/referral_system.py:55-310` vs `bot/handlers/admin/user_management_states.py:234-465`
- Admin referral viewing is an almost exact copy of user's referral system.

### DRY-04: Upsert BotSettings Pattern Repeated 6+ Times
- **File:** `bot/handlers/admin/settings_management.py:94-108, 177-193, 254-268, 336-350`
- Query, check exists, update or create, commit — copy-pasted in every settings handler.
- **Fix:** Extract `upsert_bot_setting(key, value)`.

### DRY-05: Session Management Boilerplate Repeated 5 Times in `inventory.py`
- **File:** `bot/database/methods/inventory.py`
- `should_commit = session is None; if session is None: session = Database().session()` with try/except/finally repeated in 5 functions.

### DRY-06: Status Emoji Map Defined in Two Places
- **File:** `bot/handlers/user/orders_view_handler.py:143-154` and `bot/handlers/admin/order_management.py:34-44`
- Same `status → emoji` mapping duplicated.

### DRY-07: `get_telegram_username` Duplicated
- **File:** `bot/utils/user_utils.py:4-23` vs `bot_cli.py:71-102`
- Same function implemented twice with slightly different signatures.

### DRY-08: `localize` Function Defined in Two Places
- **File:** `bot/i18n/main.py:47` and `bot/i18n/strings.py:4`
- Two separate `localize()` functions exist. Behavior differs depending on which is imported.

### DRY-09: Duplicate `RateLimitMiddleware` Class
- **File:** `bot/middleware/rate_limit.py` (full implementation) vs `bot/middleware/security.py:285-395`
- Two completely separate `RateLimitMiddleware` classes. One is dead code.

### PERF-02: N+1 Query in `query_user_orders`
- **File:** `bot/database/methods/read.py:441-443`
- For each order, a separate query fetches `OrderItem` rows. 10 orders = 11 queries.
- **Fix:** Use `joinedload` or `subqueryload`.

### PERF-03: N+1 Query in `query_user_referrals`
- **File:** `bot/database/methods/lazy_queries.py:99-104`
- Per-referral aggregation query. Should be a single query with subquery/join.

### PERF-04: `get_all_users` Loads All User IDs Into Memory
- **File:** `bot/database/methods/read.py:124`
- `s.query(User.telegram_id).all()` with no pagination. Large user base → OOM risk.

### PERF-05: Blocking Synchronous DB Calls in Async `executor.py`
- **File:** `bot/ai/executor.py` (multiple functions)
- `_search_orders`, `_search_chat`, `_view_inventory`, etc. use synchronous `Database().session()` inside `async def`. Blocks the event loop.

### PERF-06: Blocking Synchronous DB Calls in `image_gen.py`
- **File:** `bot/ai/image_gen.py:113, 154, 177, 211`
- Synchronous DB I/O called from async handlers.

### PERF-07: `aiohttp.ClientSession` Created Per-Request
- **File:** `bot/ai/grok_client.py:36`, `bot/ai/image_gen.py:54`
- New session per API call kills connection pooling. Should reuse sessions.

### PERF-08: Memory Leak in Rate Limiter
- **File:** `bot/middleware/rate_limit.py:40-42`
- `user_requests`, `user_actions`, `banned_users` dicts grow unboundedly. No cleanup of inactive users.

### PERF-09: Memory Leak in MetricsCollector
- **File:** `bot/monitoring/metrics.py:79-81`
- `self.conversions[funnel][step].add(user_id)` stores user IDs in sets indefinitely.

### PERF-10: CSV Sync Re-Reads/Re-Writes Entire File Per Update
- **File:** `bot/export/customer_csv.py:166-219`
- `sync_customer_to_csv()` reads all rows, iterates, and rewrites. O(n) per single customer update.

### PERF-11: `Goods` Uses String Primary Key
- **File:** `bot/database/models/main.py:225`
- String PKs are slower for joins than integers. Every FK referencing `goods.name` uses string comparisons. Renaming requires cascading updates across many tables.

### SEC-08: DSN Password Not URL-Encoded
- **File:** `bot/database/dsn.py:16`
- If password contains `@`, `:`, `/`, `%`, the connection string is malformed. Use `urllib.parse.quote_plus(password)`.

### SEC-09: Raw Exception Messages Returned to Callers
- **Files:** `bot/database/methods/delete.py:51, 72`, `bot/database/methods/create.py:156`
- `return False, str(e)` exposes table names, column names, and query structure.

### SEC-10: SQL Wildcard Injection in Search Handler
- **File:** `bot/handlers/user/search_handler.py:43`
- `pattern = f"%{query}%"` — `%` and `_` wildcards in user input are not escaped.

### SEC-11: No Size Limit on Uploaded Files
- **File:** `bot/ai/data_parser.py:28-29`
- `message.bot.download(message.document)` followed by `file.read()` with no size check. Large file → OOM.

### SEC-12: Weak Phone Number Validation
- **File:** `bot/handlers/user/order_handler.py:474-486`
- Only checks `len(phone_number) < 8`. Accepts `"aaaaaaaa"` as a phone number.

### LOGIC-23: `async_cached` — `None` Results Never Cached
- **File:** `bot/database/methods/read.py:47`
- Legitimate "not found" results (None) are never cached. Items/users that don't exist hit the DB every time.

### LOGIC-24: Detached ORM Objects Returned from Session Scope
- **File:** `bot/database/methods/lazy_queries.py:53-56, 127-130, 144-147`
- Full ORM objects returned from within `with` session block. After session closes, accessing lazy-loaded relationships raises `DetachedInstanceError`.

### LOGIC-25: Timezone Comparison Bug — Naive vs Aware
- **File:** `bot/referrals/codes.py:153-160`
- `get_localized_time()` returns timezone-aware datetime, but `expires_at` from DB may be naive. Comparison gives wrong results.

### LOGIC-26: `Goods.category_id` May Not Exist on Model
- **File:** `bot/export/sales_report.py:97`
- `good.category_id` is referenced but model uses `category_name` as FK. Column may not exist.

### LOGIC-27: `categories=select_count_categories()` Called Outside Cache
- **File:** `bot/handlers/admin/shop_management_states.py:112-113`
- DB query fires even inside the cached branch, defeating cache purpose.

---

## LOW Issues

### LOGIC-28: `isdigit()` Makes Negative Check Dead Code
- **File:** `bot/handlers/admin/goods_management_states.py:318, 326`
- `quantity_text.isdigit()` already guarantees non-negative. `if quantity < 0` can never be true.

### LOGIC-29: `check_role` Makes Two Queries Instead of Join
- **File:** `bot/database/methods/read.py:71-78`
- First queries `User.role_id`, then separately queries `Role.permissions`. Should be a single join.

### LOGIC-30: `update_item` Duplicate Invalidation Check
- **File:** `bot/database/methods/update.py:71`
- `if new_name != item_name:` is always true at this point since the equal case returned early.

### LOGIC-31: `is_safe_item_name` Blocks Legitimate Names
- **File:** `bot/handlers/other.py:46-63`
- Blocks single/double quotes, preventing names like "Mom's Cookies" or `12" Pizza`.

### LOGIC-32: `_exec_import_menu` — `failed` List Never Populated
- **File:** `bot/ai/executor.py:535, 579`
- `failed = []` initialized but never appended to. `"failed": len(failed)` is always 0.

### LOGIC-33: `_exec_send_broadcast` Returns All User IDs to AI
- **File:** `bot/ai/executor.py:815`
- Full `user_ids` list serialized to JSON and sent to AI model. Wastes tokens, may exceed API limits.

### LOGIC-34: Hardcoded `$` Instead of Configured Currency
- **File:** `bot/payments/notifications.py:108, 135, 173`
- Uses `$` instead of `EnvKeys.PAY_CURRENCY` (which is THB by default).

### LOGIC-35: Data Parser Duplicates Rows in CSV Preview
- **File:** `bot/ai/data_parser.py:68-78`
- First 5 rows shown as preview, then ALL rows (including first 5) appended again.

### LOGIC-36: `BroadcastStats.blocked` Always Equals `failed`
- **File:** `bot/communication/broadcast_system.py:183`
- Conflates blocked users with all failures (network errors, bad requests, etc.).

### LOGIC-37: Rider Group Listener Matches ALL Group Messages
- **File:** `bot/handlers/user/delivery_chat_handler.py:447`
- Matches every group message the bot receives, doing a DB query each time.

### LOGIC-38: `media_done` and `media_skip` Are Identical
- **File:** `bot/handlers/admin/adding_position_states.py:206-225`
- Both do the exact same thing. Could be a single handler matching both callback values.

### LOGIC-39: FSM Handlers Lack `F.text` Filter — Crash on Non-Text
- **File:** `bot/handlers/admin/coupon_management.py:91, 141, 165, 189, 213`
- Photos/stickers trigger these handlers and crash on `message.text.strip()`.

### PERF-12: No Validation on `rating` Range in Review Model
- **File:** `bot/database/models/main.py:855`
- Comment says "1-5" but no `CheckConstraint`. Values of 0 or 100 can be inserted.

### PERF-13: No Enum/CheckConstraint on `order_status`, `payment_method`, `delivery_type`
- **File:** `bot/database/models/main.py:447, 452, 504`
- String columns accept any arbitrary value, bypassing business logic assumptions.

### MISC-01: Singleton Pattern Not Thread-Safe
- **File:** `bot/utils/singleton.py:4-5`
- `_instance` without locking; multi-threaded first calls could create multiple instances.

### MISC-02: Delivery Zone Treats Coordinate 0.0 as "No Location"
- **File:** `bot/config/delivery_zones.py:62-63`
- `r_lat = restaurant_lat or RESTAURANT_LAT` — `0.0` is falsy, falls back to default.

### MISC-03: Timezone Cache Has No TTL
- **File:** `bot/config/timezone.py:24`
- Once cached, never expires. DB setting changes ignored until restart.

---

## Top 10 Priorities (Recommended Fix Order)

| # | ID | Issue | Impact |
|---|-----|-------|--------|
| 1 | SEC-01 | Pickle deserialization RCE | Attacker with Redis access gets shell |
| 2 | SEC-02 | Hardcoded DB credentials | Credential leak in source control |
| 3 | SEC-03 | Unauthenticated monitoring | Business data exposed publicly |
| 4 | SEC-04 | Bitcoin address race condition | Users get same payment address |
| 5 | LOGIC-05 | `update_item` destroys data on rename | Silent data loss |
| 6 | LOGIC-06 | `Permission` NameError | `can_manage_brand` crashes at runtime |
| 7 | LOGIC-09 | `Order.status` vs `order_status` | All sales reports return empty |
| 8 | LOGIC-01 | Cart race condition | Overselling inventory |
| 9 | LOGIC-10 | Global locale variable | Wrong language for concurrent users |
| 10 | LOGIC-08 | `daily_cleanup` month crash | Scheduler dies on last day of month |
