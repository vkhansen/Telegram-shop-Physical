# Baan Thai Kitchen Bot

**A complete restaurant ordering and delivery platform built entirely inside Telegram.**

No app store. No download. No sign-up forms. Your customers open Telegram, tap Start, and order food in their own language -- in under 60 seconds.

---

## Why Telegram?

Thailand has over 50 million Telegram users. Your customers already have it installed. A Telegram bot eliminates the friction of app downloads, account creation, and update fatigue. Customers message your bot exactly the way they message their friends -- and the bot handles the rest.

---

## Product Overview

Baan Thai Kitchen Bot is a turnkey restaurant delivery system that manages the entire order lifecycle: browsing the menu, customizing dishes, paying, tracking the rider, and confirming delivery -- all through a single Telegram conversation.

It is purpose-built for Thailand's restaurant market, with first-class PromptPay integration, Thai address formatting, GPS delivery zones, and support for seven languages spoken by Thailand's residents and visitors.

---

## Feature Guide

### Multi-Language Support (7 Languages)

Thailand's dining market is international. Tourists, expats, and locals all order food, and they all prefer to do it in their own language.

- **Thai** -- native experience for local customers
- **English** -- the international default
- **Russian** -- Thailand's largest European tourist demographic
- **Arabic** -- for Middle Eastern visitors and residents
- **Farsi** -- serving Iran's growing expat community
- **Pashto** -- support for Afghan communities
- **French** -- for Francophone travellers and residents

Each user selects their language at first launch via flag-emoji buttons. The preference is saved to the database and persists across sessions. Every message, button label, error prompt, and notification the user sees is translated.

---

### Restaurant Menu System

Build your menu once and manage it in real time.

- **Categories with custom ordering** -- organize by appetizers, mains, drinks, desserts, or however your kitchen works
- **Rich item descriptions** -- name, description, price, and photo for every dish
- **Real-time stock tracking** -- items automatically become unavailable when stock hits zero; restocked items reappear instantly
- **Restaurant-style modifiers** -- spice level, protein choice, add-ons, removals. Customers customize dishes exactly the way they would speaking to a waiter
- **JSON menu import** -- load your entire menu from a structured JSON file for fast initial setup or bulk updates

---

### Shopping and Ordering

A frictionless ordering flow designed for mobile screens.

- **Shopping cart** -- add items, adjust quantities, remove items, review the full order before checkout
- **Modifier selection** -- interactive buttons for choosing spice level, protein, extras, and ingredient removals
- **Unique order codes** -- every order gets a 6-character alphanumeric code for easy reference across customer, kitchen, and rider
- **Delivery address capture** -- customers share GPS location directly in Telegram or enter a Thai structured address manually
- **Delivery notes and phone number** -- special instructions for the kitchen or rider, plus a contact number for the delivery
- **Time slot preferences** -- customers can request a preferred delivery window

---

### Payment Methods

Three payment options covering local, cash, and international customers.

#### PromptPay QR (Thailand's Standard)

PromptPay is Thailand's national payment rail, used by virtually every bank in the country. The bot generates a dynamic QR code with the exact order amount embedded. The customer scans, pays through their banking app, and uploads a receipt screenshot. An admin verifies the payment and the order proceeds.

- Dynamic QR generation with order amount pre-filled
- Linked to your PromptPay ID (phone number or national ID)
- Receipt upload and admin verification workflow

#### Cash on Delivery (COD)

The rider collects payment at the door. Simple, familiar, and trusted.

#### Bitcoin

For international customers or those who prefer cryptocurrency. The bot provides a Bitcoin address for payment.

#### Referral Bonus System

Grow your customer base organically. Customers earn a configurable percentage bonus on their referral balance when their referral code is used by a new customer. Referral percentages are adjustable from the admin panel.

---

### Delivery System

Purpose-built for Bangkok's delivery logistics.

#### Three Delivery Types

| Type | Description |
|------|-------------|
| **Door Delivery** | Standard delivery to the customer's GPS-shared location or entered address |
| **Dead Drop** | Rider leaves the order at a designated spot with photo/video proof. Instructions, photos, and video are supported for describing the drop location |
| **Self-Pickup** | Customer picks up from the restaurant. No delivery fee |

#### GPS Delivery Zones

- Restaurant location is configured via GPS coordinates
- **Haversine distance calculation** determines whether a customer falls within the delivery radius
- **Distance-based delivery fees** -- charge more for farther deliveries automatically
- Customers share their location directly through Telegram's built-in location sharing

#### Delivery Proof

Dead drop deliveries require the rider to upload a photo of the placed order, providing a verifiable record for both the customer and the business.

---

### Kitchen and Driver Workflow

A real-time operations pipeline connecting customers, kitchen staff, and riders through Telegram group notifications.

#### Order Status Pipeline

```
pending --> reserved --> confirmed --> preparing --> ready --> out_for_delivery --> delivered
```

Each transition triggers automatic notifications:

- **Kitchen group** receives new orders with action buttons to accept, start preparing, and mark as ready
- **Rider group** receives delivery assignments with customer location, order details, and action buttons
- **Customer** receives status updates at every stage -- "Your order is being prepared," "Your rider is on the way," "Delivered"

#### 24-Hour Reservation System

Orders are held in a reserved state for up to 24 hours (configurable). If payment is not confirmed within the window, the reservation expires automatically and stock is returned to inventory.

---

### Driver-Customer Live Chat

Once an order is out for delivery, a real-time chat channel opens between the customer and the rider -- relayed through the bot.

- **Bidirectional text messaging** -- rider and customer communicate without exchanging personal phone numbers
- **Photo sharing** -- rider can send photos of the building entrance, gate code area, or any landmark
- **Location sharing** -- customer can send a static pin or live GPS location; rider can share live location for real-time tracking
- **Live location tracking** -- customers watch the rider approach on a map in real time
- **Full audit trail** -- every message is logged for dispute resolution
- **Post-delivery chat window** -- chat remains open for a configurable period after delivery for follow-up questions

---

### Admin Panel (via Telegram)

Manage the entire business without leaving Telegram. The admin panel is a dedicated set of bot commands and inline menus available to authorized users.

- **Order management** -- view orders by status, transition orders through the pipeline, filter and search
- **Product CRUD** -- add new items, update prices and descriptions, delete discontinued dishes, adjust stock levels
- **Category management** -- create, rename, reorder, and remove menu categories
- **User management** -- view customer profiles, ban or unban users, assign roles (admin, kitchen staff, rider)
- **Reference codes** -- create promotional codes with expiry dates, maximum use limits, and internal notes
- **Broadcast messaging** -- send announcements to all registered users
- **Bot settings** -- adjust referral percentage, order timeout duration, timezone, and other operational parameters
- **Inventory alerts** -- receive notifications when stock levels drop below thresholds

---

### Admin CLI Tool

For operators who prefer the command line, a full-featured CLI provides:

- Order management and payment verification
- Product and category management
- User management and statistics
- Revenue analytics
- Popular item reports
- Customer lifetime value calculations

---

### Infrastructure and Reliability

Production-grade infrastructure designed for unattended operation.

| Component | Technology |
|-----------|-----------|
| Database | PostgreSQL 16 |
| Cache / FSM | Redis 7 |
| Bot Framework | Python / aiogram |
| Deployment | Docker Compose |
| Monitoring | HTTP health endpoint (port 9090) |

- **Rate limiting** -- configurable per action type to prevent abuse
- **Audit logging** -- all administrative and transactional actions are logged
- **Background tasks** -- reservation auto-expiry cleaner, file watcher, and scheduled maintenance
- **Health checks** -- Docker health checks on all three services (bot, database, Redis) with automatic restart on failure
- **Persistent storage** -- database and Redis data survive container restarts via Docker volumes

---

### Testing

The codebase is backed by a comprehensive test suite.

- **495+ automated tests** covering unit, integration, and end-to-end scenarios
- **33%+ code coverage** across the full codebase
- JSON menu loader for reproducible test data
- Docker-based test infrastructure for consistent environments

---

## Target Audience

- **Restaurant owners in Thailand** looking for a low-cost, no-app ordering channel
- **Food delivery businesses** that want full control over the customer experience without marketplace commissions
- **International restaurants** serving Thailand's diverse expat and tourist communities
- **Small and medium food businesses** that want a professional ordering system without enterprise software costs

---

## Key Differentiators

| Traditional Delivery Apps | Baan Thai Kitchen Bot |
|--------------------------|----------------------|
| Customers must download and install an app | Works inside Telegram -- zero friction |
| One language, maybe two | Seven languages for Thailand's international market |
| Generic payment integrations | First-class PromptPay with dynamic QR generation |
| Kitchen and rider use separate dashboards | Entire workflow lives in Telegram groups |
| Location sharing requires app permissions | Telegram's native GPS sharing -- including live tracking |
| Chat goes through a call center | Direct driver-customer chat with full audit trail |
| 15-30% commission per order | You own the platform -- zero commission |

---

## Quick Start

### Prerequisites

- A Linux server (or any host running Docker)
- Docker and Docker Compose installed
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- Your Telegram user ID (get it from [@userinfobot](https://t.me/userinfobot))

### 1. Clone and Configure

```bash
git clone <repository-url>
cd Telegram-shop-Physical
cp .env.example .env
```

Edit `.env` with your values:

```dotenv
# Telegram bot token from @BotFather
TOKEN=your_bot_token_here

# Your Telegram user ID (becomes the bot owner/admin)
OWNER_ID=123456789

# PromptPay payment details
PROMPTPAY_ID=0812345678
PROMPTPAY_ACCOUNT_NAME=Your Restaurant Name

# Restaurant GPS coordinates (for delivery zone calculation)
RESTAURANT_LAT=13.7563
RESTAURANT_LNG=100.5018

# Kitchen and rider Telegram group IDs
KITCHEN_GROUP_ID=-100xxxxxxxxxx
RIDER_GROUP_ID=-100xxxxxxxxxx

# Database credentials (change the password)
POSTGRES_DB=telegram_shop
POSTGRES_USER=shop_user
POSTGRES_PASSWORD=your_strong_password_here

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Timezone
TIMEZONE=Asia/Bangkok
```

### 2. Deploy

```bash
docker compose up -d
```

This starts three containers:

| Container | Purpose | Port |
|-----------|---------|------|
| `telegram_shop_db` | PostgreSQL 16 database | 5432 |
| `telegram_shop_redis` | Redis 7 cache and FSM storage | 6379 |
| `telegram_shop_bot` | The bot application | 9090 (health) |

All three services include health checks and automatic restart policies.

### 3. Verify

```bash
# Check all containers are healthy
docker compose ps

# Check the health endpoint
curl http://localhost:9090/health

# View bot logs
docker compose logs -f bot
```

### 4. Start Using

1. Open Telegram and message your bot
2. Select your language
3. Use the admin panel (available to the `OWNER_ID` user) to add categories and products
4. Share the bot link with customers

---

## Architecture

```
Customer (Telegram)
       |
       v
  [ Bot Service ]  <-->  [ Redis ]     (session state, caching)
       |
       v
  [ PostgreSQL ]                        (orders, users, products, audit log)
       |
       +---> Kitchen Group (Telegram)   (new order notifications)
       +---> Rider Group (Telegram)     (delivery assignments)
```

Data flows through a single bot process. Kitchen staff and riders interact through standard Telegram groups where the bot posts order cards with inline action buttons. Customers never leave their private chat with the bot.

---

## Support and Configuration

All operational settings are adjustable at runtime through the admin panel or environment variables:

| Setting | Default | Description |
|---------|---------|-------------|
| `PAY_CURRENCY` | THB | Display currency for prices |
| `TIMEZONE` | Asia/Bangkok | Timezone for all timestamps |
| `BOT_LOCALE` | th | Default language for the bot |
| `MIN_AMOUNT` / `MAX_AMOUNT` | 20 / 10,000 | Payment amount limits |
| `MONITORING_PORT` | 9090 | Health check endpoint port |

Referral percentages, order timeout durations, and other business rules are configurable from the admin panel inside Telegram.

---

*Built for Thailand's restaurant industry. Powered by Telegram.*
