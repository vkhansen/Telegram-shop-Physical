# Brand & Branch Web Content Model

> **Status:** `accepted` for P0 design (2026-07-16)  
> **Epic:** [CARD-38](../done/CARD-38-white-label-brand-branch-sites.md)  
> **Clear-start:** [CLEAR-START.md](../CLEAR-START.md)  
> **Principle:** As much of each brand/branch **website** as possible is **populated from the database**. Vertical (food vs physical goods) does not change the model.

---

## 1. Short answer

**No — do not put everything in a single `web_metadata` JSON blob.**

Use a **hybrid model**:

| Kind of data | Storage | Why |
|--------------|---------|-----|
| **Operational / contact / legal identity** | **First-class columns** (or dedicated tables) on `brands` / `stores` | Shared by Telegram bot, web, invoices, compliance; queryable; validated |
| **Catalog (menu / products / inventory)** | **Existing relational tables** | Already the source of truth; never duplicate into JSON |
| **Flexible marketing / page chrome** | **`web_profile` JSONB** (per brand and per store) | About page body, hero, FAQ, theme, SEO extras, social link map — varies by brand without migrations every time |

Putting Address, Phone, DBD number, and core descriptions **only** inside a JSON blob is the wrong default: the bot and ops already need those fields as real data, and legal identifiers should be explicit, searchable, and hard to “lose” in unstructured JSON.

---

## 2. What already exists (reuse first)

### Brand (`brands`) — today

| Column | Use on web |
|--------|------------|
| `name`, `slug` | Title, URL |
| `description` | Short brand blurb (hero / meta) |
| `logo_file_id` | Logo via media proxy |
| `timezone`, `is_active` | Hours context, 404 if inactive |
| `promptpay_*` | Prefer **not** on public web by default (payment ops) |

### Store (`stores`) — today

| Column | Use on web |
|--------|------------|
| `name` | Branch title |
| **`address`** | **Contact / maps / footer** — first-class already |
| **`phone`** | **Click-to-call** — first-class already |
| `latitude`, `longitude` | Maps, schema.org |
| `menu_image_file_id` | Branch hero / menu board image |
| `is_active`, `is_default` | Visibility |
| Kitchen/rider group IDs | **Never public** |

### Catalog

Categories, Goods, BranchInventory, modifiers, media on goods — **relational only**. Web pages **query** these; they are not stored inside brand JSON.

---

## 3. Recommended model (hybrid)

```text
┌─────────────────────────────────────────────────────────────┐
│ BRAND (legal entity / white-label tenant)                    │
│  First-class: identity, contact, legal IDs                   │
│  JSONB web_profile: about, hero, FAQ, social, theme, SEO     │
│  Relations: stores[], categories[], goods[], bot_config      │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ STORE / BRANCH                                               │
│  First-class: address, phone, geo, hours, slug               │
│  JSONB web_profile: local about, amenities, branch SEO       │
│  Relations: branch_inventory → goods availability            │
└─────────────────────────────────────────────────────────────┘
```

### 3.1 Brand — first-class columns (add if missing)

These are **explicit**, not buried in JSON:

| Field | Purpose | Public web? |
|-------|---------|-------------|
| `legal_name` | Registered business name | Footer / About / legal |
| **`dbd_number`** | Thai DBD / company registration no. | Footer / compliance block |
| `tax_id` / VAT ID | Optional tax identity | Footer if required |
| `support_email` | Public or semi-public contact | Contact page |
| `support_phone` | Brand-level hotline (if not only per-store) | Contact |
| `description` | Short tagline/summary (exists) | Hero, meta description |
| `logo_file_id` | Brand mark (exists) | Header |

**Why DBD and legal name are columns, not JSON:**

- Compliance and admin reporting (“list all brands with DBD set”)  
- Footer templates always render the same keys  
- Validation (format length), uniqueness checks if needed  
- Avoid “forgot to put dbd inside metadata.legal.dbd” bugs  

### 3.2 Store — first-class columns (add if missing)

| Field | Purpose | Notes |
|-------|---------|--------|
| **`address`** | Full street address | **Already a column** — source for web |
| **`phone`** | Branch phone | **Already a column** |
| `latitude` / `longitude` | Maps | Already columns |
| `slug` | URL segment | Required for web routing (CARD-38) |
| `email` | Branch email (optional new) | First-class if used in contact |
| `opening_hours` | Structured hours | Prefer **JSONB column dedicated to hours** *or* normalized rows — not mixed with About prose |

**Rule:** If Telegram admin, riders, or invoices already need a field, it is **first-class** (or a shared settings key with a known name), not free-form web-only JSON.

### 3.3 Brand `web_profile` JSONB — flexible site content

Assigned **per brand**. Schema-versioned. Validated in app (Pydantic), not arbitrary junk forever.

```json
{
  "schema_version": 1,
  "web_enabled": true,
  "theme": "retail_grid",
  "tagline": "…",
  "tagline_i18n": { "th": "…", "en": "…" },
  "about": {
    "title": "About us",
    "body_md": "Long markdown for /about …",
    "body_i18n": { "th": { "title": "…", "body_md": "…" } }
  },
  "hero": {
    "headline": "…",
    "subhead": "…",
    "cta_primary": { "label": "View menu", "href": "menu" },
    "cta_secondary": { "label": "Contact", "href": "contact" }
  },
  "social": {
    "instagram": "https://…",
    "line": "https://…",
    "whatsapp_e164": "66…",
    "facebook": "https://…",
    "telegram": "https://…"
  },
  "faq": [
    { "q": "…", "a_md": "…" }
  ],
  "seo": {
    "title_template": "{brand} | …",
    "default_description": "…",
    "og_image_file_id": null
  },
  "modules": {
    "show_about": true,
    "show_faq": true,
    "show_blog": false,
    "show_lead_form": true,
    "show_order_telegram_cta": true
  },
  "compliance": {
    "show_dbd_in_footer": true,
    "extra_footer_md": "Age / product disclaimers…"
  }
}
```

**Lives in JSON because:** shape changes by theme/vertical; long prose; optional sections; i18n blobs; no need for SQL filters on every FAQ question.

### 3.4 Store `web_profile` JSONB — branch-local marketing

```json
{
  "schema_version": 1,
  "about_md": "This branch specializes in…",
  "amenities": ["parking", "wheelchair"],
  "pickup_notes_md": "Enter from soi…",
  "seo": { "description": "…" },
  "gallery_file_ids": []
}
```

**Does not replace** `address` / `phone` / geo. Those stay columns. Branch page **merges**:

```text
Contact block  = store.address + store.phone + store.lat/lng
About block    = store.web_profile.about_md  OR fallback brand.web_profile.about
Legal footer   = brand.legal_name + brand.dbd_number + brand.web_profile.compliance
Menu block     = categories/goods + branch inventory (relational)
```

---

## 4. What must **not** go in web JSON

| Data | Where it stays |
|------|----------------|
| Menu categories / items / prices / modifiers | `categories`, `goods` |
| Stock / sold out / daily limits | `goods` + `branch_inventory` |
| Orders, carts, payments, slips | order/payment tables |
| Bot tokens, kitchen/rider Telegram groups | `bot_configs`, store ops columns |
| Staff roles | `brand_staff` |
| Customer PII / leads | leads / users (later cards) |

Duplicating the menu into `web_metadata.products[]` would **fork truth** and break white-label automation.

---

## 5. Page population map (auto site)

| Page / block | Primary DB source |
|--------------|-------------------|
| Brand home hero | `brand.name`, `description`, `web_profile.hero`, `logo_file_id` |
| Store list | `stores` (active) + address/phone preview |
| Branch header | `store.name`, address, phone, geo, `menu_image_file_id` |
| Branch menu grid | categories + goods + **inventory for that store_id** |
| Item detail | goods + media + availability |
| **About us** | `brand.web_profile.about` (+ optional store override) |
| Contact | brand support_* + store address/phone; social from `web_profile.social` |
| Footer legal | `legal_name`, **`dbd_number`**, `web_profile.compliance` |
| FAQ | `brand.web_profile.faq` |
| SEO title/description | `web_profile.seo` with fallbacks from name/description |

**Result:** Most of the site is DB-driven. Editors change Telegram admin / settings / web_profile — not HTML files per brand.

---

## 6. Why not “one JSON blob for everything”?

| All-in JSON | Hybrid (recommended) |
|-------------|----------------------|
| Address/phone duplicated or ignored by bot | Same columns bot already uses |
| DBD hard to validate/report | Explicit column |
| Cannot index “stores in Bangkok” cleanly | Address/geo columns |
| Schema drift undocumented | versioned `web_profile` + Pydantic |
| Menu copy-paste into JSON | Relational catalog stays single source |

A blob is fine for **presentation extras**. It is a poor database for **identity, location, and catalog**.

---

## 7. Alternative: `BotSettings` key/value only

`bot_settings` (key + brand_id) can hold `web_profile` JSON as one key (`web_profile_json`) without a migration for every theme field. Acceptable for MVP if:

- Core legal/contact fields still get **real columns** when used in footers/compliance  
- Document keys and schema_version  

Prefer explicit `brands.web_profile` / `stores.web_profile` JSONB columns for clarity once web is first-class.

---

## 8. Admin / edit path (P0 intent)

| Field type | How operators set it |
|------------|----------------------|
| Address, phone, geo | Existing store admin flows (extend as needed) |
| DBD, legal name | Brand settings admin (new fields) |
| About / FAQ / social / theme | Brand “Web site” settings (JSON editor or form that writes `web_profile`) |
| Menu / inventory | Existing goods/stock admin |

Public API **assembles** DTOs: first-class fields + resolved media URLs + web_profile + catalog.

---

## 9. Public API DTO sketch (assembled, not raw blob dump)

```text
BrandPublicDTO
  slug, name, description
  logo_url
  legal: { legal_name, dbd_number }     # from columns
  contact: { support_email, support_phone }
  web: { tagline, hero, about, faq, social, theme, modules, compliance }  # from web_profile
  stores: [ StoreSummaryDTO ]

StorePublicDTO
  slug, name
  address, phone, latitude, longitude, maps_url   # from columns
  hours: …                                        # structured field
  web: { about_md, amenities, … }                 # from store web_profile
  menu: [ CategoryDTO → ItemDTO ]                 # relational + inventory
```

Clients (Astro shell, future apps) never need to know which part was column vs JSON.

---

## 10. P0 implementation checklist (data)

- [ ] Document this hybrid model (this file)  
- [ ] Add brand legal/contact columns as needed (`legal_name`, `dbd_number`, …)  
- [ ] Add `stores.slug`  
- [ ] Add `brands.web_profile` JSONB + `stores.web_profile` JSONB (schema v1)  
- [ ] Keep address/phone as columns; map them into public DTOs  
- [ ] Catalog remains relational  
- [ ] Validate `web_profile` with Pydantic on write  

---

## 11. One-line policy

> **Facts the business operates on (who, where, phone, DBD, menu, stock) = structured DB fields and tables.  
> Facts that only dress the website (about prose, FAQ, hero, theme, social map) = versioned `web_profile` JSON per brand/branch.**

That is how “as much as possible from the database” stays true without turning the database into an untyped CMS blob.

---

## 12. Compliance, portfolio mode, leads & bookings

**All of these are white-label tenant data** (not hardcoded per vertical):

| Concern | Where |
|---------|--------|
| Age gate + disclaimer text (nicotine, tobacco, other restricted categories) | Brand flags + `web_profile.compliance` |
| Showcase portfolio without cart (“call / book to order”) | `commerce_mode` = `portfolio` \| `hybrid` + item `inquiry_only` |
| Lead form | Module + `leads` table |
| Meeting booking (in person / Google Meet) | Module + `bookings` table (MVP = request; later calendar) |

Full specification: **[WHITE-LABEL-SITE-MODES-COMPLIANCE-LEADS.md](WHITE-LABEL-SITE-MODES-COMPLIANCE-LEADS.md)**.
