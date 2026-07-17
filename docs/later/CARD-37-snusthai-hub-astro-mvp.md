# Card 37: SnusThai Hub — Astro MVP Site

## Implementation Status

> **0% Complete** | `░░░░░░░░░░░░░░░░░░░` | Product MVP spec drafted — scaffold not started.

**Tier:** T2-Web product skin (public brand site)  
**Phase:** M3 — Multi-Platform Growth  
**Priority:** **P3 — Parked** (vertical demo / theme only; **not** the white-label platform path — see [CLEAR-START.md](../CLEAR-START.md) + [CARD-38](../done/CARD-38-white-label-brand-branch-sites.md))  
**Effort:** Medium–High (5–8 days for polished MVP)  
**Spec:** [`docs/Specifications/SNUSTHAI-HUB-MVP.md`](../Specifications/SNUSTHAI-HUB-MVP.md)  
**Dependencies:**  
- Gallery decisions: [GALLERY-JS-INSPIRATION.md](../Specifications/research/GALLERY-JS-INSPIRATION.md)  
- Funnel posture: [FUNNEL-INSTAGRAM-WEB-TELEGRAM.md](../Specifications/FUNNEL-INSTAGRAM-WEB-TELEGRAM.md)  
- Soft: [CARD-36](CARD-36-instagram-web-telegram-funnel.md) for Telegram staff webhook  
- Soft: [CARD-35](../done/CARD-35-instagram-style-web-storefront.md) Mode B catalog API later  

---

## Why

CARD-35/36 define **platform-agnostic** web storefront + funnel. **SnusThai Hub** is the **named MVP product**: Astro + Tailwind site optimized for Thailand snus/smokeless **advertising and lead capture**, Instagram-style gallery, blog, SEO, social (LINE/WA first).

Telegram bot remains optional **backend engine** after lead capture — not the public front door.

---

## MVP scope (from product brief)

| Feature | In 1.0 |
|---------|--------|
| IG-style product gallery + filters + lightbox | yes |
| Hero landing + CTAs | yes |
| Age gate + disclaimers + privacy | yes |
| Lead form (retail/wholesale/distribution) | yes |
| Resend transactional email | yes |
| Social: IG, LINE, WhatsApp (+ FB optional) | yes |
| Blog MDX + SEO sitemap/meta | yes |
| EN + Thai chrome / optional TH fields | yes |
| Catalog from Markdown/JSON | yes (Mode A) |
| Live bot catalog API | no (Mode B later) |
| On-site checkout/cart | no |

---

## Tech

```bash
npm create astro@latest snusthai-hub
# Tailwind, sitemap, React/Preact islands
# photoswipe, resend
# Host: Vercel or Netlify
```

Prefer monorepo path `apps/snusthai-hub` **or** sibling repo; document choice in PR.

---

## Pipeline (implementation order)

1. **Setup** — Astro 5 + Tailwind + deploy pipeline  
2. **Shell** — layout, age gate, social, privacy, disclaimers  
3. **Gallery** — content collection, grid, filters, sheet, PhotoSwipe  
4. **Lead** — form, `/api/lead`, Resend, thanks  
5. **Blog** — MDX collection + SEO  
6. **Polish** — UTMs, Lighthouse, optional CARD-36 webhook  

---

## Exit criteria

Match [SNUSTHAI-HUB-MVP.md §10](../Specifications/SNUSTHAI-HUB-MVP.md) acceptance checklist, including:

- [ ] No mandatory Telegram primary CTA  
- [ ] LINE + WhatsApp in preferred channel / social  
- [ ] Age gate + nicotine/adult disclaimers  
- [ ] Gallery filters work  
- [ ] Lead email fires via Resend (or documented stub in dev)  
- [ ] ≥2 blog posts  
- [ ] Production deploy URL documented  

---

## Effort

| Phase | Days |
|-------|------|
| Setup + shell + compliance | 1–1.5 |
| Gallery | 1.5–2 |
| Lead + Resend | 1 |
| Blog + SEO | 1 |
| Polish + deploy | 0.5–1.5 |
| **Total** | **5–8** |

---

## Related

| Doc | Role |
|-----|------|
| [SNUSTHAI-HUB-MVP.md](../Specifications/SNUSTHAI-HUB-MVP.md) | Full product/tech MVP |
| [CARD-35](../done/CARD-35-instagram-style-web-storefront.md) | Generic multi-brand web catalog |
| [CARD-36](CARD-36-instagram-web-telegram-funnel.md) | Lead bridge to bot |
| [FUNNEL-INSTAGRAM-WEB-TELEGRAM.md](../Specifications/FUNNEL-INSTAGRAM-WEB-TELEGRAM.md) | Funnel architecture |
