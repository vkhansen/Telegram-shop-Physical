# Menu System - Complete Reference

## Overview

The menu system is built for **restaurants selling perishable, time-sensitive goods**. It handles multi-media menu items, prep time tracking, allergen management, time-windowed availability, daily kitchen limits, and multi-currency pricing. Menus can be exported/imported as JSON for sharing between stores.

---

## Database Schema

### Categories

| Column | Type | Default | Description |
|--------|------|---------|-------------|
| `name` | String(100) | **PK** | Category name (e.g., "Appetizers", "Breakfast") |
| `sort_order` | Integer | 0 | Display order (lower = first) |
| `description` | Text | null | Category description shown to customers |
| `image_file_id` | String(255) | null | Telegram file_id for category cover image |
| `available_from` | String(5) | null | "06:00" — category visible starting this time |
| `available_until` | String(5) | null | "11:00" — category hidden after this time |
| `brand_id` | Integer FK | null | Multi-brand tenant isolation |

**Time windows**: If both `available_from` and `available_until` are set, the category is only shown during that window (in the configured timezone). Use this for breakfast/lunch/dinner menus. Leave both null for always-visible categories.

### Goods (Menu Items)

| Column | Type | Default | Description |
|--------|------|---------|-------------|
| `name` | String(100) | **PK** | Item name (e.g., "Pad Thai") |
| `price` | Numeric(12,2) | required | Base price in configured currency |
| `description` | Text | required | Full item description |
| `category_name` | String(100) FK | required | Parent category |
| `stock_quantity` | Integer | 0 | Warehouse stock (total units on hand) |
| `reserved_quantity` | Integer | 0 | Units held by pending orders |
| `modifiers` | JSON | null | Modifier schema (see below) |
| `image_file_id` | String(255) | null | Primary display photo (Telegram file_id) |
| `media` | JSON | null | Gallery: `[{"file_id": "...", "type": "photo\|video"}]` |
| `prep_time_minutes` | Integer | null | Kitchen preparation time in minutes |
| `allergens` | String(500) | null | Comma-separated: `"gluten,dairy,nuts"` |
| `is_active` | Boolean | true | Permanent on/off (seasonal items, discontinued) |
| `sold_out_today` | Boolean | false | Temporary "86'd" flag (resets at midnight) |
| `daily_limit` | Integer | null | Max units kitchen can make per day (null=unlimited) |
| `daily_sold_count` | Integer | 0 | Units sold today (resets at midnight) |
| `available_from` | String(5) | null | "06:00" — item available starting this time |
| `available_until` | String(5) | null | "22:00" — item unavailable after this time |
| `calories` | Integer | null | Nutritional info (kcal) |
| `brand_id` | Integer FK | null | Multi-brand tenant isolation |

#### Computed Properties

```python
item.available_quantity  # stock_quantity - reserved_quantity
item.daily_remaining     # daily_limit - daily_sold_count (None if no limit)
item.is_currently_available  # Checks: is_active AND NOT sold_out AND daily limit AND stock > 0
```

#### Availability Checks (enforced at add-to-cart)

When a customer tries to add an item to cart, these checks run in order:
1. `is_active` must be `True`
2. `sold_out_today` must be `False`
3. `daily_sold_count < daily_limit` (if daily_limit is set)
4. Current time within `available_from`-`available_until` window (if set)
5. `available_quantity > 0` (stock check)

Each check returns a specific error message to the customer.

---

## Modifier System

Modifiers let customers customize menu items (spice level, extras, toppings). They're stored as a JSON schema on each `Goods` row.

### Schema Format

```json
{
  "spice_level": {
    "label": "Spice Level",
    "type": "single",
    "required": true,
    "options": [
      {"id": "mild", "label": "Mild", "price": 0},
      {"id": "medium", "label": "Medium", "price": 0},
      {"id": "hot", "label": "Hot", "price": 0},
      {"id": "thai_hot", "label": "Thai Hot", "price": 10}
    ]
  },
  "extras": {
    "label": "Add-ons",
    "type": "multi",
    "required": false,
    "options": [
      {"id": "extra_cheese", "label": "Extra Cheese", "price": 20},
      {"id": "extra_protein", "label": "Extra Protein", "price": 35},
      {"id": "fried_egg", "label": "Fried Egg", "price": 15}
    ]
  }
}
```

### Field Reference

| Field | Values | Description |
|-------|--------|-------------|
| `type` | `"single"` or `"multi"` | Single-choice (radio) or multi-choice (checkbox) |
| `required` | `true`/`false` | Must the customer select something? |
| `options[].id` | string | Machine-readable ID (auto-generated from label) |
| `options[].label` | string | Human-readable label shown to customer |
| `options[].price` | number | Price adjustment (0 = free, positive = surcharge) |

### How Pricing Works

```
Final item price = base_price + sum(selected modifier option prices)
```

For multi-choice, all selected options' prices are summed. For single-choice, the selected option's price is added.

### Admin Creation

Admins can create modifiers in two ways:
1. **Interactive builder**: Step-by-step prompts for group name, type, required/optional, then options with label + price. Repeat for multiple groups.
2. **Raw JSON paste**: For power users who prepare the JSON externally.

---

## Media System

### How Images Work

Telegram stores files on its servers and gives each file a `file_id` string. This file_id is **bot-specific** — it only works with the bot that uploaded the file.

| Field | Type | Description |
|-------|------|-------------|
| `image_file_id` | String | Primary display photo (shown in item detail) |
| `media` | JSON array | Gallery of additional photos/videos |

### Media JSON Format

```json
[
  {"file_id": "AgACAgIAAxkBAAI...", "type": "photo"},
  {"file_id": "BAACAgIAAxkBAAI...", "type": "video"},
  {"file_id": "AgACAgIAAxkBAAI...", "type": "photo"}
]
```

### Admin Upload Flow

During item creation:
1. Bot prompts "Send a photo or video"
2. Admin sends photos/videos one at a time
3. First photo becomes `image_file_id` (primary display)
4. All media stored in `media` JSON array
5. Admin presses "Done" when finished, or "Skip" for no images

### Customer Display

- **Item detail page**: If `image_file_id` exists, shows photo with caption (via `answer_photo`). Otherwise text-only.
- **Gallery button**: If `media` array has >1 entry, a "Gallery (N)" button appears. Tapping sends a Telegram MediaGroup (up to 10 photos/videos).
- **Item list**: Shows prep time and sold-out indicator in button labels.

---

## Multi-Currency

### Configuration

Currency defaults to **THB (Thai Baht)**. Admins can change it via:

**Admin Panel > Settings > Currency**

Supported currencies:
| Code | Currency |
|------|----------|
| THB | Thai Baht (default) |
| USD | US Dollar |
| EUR | Euro |
| GBP | British Pound |
| JPY | Japanese Yen |
| RUB | Russian Ruble |
| AED | UAE Dirham |
| SAR | Saudi Riyal |
| IRR | Iranian Rial |
| AFN | Afghan Afghani |
| MYR | Malaysian Ringgit |
| SGD | Singapore Dollar |
| BTC | Bitcoin |

### Where Currency is Used

- All item prices display with the configured currency symbol
- Order totals, cart display, invoices/receipts
- Revenue reports and accounting exports
- Stored in `bot_settings` table as `pay_currency`
- Falls back to `PAY_CURRENCY` env var if not set in DB

### Adding a New Currency

Add to `SUPPORTED_CURRENCIES` list in `bot/handlers/admin/settings_management.py`:
```python
("🇰🇷 KRW (Korean Won)", "KRW"),
```

---

## Kitchen Integration

### Prep Time Tracking

When a kitchen notification is sent (order status -> `confirmed`), the system:

1. Queries `prep_time_minutes` for each item in the order
2. Calculates `max(prep_time * quantity)` across items (parallel kitchen work)
3. Sets `order.estimated_ready_at = now + max_prep_time`
4. Sets `order.total_prep_time_minutes` on the order
5. Includes prep time and modifier details in the kitchen group notification

### Kitchen Notification Format

```
🔔 New Order: ABC123

Items:
  - Pad Thai x2 | spice_level: hot; extras: extra_cheese, fried_egg
  - Green Curry x1
Note: No peanuts please
Type: door

⏱ Est. prep: 30 min
🕐 Ready by: 14:45
```

### Daily Reset

At midnight (in the configured timezone), a scheduler task resets:
- `daily_sold_count = 0` for all items
- `sold_out_today = False` for all items

This is handled by `reset_daily_counters()` in `bot/tasks/reservation_cleaner.py`.

### Quick Controls for Kitchen Staff

Admins can instantly:
- **86 an item** (sold out today): `toggle_soldout_{item_name}` — one-tap toggle
- **Deactivate an item** (permanent): `toggle_active_{item_name}` — one-tap toggle

Both accessible from the admin goods management panel.

---

## Menu Import/Export

### Purpose

Transfer menus between bot instances, stores, or brands. Export a complete menu as JSON + images, import it into another bot.

### Export

```python
from bot.utils.menu_io import export_menu_to_json, download_menu_images

# Step 1: Generate JSON with image references
export_dir = export_menu_to_json()  # Creates menu_export_20240115_143022/

# Step 2: Download actual image files from Telegram (requires bot instance)
count = await download_menu_images(bot, export_dir)
```

**Output structure:**
```
menu_export_20240115_143022/
├── menu.json           # Full menu data
└── images/
    ├── cat_appetizers.jpg
    ├── item_pad_thai_main.jpg
    ├── item_pad_thai_0.jpg      # Gallery photo
    ├── item_pad_thai_1.mp4      # Gallery video
    ├── item_green_curry_main.jpg
    └── ...
```

### menu.json Format

```json
{
  "version": "2.0",
  "exported_at": "2024-01-15T14:30:22.123456",
  "currency": "THB",
  "categories": [
    {
      "name": "Appetizers",
      "sort_order": 1,
      "description": "Start your meal right",
      "image": "images/cat_appetizers.jpg",
      "available_from": null,
      "available_until": null
    },
    {
      "name": "Breakfast",
      "sort_order": 0,
      "description": "Served 06:00-11:00",
      "image": "images/cat_breakfast.jpg",
      "available_from": "06:00",
      "available_until": "11:00"
    }
  ],
  "items": [
    {
      "name": "Pad Thai",
      "price": 120.00,
      "description": "Classic stir-fried rice noodles with tamarind sauce",
      "category": "Appetizers",
      "stock_quantity": 100,
      "modifiers": {
        "spice_level": {
          "label": "Spice Level",
          "type": "single",
          "required": true,
          "options": [
            {"id": "mild", "label": "Mild", "price": 0},
            {"id": "hot", "label": "Hot", "price": 0}
          ]
        }
      },
      "image": "images/item_pad_thai_main.jpg",
      "gallery": [
        {"file": "images/item_pad_thai_0.jpg", "type": "photo"},
        {"file": "images/item_pad_thai_1.mp4", "type": "video"}
      ],
      "prep_time_minutes": 15,
      "allergens": "gluten,eggs,nuts",
      "is_active": true,
      "daily_limit": 50,
      "available_from": null,
      "available_until": null,
      "calories": 450
    }
  ]
}
```

### Import

```python
from bot.utils.menu_io import validate_menu_json, import_menu_from_json, upload_menu_images

# Step 1: Validate
is_valid, errors = validate_menu_json("path/to/menu.json")
if not is_valid:
    print(f"Errors: {errors}")

# Step 2: Import data (categories + items, no images yet)
stats = import_menu_from_json("path/to/menu.json", mode="merge")
# stats = {"categories_created": 3, "items_created": 25, "items_updated": 0, ...}

# Step 3: Upload images and link file_ids (requires bot instance)
count = await upload_menu_images(bot, "path/to/menu.json", chat_id=OWNER_ID)
```

### Import Modes

| Mode | Behavior |
|------|----------|
| `merge` | Update existing items/categories, add new ones. Existing data not in JSON is preserved. |
| `replace` | Delete ALL existing items and categories first, then import fresh. |

### Image Handling on Import

Since Telegram file_ids are bot-specific, the import process:
1. Reads local image files from the `images/` folder
2. Uploads each to Telegram (sends to the owner's chat, then deletes the message)
3. Captures the new file_id from Telegram's response
4. Updates the database with the new file_id

### Validation

`validate_menu_json()` checks:
- Valid JSON structure
- Required fields (`name` on categories, `name`/`category` on items)
- Category references (items must reference existing categories in the same file)
- Price validity (must be numeric)
- Modifier structure (each group must have `options` array)
- Image file existence (warns if referenced images are missing from disk)

### CLI Usage

```bash
# Export current menu
python bot_cli.py menu-export --output ./my_menu

# Validate a menu file
python bot_cli.py menu-validate --file ./my_menu/menu.json

# Import a menu (merge mode)
python bot_cli.py menu-import --file ./my_menu/menu.json --mode merge

# Import with replace (destructive!)
python bot_cli.py menu-import --file ./my_menu/menu.json --mode replace --stock 50
```

---

## Creating a Menu from Scratch

### Via Telegram Bot (Admin Panel)

1. **Create categories first**: Admin Panel > Categories > Add Category
2. **Add items**: Admin Panel > Goods > Add Item, then follow the flow:
   - Name > Description > Photos/Videos > Price > Category > Stock
   - Prep Time > Allergens > Availability Window > Daily Limit > Modifiers

### Via JSON Import

1. Create a `menu.json` file following the format above
2. Place item images in an `images/` folder next to the JSON
3. Run import via CLI or the bot's admin import handler

### Minimal menu.json Example

```json
{
  "version": "2.0",
  "currency": "THB",
  "categories": [
    {"name": "Main Dishes", "sort_order": 0}
  ],
  "items": [
    {
      "name": "Green Curry",
      "price": 150,
      "description": "Thai green curry with coconut milk",
      "category": "Main Dishes",
      "stock_quantity": 100,
      "prep_time_minutes": 20,
      "allergens": "shellfish,dairy",
      "image": "images/green_curry.jpg"
    }
  ]
}
```

No modifiers, no daily limit, no availability window, no gallery — all optional. Only `name`, `price`, `description`, and `category` are required per item.

---

## Standard Allergens

The admin creation flow offers 8 common allergens as toggleable buttons:

| ID | Label |
|----|-------|
| `gluten` | Gluten |
| `dairy` | Dairy |
| `eggs` | Eggs |
| `nuts` | Nuts (tree nuts) |
| `shellfish` | Shellfish |
| `soy` | Soy |
| `fish` | Fish |
| `sesame` | Sesame |

Stored as comma-separated string: `"gluten,dairy,eggs"`. Additional allergens can be added by editing the `COMMON_ALLERGENS` list in `bot/handlers/admin/adding_position_states.py`.

---

## File Reference

| File | Purpose |
|------|---------|
| `bot/database/models/main.py` | Categories, Goods, OrderItem models |
| `bot/handlers/admin/adding_position_states.py` | Admin item creation flow (11 steps) |
| `bot/handlers/admin/goods_management_states.py` | Sold-out/active toggles |
| `bot/handlers/admin/settings_management.py` | Currency selection |
| `bot/handlers/user/shop_and_goods.py` | Customer browsing, photo display, gallery |
| `bot/handlers/user/cart_handler.py` | Cart with modifier selection flow |
| `bot/handlers/admin/order_management.py` | Kitchen notifications with prep time |
| `bot/utils/modifiers.py` | Modifier price calculation and validation |
| `bot/utils/menu_io.py` | Menu JSON export/import/validate |
| `bot/tasks/reservation_cleaner.py` | Daily counter reset |
| `bot/states/goods_state.py` | FSM states for item creation |
