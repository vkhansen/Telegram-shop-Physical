# Card 35: Instagram-Style Auto-Generated Web Storefront

## Implementation Status

> **✅ SUPERSEDED / CLOSED** | Implemented under **CARD-38 Phase C** (multi-tenant Astro shell). Spec retained for gallery UX patterns. Moved to `docs/done/` 2026-07-17.

**Tier:** T2-Web — Public catalog surface (parallel to Instagram messaging)  
**Phase:** M3 — Multi-Platform Growth  
**Priority:** Closed — **implement under [CARD-38](CARD-38-white-label-brand-branch-sites.md)** multi-tenant shell (not a single-brand site)  
**Effort:** Medium–High (4–7 days for P1)  
**Dependencies:**  
- Spec: [`docs/Specifications/WEB-INSTAGRAM-STYLE-STOREFRONT.md`](../Specifications/WEB-INSTAGRAM-STYLE-STOREFRONT.md)  
- [CARD-34](../done/CARD-34-conversation-workflow-specifications.md) flow **W-01** (accept web browse handoff)  
- Brand / Store / Menu data model (shipped); multi-brand [CARD-19](CARD-19-multi-brand-bot-coordination.md)  
- Prefer media proxy alignment with future MediaRef (CARD-29 related)  
**Soft dependency:** [CARD-32](CARD-32-customer-application-services.md) only for later in-web checkout  
**Does not require:** CARD-33 Instagram Messaging to ship  

**Plan:** [`CLEAR-START.md`](../CLEAR-START.md) · [`MULTI-CHANNEL-TIERED-PLAN.md`](../later/MULTI-CHANNEL-TIERED-PLAN.md)  
**Parent epic:** [CARD-38](CARD-38-white-label-brand-branch-sites.md)  
**Gallery JS research:** [`docs/Specifications/research/GALLERY-JS-INSPIRATION.md`](../Specifications/research/GALLERY-JS-INSPIRATION.md)

---

## Why

Telegram is the **main application** for ordering and ops. Customers and marketers still need a **linkable, mobile web menu** that looks like a modern visual storefront (Instagram-style grid/profile) for:

- Bio links, QR codes on tables, Google/Maps links  
- Sharing a store or dish URL  
- Browsing without installing Telegram first  

The site must be **auto-generated** from the Telegram backend hierarchy:

```text
Brand → Store → Menu (categories) → Items
```

No separate CMS: Telegram admin (or DB) remains the content source.

---

## Spec authority

All UX, IA, API, availability, and acceptance rules live in:

**[WEB-INSTAGRAM-STYLE-STOREFRONT.md](../Specifications/WEB-INSTAGRAM-STYLE-STOREFRONT.md)**

This card is the implementation vehicle for **Phase P1** of that spec.

---

## Scope (P1)

### In

1. **Public read API** — brands / stores / menu / item JSON (availability filtered).  
2. **Media proxy** — Telegram `file_id` → cached public image URL (catalog only).  
3. **Mobile web UI** — Brand profile, store menu grid, item detail (S1–S3).  
4. **Telegram order CTA** — deep link with brand/store/(item) start payload.  
5. **Flag** — `WEB_STOREFRONT_ENABLED` default false.  
6. **Store slug** — add/backfill `stores.slug` if missing.  
7. **Start-param handling** (minimal) in Telegram bot to honor `web_{brand}_{store}_{item?}`.

### Out (P1)

- In-web cart/checkout/PromptPay  
- Web admin  
- Pixel-perfect Instagram clone / brand impersonation  
- Full SSG multi-region CDN (optional later)  
- User accounts  

---

## Hierarchy & routes

| Level | Route |
|-------|--------|
| Brand | `/{brandSlug}` |
| Store + menu | `/{brandSlug}/{storeSlug}` |
| Item | `/{brandSlug}/{storeSlug}/i/{itemSlug}` |

Data sources: `brands`, `stores`, `categories`, `goods`, `bot_configs`, branch inventory when present.

---

## Instagram-style UX (summary)

- Responsive: mobile 3-col grid; desktop wider multi-col (max ~960–1200px)  
- Profile header (logo, name, bio)  
- Horizontal **store** chips  
- Category pills + **3-column item grid**  
- Item detail with media carousel + Order CTA  
- Full detail in the specification doc §4–5, §10  

---

## Implementation sketch

```text
bot/services/catalog_public.py   # shared catalog queries
bot/web/ or apps/storefront/
  api/v1/...
  media_proxy.py
  app shell (SSR preferred for SEO of menu links)
```

Reuse availability logic from menu/goods helpers — do not fork rules.

---

## Tests

- API: active vs inactive brand/store; category time window; sold_out badge  
- Media proxy: valid catalog file_id; reject random file_id  
- UI smoke: 375px layout renders brand → item  
- Flag off: no public menu  
- Deep link format unit test  

---

## Exit criteria (P1)

- [ ] Spec §14 acceptance criteria checked  
- [ ] Auto-update: admin adds item in Telegram → appears on web within cache TTL without redeploy  
- [ ] Order CTA opens Telegram with brand/store context  
- [ ] Suite green; feature flag default off  

---

## Effort

| Task | Days |
|------|------|
| Store slug migration + catalog_public service | 0.5–1 |
| Read API + availability | 1 |
| Media proxy + cache | 1 |
| S1–S3 UI | 1.5–2.5 |
| Telegram start payload | 0.5 |
| Tests + flag/docs | 0.5–1 |
| **Total P1** | **4–7** |

---

## Related

| Doc | Role |
|-----|------|
| [WEB-INSTAGRAM-STYLE-STOREFRONT.md](../Specifications/WEB-INSTAGRAM-STYLE-STOREFRONT.md) | Full specification |
| [MENU-SYSTEM.md](../Specifications/MENU-SYSTEM.md) | Menu rules |
| [CARD-34](../done/CARD-34-conversation-workflow-specifications.md) | W-01 web flows |
| [CARD-33](../later/CARD-33-instagram-messaging-channel.md) | IG DMs (parallel channel) |
| [CARD-32](CARD-32-customer-application-services.md) | Future web checkout |
