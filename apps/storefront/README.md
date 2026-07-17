# White-label storefront (CARD-38 Phase C)

Multi-tenant **Astro** app: Instagram-like product grid for **desktop and mobile**, data from the platform public catalog API.

## Setup

```bash
cd apps/storefront
cp .env.example .env
# PUBLIC_API_BASE=http://127.0.0.1:9090
npm install
npm run dev
```

Requires the bot **monitoring server** (catalog + media on port 9090 by default) and migrated DB (CARD-38 Phase A/B).

## Routes

| Path | Page |
|------|------|
| `/` | Brand directory |
| `/{brand}` | Brand home + featured branch grid |
| `/{brand}/{store}` | Branch menu |
| `/{brand}/{store}/i/{item}` | Item detail |
| `/{brand}/about` | About (`web_profile`) |
| `/{brand}/contact` | Contact + branches |
| `/{brand}/inquire` | Lead form stub → CARD-36 |
| `/{brand}/book` | Meeting booking stub → CARD-36 |
| `/{brand}/login` | OAuth / dev login (CARD-39) |
| `/{brand}/account` | Profile (email, name, avatar) |
| `/{brand}/cart` | Cart (C-08 · same cart service as Telegram) |
| `/{brand}/checkout` | Checkout delivery + cash/PromptPay (C-11–C-14) |
| `/{brand}/orders` | My orders (C-17) |
| `/{brand}/orders/{code}` | Order detail + PromptPay QR |
| `/{brand}/tickets` | Support ticket list (auth required) |
| `/{brand}/tickets/new` | Create ticket |
| `/{brand}/tickets/{code}` | Ticket thread + reply |

## Commerce parity (Telegram spine)

Web uses the **same** application services as Telegram:

`catalog` → `cart` → `checkout.ensure_delivery_profile` → `start_cash_order` / `start_promptpay_order` → `order_query`

Adapters: `bot/web/commerce_api.py` · client `src/lib/commerce.ts`.

### Browser e2e (Playwright)

```bash
# Terminal 1 — API (full_store seed so cart/checkout caps are ON)
# from repo root
$env:SEED_SNUS_COMMERCE_MODE="full_store"   # PowerShell; default in run_public_api.py
python scripts/run_public_api.py

# Terminal 2 — storefront
cd apps/storefront
# PUBLIC_API_BASE=http://127.0.0.1:9090
npm run dev

# Terminal 3 — tests
npx playwright install chromium
npm run test:e2e
```

Portfolio-only demo (inquire, no cart): `SEED_SNUS_COMMERCE_MODE=portfolio`.

### Auth env (API / bot process)

```bash
OAUTH_DEV_LOGIN=true
WEB_SESSION_SECRET=change-me
PUBLIC_SITE_URL=http://127.0.0.1:4321
# Optional Google:
# OAUTH_GOOGLE_CLIENT_ID=
# OAUTH_GOOGLE_CLIENT_SECRET=
# OAUTH_GOOGLE_REDIRECT_URI=http://127.0.0.1:9090/api/public/auth/google/callback
```

## Build

```bash
npm run build
node ./dist/server/entry.mjs
```
