# Card 16: LINE Messaging API Integration (Tier 3)

## Implementation Status

> **~55% Complete** | `███████████░░░░░░░░░` | Foundation 2026-07-17 — webhook, identity, masked shop FSM, Messenger, router. Live LINE credentials + Flex polish open.

**Tier:** T3 — Additional channels (after Instagram pattern)  
**Phase:** M3 — Multi-Platform Growth  
**Priority:** Medium  
**Effort:** High (5–8 days) after foundation — **~foundation day landed**  
**Dependencies:**  
- CARD-29–32 ✅ · CARD-40 freeze ✅ · CARD-33 pattern ✅  
- [CARD-34](CARD-34-conversation-workflow-specifications.md) flow docs still soft  

**Plan:** [`MULTI-CHANNEL-TIERED-PLAN.md`](MULTI-CHANNEL-TIERED-PLAN.md)

---

## Why

LINE is the dominant messaging platform in Thailand. After Telegram (primary) and Instagram (Phase 2), LINE reuses the same:

- `Messenger` port + `messenger_router`  
- `user_identities` / `ensure_line_user`  
- `features_for("line", "customer")`  
- `bot/services/*` cart / checkout / orders / tickets  

Admin, kitchen, riders, and drivers stay on **Telegram**.

---

## Architecture (landed)

```text
LINE user ──webhook──▶ LineAdapter
                          │ resolve identity (CARD-30)
                          │ capability check (CARD-31)
                          ▼
                     services (CARD-32)
                          ▼
              LineMessenger reply/push + registry
```

Flag: `LINE_CHANNEL_ENABLED` (default **false**).

---

## Feature mask (enforced)

| Feature | On LINE? |
|---------|----------|
| Browse / cart / checkout | Yes |
| Cash / PromptPay | Yes |
| Order status / tickets | Yes |
| Live location / delivery chat | **No** |
| Admin / kitchen / driver | **No** |

---

## Code map

| Path | Role |
|------|------|
| `bot/channels/line/config.py` | Env flag + tokens |
| `bot/channels/line/signature.py` | `X-Line-Signature` HMAC |
| `bot/channels/line/webhook.py` | POST receive + GET health |
| `bot/channels/line/adapter.py` | Intents → services |
| `bot/channels/line/messenger.py` | Reply / push API |
| `bot/channels/line/renderer.py` | Text + quick replies / postback |
| `bot/channels/line/session.py` | Per-userId FSM |
| `bot/platform/identity.py` | `ensure_line_user` |
| `tests/unit/channels/test_line_card16.py` | Unit suite |

---

## Config

```bash
LINE_CHANNEL_ENABLED=false
LINE_CHANNEL_ACCESS_TOKEN=
LINE_CHANNEL_SECRET=
LINE_WEBHOOK_PATH=/webhooks/line
LINE_DEFAULT_BRAND_ID=1
# Optional: LINE_API_BASE=https://api.line.me
```

Webhook URL (monitoring host): `https://<host>/webhooks/line`  
Header: `X-Line-Signature` verified with channel secret.

---

## Exit criteria

- [x] Foundation cards 29–32 done  
- [x] Instagram pattern reused  
- [x] Flag-off: no Telegram impact  
- [x] Flag-on path: LINE customer can place masked cash/PromptPay order via services (needs tokens + brand id)  
- [x] `can("line", …)` enforced; no ops surfaces  
- [x] Suite green (`test_line_card16.py`)  
- [ ] Flex Message rich menus / image QR host polish  
- [ ] Multi-OA multi-brand map  
- [ ] Redis session for multi-worker  

---

## Effort remaining

| Task | Days |
|------|------|
| Flex UI + QR image host | 1–2 |
| Multi-brand OA mapping | 0.5–1 |
| Redis sessions + ops docs | 0.5 |
| Meta/LINE App production | ops |

---

## Related

- Tier plan: [MULTI-CHANNEL-TIERED-PLAN.md](MULTI-CHANNEL-TIERED-PLAN.md)  
- Phase 2: [CARD-33](CARD-33-instagram-messaging-channel.md)  
- Parity freeze: [CARD-40](CARD-40-web-telegram-abstracted-feature-parity.md)  
