# Clear Start — White-Label Brand Sites (Astro)

> **Open this file first in any new session.**  
> **Status board:** [`FEATURE_CARDS.md`](FEATURE_CARDS.md) · **Epic:** [`CARD-38`](later/CARD-38-white-label-brand-branch-sites.md)  
> **Build contract:** [`Specifications/WHITE-LABEL-ASTRO-IMPLEMENTATION.md`](Specifications/WHITE-LABEL-ASTRO-IMPLEMENTATION.md)  
> **Last updated:** 2026-07-16

---

## 1. Context (one minute)

| | |
|--|--|
| **What we have** | Multi-brand **Telegram** shop platform: Brand → Store → Menu/Goods → Inventory → Orders/Payments; kitchen, riders, multi-bot (CARD-19). M0–M2 done. |
| **What we’re building** | **White-label auto websites** for every brand + every branch from that DB — any vertical (food, physical goods, portfolio-only restricted catalogs). |
| **How sites look** | **Astro + Tailwind**, **Instagram-like** experience that works on **desktop and mobile** (responsive profile grid, chips, sheets/lightbox, age gate). |
| **How sites get data** | Public catalog API + media proxy + hybrid content (columns + tables + `web_profile` JSON). **Not** hand-written Markdown products per brand. |
| **What Telegram stays** | Primary **ops + order engine** (and full_store checkout). Web is projection + leads/booking. |

**North star:**

> One platform · N brands · each brand gets bot + web · each branch gets a page · menu/inventory/about/contact/disclaimers from DB · one Astro deploy serves all tenants.

---

## 2. Documented decisions (do not re-litigate)

| Topic | Decision | Spec |
|-------|----------|------|
| Storage | Hybrid: columns for address/phone/DBD; tables for catalog; JSON for about/FAQ/disclaimers/theme | [BRAND-BRANCH-WEB-CONTENT-MODEL](Specifications/BRAND-BRANCH-WEB-CONTENT-MODEL.md) |
| Commerce | `full_store` \| `portfolio` \| `hybrid` (call/book to order OK) | [WHITE-LABEL-SITE-MODES…](Specifications/WHITE-LABEL-SITE-MODES-COMPLIANCE-LEADS.md) |
| Compliance | Age gate + disclaimer text per brand in DB | same |
| Leads + booking | Lead form + in-person / Google Meet **request** (CARD-36) | same + CARD-36 |
| Frontend | **Astro**, multi-tenant, IG-like mobile | [WHITE-LABEL-ASTRO-IMPLEMENTATION](Specifications/WHITE-LABEL-ASTRO-IMPLEMENTATION.md) |
| Gallery | CSS Grid 3-col primary; PhotoSwipe/sheet; research done | [GALLERY-JS-INSPIRATION](Specifications/research/GALLERY-JS-INSPIRATION.md) |
| Not next | SnusThai as architecture, IG DM first, handler rewrite | P3 / P2 |

---

## 3. Done vs open

### Done (leave alone)

M0 launch gate · M1 hardening · M2 dispatch · CARD-19 multi-brand · CARD-28 store assets · full restaurant/payment/i18n suite.  
Index: [`FEATURE_CARDS.md`](FEATURE_CARDS.md) DONE table · files in `docs/done/`.

### Open priority

```text
P0  CARD-38  White-label sites
      A  DB fields + public API
      B  Media proxy
      C  Astro multi-tenant IG-like shell
P1  CARD-29 → 30 → 31 → 32   Messenger, identities, caps, services
P2  CARD-36 leads+booking · 34 specs · 33 IG · 16 LINE
P3  CARD-37 vertical demo only
```

---

## 4. Architecture (runtime)

```text
                    PostgreSQL (source of truth)
         Brand · Store · Goods · Inventory · web_profile · BotConfig
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
     Public Catalog API                 Telegram BotPool
     + Media proxy                      (admin, order, kitchen)
              │
              ▼
     apps/storefront (Astro)
     /{brand}  /{brand}/{store}  /{brand}/about  …
     Instagram-like UI (desktop + mobile)
              │
              ▼  (later CARD-36)
     Lead form · Book meeting → staff notify
```

---

## 5. Responsive UX bar (desktop + mobile)

Must-have for Phase C — **both** viewports:

| | Mobile | Desktop |
|--|--------|---------|
| Grid | 3-col IG-style | 3–5 col, wider max-width (~960–1200px) |
| Item | Sheet / full page | Modal or page + keyboard/hover |
| Header / chips | Stack + horizontal scroll | Wider hero; chips wrap or scroll |
| CTAs | Full-width touch targets | Inline + hover/focus |
| Legal | Age gate + footer DBD/disclaimers from DB | Same |

- Responsive Tailwind breakpoints (not mobile-only)  
- Profile header, store/category chips, mode-aware CTAs  
- Fast loads (lazy images via media proxy)

---

## 6. Clear-and-start engineering order

### Done → CARD-38 A + B + C ✅ (2026-07-16)

| Phase | Deliverable |
|-------|-------------|
| A | Schema, `catalog_public`, `/api/public/*` |
| B | `media_proxy`, `/media/{token}`, catalog allowlist |
| C | `apps/storefront` Astro IG-like UI (desktop + mobile) |

### Run locally

```bash
# API (with bot monitoring server)
# PUBLIC catalog on MONITORING_PORT (default 9090)

cd apps/storefront
cp .env.example .env   # PUBLIC_API_BASE=http://127.0.0.1:9090
npm install && npm run dev   # http://127.0.0.1:4321
```

### Auth + tickets (CARD-39)

- Spec: [WHITE-LABEL-OAUTH-TICKETS.md](Specifications/WHITE-LABEL-OAUTH-TICKETS.md)  
- Login: `/{brand}/login` · Account · **Tickets** (list / new / thread)  
- Dev: `OAUTH_DEV_LOGIN=true` · Google: `OAUTH_GOOGLE_CLIENT_ID/SECRET` + redirect URI  
- API: `/api/public/auth/*`, `/api/public/tickets*` with session cookie  

### Next product work

1. Finish Google OAuth deploy config; optional brand-scoped tickets  
2. **CARD-36** — wire lead + booking forms to DB + staff notify  
3. **CARD-29** — Messenger port for staff alerts

**Do not start with:** CARD-37 Markdown demo · IG Messaging · full web checkout.

---

## 7. Session checklist

- [ ] Read this file  
- [ ] CARD-38 A+B+C done — run storefront against live API  
- [ ] Next: CARD-36 lead/booking wire-up  
- [ ] Keep Telegram tests green  

---

## 8. Full doc index

| Doc | Role |
|-----|------|
| **This file** | Session bootstrap |
| [WHITE-LABEL-ASTRO-IMPLEMENTATION.md](Specifications/WHITE-LABEL-ASTRO-IMPLEMENTATION.md) | **Astro build contract** |
| [CARD-38](later/CARD-38-white-label-brand-branch-sites.md) | Epic phases A–C |
| [BRAND-BRANCH-WEB-CONTENT-MODEL.md](Specifications/BRAND-BRANCH-WEB-CONTENT-MODEL.md) | Hybrid data model |
| [WHITE-LABEL-SITE-MODES-COMPLIANCE-LEADS.md](Specifications/WHITE-LABEL-SITE-MODES-COMPLIANCE-LEADS.md) | Portfolio, disclaimers, leads, booking |
| [WEB-INSTAGRAM-STYLE-STOREFRONT.md](Specifications/WEB-INSTAGRAM-STYLE-STOREFRONT.md) | Routes/UI detail |
| [GALLERY-JS-INSPIRATION.md](Specifications/research/GALLERY-JS-INSPIRATION.md) | Gallery libraries |
| [FEATURE_CARDS.md](FEATURE_CARDS.md) | Board |
| [MASTER-PLAN.md](MASTER-PLAN.md) | Milestones |
| [FUNNEL-…](Specifications/FUNNEL-INSTAGRAM-WEB-TELEGRAM.md) | Funnel narrative |
| Claude.md / CLAUDE.md | Commands, bug class rule |

---

## 9. Ready statement

**Documentation is complete for a clean start.**

Next concrete work: **implement CARD-38 Phase A** (schema + public catalog API), then media proxy, then **Astro multi-tenant Instagram-like storefront** in `apps/storefront`.

When starting code, say: *“Implement CARD-38 Phase A”* or *“Scaffold apps/storefront after API.”*
