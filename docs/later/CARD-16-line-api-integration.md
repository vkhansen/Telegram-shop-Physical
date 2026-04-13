# Card 16: Parallel Line Messaging API Integration

## Implementation Status

> **0% Complete** | `░░░░░░░░░░░░░░░░░░░` | Audit only — no implementation started.

**Phase:** 5 — Multi-Platform Expansion
**Priority:** Medium-High
**Effort:** High (5-8 days)
**Dependencies:** All existing cards (mirrors full Telegram feature set)

---

## Why

Line is the dominant messaging platform in Thailand (~53M users vs Telegram's ~15M). Adding Line as a parallel channel dramatically increases the addressable market for this Bangkok restaurant delivery bot. The bot should support both platforms simultaneously with shared business logic, database, and admin tools.

---

## Audit Summary

### Current Architecture (Telegram-Only)

The codebase is **tightly coupled to aiogram/Telegram** across every layer:

| Layer | Telegram Coupling | Files Affected |
|-------|-------------------|----------------|
| **Handlers** | `aiogram.types.Message`, `CallbackQuery`, `Router`, `F` filters | 15+ handler files in `bot/handlers/` |
| **Keyboards** | `InlineKeyboardBuilder`, `InlineKeyboardButton`, callback_data strings | `bot/keyboards/inline.py` |
| **States (FSM)** | `aiogram.fsm.state.StatesGroup`, Redis-backed FSM storage | `bot/states/user_state.py`, `bot/config/storage.py` |
| **Middleware** | `aiogram.BaseMiddleware`, `aiogram.Dispatcher` middleware chain | `bot/middleware/` (auth, rate limit, security, analytics) |
| **Payments** | Telegram `pre_checkout_query`, receipt photo via `message.photo` | `bot/payments/`, `bot/handlers/user/order_handler.py` |
| **Notifications** | `bot.send_message()`, `bot.send_photo()`, `bot.forward_message()` | `bot/payments/notifications.py`, admin handlers |
| **Delivery Chat** | `bot.forward_message()`, Telegram live location updates | `bot/handlers/user/delivery_chat_handler.py` |
| **Database** | `telegram_id` as User PK, `telegram_message_id` in chat logs | All models in `bot/database/models/` |
| **Config** | `TOKEN` (Telegram bot token), `OWNER_ID` (Telegram user ID) | `bot/config/env.py` |
| **Entry Point** | `aiogram.Bot`, `Dispatcher`, polling loop | `bot/main.py`, `run.py` |

### Key Differences: Telegram vs Line Messaging API

| Feature | Telegram (aiogram) | Line Messaging API |
|---------|--------------------|--------------------|
| **SDK** | `aiogram` (Python, async) | `line-bot-sdk` (Python, sync/async) |
| **Webhook vs Polling** | Long-polling or webhook | **Webhook only** (requires HTTPS endpoint) |
| **User ID** | Numeric `telegram_id` (int) | String `userId` (e.g., `U1234abcd...`) |
| **Rich Menus** | `InlineKeyboardMarkup`, `ReplyKeyboardMarkup` | `RichMenu`, `FlexMessage`, `QuickReply`, `TemplateMessage` |
| **Callback Data** | `callback_data` string on inline buttons | `postbackAction` with `data` field |
| **Image Sending** | `send_photo(file_id)` or bytes | Upload to Line CDN, get `contentUrl`, send via `ImageMessage` |
| **Location** | `Message.location` (lat/lng), live location updates | `LocationMessage` (lat/lng) — **no native live location** |
| **Groups** | Bot added to group, `send_message(chat_id)` | `push_message(group_id)` or `reply_message(reply_token)` |
| **Payment** | Built-in `Telegram Payments` provider | **No built-in payments** — use LINE Pay API (separate) or external |
| **FSM/State** | aiogram FSM with Redis storage | Must be custom-built (same Redis approach works) |
| **File Handling** | `file_id` references, `bot.download()` | Content API: `GET /content/{messageId}`, binary download |
| **Message Length** | 4096 chars | 5000 chars |
| **Markdown** | Telegram MarkdownV2/HTML | **No markdown** — use FlexMessage JSON for formatting |

---

## Scope of Work

### Phase A: Platform Abstraction Layer (2-3 days)

Create a platform-agnostic messaging interface so handlers don't directly depend on Telegram or Line types.

#### A1. Unified Message Types

```
bot/platform/
├── __init__.py
├── types.py          # Platform-agnostic Message, User, Callback, Location
├── telegram.py       # Telegram adapter (wraps aiogram types)
├── line.py           # Line adapter (wraps line-bot-sdk types)
└── keyboards.py      # Unified keyboard builder → platform-specific output
```

**Key abstractions needed:**

```python
# bot/platform/types.py
class PlatformUser:
    platform: str          # "telegram" | "line"
    platform_id: str       # telegram_id or line userId (both stored as str)
    display_name: str

class PlatformMessage:
    user: PlatformUser
    text: str | None
    photo_bytes: bytes | None
    location: tuple[float, float] | None
    callback_data: str | None
    raw: Any               # Original platform object for escape hatches

class PlatformContext:
    """Passed to handlers instead of aiogram types"""
    message: PlatformMessage
    async def reply_text(self, text: str, keyboard=None): ...
    async def reply_photo(self, photo: bytes, caption: str = None): ...
    async def reply_location(self, lat: float, lng: float): ...
    async def send_to_user(self, platform_id: str, text: str, keyboard=None): ...
    async def send_to_group(self, group_id: str, text: str): ...
```

#### A2. Database Schema Changes

```sql
-- Change User PK from telegram_id (int) to platform-aware
ALTER TABLE users ADD COLUMN platform VARCHAR(10) DEFAULT 'telegram';
ALTER TABLE users ALTER COLUMN telegram_id TYPE VARCHAR(50);
-- Composite unique: (platform, platform_id)

-- DeliveryChatMessage.sender_id → VARCHAR
-- Order.buyer_id → VARCHAR
-- All FK references updated
```

**Impact:** Every query using `telegram_id` must be updated. ~30+ database methods affected.

#### A3. Config Extension

```python
# New env vars
LINE_CHANNEL_ACCESS_TOKEN = ""
LINE_CHANNEL_SECRET = ""
LINE_WEBHOOK_PORT = 8443
LINE_KITCHEN_GROUP_ID = ""
LINE_RIDER_GROUP_ID = ""
```

### Phase B: Line Bot Implementation (2-3 days)

#### B1. Webhook Server

Line requires an HTTPS webhook endpoint. Options:
- **aiohttp** server alongside aiogram polling (recommended — already async)
- **FastAPI** if more structure needed
- **ngrok** for development

```python
# bot/platform/line_webhook.py
from aiohttp import web
from linebot.v3 import WebhookParser
from linebot.v3.messaging import MessagingApi

async def handle_line_webhook(request):
    body = await request.text()
    signature = request.headers.get("X-Line-Signature")
    events = parser.parse(body, signature)
    for event in events:
        ctx = LineContext(event, messaging_api)
        await route_event(ctx)
    return web.Response(text="OK")
```

#### B2. Keyboard Translation

| Telegram | Line Equivalent | Notes |
|----------|----------------|-------|
| `InlineKeyboardMarkup` (grid of buttons) | `FlexMessage` with button components | FlexMessage is JSON-based, very flexible but verbose |
| `callback_data` | `PostbackAction(data=...)` | Same concept, string payload |
| `ReplyKeyboardMarkup` | `QuickReply` (max 13 items) | Disappears after tap; for persistent menus use `RichMenu` |
| URL buttons | `URIAction` | Direct equivalent |
| Main menu (`/start`) | `RichMenu` (persistent bottom menu) | Must be created via API, image-based |

**Major effort:** The `inline.py` keyboard file (~500+ lines) needs a parallel Line implementation. Every keyboard function must produce both Telegram and Line output.

#### B3. Feature Parity Matrix

| Feature | Telegram | Line | Migration Difficulty |
|---------|----------|------|---------------------|
| Text messages | Direct | Direct | **Low** |
| Photo send/receive | `file_id` system | Content API upload/download | **Medium** |
| Location sharing | Native | Native | **Low** |
| Live location | Native (updates stream) | **Not supported** | **High** — must poll or use external map |
| Inline keyboards | Native | FlexMessage + PostbackAction | **Medium** |
| Payment QR | Send as photo | Send as photo | **Low** |
| Receipt photo upload | `message.photo` | `ImageMessage` content download | **Medium** |
| Kitchen/Rider group notifications | `send_message(group_id)` | `push_message(group_id)` | **Low** |
| Driver-customer chat relay | `forward_message()` | No forward — must copy content | **Medium** |
| Admin commands | `/` commands + callbacks | Postback actions (no `/` commands) | **Medium** |
| Deep linking (`/start ref_code`) | `start` parameter | **Not native** — use LIFF or query params | **Medium** |
| Live location tracking (Card 15) | Native Telegram feature | **No equivalent** — need LIFF web app | **Very High** |
| File watcher (BTC addresses) | Works (platform-independent) | Same | **None** |
| Rate limiting middleware | aiogram middleware | Custom middleware on webhook | **Low** |
| FSM state management | aiogram FSM + Redis | Custom FSM + same Redis | **Medium** |

### Phase C: Line-Specific Features (1-2 days)

#### C1. Rich Menu Setup

Line's persistent bottom menu (equivalent to Telegram's main menu) requires:
- Designing a menu image (1200x810 or 2500x1686 px)
- Uploading via Line API
- Mapping tap areas to postback actions

#### C2. LIFF (Line Front-end Framework) for Live Location

Since Line has no native live location sharing, Card 15 functionality requires:
- A **LIFF web app** (mini web page inside Line) that uses browser Geolocation API
- Periodic GPS updates sent to bot backend via REST API
- WebSocket or polling for driver→customer location display

**This is the single largest gap and effort item.**

#### C3. LINE Pay Integration (Optional)

If accepting payments via Line:
- LINE Pay API v3 (separate from Messaging API)
- Request → Confirm → Capture flow
- QR code or in-app payment
- Not required if PromptPay QR and BTC are sufficient

---

## Risks & Considerations

### 1. Live Location Gap (Critical)
Telegram's live location is a first-class feature (Card 15). Line has no equivalent. Workarounds:
- **LIFF web app** — adds frontend development (HTML/JS), hosting, HTTPS cert
- **Google Maps link** — one-time location only, no updates
- **Accept the gap** — offer one-time location on Line, live only on Telegram

### 2. Webhook Infrastructure
Telegram bot runs via long-polling (no server needed). Line requires:
- HTTPS endpoint with valid SSL certificate
- Public-facing server or tunnel (ngrok for dev)
- Health monitoring for webhook uptime

### 3. Database Migration Risk
Changing `telegram_id` (int PK) to a string-based platform-aware ID is a **breaking migration** affecting every table and query. Safest approach:
- Add `platform` + `platform_user_id` columns
- Keep `telegram_id` as legacy column during transition
- Migrate queries incrementally

### 4. Message Formatting
Telegram supports MarkdownV2/HTML formatting. Line uses plain text or FlexMessage JSON. All formatted messages need dual rendering paths.

### 5. Admin Experience
Admin currently operates via Telegram. Options:
- Admin stays Telegram-only (simplest)
- Admin works on both platforms (doubles admin handler work)
- Admin uses CLI tool only (`bot_cli.py` — already platform-independent)

### 6. Testing
- Need Line webhook mock/simulator for testing
- `line-bot-sdk` has `WebhookParser` for signature verification testing
- Existing 171 tests need updating for platform abstraction

---

## Recommended Approach

### Option A: Full Abstraction (Recommended)
Build a platform abstraction layer, refactor handlers to be platform-agnostic, implement Line adapter. **5-8 days.** Enables future platforms (WhatsApp, Facebook Messenger) with minimal effort.

### Option B: Parallel Bot
Copy handlers and create a separate Line bot with shared database. **3-5 days** initially, but **doubles maintenance** long-term. Not recommended.

### Option C: Line-First Features Only
Only implement core shop/order flow on Line, keep advanced features (live location, delivery chat) Telegram-only. **3-4 days.** Pragmatic compromise.

---

## Dependencies

- `line-bot-sdk>=3.0` (Python SDK for Line Messaging API v3)
- `aiohttp>=3.9` (already likely available — webhook server)
- Line Developer Console account + Messaging API channel
- HTTPS domain/certificate for webhook
- Optional: LIFF app for live location

## Files to Create

```
bot/platform/__init__.py
bot/platform/types.py
bot/platform/context.py
bot/platform/telegram_adapter.py
bot/platform/line_adapter.py
bot/platform/line_webhook.py
bot/platform/keyboards/telegram.py
bot/platform/keyboards/line.py
```

## Files to Modify (Major)

```
bot/main.py                          — dual bot startup (polling + webhook)
bot/config/env.py                    — Line credentials + webhook config
bot/database/models/*.py             — platform-aware user IDs
bot/database/methods/*.py            — all queries using telegram_id
bot/handlers/**/*.py                 — accept PlatformContext instead of aiogram types
bot/keyboards/inline.py              — platform-aware keyboard generation
bot/middleware/*.py                   — platform-agnostic middleware
bot/payments/notifications.py        — platform-aware message sending
bot/states/user_state.py             — platform-aware FSM
```

## Estimated Total Effort

| Phase | Effort | Description |
|-------|--------|-------------|
| A: Abstraction Layer | 2-3 days | Types, adapters, DB migration |
| B: Line Implementation | 2-3 days | Webhook, keyboards, handler wiring |
| C: Line-Specific | 1-2 days | Rich menu, LIFF (if live location needed) |
| **Total** | **5-8 days** | Full parity (minus live location LIFF) |

If live location LIFF app is required, add **2-3 additional days** for frontend development and hosting setup.
