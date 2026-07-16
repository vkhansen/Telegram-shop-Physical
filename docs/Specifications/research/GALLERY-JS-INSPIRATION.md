# Research: JS Instagram-Style Gallery Solutions & Inspiration

> **Status:** research note (2026-07-16)  
> **Feeds:** [WEB-INSTAGRAM-STYLE-STOREFRONT.md](../WEB-INSTAGRAM-STYLE-STOREFRONT.md), [CARD-35](../../later/CARD-35-instagram-style-web-storefront.md), [FUNNEL-INSTAGRAM-WEB-TELEGRAM.md](../FUNNEL-INSTAGRAM-WEB-TELEGRAM.md)  
> **Stack target:** Astro + Tailwind (+ light React islands)

---

## 1. What “Instagram-style gallery” actually means

There are **three different layout metaphors** people mix up:

| Metaphor | Visual | Best for products |
|----------|--------|-------------------|
| **IG profile grid** | Uniform 1:1 (or 4:5) cells, 3 columns, tight gaps | Catalog SKUs with consistent product photography |
| **Pinterest masonry** | Variable height, packed columns | Lifestyle / mixed AR photos, editorial “storms” |
| **Justified / Flickr** | Rows of equal height, variable width | Photo portfolios (less common for e-com cards) |

**NOVA Sweden Snus** ([novaswedensnus.com](https://novaswedensnus.com/)) is closer to a **brand landing + featured product storm** than a pure Pinterest wall: age gate, bold sections, featured flavor hero, “tap to feature / scroll the storm,” strength badges — not a dense masonry marketplace.

**Recommendation for this funnel:**  
- **Default grid:** IG-like **uniform 3-col product cards** (predictable, mobile-native, matches Reels/feed mental model).  
- **Optional “storm” mode:** masonry or mixed-height **for lifestyle/story images only**.  
- **Detail:** lightbox / bottom sheet with inquire CTA (not cart-first).

---

## 2. Layout libraries (JS / CSS)

| Solution | Type | Size / era | Strengths | Weaknesses | Fit for Astro storefront |
|----------|------|------------|-----------|------------|---------------------------|
| **[Masonry](https://masonry.desandro.com/)** (`masonry-layout`) | JS absolute positioning | Classic, ~200k npm/wk | Battle-tested, imagesLoaded ecosystem | Layout thrash, dated, SSR awkward | Avoid for greenfield |
| **[Isotope](https://isotope.metafizzy.co/)** | JS layout + **filter/sort** | Classic | Filter by flavor/strength = killer feature | Heavier; GPL/commercial for some uses | Only if heavy client filter UX |
| **[Packery](https://packery.metafizzy.co/)** | Bin-packing | Classic | Draggable layouts | Overkill for catalog | No |
| **[Macy.js](http://macyjs.com/)** | Lightweight masonry | ~4kb | Simple, no deps | Less ecosystem | OK for pure masonry section |
| **[MiniMasonry](https://github.com/Spope/MiniMasonry)** | Tiny masonry | Very small | Easy drop-in | Fewer features | Optional |
| **[react-responsive-masonry](https://www.npmjs.com/package/react-responsive-masonry)** | React + flex columns | Lightweight | Easy in React islands | Column reflow quirks | Good for Astro React island |
| **[react-masonry-css](https://www.npmjs.com/package/react-masonry-css)** | React CSS columns pattern | Simple | SSR-friendly pattern | Not true packing | Good enough for many shops |
| **[masonic](https://github.com/jaredLunde/masonic)** | Virtualized React masonry | Performance | 10k+ items, 60fps | Overkill for &lt;100 SKUs | Only huge catalogs |
| **[masonry-grid](https://masonry-grid.js.org/)** (Trigen) | Modern ~1.4kb | 2025 | SSR-friendly, multi-framework | Newer ecosystem | Worth evaluating |
| **CSS multi-column** (`column-count`) | Pure CSS | Native | Zero JS | Order reading, break issues | Acceptable fallback |
| **CSS Grid Lanes / masonry** | Native experimental | 2025–26 drafts | Future-proof | **Not baseline** yet | Progressive enhancement only |

### Takeaway — layout

For **Brand → Store → Menu → Items** with dozens of products:

1. Prefer **CSS Grid 3-column uniform cards** (IG profile) + Tailwind.  
2. Add **filter chips** (category / tags) with plain JS or Alpine/React island — **Isotope only if** complex multi-filter animation is required.  
3. Use **true masonry JS only** for a “lifestyle storm” section, not the whole shop.  
4. Do **not** start with Desandro Masonry unless maintaining legacy.

---

## 3. Lightbox / detail viewers (JS)

| Solution | Type | Strengths | Weaknesses | Fit |
|----------|------|-----------|------------|-----|
| **[PhotoSwipe 5](https://photoswipe.com/)** | Vanilla, mobile-first | Touch gestures, zoom, a11y history, dynamic import | Needs wiring for product meta UI | **Strong default** for Astro |
| **[lightGallery](https://www.lightgalleryjs.com/)** | Feature-rich | Plugins (thumbnails, video, zoom) | Heavier / licensing for some builds | If need video Reels embeds |
| **[GLightbox](https://biati-digital.github.io/glightbox/)** | Lightweight vanilla | Simple API | Fewer advanced gestures | Fine for MVP |
| **[Yet Another React Lightbox](https://yet-another-react-lightbox.com/)** | React | Modern React 18/19, plugins | React-only | Good if detail is React island |
| **[Viewer.js](https://fengyuanchen.github.io/viewerjs/)** | Vanilla | Zoom/rotate | Less “gallery story” UX | Secondary |
| Custom modal + Tailwind | DIY | Full control over **Inquire** form CTA | More code | Best for funnel forms |

### Takeaway — lightbox

- **PhotoSwipe 5** for image swipe/zoom.  
- **Custom product sheet** (Astro/React) on top or instead of pure lightbox: price, badges, strength, **Request / Inquire** (CARD-36) — pure image lightboxes omit conversion.

---

## 4. Common gallery stacks (what production sites actually pair)

| Stack | Pattern | Notes |
|-------|---------|-------|
| **Next.js + react-masonry-css + lightGallery** | [Fullstack Foundations tutorial](https://www.fullstackfoundations.com/blog/nextjs-masonry-image-gallery-lightbox) | Close to our needs; swap Next → Astro |
| **Isotope + PhotoSwipe** | Filter grid + lightbox | Classic photography shops |
| **Macy.js + PhotoSwipe** | WP / builder sites | Simple |
| **masonic + YARL** | Large React catalogs | Overkill for snus/menu SKU counts |
| **Pure CSS grid + dialog** | No layout lib | Fastest LCP; recommended base |

---

## 5. Brand / product-site inspiration (not just libs)

### NOVA Sweden Snus ([novaswedensnus.com](https://novaswedensnus.com/))

| Pattern | Steal for our storefront |
|---------|---------------------------|
| **Age gate** first | Required for nicotine categories; soft-gate other verticals if needed |
| Sectioned “storm” narrative | Homepage as story, not only grid |
| Featured product hero | “Tap to feature” one SKU large |
| Strength as **n/7 badge** | Map to product metadata / modifiers |
| Marquee ticker of attributes | Premium motion, use sparingly |
| FAQ + heritage | Trust layer before form |
| Email capture | Secondary to our **lead form** (LINE/WA preference) |

**Do not copy** as full checkout-first EU snus shop if funnel is **form → private close**.

### Other e-com snus shops (globalsnus, snusdirect, swedishproducts)

- Dense **catalog grids**, filters by brand/strength, classic cart.  
- Inspiration for **filter dimensions** (flavor, strength, format), not for funnel privacy model.

### Instagram product patterns

| IG pattern | Web equivalent |
|------------|----------------|
| Profile 3-col grid | Product grid |
| Story highlights | Category / store chips |
| Post + caption | Item detail + short copy |
| “Link in bio” | Single web hub URL |
| Shopping tags | Inquire / pre-filled form |

---

## 6. UX patterns to adopt (gallery-specific)

1. **Aspect ratio lock** on catalog thumbs (1:1 or 4:5) → fewer layout jumps than true masonry.  
2. **Blur-up / LQIP** placeholders while media proxy loads Telegram images.  
3. **Hover (desktop): darken + “Inquire”**; **tap (mobile): open sheet**.  
4. **Sold out / outside window:** keep tile, grayscale + badge (don’t collapse masonry).  
5. **Filter chips sticky** under header (category = menu section).  
6. **Lightbox footer actions:** Inquire · Share link · (optional) Order request — never raw `t.me` as only button.  
7. **Keyboard:** Esc close, arrows next — PhotoSwipe handles this.  
8. **Reduced motion:** respect `prefers-reduced-motion`.

---

## 7. Recommended stack for *this* project

```text
Astro (SSR/SSG pages)
  + Tailwind (layout, dark premium theme)
  + CSS Grid product grid (3 col mobile-first)     ← primary “IG grid”
  + Optional: react-masonry-css island               ← “storm” lifestyle strip only
  + PhotoSwipe 5 (image zoom) OR custom <dialog>
  + React/Preact island: ProductSheet + Lead/Inquiry forms (CARD-36)
  + Catalog JSON from bot backend (CARD-35 API)
```

| Concern | Choice |
|---------|--------|
| Default product wall | CSS Grid, uniform cells |
| Lifestyle “storm” | Masonry island (macy / react-masonry-css) |
| Zoom | PhotoSwipe 5 |
| Conversion UI | Custom sheet + forms (not lightGallery theme) |
| Filtering | Client chips + server query params first; Isotope only if needed |
| Virtualization | Skip until &gt;200 tiles |

---

## 8. Anti-patterns

| Avoid | Why |
|-------|-----|
| Full-page Desandro Masonry for SKUs | CLS, SSR pain, old stack |
| Lightbox-only product UX | No place for preferred_channel form |
| Infinite masonry of unoptimized Telegram full-res | Kill mobile data / LCP |
| Copying Instagram UI chrome/glyphs | Trademark / trust issues |
| Primary CTA “Join Telegram” on every tile | Violates funnel spec |

---

## 9. Prototype checklist (before full CARD-35 build)

- [ ] 12 fake products, 3 categories, uniform grid in Astro + Tailwind  
- [ ] Sticky category chips + scroll-spy sections  
- [ ] Item open → sheet with Inquire (mock submit)  
- [ ] Optional PhotoSwipe on image only  
- [ ] Compare one page with masonry-only variant (A/B feel)  
- [ ] Age-gate stub if product requires it  
- [ ] Lighthouse mobile: LCP image from media proxy path  

---

## 10. Links (quick index)

**Layout**

- https://masonry.desandro.com/  
- https://isotope.metafizzy.co/  
- http://macyjs.com/  
- https://github.com/jaredLunde/masonic  
- https://masonry-grid.js.org/  
- https://www.smashingmagazine.com/2025/12/masonry-things-you-wont-need-library-anymore/  

**Lightbox**

- https://photoswipe.com/  
- https://www.lightgalleryjs.com/  
- https://yet-another-react-lightbox.com/  

**Tutorials / stacks**

- https://www.fullstackfoundations.com/blog/nextjs-masonry-image-gallery-lightbox  
- https://piccalil.li/blog/a-simple-masonry-like-composable-layout/  

**Brand reference**

- https://novaswedensnus.com/  

---

## 11. Decision log (proposal)

| Decision | Proposal | Rationale |
|----------|----------|-----------|
| Primary grid | Uniform IG-style CSS Grid | Matches mobile IG; simpler than masonry for commerce |
| Masonry | Secondary “storm” section only | NOVA-like editorial, not whole shop |
| Lightbox | PhotoSwipe 5 + custom product actions | Mobile gestures + funnel CTAs |
| Filters | Chips + URL params first | Avoid Isotope weight |
| Forms | Outside pure gallery libs | CARD-36 funnel |
| Age gate | Spec as optional brand flag | Required for nicotine verticals |

Review this before implementing CARD-35 gallery components.
