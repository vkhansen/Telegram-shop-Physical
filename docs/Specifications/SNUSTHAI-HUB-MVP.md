# SnusThai Hub — Product & Technical MVP Spec

> **Project name:** SnusThai Hub (Premium Snus & Smokeless Products – Thailand)  
> **Version:** 1.0 MVP  
> **Spec status:** `draft`  
> **Date:** 2026-07-16  
> **Implementation card:** [CARD-37](../later/CARD-37-snusthai-hub-astro-mvp.md)  
> **Related:** [FUNNEL-INSTAGRAM-WEB-TELEGRAM.md](FUNNEL-INSTAGRAM-WEB-TELEGRAM.md) · [WEB-INSTAGRAM-STYLE-STOREFRONT.md](WEB-INSTAGRAM-STYLE-STOREFRONT.md) · [research/GALLERY-JS-INSPIRATION.md](research/GALLERY-JS-INSPIRATION.md) · [CARD-35](../done/CARD-35-instagram-style-web-storefront.md) · [CARD-36](../later/CARD-36-instagram-web-telegram-funnel.md)

---

## 1. Primary goal

Build a **fast, visually stunning, Instagram-style product website** with:

- Product gallery  
- Lead generation  
- Educational blog  
- SEO optimization  
- Multi-channel social integration  

**Market focus:** Snus / smokeless product **advertising and lead capture** in Thailand (and SE Asia as secondary).  
**Constraints:** Compliant presentation, lightweight, easy to maintain.  
**Funnel posture:** Instagram/social → **this site** → lead form → staff / private channels (LINE, WhatsApp, optional Telegram backend). **No** primary “join Telegram” spam.

Operators must ensure **local legality** of advertising, age gates, and distribution. This spec is technical/product only — not legal advice.

---

## 2. Relationship to Telegram bot monorepo

| System | Role |
|--------|------|
| **SnusThai Hub (Astro)** | Public brand site: gallery, blog, SEO, leads, social links |
| **Telegram-shop-Physical bot** | Optional private fulfillment engine (orders, payments, kitchen) after lead opt-in |
| **Bridge (CARD-36)** | Form → `leads` + staff notify; later catalog API (CARD-35) |

### MVP data strategy (two modes)

| Mode | Products source | When |
|------|-----------------|------|
| **A — Content-first (ship first)** | Markdown/MDX or JSON in Astro repo | Fast MVP, no bot deploy required |
| **B — Backend-synced** | Public catalog API from bot (`Brand → Store → Menu → Items`) | When CARD-35 API exists |

MVP **1.0 ships Mode A**; Mode B is a flag-ready upgrade path (same UI components).

---

## 3. Core features (MVP 1.0)

### 3.1 Instagram-style product gallery

| Requirement | Detail |
|-------------|--------|
| Layout | **Primary:** uniform 3-col IG-style CSS Grid. **Optional:** masonry “storm” strip for lifestyle images ([research note](research/GALLERY-JS-INSPIRATION.md)) |
| Interactions | Hover (desktop), tap sheet (mobile), lightbox zoom (PhotoSwipe 5) |
| Filters | Flavor, strength, type (chips + URL query params) |
| Media | Optimized images (Astro assets / `<Image />`); high-res in lightbox |
| Card content | Image, name, strength badge, short tagline, sold-out/state |
| CTA on card/sheet | **Inquire / Request info** → lead form pre-filled (not forced cart) |

### 3.2 Hero landing page

- Eye-catching visual (product storm / lifestyle)  
- Benefit-focused headline (EN + optional TH)  
- Clear CTAs: **Browse products** · **Request catalog** · social row  
- Trust strip: discreet delivery framing, adult-only, brand signals  
- **Age gate** before main content (session/localStorage acknowledgement)

### 3.3 Lead form (compliant)

| Field | Required | Notes |
|-------|----------|-------|
| Age confirmation | yes | “I am of legal age in my country” |
| Name | yes | |
| Phone and/or email | yes (at least one) | Thai phone validation preferred |
| Preferred channel | yes | `line` \| `whatsapp` \| `email` \| `telegram` \| `phone` |
| Interest type | yes | `retail` \| `wholesale` \| `distribution` \| `other` |
| Product interest | no | free text or multi-select from catalog tags |
| Message | no | |
| Consent contact + privacy | yes | |
| UTM / ref | auto | hidden |

**Submit pipeline (MVP):**

1. Astro server endpoint **or** Formspree →  
2. **Resend** transactional “we received your request”  
3. Optional: webhook to bot bridge (CARD-36) for staff Telegram alert  
4. Optional: Resend Audience / list subscribe if user opts into newsletter  

### 3.4 Multi-channel social links

Prominent, accessible icon row (footer + hero optional):

| Channel | Behavior |
|---------|----------|
| Instagram | Profile URL |
| LINE Official | LINE URL / QR page |
| WhatsApp | `https://wa.me/{E164}?text=...` click-to-chat |
| Facebook | Page URL |
| Pixelfed / other | Optional |
| Telegram | **Secondary only** — labeled private support, not primary CTA |

Config via env or `src/data/site.ts` — no hardcode secrets.

### 3.5 Blog section

- MDX/Markdown under `src/content/blog/`  
- Categories (e.g. lifestyle, guides, compliance education)  
- SEO: title, description, OG image, canonical  
- Example topics (editorial — must stay accurate/compliant): heat/lifestyle practicality, usage guides, **compliance disclaimers**, product education  
- Index + post template; simple client search optional (Pagefind or filter list)  
- **Bilingual:** EN primary; Thai title/summary fields optional per post (`title_th`, `summary_th`)

### 3.6 SEO & performance

| Item | Implementation |
|------|----------------|
| Sitemap | `@astrojs/sitemap` |
| Meta / OG | Layout defaults + per-page frontmatter |
| Images | Astro image optimization, width/srcset |
| Structured data | `Organization`, `WebSite`, `Article` (blog), `Product` (where appropriate) |
| Core Web Vitals | Static-first; islands only for gallery/form |
| robots | Allow public pages; noindex thanks/private if any |
| hreflang | Optional `en` / `th` when dual pages exist |

### 3.7 Mail list & emails

| Use | Tool |
|-----|------|
| Transactional (form receipt) | **Resend** |
| Newsletter / audience | Resend Audiences **or** Listmonk (later) |
| Double opt-in | Preferred for marketing list |

### 3.8 Compliance (built-in)

- Age gate on entry  
- Persistent footer disclaimers (nicotine addictiveness, adult-only, no sales to minors)  
- Privacy policy page  
- No underage creative; no medical cure claims  
- Where direct e-com is restricted: site is **lead / education / brand** — order close off-site or via private channel  
- Config flag `SHOW_DIRECT_PRICES` default per operator policy  

---

## 4. Tech stack (Astro-centric)

| Layer | Choice |
|-------|--------|
| Framework | **Astro 5+** (static-first, islands) |
| Styling | **Tailwind CSS** |
| Content | **Markdown/MDX** products + blog (`src/content/`) |
| Interactivity | React or Preact islands: gallery filters, lightbox, form |
| Forms | Astro server endpoints **or** Formspree → Resend |
| Email | Resend |
| Hosting | Netlify / Vercel (Git deploys) or VPS |
| CI | GitHub Actions build + deploy |
| Optional bridge | Same monorepo `bot/` API or external webhook to Telegram staff |

### Suggested repo layout

```text
snusthai-hub/                    # or apps/snusthai-hub inside monorepo
  src/
    pages/
      index.astro
      products/index.astro
      products/[slug].astro
      blog/index.astro
      blog/[...slug].astro
      privacy.astro
      thanks.astro
      api/lead.ts                # server endpoint
    components/
      AgeGate.tsx
      Hero.astro
      ProductGrid.tsx            # island
      ProductSheet.tsx
      LeadForm.tsx
      SocialLinks.astro
      SiteFooter.astro
    content/
      products/*.md
      blog/*.mdx
    data/site.ts                 # social URLs, brand copy
    layouts/BaseLayout.astro
  public/
  astro.config.mjs
  tailwind.config.*
```

### Bootstrap (reference)

```bash
npm create astro@latest snusthai-hub
cd snusthai-hub
npx astro add tailwind
npx astro add sitemap
# optional islands
npx astro add react   # or preact
npm install photoswipe resend
```

---

## 5. Information architecture

```text
/                     Hero + featured products + CTA + social
/products             Gallery + filters
/products/[slug]      Product detail + inquire CTA
/blog                 Article index
/blog/[slug]          Article
/request              Lead form (or modal only)
/privacy
/thanks
/api/lead             POST lead (server)
```

UTM preserved: `?utm_source=instagram&utm_medium=bio|story|reel`

---

## 6. Content model (Mode A)

### Product MD frontmatter (example)

```yaml
title: "Berries Storm"
slug: berries-storm
flavor: berries
strength: 4          # 1–7 scale display
type: pouch          # pouch | portion | other
tags: [ice, limited]
summary: "..."
summary_th: "..."
image: ./berries.jpg
gallery: []
featured: true
available: true
interest_default: retail
```

### Blog frontmatter

```yaml
title: "..."
title_th: "..."
description: "..."
pubDate: 2026-07-01
category: guides
draft: false
heroImage: ./hero.jpg
```

---

## 7. Design direction

| Token | Guidance |
|-------|----------|
| Mood | Premium, dark-capable, bold accents (NOVA-adjacent, not a clone) |
| Gallery | IG 3-col; optional masonry lifestyle strip |
| Type | Clean sans; bilingual friendly |
| Motion | Subtle hover; respect `prefers-reduced-motion` |
| Mobile | Primary; max content width ~480–720px for “app-like” feel on desktop center |

See [GALLERY-JS-INSPIRATION.md](research/GALLERY-JS-INSPIRATION.md) for library choices.

---

## 8. Implementation pipeline

### Phase 0 — Setup (0.5 d)

1. `npm create astro@latest snusthai-hub`  
2. Tailwind + sitemap + React/Preact  
3. Base layout, fonts, env template  
4. Deploy empty site to Vercel/Netlify  

### Phase 1 — Shell & compliance (1 d)

1. Age gate  
2. Hero + footer disclaimers + privacy  
3. Social links config  
4. i18n strings EN + key TH chrome  

### Phase 2 — Gallery (1.5–2 d)

1. Product content collection  
2. Grid + filters  
3. Product page + sheet  
4. PhotoSwipe on images  
5. Inquire deep-link to form with `?product=`  

### Phase 3 — Lead & mail (1 d)

1. Lead form + validation  
2. `/api/lead` + Resend receipt  
3. Optional staff webhook (Telegram / email)  
4. Thanks page  

### Phase 4 — Blog & SEO (1 d)

1. MDX blog collection  
2. Index + post templates  
3. OG tags, JSON-LD, sitemap verify  

### Phase 5 — Polish & funnel (0.5–1 d)

1. UTM capture  
2. Lighthouse pass  
3. IG bio link checklist  
4. Optional CARD-36 bridge  

**MVP effort band:** ~5–8 days for a polished 1.0.

---

## 9. Env / config

```bash
PUBLIC_SITE_URL=https://snusthai.example.com
PUBLIC_IG_URL=
PUBLIC_LINE_URL=
PUBLIC_WA_E164=66xxxxxxxxx
PUBLIC_FB_URL=
PUBLIC_TELEGRAM_URL=          # optional, secondary
RESEND_API_KEY=
RESEND_FROM=noreply@...
LEAD_NOTIFY_EMAIL=
LEAD_WEBHOOK_URL=             # optional bot/bridge
AGE_GATE_ENABLED=true
```

---

## 10. Acceptance criteria (MVP 1.0)

- [ ] Age gate before main browse  
- [ ] Hero loads with CTA to gallery + request  
- [ ] Gallery filters by flavor / strength / type  
- [ ] Product detail + lightbox  
- [ ] Lead form requires age + consent; at least phone or email  
- [ ] Preferred channel includes LINE and WhatsApp  
- [ ] Resend (or configured mail) confirmation on submit  
- [ ] Social icons: IG, LINE, WA minimum  
- [ ] ≥2 blog posts published via MDX  
- [ ] Sitemap + basic meta on all public pages  
- [ ] Mobile Lighthouse performance acceptable (target Performance ≥ 90 on static pages)  
- [ ] No mandatory Telegram join as primary CTA  
- [ ] Privacy + nicotine/adult disclaimers visible  

---

## 11. Out of scope (MVP 1.0)

- Full e-commerce cart/checkout/card payments on site  
- User accounts  
- Instagram Graph API auto-post  
- Live Telegram catalog sync (Mode B — post-MVP)  
- Multi-brand marketplace directory  
- CMS admin UI (Git-based content is enough)

---

## 12. Success metrics

| Metric | Target (directional) |
|--------|----------------------|
| IG/social → site CTR | Track UTMs |
| Form conversion | form views → submits |
| Channel mix | % LINE vs WA vs email |
| Blog SEO | Indexed posts, organic landing |
| Core Web Vitals | Pass mobile |

---

## 13. Decision log

| Decision | Choice |
|----------|--------|
| Framework | Astro 5 + Tailwind |
| Gallery default | CSS Grid IG-style; masonry optional |
| Lightbox | PhotoSwipe 5 |
| Content v1 | MD/MDX in repo (Mode A) |
| Forms | Server endpoint + Resend |
| Funnel | Lead capture, not direct Telegram spam |
| Bot integration | Optional webhook; full bridge CARD-36 |
