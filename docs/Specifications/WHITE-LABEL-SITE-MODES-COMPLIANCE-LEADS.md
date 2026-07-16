# White-Label Sites: Content, Compliance, Portfolio Mode, Leads & Bookings

> **Status:** `draft` / design accepted for backlog (2026-07-16)  
> **Parent:** [CARD-38](../later/CARD-38-white-label-brand-branch-sites.md) · [BRAND-BRANCH-WEB-CONTENT-MODEL.md](BRAND-BRANCH-WEB-CONTENT-MODEL.md)  
> **Related:** [CARD-36](../later/CARD-36-instagram-web-telegram-funnel.md) leads · funnel spec  
> **Legal note:** Operators are responsible for what they advertise and where. Platform stores **configurable** age gates, disclaimers, and commerce modes — it does not assert that any restricted category is legal in a given market.

---

## 1. Answers up front

| Question | Answer |
|----------|--------|
| Should **all website data** live in white-labeling (incl. tobacco/age disclaimers)? | **Yes, almost all site-facing content is tenant data** (brand/store + catalog + `web_profile`). Disclaimers and age gates are **first-class compliance config**, not hardcoded in the theme. |
| One big JSON for everything? | **No** — hybrid: columns for legal/contact; tables for catalog; `web_profile` for prose/FAQ/disclaimers/theme ([content model](BRAND-BRANCH-WEB-CONTENT-MODEL.md)). |
| Portfolio only — advertise products, **call/book to order**, not in “store” cart? | **Yes — supported as a commerce mode** per brand (and optionally per item). |
| Lead form on white-label site? | **Yes** — core conversion module. |
| Meeting booking (in person or Google Meet)? | **Yes** — booking requests (and later real calendar slots) as a module on the same tenant site. |

Reference UX patterns (e.g. [NOVA](https://novaswedensnus.com/)): age gate → hero → product lineup → story/FAQ → newsletter — **without** requiring an open cart. That maps cleanly to **portfolio + lead** mode.

---

## 2. What the white-label tenant owns (everything the public site needs)

All of the following are **per Brand** (and Branch where noted), stored in DB, rendered by one multi-tenant shell:

### 2.1 Always structured (columns / tables)

| Domain | Examples |
|--------|----------|
| Identity | name, slug, logo, description |
| Legal | legal_name, **dbd_number**, tax_id |
| Branch contact | address, phone, lat/lng, hours |
| Catalog | categories, goods, media, prices (optional display) |
| Inventory | branch stock when mode uses real stock |
| Ops (not public) | bot token, kitchen groups |

### 2.2 Web profile JSON (+ small first-class flags)

| Domain | Examples |
|--------|----------|
| About / heritage | about body, story sections |
| Marketing | hero, taglines, FAQ |
| Social | LINE, WA, IG, FB |
| **Compliance** | age gate copy, nicotine/tobacco/general disclaimers, footer warnings |
| **Commerce mode** | full store vs portfolio-only vs hybrid |
| Modules | lead form on/off, booking on/off, show prices on/off |
| Theme | layout skin |

### 2.3 Disclaimers for age-restricted / sensitive verticals

Disclaimers are **tenant-configured**, not compiled into the platform for one product type.

**Recommended first-class brand flags (queryable):**

| Field | Purpose |
|-------|---------|
| `age_gate_enabled` | Boolean — force gate before browse |
| `min_age` | e.g. 18 / 20 / 21 (jurisdiction-specific; operator sets) |
| `catalog_visibility` | `public` \| `after_age_gate` \| `private` |

**Recommended `web_profile.compliance` (prose + lists):**

```json
{
  "age_gate": {
    "title": "Are you of legal age?",
    "body_md": "…contains nicotine… / operator text…",
    "confirm_label": "I am of legal age",
    "deny_label": "I am under age",
    "deny_redirect_url": "https://www.google.com"
  },
  "footer_warnings": [
    "This product may contain nicotine. Nicotine is addictive. Adults only."
  ],
  "product_disclaimer_md": "Longer legal text…",
  "restricted_categories_note_md": "Optional note for portfolio of restricted goods…",
  "show_dbd_in_footer": true
}
```

**Item-level (optional column or goods flag):**

| Field | Purpose |
|-------|---------|
| `requires_age_gate` | Inherit brand default or force |
| `disclaimer_key` | Pick a named disclaimer block from brand profile |
| `is_restricted` | UI badge; does not equal “illegal” — operator meaning |

Platform behavior:

1. If `age_gate_enabled` → block site until confirmed (cookie/session).  
2. Always render footer warnings when configured.  
3. Never ship a default “weed” or “tobacco” marketing pack as core — **operators paste their own legal text**.

---

## 3. Commerce modes (portfolio vs real store)

White-label must support **more than restaurant delivery**.

### 3.1 Brand-level `commerce_mode`

| Mode | Catalog | Prices | Cart / online order | Primary CTA |
|------|---------|--------|---------------------|-------------|
| **`full_store`** | Live goods + inventory | Usually show | Yes (Telegram/bot or later web) | Add / Order |
| **`portfolio`** | Showcase lineup (may still use `goods` rows) | Optional / hide | **No** public cart | Call · Lead · Book meeting · Inquire |
| **`hybrid`** | Mix | Per item | Only items marked orderable | Mixed CTAs |

Stored as: **brand column** `commerce_mode` or `web_profile.modules.commerce_mode`.

### 3.2 Item-level flags (for hybrid / portfolio)

| Field | Meaning |
|-------|---------|
| `web_listable` | Show on website portfolio |
| `web_orderable` | Allow online/Telegram order path |
| `inquiry_only` | CTA = inquire / call / book (not add-to-cart) |
| `show_price_on_web` | Override brand default |

**Portfolio of restricted items not “in the store”:**

- Still store rows in `goods` (name, media, description, category) for the **auto gallery**.  
- Set brand `commerce_mode = portfolio` (or items `inquiry_only = true`).  
- **Do not** reserve inventory or open bot checkout from web for those items.  
- CTA: “Request info”, “Call branch”, “Book a meeting”.  
- Optional: item not linked to branch stock at all (`web_listable` only).

This matches “advertise a portfolio → customer must call / meet to order.”

### 3.3 Mapping to existing bot

| Mode | Telegram bot |
|------|----------------|
| `full_store` | Existing cart/order/pay/kitchen flow |
| `portfolio` | Bot optional for staff; web leads/bookings notify staff; no customer self-checkout required |
| `hybrid` | Orderable SKUs use bot; inquiry-only SKUs use leads |

---

## 4. Lead form (required module)

Per-brand module: `web_profile.modules.show_lead_form = true`.

### 4.1 Purpose

Capture demand when:

- Portfolio / inquiry-only  
- Wholesale / distribution interest  
- Age-gated brands that won’t take open web checkout  

### 4.2 Minimum fields

| Field | Required |
|-------|----------|
| name | yes |
| phone and/or email | yes (one of) |
| preferred_channel | line \| whatsapp \| phone \| email \| telegram |
| interest_type | retail \| wholesale \| distribution \| product_inquiry \| other |
| product context | optional (item slug from gallery) |
| message | optional |
| age_confirmed | yes if age_gate |
| privacy consent | yes |
| utm/ref | auto |

### 4.3 Storage

New table **`leads`** (CARD-36), always with:

- `brand_id`, optional `store_id`  
- `source = web_site`  
- `status` pipeline  

Notify staff via Messenger (CARD-29) on Telegram ops chat — **not** cold-spam customers.

### 4.4 NOVA-like “Stay in the loop”

Newsletter signup = lead or `lead_type = newsletter` with email; Resend optional. Same module family.

---

## 5. Meeting booking (in person or Google Meet)

### 5.1 Product intent

White-label site offers **Book a meeting**:

| Type | Meaning |
|------|---------|
| `in_person` | At branch address (from `stores`) or HQ |
| `google_meet` | Video call — Meet link issued by staff or automation |
| `phone_call` | Optional third type |

### 5.2 MVP vs later

| Phase | Behavior |
|-------|----------|
| **MVP (P0/P2)** | **Booking request form**: datetime preference(s), type, notes → row in `bookings` or `leads` with `type=booking` → staff notify → staff confirms out-of-band (LINE/WA/email) and sends Meet link or address |
| **Later** | Real availability calendar, Google Calendar API, auto Meet link creation, confirm/cancel emails |

MVP is enough for portfolio/restricted brands: “request a slot” without building full Calendly yet.

### 5.3 Data model (recommended)

**`bookings`** (prefer dedicated table, not only leads):

| Column | Purpose |
|--------|---------|
| id | PK |
| brand_id, store_id nullable | Tenant + branch for in-person |
| lead_id nullable | Link if created from lead |
| name, phone, email | Contact |
| meeting_type | `in_person` \| `google_meet` \| `phone_call` |
| preferred_slots | JSON list of ISO datetimes or free text |
| scheduled_at | Set when staff confirms |
| meet_url | Google Meet link when known |
| status | `requested` \| `confirmed` \| `cancelled` \| `completed` \| `no_show` |
| notes | Customer + staff notes |
| created_at | |

**Brand `web_profile.booking`:**

```json
{
  "enabled": true,
  "types": ["in_person", "google_meet"],
  "intro_md": "Book a private consultation…",
  "duration_minutes_default": 30,
  "timezone": "Asia/Bangkok",
  "staff_notify": true,
  "in_person_store_ids": [1, 2],
  "google_meet_mode": "staff_sends_link"
}
```

### 5.4 UI

- `/book` or modal on brand/branch site  
- Choose: In person (pick store) vs Google Meet  
- Pick preferred date/time (simple datetime or 2–3 preferences in MVP)  
- Age + privacy consent when compliance enabled  
- Thanks: “We’ll confirm on your preferred channel”

### 5.5 Google Meet integration levels

| Level | Implementation |
|-------|----------------|
| L0 MVP | Staff pastes Meet link into booking when confirming |
| L1 | Env service account / Calendar API creates event + Meet |
| L2 | Customer self-serve free/busy from connected calendar |

**P0/P2 ship L0**; design tables so L1 plugs in without rewrite.

---

## 6. Site information architecture (modules on/off per brand)

```text
/{brand}                 Home (hero, featured portfolio)
/{brand}/about           About (web_profile)
/{brand}/contact         Address/phone/DBD/social + lead form
/{brand}/menu|products   Catalog (mode-aware CTAs)
/{brand}/{store}         Branch page
/{brand}/book            Meeting booking
/{brand}/inquire         Lead / product inquiry
```

Footer always: legal_name, dbd_number, compliance warnings when set.

---

## 7. Database vs schema today

| Need | Today | Add for white-label |
|------|-------|---------------------|
| Address/phone | `stores` columns | reuse |
| Brand description/logo | `brands` | + legal/dbd/support |
| Menu/items | goods/categories | + web_listable / inquiry_only flags |
| Inventory | branch_inventory | only when full_store |
| Disclaimers / age gate | — | brand flags + web_profile.compliance |
| Commerce mode | — | brand commerce_mode |
| Leads | — | `leads` table (CARD-36) |
| Bookings | — | `bookings` table |
| web_profile | — | JSONB brand/store |

No need to invent a second CMS database outside this platform for P0.

---

## 8. Sequencing (how this sits on the backlog)

| Work | Card / phase |
|------|----------------|
| Hybrid content + compliance fields + commerce_mode | **CARD-38** Phase A (extend) |
| Catalog API respects portfolio vs orderable | **CARD-38** A |
| Multi-tenant pages including About/Contact/disclaimers | **CARD-38** C |
| Lead form + staff notify | **CARD-36** (P2, can start after 38A) |
| Booking requests MVP | **CARD-36** extension or **CARD-39** (bookings) — recommend extend 36 or thin CARD-39 |
| Google Calendar auto-Meet | Later, after L0 bookings |

---

## 9. Policy summary

1. **White-label stores the site:** identity, branch info, catalog, inventory (when used), **disclaimers, age gate copy, portfolio mode, leads, bookings**.  
2. **Hybrid storage:** columns for legal/contact; tables for catalog; JSON for compliance prose and modules.  
3. **Portfolio / call-to-order is a first-class commerce mode**, not a hack — restricted or B2B brands can showcase without a web cart.  
4. **Lead form + meeting booking** are standard modules for that mode (and optional for full_store).  
5. **Operators supply** regulated-product legal text; platform provides the slots and gates.

---

## 10. Acceptance criteria (design)

- [ ] Brand can enable age gate + custom disclaimer text without code deploy  
- [ ] Brand can set `portfolio` mode: gallery shows, no add-to-cart, CTA inquire/call/book  
- [ ] Item can be inquiry-only while another is orderable (`hybrid`)  
- [ ] Lead form stores brand_id/store_id/product context  
- [ ] Booking request supports in_person vs google_meet and staff confirmation flow  
- [ ] DBD + address + phone render from structured fields on contact/footer  
