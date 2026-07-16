# CARD-40 Parity Matrix (Tier A)

> Machine vocabulary lives in `bot/platform/capabilities.py`.  
> **Parity** = same service + same domain outcomes + same capability keys — not the same UI.  
> Status legend: **done** · **debt** · **web-only** · **tg-ops-only** · **shared** (mask-gated)

Last updated: 2026-07-17 (Tier A freeze)

## 1. How to read

| Column | Meaning |
|--------|---------|
| **Key** | `CAPABILITY_KEYS` entry (aliases: `shop_browse` → `catalog`) |
| **Service** | Application service / platform module (adapters must not fork business rules) |
| **Web** | Default customer mask on `channel=web` |
| **Telegram** | Default customer mask on `channel=telegram` |
| **Status** | Parity classification |

Default masks come from `PLATFORM_CAPS ∩ ROLE_FEATURES ∩ CHANNEL_DEFAULT_OFF` then brand `web_profile`.

---

## 2. Capability rows

| Key | Service module | Web (customer) | Telegram (customer) | Status |
|-----|----------------|----------------|---------------------|--------|
| `catalog` | `catalog_public` | ON | ON | **shared** — parity required |
| `item_detail` | `catalog_public` | ON | ON | **shared** |
| `media` | `media_ref` / `media_proxy` | ON | ON | **shared** |
| `cart` | `services/cart` | ON if commerce_mode allows | ON if commerce_mode allows | **shared** (web UI may lag; service is law) |
| `modifiers_full` | cart / catalog | ON (web) | ON | **shared** |
| `modifiers_basic` | cart | limited surfaces | off default (full on TG) | platform-specific |
| `checkout` | `services/checkout` | ON if full_store/hybrid | ON if full_store/hybrid | **shared** |
| `portfolio` | catalog + leads mode | ON if portfolio/hybrid | ON if portfolio/hybrid | mode-driven |
| `payment_promptpay` | `checkout` | follows checkout | follows checkout | **shared** |
| `payment_crypto` | `checkout` | follows checkout | follows checkout | **shared** |
| `payment_cash` | `checkout` | follows checkout | follows checkout | **shared** |
| `order_status` | `order_query` | ON | ON | **shared** — parity required |
| `tickets` | `tickets_web` → unify TG | ON | ON | **shared** — Tier C unify |
| `auth` | `web_auth` + identities | ON (OAuth) | **OFF** (implicit TG identity) | adapter differs; same user spine |
| `ai_customer` | Grok tools → services | optional later | ON | **shared tools** when mask on (Tier D) |
| `referrals` | domain / later service | ON | ON | shared if product uses |
| `reviews` | domain / later service | ON | ON | shared if product uses |
| `location_once` | delivery / profile | optional | ON | channel-native I/O |
| `location_live` | delivery | optional / rare | ON | TG-strong; web optional |
| `delivery_chat` | Messenger + domain | **OFF** default | ON | channel-native |
| `maps_widget` | storefront | ON | OFF (not in TG ceiling) | **web-only** UX |
| `leads` | `leads_bookings` | ON | **OFF** default (mask may re-enable) | **web-only** by policy |
| `booking` | `leads_bookings` (+ calendar) | ON | **OFF** default (mask may re-enable) | **web-only** by policy |
| `age_gate` | brand / compliance | ON if brand flag | **OFF** default | **web-typical** |
| `about` | content / `web_profile` | ON | **OFF** default | **web-only** marketing |
| `faq` | content | ON | **OFF** default | **web-only** |
| `benefits` | content | ON | **OFF** default | **web-only** |
| `featured` | content | ON | **OFF** default | **web-only** |
| `ticker` | content | ON | **OFF** default | **web-only** |
| `contact` | content / brand contact | ON | **OFF** default | **web-only** chrome |
| `social_links` | `web_profile` | ON | **OFF** default | **web-only** |
| `admin_console` | ops (later services) | **OFF** (not in web ceiling) | role=admin only | **tg-ops-only** |
| `kitchen_ops` | ops | **OFF** | role=admin/kitchen | **tg-ops-only** |
| `driver_dispatch` | ops | **OFF** | role=driver | **tg-ops-only** |
| `broadcast` | ops / Messenger | **OFF** | role=admin | **tg-ops-only** |

---

## 3. Default customer masks (summary)

### Telegram customer

```text
ON:  catalog, item_detail, media, cart*, checkout*, payment_*, order_status,
     tickets, ai_customer, referrals, reviews, location_*, delivery_chat,
     modifiers_full, portfolio*
OFF: leads, booking, age_gate, about, faq, benefits, featured, ticker,
     contact, social_links, auth, maps_widget, admin_console, kitchen_ops,
     driver_dispatch, broadcast
```

`*` = also gated by `commerce_mode` / brand modules.

### Web customer

```text
ON:  catalog, item_detail, media, about, faq, benefits, featured, ticker,
     contact, leads, booking, age_gate†, tickets, auth, social_links,
     maps_widget, cart*+checkout*+payment_*, order_status, portfolio*,
     referrals, reviews, ai_customer (optional product)
OFF: admin_console, kitchen_ops, driver_dispatch, broadcast, delivery_chat
```

`†` = `brand.age_gate_enabled`.

---

## 4. Adapter enforcement helpers

```python
from bot.platform.capabilities import can, cap_enabled, features_for, resolve_capabilities

# Platform policy only (no brand):
assert can("instagram", "location_live") is False
assert can("telegram", "shop_browse") is True  # alias → catalog

# Brand-resolved mask (public API / storefront / future TG gate):
caps = resolve_capabilities(
    commerce_mode=brand.commerce_mode,
    age_gate_enabled=brand.age_gate_enabled,
    web_profile=brand.web_profile,
    channel="telegram",  # or "web"
    role="customer",
)
if not cap_enabled(caps, "checkout"):
    ...
```

- **Telegram T0:** no mandatory handler churn; prefer services + masks for new code.
- **Instagram / LINE (CARD-33/16):** must call `can` / resolved mask at adapter boundary.
- **Web:** storefront already gates UI via resolved `capabilities`.

---

## 5. Tier tracking (parity work beyond A)

| Tier | Focus | Matrix impact |
|------|--------|----------------|
| **A** ✅ | Contract freeze | This file + tests |
| **B** ✅ | Commerce spine | cart/checkout/order_status via services + `commerce_api.py` |
| **C** | Tickets + identity + Messenger | tickets row → unify; notify via Messenger |
| **D** | Grok tools | `ai_customer` tools respect mask + services |
| **E** | Explicit non-parity | leads/booking/ops enforcement tests |
| **F** | Scorecard + PR gate | checklist green |

---

## 6. One-line law

> Web and Telegram share every business capability both should have; masks deliberately omit the rest — especially web lead/booking on Telegram and ops consoles on web customers.
