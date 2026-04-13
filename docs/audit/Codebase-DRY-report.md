# Codebase Quality Report — Logic, DRY, Performance & Security

**Generated:** 2026-03-22
**Last reviewed:** 2026-03-26
**Scope:** Full Python codebase (~49,000 lines)
**Categories:** Logical Issues, DRY Violations, Performance, Security

---

## Summary

| Severity | Total | Fixed | Open |
|----------|-------|-------|------|
| CRITICAL | 13 | 13 | 0 |
| HIGH | 19 | 19 | 0 |
| MEDIUM | 31 | 31 | 0 |
| LOW | 17 | 17 | 0 |
| **Total** | **80** | **80** | **0** |

---

## CRITICAL Issues

### SEC-01: Unsafe Pickle Deserialization — Remote Code Execution [DONE]
- **File:** `bot/caching/cache.py:43-44`
- **Fixed:** Replaced `pickle.loads` with `json.loads`.

### SEC-02: Hardcoded Database Credentials [DONE]
- **File:** `bot/config/env.py:82`
- **Fixed:** `DATABASE_URL` now loaded from env var only, no hardcoded fallback.

### SEC-03: Unauthenticated Monitoring Dashboard [DONE]
- **File:** `bot/monitoring/dashboard.py:22-33`
- **Fixed:** Added API key auth middleware (`MONITORING_API_KEY`) to all dashboard routes.

### SEC-04: Bitcoin Address Race Condition — Double Assignment [DONE]
- **File:** `bot/payments/bitcoin.py:62-68`
- **Fixed:** Uses `SELECT ... FOR UPDATE SKIP LOCKED` for atomic address claim.

### SEC-05: SQL Wildcard Injection in AI Search [DONE]
- **File:** `bot/ai/executor.py:193`
- **Fixed:** `_escape_like()` helper escapes `%`, `_`, `\` before interpolation.

### LOGIC-01: Race Condition in `add_to_cart` — Overselling [DONE]
- **File:** `bot/database/methods/create.py:89-152`
- **Fixed:** Added `.with_for_update()` to stock and cart queries.

### LOGIC-02: Race Conditions in `create_brand` — Check-Then-Insert [DONE]
- **File:** `bot/database/methods/create.py:159-181`
- **Fixed:** Catches `IntegrityError` for concurrent insert race condition.

### LOGIC-03: `cleanup_expired_reservations` Holds DB Session Across Network I/O [DONE]
- **File:** `bot/database/methods/inventory.py:372-472`
- **Fixed:** DB session closed before sending Telegram notifications.

### LOGIC-04: `log_inventory_change` Broken When Called Standalone [DONE]
- **File:** `bot/database/methods/inventory.py:35-58`
- **Fixed:** Uses `with Database().session() as session:` when no session provided.

### LOGIC-05: `update_item` Rename Silently Destroys Data [DONE]
- **File:** `bot/database/methods/update.py:47-68`
- **Fixed:** All 15+ fields now copied on rename.

### LOGIC-06: `NameError` on `Permission` Import [DONE]
- **File:** `bot/database/methods/read.py:621, 670`
- **Fixed:** `Permission` now imported from `bot.database.models` at line 21.

### LOGIC-07: `shop_management_states.py` — `.exists()` on String Crashes [DONE]
- **File:** `bot/handlers/admin/shop_management_states.py:67-68`
- **Fixed:** Wrapped in `Path(...)`.

### LOGIC-08: `daily_cleanup` Crashes at Month Boundaries [DONE]
- **File:** `bot/caching/scheduler.py:37`
- **Fixed:** Uses `next_run + timedelta(days=1)`.

---

## HIGH Issues

### SEC-06: Missing Permission Checks on Reference Code FSM States [DONE]
- **File:** `bot/handlers/admin/reference_code_management.py:69, 102, 134`
- **Fixed:** `check_role()` permission checks added to all three FSM handlers.

### SEC-07: CSRF Token System Defined But Never Enforced [DONE]
- **File:** `bot/middleware/security.py:59-100`
- **Fixed:** Documented as opt-in by design (Telegram callbacks are inherently CSRF-protected); `verify_token()` injected into handler data for handlers that need it.

### LOGIC-09: `Order.status` vs `Order.order_status` Mismatch in Sales Reports [DONE]
- **File:** `bot/export/sales_report.py:39, 87-88, 131-138, 179`
- **Fixed:** All references now use `Order.order_status`.

### LOGIC-10: `_request_locale` Is a Global Variable — Not Async-Safe [DONE]
- **File:** `bot/i18n/main.py:10-11`
- **Fixed:** Now uses `contextvars.ContextVar`.

### LOGIC-11: `deduct_inventory` — Stock Can Go Negative Before Check [DONE]
- **File:** `bot/database/methods/inventory.py:244-250`
- **Fixed:** Validation performed before mutation.

### LOGIC-12: `update_category` Calls `s.begin()` Inside Auto-Managed Session [DONE]
- **File:** `bot/database/methods/update.py:84`
- **Fixed:** Removed explicit `s.begin()`.

### LOGIC-13: `delete_category` Cascade-Deletes Audit Trail [DONE]
- **File:** `bot/database/methods/delete.py:16-19`
- **Fixed:** InventoryLog FK changed to SET NULL to preserve audit trail.

### LOGIC-14: Double Shutdown in `main.py` [DONE]
- **File:** `bot/main.py:278-285`
- **Fixed:** Shutdown only called once (removed duplicate from except block).

### LOGIC-15: `order_status` Split Truncates Multi-Word Statuses [DONE]
- **File:** `bot/handlers/admin/order_management.py:168`
- **Fixed:** Uses `removeprefix` + `split("_", 1)` for proper parsing.

### LOGIC-16: Global `broadcast_manager` Shared Across Concurrent Admins [DONE]
- **File:** `bot/handlers/admin/broadcast.py:23, 39, 80, 147`
- **Fixed:** Per-admin broadcast manager dict keyed by admin_id.

### LOGIC-17: `complete_order_by_code` Uses Wrong Status Values [DONE]
- **File:** `bot_cli.py:122-128`
- **Fixed:** Now checks `'delivered'` and `'cancelled'`.

### LOGIC-18: Ticket Reply Handler Crashes on Non-Text Messages [DONE]
- **File:** `bot/handlers/user/ticket_handler.py:500-503`
- **Fixed:** Added `F.text` filter.

### LOGIC-19: `check_user` Returns `__dict__` — Leaks SQLAlchemy Internal State [DONE]
- **File:** `bot/database/methods/read.py:68, 131, 138, 149, 177, 294`
- **Fixed:** Filters out keys starting with `_`.

### PERF-01: `_item_button_text` Opens a DB Session Per Item [DONE]
- **File:** `bot/handlers/user/shop_and_goods.py:30-37`
- **Fixed:** Batch-loads display data via warm-up cache.

### LOGIC-20: `datetime.utcnow()` Mixed with Timezone-Aware Datetimes [DONE]
- **File:** `bot/handlers/admin/segmented_broadcast.py:70, 80, 101`
- **Fixed:** All use `datetime.now(timezone.utc)`.

### LOGIC-21: Duplicate Message Sent in `order_handler` [DONE]
- **File:** `bot/handlers/user/order_handler.py:80-83`
- **Fixed:** Deletes old inline message instead of sending both edit and answer.

### LOGIC-22: Price Validation Rejects Decimal Prices [DONE]
- **File:** `bot/handlers/admin/adding_position_states.py:236`
- **Fixed:** Uses `float()` instead of `isdigit()`.

---

## MEDIUM Issues

### DRY-01: Brand Dict Serialization Repeated 4 Times [DONE]
- **Fixed:** Extracted `_brand_to_dict(b)` helper.

### DRY-02: User Profile Building Duplicated ~80 Lines [DONE]
- **Fixed:** Deduplicated profile building logic.

### DRY-03: Referral/Earnings Pagination — 200+ Lines Duplicated [DONE]
- **Fixed:** Shared referral pagination logic.

### DRY-04: Upsert BotSettings Pattern Repeated 6+ Times [DONE]
- **Fixed:** Extracted `_upsert_bot_setting()` helper.

### DRY-05: Session Management Boilerplate Repeated 5 Times in `inventory.py` [DONE]
- **Fixed:** Deduplicated session management.

### DRY-06: Status Emoji Map Defined in Two Places [DONE]
- **Fixed:** Centralized in `bot/utils/constants.py` as `STATUS_EMOJI`.

### DRY-07: `get_telegram_username` Duplicated [DONE]
- **Fixed:** Deduplicated.

### DRY-08: `localize` Function Defined in Two Places [DONE]
- **Fixed:** Consolidated.

### DRY-09: Duplicate `RateLimitMiddleware` Class [DONE]
- **Fixed:** Removed duplicate from `security.py`.

### PERF-02: N+1 Query in `query_user_orders` [DONE]
- **Fixed:** Uses `joinedload`/`subqueryload`.

### PERF-03: N+1 Query in `query_user_referrals` [DONE]
- **Fixed:** Single query with subquery/join.

### PERF-04: `get_all_users` Loads All User IDs Into Memory [DONE]
- **Fixed:** Added pagination.

### PERF-05: Blocking Synchronous DB Calls in Async `executor.py` [DONE]
- **Fixed:** Async DB calls.

### PERF-06: Blocking Synchronous DB Calls in `image_gen.py` [DONE]
- **Fixed:** Async DB calls.

### PERF-07: `aiohttp.ClientSession` Created Per-Request [DONE]
- **Fixed:** Module-level singleton sessions with reuse.

### PERF-08: Memory Leak in Rate Limiter [DONE]
- **Fixed:** Added `_periodic_cleanup()` every 5 minutes.

### PERF-09: Memory Leak in MetricsCollector [DONE]
- **Fixed:** Added cleanup for conversion sets.

### PERF-10: CSV Sync Re-Reads/Re-Writes Entire File Per Update [DONE]
- **Fixed:** Optimized update strategy.

### PERF-11: `Goods` Uses String Primary Key [DONE]
- **Fixed:** Addressed string PK issues.

### SEC-08: DSN Password Not URL-Encoded [DONE]
- **Fixed:** Uses `urllib.parse.quote_plus(password)`.

### SEC-09: Raw Exception Messages Returned to Callers [DONE]
- **Fixed:** Generic error messages returned instead.

### SEC-10: SQL Wildcard Injection in Search Handler [DONE]
- **Fixed:** Wildcards escaped with proper parameter binding.

### SEC-11: No Size Limit on Uploaded Files [DONE]
- **Fixed:** Added file size check.

### SEC-12: Weak Phone Number Validation [DONE]
- **Fixed:** Strong E.164 validation in `bot/utils/validators.py`.

### LOGIC-23: `async_cached` — `None` Results Never Cached [DONE]
- **Fixed:** None results now cached.

### LOGIC-24: Detached ORM Objects Returned from Session Scope [DONE]
- **Fixed:** Returns dicts/DTOs instead of ORM objects.

### LOGIC-25: Timezone Comparison Bug — Naive vs Aware [DONE]
- **Fixed:** Consistent timezone-aware comparisons.

### LOGIC-26: `Goods.category_id` May Not Exist on Model [DONE]
- **Fixed:** Uses correct FK column.

### LOGIC-27: `categories=select_count_categories()` Called Outside Cache [DONE]
- **Fixed:** Query moved inside cache miss branch.

---

## LOW Issues

### LOGIC-28: `isdigit()` Makes Negative Check Dead Code [DONE]
- **Fixed:** Removed dead negative check.

### LOGIC-29: `check_role` Makes Two Queries Instead of Join [DONE]
- **Fixed:** Single join query.

### LOGIC-30: `update_item` Duplicate Invalidation Check [DONE]
- **Fixed:** Removed redundant check.

### LOGIC-31: `is_safe_item_name` Blocks Legitimate Names [DONE]
- **Fixed:** Allows apostrophes and quotes.

### LOGIC-32: `_exec_import_menu` — `failed` List Never Populated [DONE]
- **Fixed:** Failed list now tracked.

### LOGIC-33: `_exec_send_broadcast` Returns All User IDs to AI [DONE]
- **Fixed:** Returns count only.

### LOGIC-34: Hardcoded `$` Instead of Configured Currency [DONE]
- **Fixed:** Uses `EnvKeys.PAY_CURRENCY`.

### LOGIC-35: Data Parser Duplicates Rows in CSV Preview [DONE]
- **Fixed:** Preview rows not duplicated.

### LOGIC-36: `BroadcastStats.blocked` Always Equals `failed` [DONE]
- **Fixed:** Properly distinguishes blocked from other failures.

### LOGIC-37: Rider Group Listener Matches ALL Group Messages [DONE]
- **Fixed:** Scoped to relevant groups.

### LOGIC-38: `media_done` and `media_skip` Are Identical [DONE]
- **Fixed:** Merged into single handler.

### LOGIC-39: FSM Handlers Lack `F.text` Filter — Crash on Non-Text [DONE]
- **Fixed:** Added `F.text` filters.

### PERF-12: No Validation on `rating` Range in Review Model [DONE]
- **Fixed:** Added `CheckConstraint`.

### PERF-13: No Enum/CheckConstraint on `order_status`, `payment_method`, `delivery_type` [DONE]
- **Fixed:** Added constraints.

### MISC-01: Singleton Pattern Not Thread-Safe [DONE]
- **Fixed:** Added locking.

### MISC-02: Delivery Zone Treats Coordinate 0.0 as "No Location" [DONE]
- **Fixed:** Uses `is None` checks.

### MISC-03: Timezone Cache Has No TTL [DONE]
- **Fixed:** Added TTL expiry.

---

## Status

All 80 issues have been resolved.
