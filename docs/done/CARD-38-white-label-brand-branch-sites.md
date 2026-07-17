# Card 38: White-Label Brand & Branch Auto-Sites

## Implementation Status

> **✅ DONE (A+B+C)** | `████████████████████` | **Phases A+B+C shipped 2026-07-16** (API, media proxy, Astro storefront). Leads/booking remain CARD-36; OAuth/tickets CARD-39. Moved to `docs/done/` 2026-07-17.

**Priority:** Closed spine  
**Milestone:** M3 — White-label public surfaces  
**Effort:** High (phased A–C shipped)  
**Dependencies:** CARD-19 multi-brand runtime ✅ · CARD-28 store assets ✅ · domain models Brand/Store/Goods/BranchInventory ✅  
**Supersedes for sequencing:** CARD-35 as standalone “one storefront”; CARD-37 as platform path  
**Clear-start:** [`docs/CLEAR-START.md`](../CLEAR-START.md)  
**Astro build contract:** [`docs/Specifications/WHITE-LABEL-ASTRO-IMPLEMENTATION.md`](../Specifications/WHITE-LABEL-ASTRO-IMPLEMENTATION.md)  
**Backend law:** Web is an **adapter** on the same services as bots — [`UNIFIED-BACKEND-CHANNEL-INTERFACE.md`](../Specifications/UNIFIED-BACKEND-CHANNEL-INTERFACE.md)

---

## Why

Every **Brand** needs its own public presence; every **Store/branch** needs its own page with branch info and **that branch’s** menu/inventory. Vertical (food vs physical goods) is a **theme**, not a separate product.

The DB and Telegram multi-bot runtime already tenancy-isolate brands. This card adds the **auto-generated web (and shared read API)** layer so operators do not hand-build one site per brand.

---

## Web content model (critical)

**Do not store Address, Phone, DBD, menu, or inventory only inside one JSON blob.**

Full policy: [`docs/Specifications/BRAND-BRANCH-WEB-CONTENT-MODEL.md`](../Specifications/BRAND-BRANCH-WEB-CONTENT-MODEL.md)

| Data | Storage |
|------|---------|
| Address, phone, geo | **Store columns** (already exist) |
| DBD number, legal name, support email/phone | **Brand columns** (explicit) |
| Menu / products / stock | **Relational** categories/goods/branch_inventory |
| About us, FAQ, hero, social map, theme, SEO extras | **`web_profile` JSONB** on brand (and optional store override) |
| Age gate, disclaimer text, footer warnings | Brand flags + **`web_profile.compliance`** (tenant-owned legal prose) |
| Portfolio vs full store vs hybrid | Brand **`commerce_mode`** + item `inquiry_only` / `web_orderable` |
| Lead form + meeting booking | Modules; tables in CARD-36 / bookings (see below) |

Public pages **merge** first-class fields + `web_profile` + catalog queries.  

**Full modes/compliance/leads/bookings:** [`WHITE-LABEL-SITE-MODES-COMPLIANCE-LEADS.md`](../Specifications/WHITE-LABEL-SITE-MODES-COMPLIANCE-LEADS.md)

---

## Scope by phase

### Phase A — Public Catalog API + identity fields — **DONE 2026-07-16**

- [x] `stores.slug` (unique per brand) + backfill from name (migration `d4a8f1c2e9b0`)  
- [x] Brand legal/contact: `legal_name`, `dbd_number`, `support_email`, `support_phone`  
- [x] Brand `commerce_mode`, `age_gate_enabled`, `min_age`  
- [x] Goods flags: `web_listable`, `web_orderable`, `inquiry_only`  
- [x] `brands.web_profile` + `stores.web_profile` JSON  
- [x] Pydantic validation helpers (`bot/services/web_profile.py`)  
- [x] Read service `bot/services/catalog_public.py` + HTTP `bot/web/public_api.py` on monitoring server:
  - `GET /api/public/brands`
  - `GET /api/public/brands/{brand_slug}`
  - `GET /api/public/brands/{brand_slug}/stores`
  - `GET /api/public/brands/{brand_slug}/stores/{store_slug}`
  - `GET /api/public/brands/{brand_slug}/stores/{store_slug}/items/{item_slug}`
- [x] Inactive brand/store → 404  
- [x] Availability parity (sold_out, daily limit, hours, branch stock)  
- [x] Unit tests: `tests/unit/services/test_catalog_public.py` (12 passed)

### Phase B — Media proxy — **DONE 2026-07-16**

- [x] Catalog images: Telegram `file_id` → `/media/{token}` + disk cache (`bot/services/media_proxy.py`)  
- [x] Allowlist only catalog media (not slips/proof)  
- [x] Bot token from `BotConfig` per brand, else `TOKEN`  
- [x] Catalog DTOs use proxy URLs; `tests/unit/services/test_media_proxy.py`  

### Phase C — Multi-tenant Astro shell — **DONE 2026-07-16** (forms stub → CARD-36)

**Stack:** Astro 5+ · Tailwind · `apps/storefront` · SSR node adapter · **desktop + mobile**.

- [x] Scaffold `apps/storefront`  
- [x] Profile header, chips, product grid (3-col mobile / up to 5-col desktop), item detail  
- [x] Age gate when `age_gate_enabled`  
- [x] Pages: `/`, `/{brand}`, about, contact, branch, item, inquire/book stubs  
- [x] Footer legal + DBD + compliance warnings  
- [x] Mode-aware CTA labels (order vs inquire)  
- [x] Lazy images via API media URLs  

### Out of scope (later cards)

- Full web checkout (CARD-32 + future)  
- Lead form + booking persistence (CARD-36 — wire after shell)  
- Per-vertical marketing blogs as core (optional module)  
- Instagram/LINE messaging (33/16)  
- Custom domain DNS automation (v2)  
- Per-brand Markdown product catalogs (CARD-37 path — rejected as architecture)

---

## Data contracts (conceptual)

```text
BrandPublicDTO
  slug, name, description, logo_url, timezone
  legal: { legal_name, dbd_number }          # columns
  contact: { support_email, support_phone }  # columns
  web: { hero, about, faq, social, theme, modules, compliance }  # web_profile JSON
  stores: [ StoreSummary… ]

StorePublicDTO
  slug, name
  address, phone, latitude, longitude, maps_url   # columns (not JSON-only)
  hours: …                                        # dedicated structured field
  web: { about_md, amenities, … }                 # store web_profile JSON
  menu: [ Category → Item ]                       # relational + inventory

ItemDTO: slug, name, price, image_urls, available, badges, modifiers_schema
```

---

## Exit criteria

- [x] Two brands can expose distinct brand + branch URLs from same Astro app (API multi-tenant)  
- [x] Catalog/availability driven from DB service  
- [x] Branch inventory affects availability when used  
- [x] Age gate + disclaimers + DBD/address/phone fields supported  
- [x] Portfolio mode CTA = inquire (no cart)  
- [x] Mobile + desktop responsive grid shell  
- [x] Media proxy allowlists catalog only  
- [ ] E2E smoke against live bot+storefront in deploy env  
- [ ] Lead/booking POST wired (CARD-36)

---

## Related

| Doc | Role |
|-----|------|
| [CLEAR-START.md](../CLEAR-START.md) | Session bootstrap |
| [WHITE-LABEL-ASTRO-IMPLEMENTATION.md](../Specifications/WHITE-LABEL-ASTRO-IMPLEMENTATION.md) | **Astro build contract** |
| [BRAND-BRANCH-WEB-CONTENT-MODEL.md](../Specifications/BRAND-BRANCH-WEB-CONTENT-MODEL.md) | Hybrid data |
| [WHITE-LABEL-SITE-MODES-COMPLIANCE-LEADS.md](../Specifications/WHITE-LABEL-SITE-MODES-COMPLIANCE-LEADS.md) | Modes, disclaimers, leads, booking |
| [WEB-INSTAGRAM-STYLE-STOREFRONT.md](../Specifications/WEB-INSTAGRAM-STYLE-STOREFRONT.md) | UI/IA detail |
| [GALLERY-JS-INSPIRATION.md](../Specifications/research/GALLERY-JS-INSPIRATION.md) | Gallery libs |
| [CARD-35](CARD-35-instagram-style-web-storefront.md) | UI patterns under this epic |
| [CARD-36](../later/CARD-36-instagram-web-telegram-funnel.md) | Leads + booking after shell |
| [CARD-19](CARD-19-multi-brand-bot-coordination.md) | Telegram multi-brand done |
| [CARD-28](CARD-28-per-store-menu-image-and-payment-qr.md) | Store assets done |
