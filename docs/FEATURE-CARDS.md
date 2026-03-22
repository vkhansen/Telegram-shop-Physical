# Feature Cards - Prioritized Implementation

> See [MENU-SYSTEM.md](MENU-SYSTEM.md) for complete menu schema, modifier format, media handling, import/export, and multi-currency docs.

## P0 - Restaurant Core (Menu Optimization)

### CARD-RC1: Multi-Media Menu Items
- **Status**: IMPLEMENTED
- **Files**: `bot/database/models/main.py` (Goods.image_file_id, Goods.media), `bot/handlers/user/shop_and_goods.py`, `bot/handlers/admin/adding_position_states.py`
- **What**: Items support a primary display photo + gallery of multiple photos/videos. Item detail shows photo via `answer_photo()`. Gallery button sends MediaGroup.
- **Admin Flow**: During item creation, send photos/videos one at a time -> first becomes primary -> all stored in media JSON array

### CARD-RC2: Prep Time + Kitchen Prep Tracking
- **Status**: IMPLEMENTED
- **Files**: `bot/database/models/main.py` (Goods.prep_time_minutes, Order.estimated_ready_at), `bot/handlers/admin/order_management.py`
- **What**: Each item has a prep time in minutes. Kitchen notifications show total prep time and estimated ready time. Orders track `estimated_ready_at`.
- **Calculation**: `max(item.prep_time * quantity)` across all order items (parallel kitchen work)

### CARD-RC3: Allergen Management
- **Status**: IMPLEMENTED
- **Files**: `bot/database/models/main.py` (Goods.allergens), `bot/handlers/admin/adding_position_states.py`
- **What**: 8 standard allergens (gluten, dairy, eggs, nuts, shellfish, soy, fish, sesame) as toggleable buttons during item creation. Shown on item detail page.
- **Storage**: Comma-separated string: `"gluten,dairy,nuts"`

### CARD-RC4: Availability Windows + Daily Limits
- **Status**: IMPLEMENTED
- **Files**: `bot/database/models/main.py`, `bot/database/methods/create.py` (add_to_cart), `bot/tasks/reservation_cleaner.py`
- **What**: Items and categories can have time windows (breakfast 06:00-11:00). Items can have daily kitchen limits. `sold_out_today` flag for instant 86-ing.
- **Daily reset**: Midnight scheduler resets `daily_sold_count` and `sold_out_today`

### CARD-RC5: Multi-Currency
- **Status**: IMPLEMENTED
- **Files**: `bot/handlers/admin/settings_management.py`, `bot/keyboards/inline.py`
- **What**: Admin can select from 13 currencies (THB default). Stored in `bot_settings` table.
- **Currencies**: THB, USD, EUR, GBP, JPY, RUB, AED, SAR, IRR, AFN, MYR, SGD, BTC

### CARD-RC6: Menu Import/Export
- **Status**: IMPLEMENTED
- **Files**: `bot/utils/menu_io.py`
- **What**: Export entire menu as JSON + images folder. Import into another store. Validates structure, handles image upload/download via Telegram API.
- **Modes**: merge (add/update) or replace (wipe and reimport)

### CARD-RC7: Interactive Modifier Builder
- **Status**: IMPLEMENTED
- **Files**: `bot/handlers/admin/adding_position_states.py`
- **What**: Step-by-step modifier group creation instead of raw JSON paste. Group name -> type (single/multi) -> required? -> options (label + price). Power users can still paste raw JSON.

---

## P0 - Critical User Experience

### CARD-FC1: Product Search
- **Status**: IMPLEMENTED
- **Files**: `bot/handlers/user/search_handler.py`
- **What**: Text search for products by name and description (ILIKE query)
- **User Flow**: Main menu -> Search -> Enter keywords -> See results -> Tap to view item
- **Integration**: Results link to existing item detail handler (`item_{name}_{category}_goods-page_...`)

### CARD-FC2: Reorder Button
- **Status**: IMPLEMENTED
- **Files**: `bot/handlers/user/orders_view_handler.py` (reorder_handler)
- **What**: One-tap reorder from order history - copies all items from a delivered order into cart
- **User Flow**: My Orders -> View Order -> Reorder -> Items added to cart
- **Handles**: Out-of-stock items skipped with notification

---

## P1 - Revenue & Trust

### CARD-FC3: Coupon / Promo Codes
- **Status**: IMPLEMENTED
- **Files**:
  - Model: `bot/database/models/main.py` (Coupon, CouponUsage)
  - Admin: `bot/handlers/admin/coupon_management.py`
  - Utils: `bot/utils/coupon_utils.py`
- **What**: Full coupon system with percent/fixed discounts, min order, max uses, per-user limits, expiry
- **Admin Flow**: Console -> Coupons -> Create (code/auto, type, value, min order, max uses, expiry)
- **User Flow**: During checkout, enter coupon code -> validate -> apply discount to order
- **Validation**: Active, not expired, not over-used, min order met, per-user limit

### CARD-FC4: Review / Rating System
- **Status**: IMPLEMENTED
- **Files**:
  - Model: `bot/database/models/main.py` (Review)
  - Handler: `bot/handlers/user/review_handler.py`
- **What**: 1-5 star ratings with optional comments, post-delivery
- **User Flow**: Order delivered -> "Leave Review" button -> Select 1-5 stars -> Optional comment
- **Constraints**: One review per order per user (UniqueConstraint)
- **Product View**: Average rating shown on product cards via `get_item_rating()`

---

## P2 - Professional Operations

### CARD-FC5: Invoice / Receipt Generation
- **Status**: IMPLEMENTED
- **Files**: `bot/utils/invoice.py`
- **What**: Text-based receipt with itemized breakdown, fees, discounts, totals
- **User Flow**: View Order -> Receipt button -> Formatted receipt in `<pre>` block
- **Includes**: Items, subtotal, delivery fee, coupon discount, bonus, total, delivery info

### CARD-FC6: Support Ticketing
- **Status**: IMPLEMENTED
- **Files**:
  - Models: `bot/database/models/main.py` (SupportTicket, TicketMessage)
  - User: `bot/handlers/user/ticket_handler.py`
  - Admin: `bot/handlers/admin/ticket_management.py`
- **What**: Full ticket lifecycle with IDs, status tracking, message history
- **User Flow**: Support -> New Ticket -> Subject -> Description -> Ticket #ABC12345 created
- **Admin Flow**: Console -> Tickets -> View -> Reply -> Resolve (notifies user)
- **Statuses**: open -> in_progress -> resolved -> closed
- **Priorities**: low, normal, high, urgent
- **Features**: Link ticket to order, user/admin replies, close ticket

### CARD-FC7: Accounting / Revenue Export
- **Status**: IMPLEMENTED
- **Files**:
  - Export: `bot/export/sales_report.py`
  - Admin: `bot/handlers/admin/accounting_handler.py`
- **What**: Sales reports, revenue by product, payment reconciliation
- **Admin Flow**: Console -> Accounting -> Summary (today/week/month/all) or Export CSV
- **Reports**:
  - Revenue summary: total, orders, avg, by payment method, top 5 products
  - Sales CSV: order code, date, items, total, payment, delivery fee, discounts
  - Revenue by product CSV: product, category, units sold, revenue, avg price
  - Payment reconciliation CSV: method, count, total, avg value

---

## P3 - Growth & Scale

### CARD-FC8: Customer Segmentation
- **Status**: IMPLEMENTED
- **Files**: `bot/handlers/admin/segmented_broadcast.py`
- **What**: Targeted broadcasts to customer segments instead of all users
- **Admin Flow**: Console -> Targeted Broadcast -> Select segment -> Type message -> Send
- **Segments**:
  - High Spenders: total_spendings >= 2x average
  - Recent Buyers: ordered in last 7 days
  - Inactive Users: no order in 30+ days
  - New Users: registered in last 7 days
- **Integration**: Uses existing BroadcastManager for batch sending

### CARD-FC9: Multi-Store / Multi-Location
- **Status**: IMPLEMENTED
- **Files**:
  - Model: `bot/database/models/main.py` (Store)
  - Admin: `bot/handlers/admin/store_management.py`
  - Order: `bot/database/models/main.py` (Order.store_id)
- **What**: Multiple store/branch locations with GPS, active/inactive toggle, default store
- **Admin Flow**: Console -> Stores -> Add (name, address, GPS) / Toggle / Set Default
- **Order Integration**: Order.store_id FK to stores table for per-order store assignment
- **Features**: Store list, detail view, activate/deactivate, set default, GPS location

---

## Database Schema Additions

| Model | Table | Key Fields |
|-------|-------|------------|
| Coupon | coupons | code, discount_type, discount_value, min_order, max_discount, valid_until, max_uses |
| CouponUsage | coupon_usages | coupon_id, user_id, order_id, discount_applied |
| Review | reviews | order_id, user_id, item_name, rating (1-5), comment |
| SupportTicket | support_tickets | ticket_code, user_id, subject, status, priority, order_id |
| TicketMessage | ticket_messages | ticket_id, sender_id, sender_role, message_text |
| Store | stores | name, address, latitude, longitude, is_active, is_default |

Order model additions: `coupon_code`, `coupon_discount`, `store_id`
