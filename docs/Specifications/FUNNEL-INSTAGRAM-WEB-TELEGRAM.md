# Funnel Spec — Instagram Discovery → Secure Web → Telegram Backend

> **Spec status:** `draft`  
> **Mode:** desired (customer acquisition architecture)  
> **Cards:** [CARD-36](../later/CARD-36-instagram-web-telegram-funnel.md), [CARD-35](../later/CARD-35-instagram-style-web-storefront.md), [CARD-34](../later/CARD-34-conversation-workflow-specifications.md)  
> **Related surfaces:** [WEB-INSTAGRAM-STYLE-STOREFRONT.md](WEB-INSTAGRAM-STYLE-STOREFRONT.md), multi-channel [MULTI-CHANNEL-TIERED-PLAN.md](../later/MULTI-CHANNEL-TIERED-PLAN.md)  
> **Last updated:** 2026-07-16

---

## 1. Goal

Turn the existing **Telegram bot into the backend engine** while the **entire public customer experience** feels native to **Instagram** and a **matching high-trust website**.

| Layer | Role | What the user sees |
|-------|------|--------------------|
| **Instagram** | Discovery + trust | Profile, Reels, Stories, DMs as traffic — **not** “join our Telegram” spam |
| **Secure web** | Conversion + catalog | Instagram-style site, forms, gallery, inquiry/order capture |
| **Telegram bot** | Private fulfillment engine | Orders, catalog personalization, payment, support, kitchen/dispatch — **after** user opts in via form |

**Non-goal:** Pushing cold traffic straight into Telegram.  
**Principle:** Users stay in Instagram → secure web forms → bot handles fulfillment/support **privately**.

Operators remain responsible for **local legal/regulatory compliance** for their product category and market (Thailand / SE Asia). This document is a **technical and UX funnel** specification, not legal advice.

---

## 2. Why this funnel

- Instagram is the discovery + trust layer (visual product “storms”, Stories, Reels).  
- Secure web forms are the conversion layer (high control, brandable, CAPTCHA, privacy policy).  
- Existing Telegram bot stays the fast private backend (orders, catalog, support, personalization).  
- Full abstraction: users never need to “find” the bot themselves.  
- Thailand/SE Asia preference: forms can prioritize **LINE / WhatsApp** contact; Telegram is optional “private channel” after consent.

---

## 3. Core architecture

```text
┌─────────────────────────────────────────────────────────────┐
│ 1. INSTAGRAM (top of funnel)                                 │
│    Profile · Reels · Stories · optional DM → link in bio     │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTPS only
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. SECURE WEB (trusted hub)                                  │
│    Astro + Tailwind storefront (CARD-35)                      │
│    Masonry gallery · product detail · lead / inquiry / order  │
│    forms · privacy · CAPTCHA · rate limits                    │
└───────────────────────────┬─────────────────────────────────┘
                            │ POST /api/v1/leads | inquiries | orders
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. BRIDGE API (this repo / FastAPI-style endpoint)           │
│    Validate · store Lead · notify staff · trigger bot engine  │
└───────────────────────────┬─────────────────────────────────┘
                            │ Messenger port (CARD-29) / admin alert
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. TELEGRAM BOT (backend engine — existing product)          │
│    Admin/kitchen/rider · inventory · payments · tickets      │
│    Optional: private customer thread AFTER opt-in            │
└─────────────────────────────────────────────────────────────┘
```

### Role of existing bot capabilities

| Bot capability (already built) | Funnel use |
|--------------------------------|------------|
| Catalog Brand→Store→Menu→Item | Powers auto-generated web gallery (read API) |
| Cart / checkout / PromptPay / crypto | Staff-assisted or post-opt-in private close |
| Support tickets | Web inquiry → ticket or admin DM |
| Kitchen / rider / dispatch | Unchanged — ops stay on Telegram |
| Multi-brand | Per-brand site slug + IG bio link |

---

## 4. Layer 1 — Instagram (discovery & traffic)

### 4.1 Profile & content (operator process — not code)

| Element | Spec |
|---------|------|
| Bio | Product positioning + **single** CTA to web hub (custom domain preferred over raw t.me) |
| Feed / Reels / Stories | Product photography, lifestyle, social proof, limited offers |
| CTAs | “Shop discreetly →” / “Request catalog →” → **web**, not public Telegram invite spam |
| Lead magnets | Flavor guide / price list → **web form** (or IG native lead form → same bridge webhook) |
| Stories polls | Link sticker → web form with UTM |

### 4.2 What we implement in software

- UTM + `ref` query params on all web landings (`?utm_source=instagram&utm_medium=bio|story|reel&ref=…`)  
- Optional: store `instagram_handle` if user provides it on form  
- Analytics events: `ig_landing`, `form_start`, `form_submit`, `bot_notified`  

### 4.3 Explicitly forbidden (v1 marketing UX)

- Homepage primary CTA “Join Telegram” / raw `t.me` as only path  
- Unsolicited mass Telegram adds  
- Public posting of bot deep links in every caption without web intermediate  

Telegram may appear **after** form consent as one of several contact options.

---

## 5. Layer 2 — Secure web frontend (trusted hub)

**Stack (recommended):** Astro + Tailwind (+ React islands for lightbox/forms). Deploy Vercel/Netlify/static+API.  
**Catalog data:** Auto from Telegram backend ([WEB-INSTAGRAM-STYLE-STOREFRONT.md](WEB-INSTAGRAM-STYLE-STOREFRONT.md)).  
**Hierarchy:** Brand → Store → Menu → Items.

### 5.1 Visual direction

- Mobile-first, premium, Instagram-adjacent: masonry “storm” gallery, hover/lightbox cards, dark mode option, bold accents.  
- Match brand Instagram so trust transfers.  
- Do **not** use Meta/Instagram trademarks in chrome.

### 5.2 Key pages

| Page | Purpose |
|------|---------|
| `/` or `/{brandSlug}` | Gallery landing + primary CTAs |
| `/{brandSlug}/{storeSlug}` | Location-scoped menu if multi-store |
| Product / item detail | Lightbox or page; **Inquire** / **Request order** |
| `/request` or modal | Lead form |
| `/inquire` | Product inquiry (pre-filled from gallery) |
| `/order-request` | Order intent form (v1 — not necessarily full card payment) |
| `/privacy` | Privacy policy (required) |
| `/thanks` | Confirmation + next-steps (no forced Telegram) |

### 5.3 Forms (conversion layer)

#### F1 — Lead form (catalog / guide magnet)

| Field | Required | Notes |
|-------|----------|-------|
| name | yes | |
| phone | yes* | E.164 / Thai validation (reuse bot validators) |
| preferred_channel | yes | `line` \| `whatsapp` \| `telegram` \| `phone` — default weight toward line/whatsapp for TH |
| line_id / wa_number / telegram_username | conditional | Based on preferred_channel |
| interest_tags | no | flavors / categories / free text |
| delivery_area | no | province / zone text |
| consent_contact | yes | checkbox |
| consent_privacy | yes | link to /privacy |
| utm_* / ref | auto | hidden |
| honeypot + CAPTCHA | yes | anti-spam |

\*Email optional alternative if product allows.

#### F2 — Product inquiry

All of F1 plus:

| Field | Required |
|-------|----------|
| brand_slug / store_slug | yes (hidden from selection context) |
| item_slug or item_name | yes |
| quantity_interest | no |
| message | no |

#### F3 — Order request (intent)

All of F2 plus:

| Field | Required | Notes |
|-------|----------|-------|
| delivery_address | yes for delivery | or pickup flag |
| delivery_type | yes | door / pickup / other |
| payment_preference | no | cash / promptpay / crypto — closed privately |
| notes | no | |

**v1 rule:** Prefer **not** collecting full card PAN on site. Payment closes via bot/staff on preferred channel (PromptPay QR already in bot).

### 5.4 Client UX after submit

1. Show `/thanks` with clear copy: “We’ll contact you on {preferred_channel} shortly.”  
2. Optional: “Prefer a private chat link?” only if user selected Telegram **and** consented.  
3. Optional confirmation email (Resend/etc.) — no Telegram mention required.

---

## 6. Layer 3 — Bridge API (bot as engine)

### 6.1 Endpoints

| Method | Path | Body | Result |
|--------|------|------|--------|
| POST | `/api/v1/leads` | F1 payload | `Lead` row + staff notify + optional automations |
| POST | `/api/v1/inquiries` | F2 | `Lead` + item context + staff/ticket |
| POST | `/api/v1/order-requests` | F3 | `Lead` + draft intent; staff completes order in bot/admin |
| GET | `/api/v1/catalog/...` | — | Public catalog (CARD-35) |

Security: rate limit, CAPTCHA verify server-side, CORS allowlist web origin, idempotency key optional.

### 6.2 Data model (new)

```text
leads
  id, brand_id, store_id nullable
  name, phone, email nullable
  preferred_channel  -- line | whatsapp | telegram | phone
  channel_handle     -- line id / wa / tg username
  interest_json, delivery_area, message
  source             -- instagram_bio | story | reel | direct | other
  utm_json
  status             -- new | contacted | qualified | ordered | closed | spam
  consent_at
  created_at

lead_items (optional)
  lead_id, item_name, quantity, payload_json
```

Link to `users.telegram_id` only when known (CARD-30 identities).

### 6.3 Notifications (private)

On create:

1. **Staff/admin Telegram** (existing ops channel): formatted lead card + deep link to admin UI or callback buttons later.  
2. **Do not** auto-spam unknown Telegram users.  
3. If `preferred_channel=telegram` **and** resolvable `telegram_id` (user already in DB): optional welcome via Messenger port.  
4. If only username: staff handles manually or bot uses deep-link invite **only after** explicit process (no cold spam).  
5. If `line` / `whatsapp`: staff notified to contact on that channel (automation later via CARD-16 / WA).

### 6.4 Bot automations (after opt-in)

| Trigger | Automation |
|---------|------------|
| Lead created | Admin alert |
| Staff marks “contacted” | optional CRM state |
| User opens personal bot link with signed token | Bind identity; send personalized catalog / payment options |
| Order completed in bot | Optional web tracking page by opaque token |

Welcome sequence content uses existing i18n + catalog services — not a second product catalog.

---

## 7. Safe & compliant bridges

| Path | Description | v1 priority |
|------|-------------|-------------|
| A | IG → Web form → Staff on LINE/WA | **Primary** |
| B | IG → Web form → Staff on Telegram | Secondary |
| C | IG → Web form → Signed bot deep link after TG opt-in | Opt-in only |
| D | IG DM auto-reply with **web** link only | Content ops |
| E | Direct Telegram cold traffic | **Discouraged** |

### Consent

- Contact consent checkbox required.  
- Privacy policy page required.  
- Store consent timestamp.  
- Respect preferred_channel for first human/bot outreach.

---

## 8. Flow specs (CARD-34 IDs)

### F-01 — Instagram → Lead form → Staff

| Step | Actor | Action | System |
|------|-------|--------|--------|
| 1 | user | Taps bio/story link | Open web + UTM |
| 2 | user | Submits lead form | Validate; CAPTCHA |
| 3 | system | Persist `leads` | status=new |
| 4 | system | Notify staff Telegram | Messenger |
| 5 | staff | Contact via preferred_channel | Manual v1 |
| 6 | staff/bot | Close sale / create order | Existing bot order flow |

### F-02 — Gallery → Product inquiry

| Step | Actor | Action |
|------|-------|--------|
| 1 | user | Opens item lightbox / page |
| 2 | user | Inquire — form pre-filled with item |
| 3 | system | Lead + lead_items; staff alert |
| 4 | staff/bot | Personalized reply / order |

### F-03 — Order request → Bot fulfillment

| Step | Actor | Action |
|------|-------|--------|
| 1 | user | Submits order-request form |
| 2 | system | Lead status=qualified intent; admin order card |
| 3 | staff | Creates/completes order in Telegram admin or bot_cli |
| 4 | system | Optional customer update on preferred channel |

### F-04 — Opt-in Telegram private session

| Step | Actor | Action |
|------|-------|--------|
| 1 | user | On thanks page or SMS/LINE message, chooses “Open private chat” |
| 2 | system | Issues signed one-time `start` payload |
| 3 | user | Opens bot (first time allowed) |
| 4 | bot | Binds lead_id ↔ user; welcome + catalog tools |

---

## 9. Tech stack

| Layer | Choice | Notes |
|-------|--------|-------|
| Web UI | **Astro + Tailwind** (+ React islands) | Masonry, forms, lightbox |
| Deploy | Vercel / Netlify / static host | CDN for gallery |
| Bridge API | Existing Python stack (aiohttp/FastAPI route co-located or separate) | Same DB as bot |
| Bot | Existing aiogram app | Fulfillment engine |
| Email | Resend/SES optional | Form receipts |
| Analytics | Plausible/GA4 + server events | Funnel metrics |
| MVP alternatives | Carrd/Framer + Tally → same bridge webhook | Faster design validation |

---

## 10. Risk mitigation

| Risk | Mitigation |
|------|------------|
| Platform blocks / reports | No cold Telegram spam; branded web intermediate |
| Form spam | CAPTCHA, honeypot, rate limit, spam status |
| Trust mismatch | Same visual brand IG ↔ web |
| PII leakage | Public catalog only; leads admin-only |
| Payment PCI | No card PAN on web v1; use bot PromptPay/crypto/cash |
| Regulatory | Operator responsibility; discreet language, age gates if required by product/law |

---

## 11. Implementation priority

| Priority | Work | Card |
|----------|------|------|
| 1 | Astro Instagram-style site + gallery from catalog API | CARD-35 |
| 2 | Lead + inquiry + order-request forms + bridge API + staff Telegram notify | CARD-36 |
| 3 | IG content process (ops) — bio link, UTMs | Ops runbook in CARD-36 |
| 4 | Bot: signed opt-in start payload + welcome bind lead | CARD-36 |
| 5 | LINE/WA outbound automation | Later (CARD-16 / future) |

---

## 12. Metrics

| Funnel stage | Metric |
|--------------|--------|
| Discovery | IG sessions → web landings (UTM) |
| Conversion | form_start → form_submit rate |
| Bridge | leads created / spam rejected |
| Fulfillment | lead → order conversion (status) |
| Channel mix | preferred_channel distribution |
| Bot | opt-in rate (F-04), ticket volume |

---

## 13. Config

```bash
WEB_STOREFRONT_ENABLED=false
WEB_FUNNEL_FORMS_ENABLED=false
WEB_BASE_URL=https://shop.example.com
WEB_CORS_ORIGINS=https://shop.example.com
WEB_CAPTCHA_SECRET=
WEB_LEAD_NOTIFY_ADMIN=true
# Optional signed bot opt-in
WEB_TELEGRAM_OPTIN_ENABLED=false
WEB_TELEGRAM_OPTIN_SECRET=
```

---

## 14. Acceptance criteria

- [ ] User can complete F-01 without seeing a mandatory Telegram join CTA.  
- [ ] Staff receive Telegram notification for each valid lead.  
- [ ] Preferred channel LINE/WhatsApp/Telegram/phone stored and shown to staff.  
- [ ] Product inquiry carries brand/store/item context.  
- [ ] Catalog on web stays auto-synced from bot backend.  
- [ ] CAPTCHA + rate limit block trivial spam.  
- [ ] Privacy + consent required for submit.  
- [ ] Flags default off; Telegram ops unchanged when flags off.  
- [ ] Opt-in bot path (F-04) only when user selected Telegram and feature enabled.

---

## 15. Relationship to other specs

| Spec / card | Relationship |
|-------------|--------------|
| WEB-INSTAGRAM-STYLE-STOREFRONT | Catalog UI & Brand→Store→Menu→Item |
| CARD-35 | Implements storefront + catalog API |
| CARD-36 | Implements forms, leads, bridge, staff notify, opt-in |
| CARD-29 Messenger | Staff alerts + optional customer messages |
| CARD-30 Identities | Bind web lead ↔ telegram/line later |
| CARD-32 Services | Future: create real orders from form without staff |
| CARD-33 IG Messaging | Optional later; this funnel does **not** require IG API for v1 |
| CARD-16 LINE | Preferred contact channel automation later |

---

## 16. Out of scope (v1)

- Full in-browser payment capture (card)  
- Unsolicited Telegram outreach to non-users  
- Replacing kitchen/rider Telegram ops  
- Automated Instagram posting / content calendar (ops only)  
