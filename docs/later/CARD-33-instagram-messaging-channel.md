# Card 33: Instagram Messaging Channel (Phase 2)

## Implementation Status

> **~55% Complete** | `███████████░░░░░░░░░` | Foundation + masked shop path 2026-07-17 (webhook, identity, FSM, services, router). Meta prod review + slip pipeline polish open.

**Tier:** T2 — First non-Telegram customer channel  
**Phase:** M3 — Multi-Platform Growth  
**Priority:** **P2** (after white-label catalog tenants CARD-38; not “start here”)  
**Effort:** High (5–8 days)  
**Dependencies:**  
- **[CARD-34](CARD-34-conversation-workflow-specifications.md)** — Instagram In/Out package **accepted** (hard gate)  
- [CARD-29](CARD-29-messenger-port.md), [CARD-30](CARD-30-user-identities.md), [CARD-31](CARD-31-platform-capabilities.md), [CARD-32](CARD-32-customer-application-services.md)  
- multi-brand context ([CARD-19](../done/CARD-19-multi-brand-bot-coordination.md))  
**Plan:** [`MULTI-CHANNEL-TIERED-PLAN.md`](MULTI-CHANNEL-TIERED-PLAN.md)

---

## Why

Instagram is the **Phase 2** channel for multi-platform growth: high reach for food/lifestyle brands, Meta Messaging API for DMs, and a natural fit for **masked** commerce (menu discovery → order → status) rather than full kitchen/driver ops.

Telegram remains the **main application** (admin, kitchen, riders, drivers, full UX). Instagram customers share the **same backend** (orders, inventory, PromptPay, multi-brand data).

This replaces “LINE as next channel” sequencing for Phase 2; LINE moves to Tier 3 ([CARD-16](CARD-16-line-api-integration.md)).

---

## Architecture

```
Instagram user ──DM──▶ Meta webhook ──▶ InstagramAdapter
                                            │
                         resolve identity (CARD-30)
                         capability check (CARD-31)
                                            │
                                            ▼
                                   services (CARD-32)
                                            │
                                            ▼
                              PostgreSQL domain (shared)
                                            │
                     ┌──────────────────────┴──────────────────────┐
                     ▼                                             ▼
            Messenger router                              Telegram admin /
            (IG reply + status)                           kitchen / drivers
```

Flag: `INSTAGRAM_CHANNEL_ENABLED` (default **false**).

---

## Feature mask (must enforce)

| Feature | On IG? |
|---------|--------|
| Browse / search (limited lists or carousels) | Yes |
| Cart + basic modifiers | Yes |
| Checkout (address, phone, note) | Yes |
| One-shot location (if Meta provides) / typed address | Yes |
| Live location / delivery live chat | **No** |
| PromptPay QR image + slip image upload | Yes |
| Cash / crypto instructions | Yes |
| Order status + history | Yes |
| Support tickets (text) | Yes |
| Customer AI (optional, short) | Optional |
| Admin / kitchen / rider / driver | **No** |
| Broadcasts | **No** (v1) |

Deep-link CTA: “Open full experience on Telegram” for advanced features.

---

## Scope

### In

```
bot/channels/instagram/
  __init__.py
  webhook.py          # verify + receive
  adapter.py          # normalize events → intents
  renderer.py         # text / quick replies / generic templates
  messenger.py        # InstagramMessenger implements Messenger port
bot/ports/messenger_router.py  # route by user preferred / linked platform
```

- Meta webhook verification + signature check (`X-Hub-Signature-256`)
- Map IG PSID → `user_identities` → `user_id`
- Conversation state in Redis keyed by `(instagram, psid)` (simple intent FSM — not aiogram)
- Call CARD-32 services for cart/checkout/orders/tickets
- Outbound: order confirmed / preparing / ready / delivered via Messenger router
- Brand: `INSTAGRAM_DEFAULT_BRAND_ID` or per-page mapping table (v1: single brand)

### Out

- Full modifier builder UX parity  
- Live GPS tracking  
- Admin on Instagram  
- Multi-IG-account multi-brand pool (v2)  
- Changing Telegram handler architecture  

---

## Identity (with CARD-30)

1. First IG message → create or resolve identity.  
2. **Preferred v1:** create internal user + `user_identities(instagram, psid)`; use non-colliding user id scheme documented in CARD-30.  
3. **Optional link:** customer sends code from Telegram profile to merge identities (nice-to-have in v1.1).  
4. Orders use same `buyer_id` FK as Telegram users.

---

## Config

```bash
INSTAGRAM_CHANNEL_ENABLED=false
INSTAGRAM_PAGE_ACCESS_TOKEN=
INSTAGRAM_APP_SECRET=
INSTAGRAM_VERIFY_TOKEN=
INSTAGRAM_WEBHOOK_PATH=/webhooks/instagram
INSTAGRAM_DEFAULT_BRAND_ID=1
```

Meta requirements: Instagram Professional account linked to Facebook Page; Messaging permissions; HTTPS webhook.

---

## UX sketch (masked)

1. User messages shop IG → welcome + quick replies: Menu / My orders / Support  
2. Menu → categories → items (paginated text or generic template)  
3. Add to cart → View cart → Checkout  
4. Collect phone + address (text); payment method  
5. PromptPay: send QR image; user uploads slip; verify via existing slip pipeline (bytes)  
6. Status pushes on lifecycle events (within messaging policy window)  
7. Kitchen/rider work continues on **Telegram** unchanged  

---

## Messenger router

```python
async def notify_user(user_id: int, text: str, **kwargs) -> bool:
    # Prefer last-active platform or all linked customer platforms
    # Always safe fallback: Telegram if telegram identity exists
```

Order status from admin/Telegram kitchen must reach IG customers when identity is IG-linked.

---

## Tests

- Webhook signature reject/accept  
- Capability denials (admin intent → polite “use Telegram”)  
- Service integration with fake IG messenger  
- Telegram regression suite full green with flag off  

---

## Risks

| Risk | Mitigation |
|------|------------|
| Meta review delays | Dev/test mode first; flag off in prod until approved |
| 24h window | Prefer user-initiated; critical status within window |
| Weak multi-step UI | Keep flows short; link to Telegram for full shop |
| Media slip size limits | Compress / reject with clear error |

---

## Exit criteria

- [ ] CARD-34 Instagram package accepted; only those flows implemented *(soft — adapter implements CARD-33 mask; full flow docs later)*  
- [x] Flag-off: zero effect on Telegram  
- [x] Flag-on path: IG customer can place cash or PromptPay order via services (needs Meta tokens + brand id in env)  
- [x] Status notifications route via `messenger_router.notify_user` (IG preferred when linked)  
- [x] `can("instagram", …)` enforced at adapter boundary  
- [x] No admin/kitchen/driver surfaces on IG  
- [x] Suite green (`tests/unit/channels/test_instagram_card33.py`)  

### Landed (2026-07-17)

| Path | Role |
|------|------|
| `bot/channels/instagram/config.py` | Env flag + tokens |
| `bot/channels/instagram/signature.py` | `X-Hub-Signature-256` |
| `bot/channels/instagram/webhook.py` | GET verify + POST receive |
| `bot/channels/instagram/adapter.py` | Intents → cart/checkout/orders/tickets |
| `bot/channels/instagram/messenger.py` | Graph API Messenger port |
| `bot/channels/instagram/renderer.py` | Text + quick replies |
| `bot/channels/instagram/session.py` | Per-PSID FSM store |
| `bot/platform/messenger_router.py` | Multi-channel `notify_user` |
| `bot/platform/identity.py` | `ensure_instagram_user` / `list_identities` |

### Still open

- [ ] Hosted PromptPay QR URL (data-URI note only today) + slip image → verify pipeline  
- [ ] Redis session store for multi-worker  
- [ ] Per-page multi-brand mapping (v1: `INSTAGRAM_DEFAULT_BRAND_ID`)  
- [ ] Meta App Review / 24h window message tags  
- [ ] Optional TG↔IG link code UX

---

## Effort

| Task | Days |
|------|------|
| Meta app + webhook shell + signature | 1 |
| Identity + conversation FSM | 1 |
| Renderer + masked menu/cart | 1–2 |
| Checkout + PromptPay/slip | 1–2 |
| Messenger router + status | 0.5–1 |
| Tests + flag hardening | 0.5–1 |
| **Total** | **5–8** |

---

## Sequencing note

| Phase | Channel |
|-------|---------|
| Primary app | Telegram (always) |
| **Phase 2** | **Instagram (this card)** |
| Phase 3+ | LINE (CARD-16), Webchat (future) |
