# White-Label Site Generation — Astro Implementation Brief

> **Status:** ready to implement  
> **Epic:** [CARD-38](../done/CARD-38-white-label-brand-branch-sites.md)  
> **Bootstrap:** [CLEAR-START.md](../CLEAR-START.md)  
> **Last updated:** 2026-07-16

This document is the **build contract** for generating **Instagram-like brand and branch websites** from the platform database using **Astro**. Sites **must work fully on both desktop and mobile** (responsive), with an Instagram-inspired visual language optimized for touch and scaled cleanly for large screens.

---

## 1. Goal

One **Astro multi-tenant app** that, for every Brand in the DB:

- Renders a **brand site** and **branch sites** from live data  
- **Works on desktop and mobile** (not mobile-only): responsive layout, keyboard + mouse and touch  
- Feels **Instagram-like** (profile grid, sticky chips, detail sheet/lightbox, age gate, fast LCP) while remaining usable on wide viewports  
- Supports **full_store**, **portfolio** (call/book to order), and **hybrid** commerce modes  
- Carries **tenant disclaimers / age gates** from DB  
- Later attaches **lead form + meeting booking** (CARD-36) without a second site stack  

**Not a goal:** one hand-built Astro repo per brand, or Markdown-only product catalogs as source of truth.

---

## 2. Locked decisions

| Decision | Choice |
|----------|--------|
| Frontend framework | **Astro 5+** (static-first where possible; server for API-backed multi-tenant + forms) |
| Styling | **Tailwind CSS** (responsive breakpoints: mobile → tablet → desktop) |
| Viewport | **Desktop + mobile required** — mobile-first CSS, desktop layouts fully supported |
| Gallery UX | **IG-style product grid** (3-col on phone, 3–4+ col on desktop); optional masonry “storm” strip; PhotoSwipe or custom sheet/lightbox for detail ([gallery research](research/GALLERY-JS-INSPIRATION.md)) |
| Data source | **PostgreSQL via public catalog API** (platform), not content collections for products |
| Tenancy | Path prefix `/{brandSlug}/…` (custom domains later) |
| Ops / checkout engine | **Telegram bot** remains primary for full_store orders |
| Vertical | Theme + compliance config only — food, physical goods, restricted portfolio all same engine |

---

## 3. Context (platform)

### Already built (reuse)

- Multi-brand Telegram (`Brand`, `BotConfig`, BotPool) — CARD-19  
- Multi-store + menu image + PromptPay — CARD-28  
- Goods: `product` vs `prepared`, modifiers, media file_ids, availability rules  
- Branch inventory, carts, orders with `brand_id` / `store_id`  

### Must add (CARD-38)

| Layer | Deliverable |
|-------|-------------|
| DB | `store.slug`, brand legal/DBD/support, `commerce_mode`, age flags, goods web flags, `web_profile` JSONB |
| API | Public read: brand, stores, menu, item (+ about/contact payload) |
| Media | Proxy Telegram catalog `file_id` → HTTPS URL |
| Astro app | Multi-tenant Instagram-like shell consuming API |

### Content model (hybrid)

See [BRAND-BRANCH-WEB-CONTENT-MODEL.md](BRAND-BRANCH-WEB-CONTENT-MODEL.md):

- **Columns:** address, phone, geo, DBD, legal name  
- **Tables:** categories, goods, inventory  
- **web_profile JSON:** about, hero, FAQ, social, **compliance/disclaimers**, theme, modules  

### Commerce & compliance

See [WHITE-LABEL-SITE-MODES-COMPLIANCE-LEADS.md](WHITE-LABEL-SITE-MODES-COMPLIANCE-LEADS.md):

- Modes: `full_store` | `portfolio` | `hybrid`  
- Age gate + disclaimer text from tenant config  
- Lead form + booking (CARD-36 after shell works)

---

## 4. Responsive UX requirements (desktop + mobile)

**Requirement:** Full product experience on **desktop (≥1024px)** and **mobile (≤480px)**, plus tablet in between.  
**Design language:** Instagram-inspired (visual grid, chips, fast media) — **not** “mobile only, desktop afterthought.”

### 4.1 Breakpoint strategy (Tailwind)

| Breakpoint | Intent |
|------------|--------|
| default (&lt;640px) | Phone: 3-col grid, bottom-friendly CTAs, optional bottom sheet for item |
| `sm` / `md` | Tablet: slightly wider grid/gaps, same components |
| `lg`+ (≥1024px) | Desktop: max-width content area (e.g. 960–1200px), multi-col grid (3–4–5), side-by-side item detail optional, hover states for cards |

Desktop must **not** be only a thin 480px column in the middle of an empty screen unless the brand theme explicitly chooses “phone mock” mode. Default theme uses a **proper desktop width** with Instagram-like density.

### 4.2 Pattern matrix

| Pattern | Mobile | Desktop |
|---------|--------|---------|
| Profile header | Stacked logo + name + CTAs | Same row or wider hero with logo left / CTAs right |
| Store / category chips | Horizontal scroll | Horizontal scroll or wrap row |
| Product grid | **3 columns**, tight gap | **3–5 columns**, same card language |
| Item open | Bottom sheet or full page | Modal lightbox **or** split panel / full page (mouse + Esc) |
| Sticky filters | Sticky under header | Sticky under header / optional sidebar filter on `lg` |
| Age gate | Full viewport | Full viewport (centered card OK) |
| Footer | Stacked legal + disclaimers | Multi-column footer |
| CTAs by mode | Full-width primary buttons | Inline + hover; same modes |
| Performance | Lazy images, small srcset | Larger srcset, same proxy |
| Input | 44px touch targets | Hover, focus rings, keyboard nav |

**Do not** use Instagram trademarks or official glyphs. “Instagram-like” = layout/interaction language only.

Detail UI: [WEB-INSTAGRAM-STYLE-STOREFRONT.md](WEB-INSTAGRAM-STYLE-STOREFRONT.md) · research: [GALLERY-JS-INSPIRATION.md](research/GALLERY-JS-INSPIRATION.md).

---

## 5. Routes (Astro)

```text
/{brandSlug}                         Brand home (hero + featured + store chips)
/{brandSlug}/about                   About from web_profile
/{brandSlug}/contact                 Address list / support / social / lead CTA
/{brandSlug}/products                Portfolio or menu index (all stores or default)
/{brandSlug}/{storeSlug}             Branch: contact block + IG grid menu
/{brandSlug}/{storeSlug}/i/{item}  Item detail + mode-aware CTA
/{brandSlug}/inquire                 Lead form (CARD-36; stub link OK in 38C)
/{brandSlug}/book                    Booking (CARD-36)
/api/...                             Prefer platform Python API; Astro can BFF-proxy if needed
```

Inactive brand/store → 404.

---

## 6. Repo layout (recommended)

```text
apps/storefront/                 # multi-tenant Astro white-label app
  src/pages/[brand]/...
  src/components/ig/             # ProfileHeader, StoryChips, ProductGrid, ProductSheet, AgeGate
  src/lib/api.ts                 # fetch public catalog
  src/lib/commerce.ts            # CTA resolution by mode
  src/styles/global.css          # Tailwind

bot/                             # existing Telegram platform
  services/catalog_public.py     # or bot/web/api — public read
  web/media_proxy.py
```

**Single deploy** of `apps/storefront` serves all brands.  
Env: `PUBLIC_API_BASE`, `WEB_STOREFRONT_ENABLED`, media base URL.

---

## 7. Build sequence (clear and start)

### Phase A — Platform data + API (Python / existing bot repo)

1. Migrations: slug, legal/dbd, commerce_mode, age_*, goods web flags, web_profile JSONB  
2. Public catalog service + HTTP routes  
3. Tests: two brands isolation, portfolio flags, availability  

### Phase B — Media

1. Catalog-only media proxy  
2. DTO image URLs point at proxy  

### Phase C — Astro shell

1. Scaffold `apps/storefront` (Astro + Tailwind + Netlify/Vercel adapter as needed)  
2. AgeGate, ProfileHeader, ProductGrid, ProductSheet  
3. Brand home + branch menu + item from API  
4. About / contact / footer legal+disclaimers  
5. Mode-aware CTAs (no cart in portfolio)  
6. Flag-gated deploy; Telegram suite still green  

### Phase D — Conversion (CARD-36, after C)

1. Lead form → leads table + staff notify  
2. Booking request → bookings table  

---

## 8. CTA matrix (must implement in UI)

| commerce_mode / item | Primary CTA | Secondary |
|----------------------|-------------|-----------|
| full_store + orderable | Order on Telegram (deep link) | Call store |
| portfolio / inquiry_only | Inquire / Lead form | Call · Book meeting |
| hybrid | Per item flags | — |
| age_gate on | Gate first | Then CTAs |

---

## 9. Acceptance criteria (Astro P0)

- [ ] Two brands in DB → two different sites under `/{slug}` same Astro deploy  
- [ ] Branch page shows **DB** address, phone, menu from API  
- [ ] Footer shows legal_name + dbd_number when set  
- [ ] Age gate + disclaimer text from `web_profile.compliance`  
- [ ] Portfolio mode: grid works, no add-to-cart  
- [ ] **Mobile (375px):** 3-col grid, sticky chips, usable sheets/CTAs  
- [ ] **Desktop (1280px+):** usable multi-col grid, hover/focus, no broken layout or unusable thin-only strip by default  
- [ ] Tablet mid-width does not overflow or hide primary CTAs  
- [ ] Menu change in admin visible after cache TTL without redeploy  
- [ ] `WEB_STOREFRONT_ENABLED=false` disables public site safely  

---

## 10. Explicit non-goals for first ship

- Per-brand Markdown product folders as source of truth (CARD-37 path)  
- Full web checkout / PromptPay on web  
- Google Calendar auto-Meet (booking **request** only until CARD-36)  
- Instagram Messaging API  
- Rewriting Telegram handlers into PlatformContext  

---

## 11. Doc map (read in this order)

1. [CLEAR-START.md](../CLEAR-START.md)  
2. This file  
3. [CARD-38](../done/CARD-38-white-label-brand-branch-sites.md)  
4. [BRAND-BRANCH-WEB-CONTENT-MODEL.md](BRAND-BRANCH-WEB-CONTENT-MODEL.md)  
5. [WHITE-LABEL-SITE-MODES-COMPLIANCE-LEADS.md](WHITE-LABEL-SITE-MODES-COMPLIANCE-LEADS.md)  
6. [WEB-INSTAGRAM-STYLE-STOREFRONT.md](WEB-INSTAGRAM-STYLE-STOREFRONT.md)  
7. [research/GALLERY-JS-INSPIRATION.md](research/GALLERY-JS-INSPIRATION.md)  

---

## 12. Ready to code checklist

- [x] North star documented  
- [x] Hybrid content model documented  
- [x] Portfolio + compliance + leads/booking documented  
- [x] Astro + Instagram-like UX locked for **desktop and mobile**  
- [x] Phases A→B→C ordered  
- [ ] Start Phase A implementation (migrations + public API)  
