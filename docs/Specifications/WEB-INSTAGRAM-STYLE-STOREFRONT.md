# Web Storefront — Instagram-Style Auto-Generated Mobile Site

> **Spec status:** `draft`  
> **Mode:** desired (new surface; data as-built from Telegram backend)  
> **Cards:** [CARD-35](../later/CARD-35-instagram-style-web-storefront.md), [CARD-34](../later/CARD-34-conversation-workflow-specifications.md) flow **W-01**  
> **Plan:** [MULTI-CHANNEL-TIERED-PLAN.md](../later/MULTI-CHANNEL-TIERED-PLAN.md)  
> **Related:** [MENU-SYSTEM.md](MENU-SYSTEM.md), multi-brand CARD-19, media ports CARD-29/30  
> **Gallery research:** [research/GALLERY-JS-INSPIRATION.md](research/GALLERY-JS-INSPIRATION.md)

---

## 1. Purpose

Provide a **responsive Instagram-style website (desktop and mobile)** that is **auto-generated** from the same PostgreSQL backend used by the Telegram shop bot. Operators do not hand-build pages: when brands, stores, categories, and items change in Telegram admin (or DB), the site reflects them. CSS is mobile-first; desktop layouts must be fully usable (wider grid, not a phone-only strip by default).

### Hierarchy (canonical)

```text
Brand  →  Store (branch)  →  Menu (categories)  →  Items (food / goods)
```

| Level | Backend source | URL sketch |
|-------|----------------|------------|
| Brand | `brands` (`slug`, logo, description, active) | `/{brandSlug}` |
| Store | `stores` (per `brand_id`, active, address, geo, menu image) | `/{brandSlug}/{storeSlug}` |
| Menu | `categories` (brand-scoped, sort_order, time windows) | `/{brandSlug}/{storeSlug}` + category tabs/sections |
| Item | `goods` (price, media, modifiers, availability) | `/{brandSlug}/{storeSlug}/i/{itemSlug}` |

---

## 2. Goals & non-goals

### Goals

1. **Auto-generated** catalog UI from live backend (no CMS page builder).  
2. **Instagram-like** visual language: square/portrait media grid, sticky profile header, story-style store chips, large item detail, bottom-safe mobile layout.  
3. **Mobile-compatible** first (320–430px width primary); tablet/desktop acceptable as widened single column or 2-col grid.  
4. **Multi-brand / multi-store** isolation via slug routing.  
5. **Deep-link into order channels** (Telegram bot, optional Instagram DM) for checkout v1.  
6. Share same **availability rules** as Telegram menu (active, sold out, windows, stock/daily limits).  
7. Fast public read path (CDN-friendly images, cacheable JSON).

### Non-goals (v1)

- Replacing Telegram admin/kitchen/driver.  
- Full in-web checkout with PromptPay slip (v1.1+ optional; see phases).  
- User accounts / wallet on the web.  
- SEO mega-site or blog CMS.  
- Pixel-perfect Instagram clone (trademark: “Instagram-**style**” visual patterns only).

---

## 3. Personas & privilege

| Actor | Access |
|-------|--------|
| Anonymous public | Browse brand → store → menu → item |
| Customer (ordering) | CTA → Telegram (or IG) with deep link context |
| Brand staff | No web admin in v1; manage catalog via Telegram |
| Superadmin | Config: enable site, base domain, feature flags |

Platform capability key (CARD-31): `web` + `shop_browse` / `maps_widget` as applicable.

---

## 4. Information architecture

### 4.1 Site map

```text
/                              → optional directory of active brands (flag) OR redirect to default brand
/{brandSlug}                   → brand profile + store picker
/{brandSlug}/{storeSlug}       → store “profile” + menu feed (categories → item grid)
/{brandSlug}/{storeSlug}/c/{categorySlug}  → optional deep-link to category section
/{brandSlug}/{storeSlug}/i/{itemSlug}      → item detail (media carousel, price, allergens, modifiers preview)
/api/v1/...                    → read JSON used by the SPA/SSR (internal contract)
/media/{mediaKey}              → public image proxy (from MediaStore / Telegram file bridge)
```

### 4.2 Slug rules

| Entity | Slug source |
|--------|-------------|
| Brand | Existing `brands.slug` (required, unique) |
| Store | New `stores.slug` (preferred) or auto-slugify `name` unique per brand; migrate/backfill |
| Category | Slugify `categories.name` per brand (handle collisions with numeric suffix) |
| Item | Slugify `goods.name` per brand (PK is name today — stable enough with brand scope) |

Uniqueness: `(brand_id, store_slug)`, category/item slugs unique within brand.

### 4.3 Navigation mental model (Instagram-style)

| UI region | Analogy | Content |
|-----------|---------|---------|
| Top profile bar | IG profile header | Brand logo, name, short bio, locale/currency |
| Horizontal chips | Story / highlight row | Stores (branches); selected chip = active store |
| Category pills | Highlight tabs | Categories in `sort_order`, time-window filtered |
| Main grid | Profile grid | Item thumbnails 1:1 or 4:5, price badge, sold-out overlay |
| Item sheet / page | Post detail | Full media, description, allergens, prep time, Order CTA |
| Bottom bar (optional) | IG tab bar | Home (brand), Menu, Order on Telegram |

---

## 5. Screen specifications

### S1 — Brand profile (`/{brandSlug}`)

**Data**

- Brand: name, description, logo URL, timezone, active  
- Stores: list of active stores (name, slug, address, lat/lng, phone, `menu_image` URL, `is_default`)  
- Optional: Telegram bot username from `bot_configs` for CTA  

**UI**

1. Full-width hero: logo (circle or rounded square) + brand name.  
2. Bio text (clamp 3 lines + expand).  
3. Primary CTA: “Order on Telegram” (deep link).  
4. “Locations” horizontal scroll of store cards (photo = `menu_image` or map pin placeholder).  
5. Tap store → S2.  
6. If exactly one active store → auto-redirect to S2 (config: `WEB_AUTO_SELECT_SINGLE_STORE=true`).

**Empty / error**

- Brand missing or inactive → 404 page.  
- No stores → message “Opening soon” + Telegram CTA if bot exists.

### S2 — Store menu feed (`/{brandSlug}/{storeSlug}`)

**Data**

- Store metadata + maps link if lat/lng  
- Categories currently available (see §7 availability)  
- Items per category currently available for this brand (and branch inventory if used)  
- `menu_style` from `bot_configs` influences layout: `grid` (default Instagram), `list`, `category_first`

**UI (grid default)**

1. Sticky subheader: brand name · store name · back.  
2. Store row: address, phone, open maps.  
3. Category pills (horizontal); sticky under header; scroll-spy to sections.  
4. For each category section: title + optional cover image + item grid (3 columns mobile).  
5. Each cell: image, name (1 line), price, sold-out/time badge.  
6. Tap item → S3.  
7. Floating CTA: “Order on Telegram” with store/brand context.

**Pull-to-refresh / stale data:** client revalidates API with short cache (§9).

### S3 — Item detail (`/.../i/{itemSlug}`)

**Data**

- Name, description, price, currency  
- Media gallery (primary `image_file_id` + `media[]`)  
- Allergens, calories, prep_time_minutes  
- Modifiers schema (display-only in v1: list groups/options/prices)  
- Availability flags: sold out, remaining daily, outside window  
- Item type: `prepared` | `product`

**UI**

1. Media carousel (swipe); aspect 4:5 preferred.  
2. Title + price.  
3. Badges: prep time, allergens chips, “86” / unavailable.  
4. Description.  
5. “Customize options” collapsible (read-only list in v1).  
6. Primary button: **Order on Telegram** (deep link with item hint).  
7. Secondary: Back to menu.

### S4 — Brand directory (`/` optional)

- Grid/list of active brands (logo + name).  
- Disabled unless `WEB_BRAND_DIRECTORY_ENABLED=true` (multi-tenant marketplace mode).

---

## 6. Auto-generation model

### 6.1 Principle

**No hand-authored HTML per brand.** Rendering is driven by:

1. **Read API** over shared DB (same as bot).  
2. **Single responsive app shell** (SSR or SPA) that maps entities → components.  
3. **Theme tokens** optional per brand (v1.1): colors derived from logo or `BotSettings` keys.

### 6.2 Data pipeline

```text
Telegram admin CRUD
       │
       ▼
 PostgreSQL (brands, stores, categories, goods, branch_inventory, bot_configs)
       │
       ▼
 Catalog read service (filters availability, brand scope)
       │
       ├─▶ Web JSON API  ──▶  Storefront UI (this product)
       └─▶ Telegram handlers (existing)
```

### 6.3 Media auto-publish

Telegram stores `file_id` only. Web needs HTTP URLs:

| Approach | Notes |
|----------|--------|
| **A. Media proxy (required for v1)** | Backend downloads via Bot API `getFile` → cache disk/S3 → serve `/media/{key}`; store `media_assets` row keyed by file_id |
| **B. Eager sync** | On admin image upload, also push bytes to object storage (future CARD-29 MediaRef) |

v1: **lazy proxy with cache** so existing menus work without re-upload.

Privacy: media endpoints are public for active catalog images only (no order slips, no delivery proof).

### 6.4 Regeneration / cache invalidation

| Event | Action |
|-------|--------|
| Item/category/store/brand update | Bump `catalog_version` per brand (Redis or DB) |
| API responses | `ETag` / `Cache-Control: public, max-age=30–120` + version query |
| Client | Revalidate on focus / interval 60s while menu open |

No static site full rebuild required for v1 (dynamic SSR/CSR is “auto-generated” from DB). Optional later: SSG export for edge.

---

## 7. Availability & filtering (parity with bot)

Apply the same rules as [MENU-SYSTEM.md](MENU-SYSTEM.md) / goods helpers:

1. Brand `is_active`  
2. Store `is_active`  
3. Category time window (`available_from` / `available_until`) in brand/platform timezone  
4. Item `is_active`, not `sold_out_today`  
5. Item time window  
6. Daily limit remaining if set  
7. Stock: `product` uses available qty; `prepared` with stock_quantity=0 means unlimited (project rule)  
8. Branch inventory when multi-store stock is in use  

Outside window / sold out: **still show** item with disabled styling + badge (Instagram “archive” clarity), unless config `WEB_HIDE_UNAVAILABLE=true`.

---

## 8. Order handoff (v1)

Web v1 is **catalog + handoff**, not full web checkout.

### Deep links

```text
https://t.me/{botUsername}?start=web_{brandId}_{storeId}_{itemToken}
```

| Param | Meaning |
|-------|---------|
| brandId / storeId | Preselect brand/store in bot (extend start payload handler) |
| itemToken | Optional opaque short id or slug hash to open item / add intent |

Copy: “Continue in Telegram to cart & pay.”

Optional secondary CTA: Instagram profile or DM link if `INSTAGRAM_CHANNEL_ENABLED` + brand IG handle in settings.

### v1.1+ (out of this core spec detail)

- Web cart + CARD-32 checkout services  
- PromptPay QR on web page  
- Same order rows as Telegram  

Flag: `WEB_CHECKOUT_ENABLED=false` by default.

---

## 9. API contract (read-only v1)

Base: `/api/v1`  
Auth: none for public catalog (rate-limit by IP).  
Locale: `?lang=th|en|…` maps to existing i18n keys for UI chrome; catalog text is DB language as stored.

### Endpoints

| Method | Path | Returns |
|--------|------|---------|
| GET | `/brands` | Active brands (if directory on) |
| GET | `/brands/{brandSlug}` | Brand + stores summary |
| GET | `/brands/{brandSlug}/stores/{storeSlug}` | Store + categories + items (availability applied) |
| GET | `/brands/{brandSlug}/stores/{storeSlug}/items/{itemSlug}` | Item detail |
| GET | `/brands/{brandSlug}/meta` | bot username, currency, timezone, menu_style, catalog_version |

### Example store payload (abridged)

```json
{
  "brand": { "slug": "suki-house", "name": "Suki House", "logo_url": "/media/…", "description": "…" },
  "store": {
    "slug": "sukhumvit",
    "name": "Sukhumvit",
    "address": "…",
    "latitude": 13.74,
    "longitude": 100.56,
    "phone": "…",
    "menu_image_url": "/media/…",
    "maps_url": "https://www.google.com/maps?q=…"
  },
  "currency": "THB",
  "catalog_version": 42,
  "categories": [
    {
      "slug": "mains",
      "name": "Mains",
      "sort_order": 1,
      "image_url": null,
      "items": [
        {
          "slug": "pad-thai",
          "name": "Pad Thai",
          "price": "89.00",
          "image_url": "/media/…",
          "available": true,
          "badges": ["prep:15m"],
          "sold_out": false
        }
      ]
    }
  ],
  "order_cta": {
    "telegram_url": "https://t.me/SukiHouseBot?start=web_1_3",
    "label_key": "web.cta.order_telegram"
  }
}
```

Errors: `404` unknown slug; `403` brand inactive; `429` rate limit.

---

## 10. Visual design system (Instagram-style)

| Token | Guidance |
|-------|----------|
| Layout width | mobile full-bleed; desktop max ~960–1200px (IG-like density, not 480px-only) |
| Grid | 3 columns, 1–2px gap, square thumbs |
| Type | System UI / Inter; name bold; price secondary |
| Colors | Neutral base (white/black/gray); accent from brand optional |
| Radius | 0 on grid (IG-like) or 4px soft; circular logo |
| Safe areas | `env(safe-area-inset-*)` for notched phones |
| Touch | min 44px targets for pills/CTAs |
| Motion | light fade on route; no heavy parallax |
| A11y | alt text from item name; contrast WCAG AA for text |

**Do not** use Instagram trademarks, glyphs, or “Instagram” branding in the product UI chrome. Describe as “visual grid storefront” in customer-facing copy.

---

## 11. i18n & currency

- Chrome strings via existing `localize()` catalogs (`web.*` keys).  
- Default lang: brand `bot_configs.default_language` or `BOT_LOCALE`.  
- Currency format: existing `format_currency` / `PAY_CURRENCY` / brand default.  
- Catalog content: as stored in DB (operators enter Thai/EN in Telegram).

---

## 12. Security & ops

| Topic | Requirement |
|-------|-------------|
| Public data only | No buyer PII, slips, kitchen notes on web API |
| Rate limit | Catalog API + media |
| HTTPS | Required in production |
| CORS | Same-origin preferred if SSR; else allow configured web origin |
| Secrets | Bot token never sent to browser; media proxy server-side only |
| Flag | `WEB_STOREFRONT_ENABLED=false` default |
| Multi-bot | Media proxy must use correct brand bot token for `getFile` |

---

## 13. Conversation / interaction flows (web)

Align with CARD-34 style acceptance (web is click UX, not chat).

### W-01 — Browse brand → store → item → handoff

| Step | Actor | Action | System |
|------|-------|--------|--------|
| 1 | user | Open `/{brandSlug}` | Load brand+stores API |
| 2 | user | Select store | Navigate S2; load menu |
| 3 | user | Filter category pill | Scroll/filter client-side |
| 4 | user | Open item | S3 detail |
| 5 | user | Tap Order on Telegram | Open deep link; bot start payload |
| 6 | user | Completes order in Telegram | Existing C-08…C-18 flows |

### W-02 — Shared item link

| Step | Actor | Action |
|------|-------|--------|
| 1 | user | Opens item URL from social share |
| 2 | system | Renders S3; breadcrumbs to store menu |
| 3 | user | Order CTA → Telegram with item context |

### W-03 — Unavailable item

| Step | Result |
|------|--------|
| Item sold out | Detail visible; CTA disabled or “Notify via Telegram”; badge shown |

---

## 14. Acceptance criteria

- [ ] With `WEB_STOREFRONT_ENABLED=true`, active brand slug serves mobile-usable profile.  
- [ ] Active stores appear; inactive brands/stores 404 or hidden.  
- [ ] Menu categories respect sort_order and time windows.  
- [ ] Items show price, image (or placeholder), sold-out state consistent with bot rules.  
- [ ] Item detail shows description, allergens, prep time when set.  
- [ ] New item added via Telegram admin appears on web within cache TTL without redeploy.  
- [ ] Telegram CTA deep link includes brand/store (and item when from S3).  
- [ ] No admin/kitchen/driver UI on site.  
- [ ] Works on iOS Safari & Android Chrome at 375px width.  
- [ ] Media proxy does not expose non-catalog file_ids.  
- [ ] Flag off: web routes return 404 or disabled page.

---

## 15. Phased delivery

| Phase | Scope | Card |
|-------|--------|------|
| **P0** | Spec (this doc) + inventory in CARD-34 | CARD-34 / 35 |
| **P1** | Read API + media proxy + S1–S3 SSR/SPA + Telegram handoff | CARD-35 |
| **P2** | Brand directory, themes, start-param handling in bot | CARD-35 follow-up |
| **P3** | In-web cart/checkout via CARD-32 | Future card |

---

## 16. Dependencies

| Dependency | Role |
|------------|------|
| Brand / Store / Categories / Goods models | Source data |
| MENU-SYSTEM availability rules | Filtering |
| BotConfig.bot_username, menu_style | CTA + layout |
| CARD-30 identities | Only if web accounts later |
| CARD-32 services | Web checkout later |
| CARD-33 Instagram | Optional dual CTA; not required for P1 |
| Media proxy / MediaRef | Images on web |

---

## 17. Config preview

```bash
WEB_STOREFRONT_ENABLED=false
WEB_BASE_URL=https://menu.example.com
WEB_BRAND_DIRECTORY_ENABLED=false
WEB_AUTO_SELECT_SINGLE_STORE=true
WEB_HIDE_UNAVAILABLE=false
WEB_CHECKOUT_ENABLED=false
WEB_CATALOG_CACHE_SECONDS=60
WEB_MEDIA_CACHE_DIR=/var/cache/storefront-media
```

---

## 18. Code map (target)

```text
bot/services/catalog_public.py    # shared read queries for web + future channels
bot/web/                          # or apps/storefront/
  app.py                          # HTTP routes / SSR
  api/v1/catalog.py
  media_proxy.py
  templates/ or frontend/
docs/Specifications/WEB-INSTAGRAM-STYLE-STOREFRONT.md  # this file
```

Telegram handlers remain the system of record for mutations.
