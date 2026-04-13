# AI Customer Assistant — Complete Reference

## Overview

The AI Customer Assistant is a Grok-powered conversational interface for end customers. It is **read-only** against the catalog and **scoped to the current user's own data**. Its only write operations are opening support tickets and escalating to live chat sessions.

Implemented in Card 22. Reuses the `call_grok()` client and `schema_to_tool()` pattern introduced in Card 17 (Admin Grok Assistant).

---

## Entry Points

| Trigger | Handler | Notes |
|---------|---------|-------|
| `/ask` command | `ask_command` | Any private chat |
| "🤖 AI Assistant" button | `ai_assistant_button` | Main menu `callback_data="ai_assistant_customer"` |

Both entry points clear existing FSM state and call `_start_customer_assistant()`.

---

## File Map

| File | Purpose |
|------|---------|
| `bot/handlers/user/grok_customer.py` | FSM handler — entry, chat loop, tool dispatch, live chat relay |
| `bot/ai/customer_schemas.py` | 10 Pydantic schemas + `CUSTOMER_TOOL_SCHEMA_MAP` |
| `bot/ai/customer_tool_defs.py` | `CUSTOMER_TOOLS` list (OpenAI function-calling format) |
| `bot/ai/customer_executor.py` | DB queries + support ticket creation functions |

---

## FSM States

Defined in `bot/states/user_state.py` as `GrokCustomerStates`:

| State | Description |
|-------|-------------|
| `chatting` | Normal AI conversation loop |
| `app_live_chat` | Live relay session to `MAINTAINER_IDS` / `SUPPORT_CHAT_ID` |
| `store_live_chat` | Live relay session to store admins |

---

## Tools

### Catalog tools (no user scope)

#### `browse_menu`
Search the catalog by keyword, category, price range, and stock status.

```python
class BrowseMenuAction(BaseModel):
    keyword: Optional[str] = None           # matches name, description, allergens
    category: Optional[str] = None          # ilike match on category_name
    max_price: Optional[Decimal] = None
    min_price: Optional[Decimal] = None
    in_stock_only: bool = True              # filters sold_out_today=True items
    limit: int = Field(default=10, ge=1, le=20)
```

Returns `{items: [...], count: int}`. Each item includes `name`, `price`, `category`, `description` (truncated to 200 chars), `allergens`, `prep_time_minutes`, `calories`, `available`.

#### `get_today_specials`
Items with an active `available_from`/`available_until` window at current Bangkok time.

```python
class GetTodaySpecialsAction(BaseModel):
    category: Optional[str] = None
```

Returns items with `current_time_bangkok` included in the response for transparency.

#### `find_deals`
Currently active public coupon codes (expired, inactive, and maxed-out coupons excluded).

```python
class FindDealsAction(BaseModel):
    min_order_max: Optional[Decimal] = None   # filter: only coupons requiring ≤ this min order
```

Returns `{deals: [...], count: int}`. Does **not** expose `single_use` or user-specific coupons.

#### `find_nearby_stores`
Active stores sorted by Haversine distance from the customer's GPS coordinates.

```python
class FindNearbyStoresAction(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    max_distance_km: float = Field(default=10.0, gt=0, le=50)
```

Returns `{stores: [...], count: int}`. Each entry includes `name`, `address`, `distance_km`, `phone`.

**GPS privacy**: `find_nearby_stores` only runs if the customer explicitly shares a Telegram location attachment. The handler converts it to the instruction text `[Customer shared location: lat=X, lon=Y] Please use find_nearby_stores to help.`

#### `check_coupon`
Validate a coupon code and optionally compute the effective discount.

```python
class CheckCouponAction(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    order_total: Optional[Decimal] = None   # enables effective_discount + final_total calc
```

Returns `{valid: bool, reason?: str, ...discount fields}`. Code is auto-uppercased before lookup.

---

### Own-account tools (filtered by `user_id` from Telegram auth)

#### `get_order_status`
The **customer's own** recent orders. Cannot access other users' orders.

```python
class GetOrderStatusAction(BaseModel):
    order_code: Optional[str] = None    # None → last N orders
    limit: int = Field(default=5, ge=1, le=10)
```

DB filter: `Order.buyer_id == user_id` (hard-coded in executor, not from AI payload).

Returns `{orders: [...]}` with `order_code`, `status`, `total_price`, `payment_method`, `delivery_type`, `created_at`, `delivery_time`.

#### `get_my_account`
Customer's own profile data — bonus balance, referral stats, spending totals.

```python
class GetMyAccountAction(BaseModel):
    pass  # no arguments needed — user_id from Telegram auth
```

Returns `telegram_id`, `registered_at`, `bonus_balance`, `total_spent`, `completed_orders`, `referral_count`.

---

### Support tools

#### `open_support_ticket`
Create a `SupportTicket` row and notify maintainers.

```python
class OpenSupportTicketAction(BaseModel):
    subject: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10, max_length=2000)
    priority: Literal["low", "normal", "high"] = "normal"
    order_code: Optional[str] = None    # links to Order WHERE buyer_id=user_id
```

`order_code` is resolved to an `order_id` only if the matching order's `buyer_id` equals the current user — cross-user linkage is not possible.

Returns `{success: true, ticket_code: str}`.

#### `start_app_live_chat`
Escalate to a real-time relay session with the **platform maintainers** (`MAINTAINER_IDS` env var, falling back to `OWNER_ID`).

```python
class StartAppLiveChatAction(BaseModel):
    reason: str = Field(..., min_length=5, max_length=500)
```

Creates a `SupportTicket` with subject prefix `[APP_LIVE_CHAT]` and `priority="high"`. Sets FSM state to `GrokCustomerStates.app_live_chat`. Returns `{success: true, ticket_code, ticket_id, relay_target: "maintainers"}`.

**Use for:** bot bugs, payment failures, technical issues with the app itself.

#### `start_store_live_chat`
Escalate to a real-time relay session with **store support staff**.

```python
class StartStoreLiveChatAction(BaseModel):
    reason: str = Field(..., min_length=5, max_length=500)
    order_code: Optional[str] = None
```

Creates a `SupportTicket` with subject prefix `[STORE_LIVE_CHAT]`. Sets FSM state to `GrokCustomerStates.store_live_chat`. Currently notifies `MAINTAINER_IDS` (same as app); per-brand admin targeting via `Permission.USERS_MANAGE` lookup can be added later.

**Use for:** wrong item, late delivery, refund requests, food quality complaints.

---

## Tool Routing Summary

| Scenario | Tool |
|----------|------|
| Bot broken / payment failed | `start_app_live_chat` |
| Order / delivery / food issue | `start_store_live_chat` |
| Leave written record first | `open_support_ticket`, then offer live chat |
| Either live chat | Either can be preceded by `open_support_ticket` |

---

## Conversation Loop

```
_start_customer_assistant()
  └─ set_state(GrokCustomerStates.chatting)
  └─ seed history: [system_prompt]

handle_customer_message()  (called on every user message)
  ├─ _check_rate_limit() → 429 if exceeded
  ├─ append user message to history
  ├─ call_grok(history, CUSTOMER_TOOLS)
  ├─ if tool_calls:
  │    for each tool_call:
  │      _process_tool_call() → validates + dispatches to executor
  │      append tool result to history
  │      if result._enter_live_chat → stop loop, return
  │    call_grok(history, CUSTOMER_TOOLS)  ← follow-up
  │    repeat up to depth=3 for chained tool calls
  └─ _trim_history() → save to FSM state
```

`_trim_history()` keeps the system prompt (index 0) plus the last `GROK_MAX_HISTORY` messages.

---

## Live Chat Relay

When either live chat tool succeeds, `_enter_live_chat()` stores `live_chat_ticket_id` and `live_chat_ticket_code` in FSM state and sets the appropriate state. All subsequent messages are handled by `live_chat_relay()`:

- Saves each customer message as a `TicketMessage` row (`sender_role="user"`)
- Relays formatted text (and photos) to all `MAINTAINER_IDS` and `SUPPORT_CHAT_ID`
- Relay format: `💬 [TICKETCODE] User 12345:\n<text>`
- `/exit_ai` in this state ends the session (`state.clear()`)

---

## Rate Limiting

| Parameter | Value |
|-----------|-------|
| Window | 3600 seconds (1 hour) |
| Default limit | 20 calls per user per window |
| Env var | `GROK_CUSTOMER_RATE_LIMIT` |
| Storage | `grok_call_timestamps` list in FSM state data |
| On exceed | Message with time-until-reset + offer to open ticket |

Each authenticated Grok API call appends a `time.monotonic()` timestamp. On every message, timestamps older than 3600s are pruned before the check.

---

## Security Invariants

| Invariant | Enforcement |
|-----------|-------------|
| No cross-user order access | `Order.buyer_id == user_id` in every query; `user_id` from `message.from_user.id`, never from AI payload |
| No cross-user ticket attachment | `order_code` resolution re-checks `buyer_id == user_id` |
| No mutation tools | No price, order, or inventory modification tools exist in `CUSTOMER_TOOLS` |
| No admin tool bleedthrough | Handler imports only `customer_tool_defs`; never imports `bot/ai/tool_defs.py` or `bot/ai/schemas.py` |
| Coupon exposure | Only `is_active=True`, non-expired, non-maxed coupons — personal/single-use logic not in `find_deals` |
| GPS voluntary only | `find_nearby_stores` only executes if customer explicitly shares a Telegram location |
| Pydantic validation at boundary | `_process_tool_call()` validates every tool argument against the schema before executor call |

---

## System Prompt (as-implemented)

```
You are a friendly AI shopping assistant. You help customers find menu items,
check available deals, look up their orders, and get support.

Rules:
- You can ONLY read catalog data and the current customer's own orders.
- You CANNOT modify prices, orders, or any menu items.
- Never reveal other customers' data.
- For support issues, always offer to open a ticket or start a live chat.
- Respond in the same language the customer writes in.
- Keep responses concise — Telegram messages are short.
- If the customer shares their location, use find_nearby_stores to help them.

Support routing:
- For app/bot/payment bugs → use start_app_live_chat (reaches platform developers)
- For order/food/delivery issues → use start_store_live_chat (reaches store staff)
- Either can be preceded by open_support_ticket to leave a written record first

Available tools: browse_menu, get_today_specials, find_deals, find_nearby_stores,
                 check_coupon, get_order_status, get_my_account,
                 open_support_ticket, start_app_live_chat, start_store_live_chat
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GROK_API_KEY` | — | Required; assistant disabled if absent |
| `GROK_CUSTOMER_RATE_LIMIT` | `20` | Max AI calls per user per hour |
| `GROK_MAX_HISTORY` | (from env.py) | Max conversation turns kept in FSM |
| `MAINTAINER_IDS` | — | Comma-separated Telegram IDs for live chat relay |
| `OWNER_ID` | — | Fallback if `MAINTAINER_IDS` is empty |
| `SUPPORT_CHAT_ID` | — | Optional group chat to mirror live relay messages |

---

## DB Writes

| Operation | Table(s) | Triggered by |
|-----------|----------|--------------|
| Open ticket | `support_tickets` + `ticket_messages` | `open_support_ticket` tool |
| App live chat | `support_tickets` + `ticket_messages` | `start_app_live_chat` tool |
| Store live chat | `support_tickets` + `ticket_messages` | `start_store_live_chat` tool |
| Relay message | `ticket_messages` | Every message in `app_live_chat` / `store_live_chat` state |

No other DB writes occur. The catalog and order tables are all read-only from this feature.

---

## Known Limitations

- **Store live chat routing**: Both `start_app_live_chat` and `start_store_live_chat` currently relay to the same `MAINTAINER_IDS`. Per-brand admin targeting (via `Permission.USERS_MANAGE`) is not yet implemented.
- **Cart add**: Adding items to cart via AI is noted as a future capability; no `add_to_cart` tool exists yet.
- **No attachment passthrough**: Only photos are relayed during live chat. Documents, stickers, and voice messages are dropped with the attachment represented as `"(attachment)"` in the ticket log.
