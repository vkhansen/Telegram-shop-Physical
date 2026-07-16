# CARD-40 Parity Scorecard (Tier F)

> **Freeze document.** Measure parity at the **service boundary**, not pixels.  
> Machine checks: `tests/unit/platform/test_card40ef_nonparity.py`  
> Vocabulary: `bot/platform/capabilities.py` · matrix: [CARD-40-parity-matrix.md](CARD-40-parity-matrix.md)

**Status:** Tier A–F complete (2026-07-17)  
**Law:** [UNIFIED-BACKEND-CHANNEL-INTERFACE.md](../Specifications/UNIFIED-BACKEND-CHANNEL-INTERFACE.md)

---

## 1. Scorecard legend

| Mark | Meaning |
|------|---------|
| ✅ | Shared parity required and met (same service + masks) |
| N/A web-only | Intentional — web customer / funnel; TG off by default |
| N/A tg-ops | Intentional — Telegram ops (or future ops web); not customer web |
| Adapter | Same user spine; different auth/I/O adapter |

---

## 2. Shared capabilities (must stay green)

Constants: `SHARED_PARITY_CAPS` in `bot/platform/capabilities.py`.

| Key | Service | Web adapter | TG adapter | Status |
|-----|---------|-------------|------------|--------|
| `catalog` / `item_detail` / `media` | `catalog_public` + `media_ref` | public API + storefront | shop handlers | ✅ |
| `cart` / `checkout` / `payment_*` | `cart` · `checkout` | `commerce_api` | cart/order handlers | ✅ |
| `order_status` | `order_query` | commerce orders API | orders view | ✅ |
| `tickets` | `tickets` (+ `tickets_web` facade) | auth_api tickets | ticket_handler | ✅ |

**P1–P5 rules** (from CARD-40): single entry · same outcomes · mask honesty · no adapter domain · identity at edge.

---

## 3. Web-only pack (N/A on Telegram customer by default)

Constants: `WEB_ONLY_CAPS` · defaults: `CHANNEL_DEFAULT_OFF["telegram"]`.

| Key | Service / surface | Web | Telegram customer | Status |
|-----|-------------------|-----|-------------------|--------|
| `leads` | `leads_bookings` + `POST /api/public/leads` | ON (mask) | OFF default | **N/A web-only** |
| `booking` | `leads_bookings` + `POST /api/public/bookings` | ON (mask) | OFF default | **N/A web-only** |
| `age_gate` | brand flag + storefront | if brand | OFF default | **N/A web-typical** |
| `about` / `faq` / `benefits` / `featured` / `ticker` / `contact` / `social_links` | content / `web_profile` | ON | OFF default | **N/A web-only** |
| `maps_widget` | storefront | ON | not in TG ceiling | **N/A web-only** |
| `auth` | `web_auth` OAuth | ON | OFF (implicit TG id) | **Adapter** |

**E2 deep-link policy:** TG may send a **URL button** via `bot/platform/deep_links.py` → `/{brand}/inquire` · `/book` · `/contact`. **No** lead/book FSM in Telegram “for parity.”

Brand may re-enable `leads`/`booking` on TG via `web_profile.channels.telegram.mask` — still **no** built-in form handlers; deep-link only unless a future product card adds chat forms.

---

## 4. TG-ops pack (N/A on customer web)

Constants: `TG_OPS_CAPS`.

| Key | Surface | Web customer | Telegram | Status |
|-----|---------|--------------|----------|--------|
| `admin_console` | admin handlers | OFF (not in web ceiling) | role=admin | **N/A tg-ops** |
| `kitchen_ops` | kitchen/admin | OFF | admin/kitchen | **N/A tg-ops** |
| `driver_dispatch` | driver handlers | OFF | driver | **N/A tg-ops** |
| `broadcast` | admin broadcast | OFF | admin | **N/A tg-ops** |
| `delivery_chat` | Messenger + domain | OFF default | ON customer | channel-native (not ops, not web parity) |

Public web API **rejects ops impersonation** (`role=admin` / ops cap claims on lead/book bodies → 403).

---

## 5. AI / optional shared tools

| Key | Notes | Status |
|-----|-------|--------|
| `ai_customer` | Grok tools → services + mask (Tier D) | ✅ tools path; web chatbox optional later |
| `referrals` / `reviews` | Shared when product uses | mask-gated shared |

---

## 6. Exit checklist (epic)

- [x] **A** Capability catalog + default masks + matrix + tests  
- [x] **B** Commerce via `cart` / `checkout` / `order_query` on both adapters  
- [x] **C** Tickets + identity edge + Messenger customer/AI pings  
- [x] **D** Grok tools → services + capability filter + Messenger  
- [x] **E** Web-only + TG-ops intentional non-parity enforced  
- [x] **F** This scorecard + PR gate + machine tests  
- [x] No new handler→domain commerce shortcuts (R1) for shared caps  
- [x] Web lead/book **not** reimplemented as Telegram FSM for parity  

---

## 7. PR gate (F2)

Every PR that adds or changes a **customer-facing feature** must answer in the PR template:

1. **Service?** Which `bot/services/*` or `bot/platform/*` owns the business rule?  
2. **Capability key?** Existing `CAPABILITY_KEYS` row or justified new key + matrix update?  
3. **Adapters?** Web / Telegram / both — and mask defaults?  
4. **Non-parity?** If web-only or tg-ops, mark N/A — **do not** clone the other surface.  
5. **Tests?** Unit test at service boundary and/or mask enforcement.

**Reject:** business logic only in Telegram handlers · second messaging channel before this freeze · “parity” by cloning lead forms into Telegram.

---

## 8. Verification commands

```bash
# Tier E+F + platform + prior CARD-40 slices
python -m pytest tests/unit/platform/test_card40ef_nonparity.py \
  tests/unit/platform/test_capabilities_media.py \
  tests/unit/ai/test_customer_card40d.py \
  tests/unit/services/test_tickets_parity_card40c.py \
  tests/unit/services/test_commerce_parity_card40b.py \
  -q --no-cov
```

---

## 9. One-line law

> Web and Telegram share every business capability both should have; masks deliberately omit the rest — especially web lead/booking on Telegram and ops consoles on web customers.
