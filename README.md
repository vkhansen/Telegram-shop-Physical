# Telegram Physical Goods Shop Bot

A Telegram bot for selling physical goods with delivery — built for Thailand restaurant delivery but works for any physical goods business. Supports PromptPay QR payments with automatic slip verification, cash on delivery, and Bitcoin. Includes GPS delivery, driver-customer chat, kitchen workflow, and a full admin panel.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Aiogram](https://img.shields.io/badge/aiogram-3.22+-green.svg)](https://docs.aiogram.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-blue.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-ready-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

> **This version is for PHYSICAL GOODS** (inventory, delivery, addresses).
> Need to sell **digital goods** (keys, accounts, licenses)? Use [Telegram Digital Goods Shop](https://github.com/interlumpen/Telegram-shop) instead.

---

## Table of Contents

- [Features at a Glance](#features-at-a-glance)
- [How It Works](#how-it-works)
- [Deployment](#deployment)
- [First-Time Setup](#first-time-setup)
- [Admin Guide](#admin-guide)
- [Payment Methods](#payment-methods)
- [Delivery System](#delivery-system)
- [Customer Features](#customer-features)
- [CLI Reference](#cli-reference)
- [Monitoring](#monitoring)
- [Testing](#testing)
- [Additional Docs](#additional-docs)

---

## Features at a Glance

| Feature | Description |
|---------|-------------|
| **PromptPay QR Payments** | Auto-generated QR codes, automatic slip verification via SlipOK/EasySlip/RDCW |
| **Cash on Delivery** | Rider confirms cash receipt on delivery |
| **Bitcoin Payments** | One-time-use address pool from file |
| **GPS Delivery** | Customers share location pin, drivers get Google Maps links |
| **Delivery Types** | Door delivery, dead drop (leave at location), self-pickup |
| **Photo Proof** | Rider uploads delivery photo — required for dead drops |
| **Driver-Customer Chat** | Message relay between rider and customer during delivery |
| **Live Location Tracking** | Driver shares real-time GPS via Telegram live location |
| **Kitchen Workflow** | Order flows through kitchen → rider → customer with group notifications |
| **Delivery Zones** | Distance-based pricing calculated from your restaurant GPS |
| **Menu Modifiers** | Spice levels, extras, removals with price adjustments |
| **Referral System** | Customers earn bonus balance for referring others |
| **Multi-Language** | Thai, English, Russian, Arabic, Persian, Pashto, French |
| **Admin Panel** | In-bot settings + CLI tool for full shop management |
| **Slip Verification** | Auto-verify PromptPay slips via 3rd-party APIs (SlipOK, EasySlip, RDCW) |

---

## How It Works

### Customer Flow

```
Browse Shop → Add to Cart → Checkout → Share Location → Choose Delivery Type
→ Enter Phone → Select Payment → Pay → Upload Slip → Order Confirmed
→ Kitchen Prepares → Rider Delivers → Done
```

### Order Lifecycle

```
pending → reserved → confirmed → preparing → ready → out_for_delivery → delivered
                  ↘ expired (auto, 24h)
                  ↘ cancelled (by admin)
```

| Status | What Happens |
|--------|-------------|
| **pending** | Customer just placed the order |
| **reserved** | Inventory held for 24 hours (configurable) |
| **confirmed** | Admin verified payment and set delivery time |
| **preparing** | Kitchen is making the order (notification sent to kitchen group) |
| **ready** | Food ready, rider notified in rider group |
| **out_for_delivery** | Rider picked up — customer gets live tracking |
| **delivered** | Rider uploaded delivery photo — inventory deducted, order complete |
| **expired** | Customer didn't pay in time — inventory auto-released |
| **cancelled** | Admin cancelled — inventory released, bonus refunded |

---

## Deployment

### Requirements

- Python 3.11+
- PostgreSQL 16+
- Redis 7+
- Docker & Docker Compose (recommended)

### Option 1: Docker (Recommended)

```bash
git clone https://github.com/yourusername/telegram_shop.git
cd telegram_shop
cp .env.example .env
nano .env                    # Fill in your values (see First-Time Setup below)
docker compose up -d --build bot
docker compose logs -f bot   # Watch for startup confirmation
```

### Option 2: Manual

```bash
git clone https://github.com/yourusername/telegram_shop.git
cd telegram_shop
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup PostgreSQL and Redis separately, then:
cp .env.example .env
nano .env
python run.py
```

---

## First-Time Setup

After deployment, configure these settings. Only the first two are required — everything else has sensible defaults.

### 1. Telegram Bot Token (Required)

Get a token from [@BotFather](https://telegram.me/BotFather) and your user ID from [@userinfobot](https://telegram.me/myidbot):

```env
TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
OWNER_ID=123456789
```

### 2. Database (Required)

```env
POSTGRES_DB=telegram_shop
POSTGRES_PASSWORD=your_strong_password_here
```

### 3. PromptPay Account

You can configure this in two ways:

**Option A — From the bot (recommended):**
Go to Admin Panel → Settings → PromptPay Account. You can either upload a screenshot of your existing PromptPay QR code (the bot reads it automatically) or type your ID manually.

**Option B — In `.env` file:**
```env
PROMPTPAY_ID=0812345678              # Your phone (10 digits) or national ID (13 digits)
PROMPTPAY_ACCOUNT_NAME=My Restaurant  # Name on the bank account
```

If not configured, PromptPay won't appear as a payment option. Cash and Bitcoin still work.

### 4. Automatic Slip Verification (Optional)

Without this, an admin must manually verify every payment slip. With it, the bot auto-verifies slips in seconds.

Configure one or more providers. The bot tries them in order and falls back to the next if one fails:

```env
# SlipOK (free tier: 100 slips/month) — best for getting started
SLIPOK_API_KEY=your_key
SLIPOK_BRANCH_ID=your_branch_id

# EasySlip — best for production (has duplicate slip detection)
EASYSLIP_API_KEY=your_key

# RDCW — best for high volume (pay-as-you-go)
RDCW_CLIENT_ID=your_id
RDCW_CLIENT_SECRET=your_secret
```

All three verify slips from **any Thai bank** (KBank, SCB, KTB, BBL, TTB, GSB, TrueMoney, etc.) with a single API key. See [Slip Verification Setup Guide](docs/SLIP-VERIFICATION-SETUP.md) for signup instructions and pricing.

Set `SLIP_AUTO_VERIFY=0` to disable auto-verification and use manual admin review only.

### 5. Kitchen & Rider Groups (Optional)

Create two Telegram groups and add the bot as admin:

```env
KITCHEN_GROUP_ID=-1001234567890    # Kitchen staff see order details when confirmed
RIDER_GROUP_ID=-1001234567891      # Riders see delivery details when food is ready
```

**How to get group IDs:** Add the bot to each group, send a message, then check bot logs for the chat ID.

Without these, the kitchen/rider workflow and driver chat features are disabled. Orders still work via the admin panel and CLI.

### 6. Restaurant Location (Optional)

For delivery zone pricing based on distance:

```env
RESTAURANT_LAT=13.7563
RESTAURANT_LNG=100.5018
```

Default zones:

| Zone | Distance | Fee |
|------|----------|-----|
| Central | 0–3 km | Free |
| Inner | 3–7 km | 30 THB |
| Mid | 7–12 km | 50 THB |
| Outer | 12–20 km | 80 THB |
| Far | 20+ km | 120 THB |

Customize zones in `bot/config/delivery_zones.py`.

### 7. Language & Currency

Defaults to Thai. Change if needed:

```env
BOT_LOCALE=th          # th, en, ru, ar, fa, ps, fr
PAY_CURRENCY=THB
TIMEZONE=Asia/Bangkok
```

Customers can also switch language in the bot via the language picker button.

---

## Admin Guide

### In-Bot Admin Panel

Accessible to users with ADMIN or OWNER roles. The admin panel provides:

**Settings** (Settings button in admin console):
- **Referral Bonus %** — percentage of order total given to referrers (0 to disable)
- **Order Timeout** — hours before unpaid orders auto-expire (default: 24)
- **Timezone** — affects all log timestamps
- **PromptPay Account** — set/change recipient account via QR upload or manual entry

**Shop Management:**
- Add/edit/delete categories and products
- Set stock quantities and prices
- Configure menu modifiers (spice levels, extras, removals with price adjustments)

**Order Management:**
- View all orders with filters (by status, date, customer)
- Verify PromptPay payments (click "Verify Payment" on receipt notification)
- Advance order status through the workflow
- Cancel orders with automatic inventory release

**User Management:**
- View customer profiles and order history
- Ban/unban users
- Manage reference codes for controlled registration

**Broadcast:**
- Send messages to all users or specific groups

### Reference Codes

Users must enter a valid reference code on first `/start`. This controls who can access the bot.

- Create codes from the admin panel or CLI
- Set expiry time and max uses per code
- Codes can be for regular users or admins (admins can create their own codes)

### Referral System

When enabled (bonus % > 0):
1. Each user gets a unique referral link
2. When a referred customer completes an order, the referrer earns a bonus
3. Bonus is added to the referrer's balance, which can be applied to future orders

---

## Payment Methods

### PromptPay QR (Thailand)

The primary payment method for Thai customers (90%+ adoption).

1. Customer selects PromptPay at checkout
2. Bot generates an EMVCo-standard QR code with the exact amount embedded
3. Customer scans with any Thai banking app (KBank, SCB, BBL, KTB, TrueMoney, etc.)
4. Customer uploads a screenshot of the payment slip
5. **With auto-verification:** Bot calls SlipOK/EasySlip/RDCW API to verify the slip instantly. If verified, order is auto-confirmed. Admin gets a notification with verification details.
6. **Without auto-verification:** Admin receives the slip photo and manually clicks "Verify Payment"

**What gets verified automatically:**
- Transaction exists in the banking network
- Amount matches the order total
- Receiver matches your PromptPay account name
- Slip hasn't been used before (EasySlip only — duplicate detection)

**If verification fails:** The order stays pending and the admin is notified with the specific issue (amount mismatch, receiver mismatch, duplicate slip, etc.) for manual review.

### Cash on Delivery

1. Customer selects Cash at checkout
2. Order is created with COD status
3. Rider sees the COD amount prominently in delivery details
4. Rider confirms cash collection
5. Admin marks payment as received

### Bitcoin

1. Add Bitcoin addresses to `btc_addresses.txt` (one per line)
2. Customer selects Bitcoin at checkout
3. Bot assigns a unique address from the pool (each address used only once)
4. Customer sends BTC to the address
5. Admin confirms payment received

The bot watches `btc_addresses.txt` for changes and auto-loads new addresses.

---

## Delivery System

### Delivery Types

| Type | Description | Photo Proof |
|------|-------------|-------------|
| **Door** | Standard delivery to customer's address | Optional |
| **Dead Drop** | Leave at specified location (e.g., guard desk, under mat) | Required |
| **Pickup** | Customer picks up from restaurant | No |

For dead drops, the customer provides text instructions and an optional photo of the drop location for the rider.

### GPS & Location

During checkout, customers can share their Telegram location pin. The bot:
- Saves GPS coordinates to the order
- Generates a Google Maps link for the rider
- Calculates the delivery zone and fee based on distance from the restaurant

### Kitchen → Rider → Customer Workflow

When kitchen and rider groups are configured:

1. **Order confirmed** → Kitchen group gets a notification with all items, modifiers, and notes
2. Kitchen marks order as **preparing**, then **ready**
3. **Order ready** → Rider group gets delivery details: address, GPS link, phone number, COD amount
4. Rider picks up and marks **out for delivery**
5. Customer gets notified at each stage

### Driver-Customer Chat

While an order is out for delivery:
- The driver sends messages in the rider group → bot relays them to the customer
- The customer replies in the bot → bot relays to the rider group
- Supports text, photos, and location messages
- All messages are recorded in the database for dispute resolution

### Live Location Tracking

The driver shares Telegram's live location in the rider group → bot forwards the real-time moving pin to the customer. Works for up to 8 hours (Telegram's built-in feature).

### Photo Proof of Delivery

Before marking an order as delivered, the rider uploads a delivery photo. For dead drop orders, this is mandatory. The photo is automatically sent to the customer as confirmation and stored in the order record.

### Menu Modifiers

Products can have configurable modifiers:
- **Spice levels** (e.g., mild / medium / hot / extra hot)
- **Extras** (e.g., extra cheese +20 THB, add egg +15 THB)
- **Removals** (e.g., no onion, no sugar)

Modifiers with price adjustments are added to the item price. Modifier choices appear on the order in kitchen notifications.

---

## Customer Features

### Shopping

- Browse categories and products with lazy-loaded pagination
- View product details, price, stock status, and available modifiers
- Add items to cart with modifier selections
- Update quantities or remove items from cart
- See running total including modifier prices

### Checkout

1. Enter or confirm delivery address (saved for future orders)
2. Share GPS location (optional but recommended)
3. Select delivery type (door / dead drop / pickup)
4. Enter phone number
5. Add delivery note (optional)
6. Apply referral bonus balance (if available)
7. Select payment method
8. Complete payment

### Order Tracking

- View all past and current orders
- See real-time status updates
- Receive notifications when order status changes
- Chat with driver during delivery
- See driver's live location on a map

### Language

Customers can switch the bot's language at any time. Supported languages:
- Thai (default)
- English
- Russian
- Arabic
- Persian
- Pashto
- French

### Referral Bonuses

Each customer gets a referral link. When someone they referred completes an order, the referrer earns a configurable percentage as bonus balance, which can be applied to future orders.

---

## CLI Reference

The `bot_cli.py` tool manages the shop while the bot is running.

### Orders

```bash
# Confirm order with delivery time
python bot_cli.py order --order-code ABCDEF --status-confirmed --delivery-time "2025-11-20 14:30"

# Mark as delivered
python bot_cli.py order --order-code ABCDEF --status-delivered

# Cancel order (releases inventory, refunds bonus)
python bot_cli.py order --order-code ABCDEF --cancel

# Add/remove items from an order
python bot_cli.py order --order-code ABCDEF --add-item "Product Name" --quantity 2 --notify
python bot_cli.py order --order-code ABCDEF --remove-item "Product Name" --quantity 1 --notify

# Update delivery time
python bot_cli.py order --order-code ABCDEF --update-delivery-time --delivery-time "2025-11-21 16:00" --notify
```

### Inventory

```bash
python bot_cli.py inventory "Product Name" --set 100    # Set to exact value
python bot_cli.py inventory "Product Name" --add 50     # Add to current stock
python bot_cli.py inventory "Product Name" --remove 25  # Remove from stock
```

### Reference Codes

```bash
python bot_cli.py refcode create --expires-hours 48 --max-uses 10 --note "VIP customers"
python bot_cli.py refcode create --expires-hours 0 --max-uses 0 --note "Permanent invite"
python bot_cli.py refcode disable CODE123 --reason "No longer valid"
python bot_cli.py refcode list
python bot_cli.py refcode list --active-only
```

### Bitcoin Addresses

```bash
python bot_cli.py btc add --address bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh
python bot_cli.py btc add --file new_addresses.txt
python bot_cli.py btc list
```

### Settings

```bash
python bot_cli.py settings set timezone "Asia/Bangkok"
python bot_cli.py settings set reference_bonus_percent 5
python bot_cli.py settings set cash_order_timeout_hours 24
python bot_cli.py settings get timezone
python bot_cli.py settings list
```

### Users

```bash
python bot_cli.py ban 123456789 --reason "Violating terms" --notify
python bot_cli.py unban 123456789 --notify
```

### Data Export

```bash
python bot_cli.py export --all --output-dir backups/
python bot_cli.py export --customers --output-dir backups/
python bot_cli.py export --orders --output-dir backups/
python bot_cli.py export --refcodes --output-dir backups/
```

---

## Monitoring

### Web Dashboard

Access at `http://localhost:9090/dashboard`:
- Real-time order and event metrics
- Handler performance timing
- Error tracking
- System health status

### Health Check

`http://localhost:9090/health` — for uptime monitoring services.

### Prometheus Metrics

`http://localhost:9090/metrics/prometheus` — for Grafana integration.

### Log Files

| File | Contents |
|------|----------|
| `logs/bot.log` | Main application log |
| `logs/audit.log` | Security events (failed auth, injection attempts, rate limits) |
| `logs/orders.log` | Order creation, status changes, delivery updates |
| `logs/reference_code.log` | Code generation, usage, deactivation |
| `logs/changes.log` | Customer profile modifications |

---

## Testing

```bash
pytest                          # Run all tests
pytest -v                       # Verbose output
pytest --cov=bot                # With coverage report
pytest tests/unit/payments/     # Run only payment tests
pytest -m unit                  # Run only unit tests
pytest -m integration           # Run only integration tests
```

---

## Additional Docs

| Document | Description |
|----------|-------------|
| [Slip Verification Setup](docs/SLIP-VERIFICATION-SETUP.md) | How to sign up for SlipOK, EasySlip, RDCW — API keys, pricing, bank coverage |
| [.env.example](.env.example) | Complete environment variable reference with all defaults |
| `bot_cli.py --help` | Full CLI usage help |

---

## License

MIT License — see [LICENSE](LICENSE).

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes
4. Push and open a Pull Request
