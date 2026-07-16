# Card 36: Instagram → Web Forms → Telegram Backend Funnel

## Implementation Status

> **~90% Complete** | `██████████████████░░` | Staff Messenger notify + form UX polish + tests (2026-07-17). Optional Resend / TG opt-in / CAPTCHA still open.

**Tier:** T2-Funnel — Customer acquisition bridge  
**Phase:** M3 — Multi-Platform Growth  
**Priority:** **P1**  
**Effort:** Remaining: optional Resend email, signed TG opt-in, CAPTCHA
**Dependencies:**  
- Spec: [`FUNNEL-INSTAGRAM-WEB-TELEGRAM.md`](../Specifications/FUNNEL-INSTAGRAM-WEB-TELEGRAM.md)  
- Spec: [`WHITE-LABEL-SITE-MODES-COMPLIANCE-LEADS.md`](../Specifications/WHITE-LABEL-SITE-MODES-COMPLIANCE-LEADS.md) (portfolio mode, leads, bookings)  
- [CARD-38](CARD-38-white-label-brand-branch-sites.md) public brand/store context  
- [CARD-29](CARD-29-messenger-port.md) preferred for staff notify  

**Does not require:** CARD-33 Instagram Messaging API (bio link is enough for v1)

---

## Why

Public trust lives on **Instagram + web**. The existing bot is the **fulfillment engine** (orders, payments, kitchen, support). Forcing “join Telegram” as the first step increases friction and platform risk.

This card implements the **bridge**:

```text
Instagram traffic → secure web forms → Lead in DB → staff Telegram alert
                 → optional signed Telegram opt-in after consent
```

Contact preference defaults support **LINE / WhatsApp** (Thailand-friendly) with Telegram as opt-in private channel.

---

## Spec authority

**[FUNNEL-INSTAGRAM-WEB-TELEGRAM.md](../Specifications/FUNNEL-INSTAGRAM-WEB-TELEGRAM.md)** — full funnel, forms, endpoints, flows F-01…F-04, metrics, acceptance.

---

## Scope

### In

1. **`leads` (+ optional `lead_items`) tables** and admin-readable model (always `brand_id` / optional `store_id`).  
2. **Bridge API:** `POST /api/v1/leads`, `/inquiries`, `/order-requests` with validation, CAPTCHA, rate limit.  
3. **Web forms** on multi-tenant site: lead, product inquiry (pre-fill item), order-request.  
4. **`bookings` table + booking request form** — `in_person` \| `google_meet` (MVP: staff confirms + pastes Meet link; no Calendar API required).  
5. **Thanks page** copy: contact on preferred channel — **no mandatory Telegram CTA**.  
6. **Staff notification** via Messenger / existing bot admin chat when lead/booking created.  
7. **UTM / ref** capture; age_confirmed when brand age gate on.  
8. **Privacy + consent** fields and `/privacy` page requirement.  
9. **Optional F-04:** signed one-time `t.me` start payload binding `lead_id` (flagged off by default).  
10. Flags: `WEB_FUNNEL_FORMS_ENABLED`, `WEB_BOOKING_ENABLED`, `WEB_TELEGRAM_OPTIN_ENABLED`.

### Out

- Cold Telegram spam / public bot promo as only path  
- Full web payment (card)  
- Google Calendar auto-Meet (later level; schema supports meet_url)  
- LINE/WhatsApp Business API send (notify staff only in v1)  
- Instagram Graph API posting  
- Content calendar generation (ops doc only)

---

## Data

```text
leads: name, phone, preferred_channel, channel_handle, brand_id, store_id,
       interest_json, delivery_area, message, source, utm_json, status, consent_at
lead_items: lead_id, item_name, quantity, payload_json
```

Statuses: `new | contacted | qualified | ordered | closed | spam`

---

## Integration with existing bot

| Event | Action |
|-------|--------|
| Form submit | Insert lead; `notify` admin/OWNER / brand staff |
| Staff works lead | Contact LINE/WA/phone outside bot or TG if opted in |
| Order closed | Use existing admin order tools / `bot_cli` / customer bot session if bound |
| Opt-in start | `/start web_lead_{token}` → resolve lead → ensure user → welcome |

Minimal change to existing shop handlers; new router for lead bind + admin lead list (optional thin UI).

---

## Implementation priority (within card)

1. Lead model + API + staff Telegram notify  
2. Lead form on web  
3. Inquiry form pre-filled from gallery item  
4. Order-request form  
5. Signed Telegram opt-in (optional flag)

---

## Tests

- Validation: phone, consent required, CAPTCHA fail  
- Rate limit  
- Staff notify called once per lead (fake Messenger)  
- Inquiry stores item context  
- Opt-in token: valid once, expired rejected  
- Flags off: endpoints 404/disabled  

---

## Exit criteria

- [x] F-01 path works end-to-end without mandatory Telegram join (web forms + API)  
- [x] Staff get Telegram alert for new lead/booking via Messenger (`notify_staff`)  
- [x] preferred_channel persisted (line/whatsapp/telegram/phone/email)  
- [x] F-02 inquiry includes product context (`item_slug` + product_inquiry interest)  
- [x] Privacy/consent enforced (`consent_required`)  
- [x] Suite green (`tests/unit/services/test_leads_card36.py`)  
- [ ] Optional CAPTCHA / rate limit product flags  
- [ ] Optional signed Telegram opt-in (F-04)  

### Landed polish (2026-07-17)

| Path | Role |
|------|------|
| `bot/services/leads_bookings.py` | create + `notify_staff` + UTM normalize |
| `bot/web/auth_api.py` | lead/booking handlers call notify (soft-fail) |
| `apps/storefront/.../inquire.astro` | success panel, UTM, handle, honeypot |
| `apps/storefront/.../book.astro` | success panel, consent, phone_call type |
| `tests/unit/services/test_leads_card36.py` | validation + notify + HTTP |

---

## Effort

| Task | Days |
|------|------|
| Schema + API + validation | 1–1.5 |
| Staff notify + admin alert format | 0.5 |
| Web forms + thanks + privacy | 1–1.5 |
| Inquiry + order-request | 0.5–1 |
| Opt-in token bind (optional) | 0.5–1 |
| Tests | 0.5 |
| **Total** | **3–5** |

---

## Ops runbook (non-code)

Document in card completion notes or `docs/later/runbooks/ig-funnel-ops.md`:

1. IG bio → `WEB_BASE_URL` with UTMs  
2. Story/Reel link stickers → same  
3. Weekly review of lead status in DB/admin  
4. Branding parity IG ↔ web  

---

## Related

| Doc | Role |
|-----|------|
| [FUNNEL-INSTAGRAM-WEB-TELEGRAM.md](../Specifications/FUNNEL-INSTAGRAM-WEB-TELEGRAM.md) | Full funnel spec |
| [CARD-35](CARD-35-instagram-style-web-storefront.md) | Gallery / catalog site |
| [CARD-29](CARD-29-messenger-port.md) | Staff messages |
| [CARD-16](CARD-16-line-api-integration.md) | Later LINE automation |
