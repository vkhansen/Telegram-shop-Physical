# Card 16: LINE Messaging API Integration (Tier 3)

## Implementation Status

> **✅ DONE (code)** | `██████████████████░░` | Foundation + Flex + QR host + Redis sessions + multi-OA map (2026-07-17). Residual: live LINE OA credentials / production HTTPS base (ops).

**Tier:** T3 — Additional channels  
**Phase:** M3 — Multi-Platform Growth  
**Priority:** Medium  
**Dependencies:** CARD-29–32 ✅ · CARD-40 freeze ✅ · [CARD-34](CARD-34-conversation-workflow-specifications.md) LINE package accepted  

**Plan:** [`MULTI-CHANNEL-TIERED-PLAN.md`](../later/MULTI-CHANNEL-TIERED-PLAN.md)  
**Flow package:** [`docs/Specifications/flows/PACKAGE-line.md`](../Specifications/flows/PACKAGE-line.md)

---

## Why

LINE is the dominant messaging platform in Thailand. Reuses Messenger, identities, capability masks, and `bot/services/*`. Admin/kitchen/drivers stay on **Telegram**.

---

## Architecture

```text
LINE user ──webhook──▶ LineAdapter
                          │ destination → brand (OA map)
                          │ resolve identity (CARD-30)
                          │ capability check (CARD-31)
                          │ session memory|Redis
                          ▼
                     services (CARD-32)
                          ▼
              LineMessenger (text / Flex / image QR)
```

Flag: `LINE_CHANNEL_ENABLED` (default **false**).

---

## Feature mask

| Feature | On LINE? |
|---------|----------|
| Browse / cart / checkout | Yes (Flex menu) |
| Cash / PromptPay (hosted QR image) | Yes |
| Order status / tickets | Yes |
| Live location / delivery chat | **No** |
| Admin / kitchen / driver | **No** |

---

## Code map

| Path | Role |
|------|------|
| `bot/channels/line/config.py` | Env + `LINE_OA_BRAND_MAP` |
| `bot/channels/line/signature.py` | HMAC signature |
| `bot/channels/line/webhook.py` | POST + destination brand |
| `bot/channels/line/adapter.py` | Intents → services |
| `bot/channels/line/messenger.py` | Reply/push + Flex |
| `bot/channels/line/renderer.py` | Text, quick reply, Flex |
| `bot/channels/line/session.py` | Memory + Redis sessions |
| `bot/channels/line/qr_host.py` | PromptPay PNG cache + public URL |
| `bot/web/public_api.py` | `GET /media/line-qr/{token}.png` |
| `tests/unit/channels/test_line_card16.py` | Unit suite |

---

## Config

```bash
LINE_CHANNEL_ENABLED=false
LINE_CHANNEL_ACCESS_TOKEN=
LINE_CHANNEL_SECRET=
LINE_WEBHOOK_PATH=/webhooks/line
LINE_DEFAULT_BRAND_ID=1
LINE_OA_BRAND_MAP=UoaBotId1:1,UoaBotId2:2
LINE_SESSION_BACKEND=memory   # or redis
LINE_USE_FLEX=true
PUBLIC_MEDIA_BASE_URL=https://your.public.host   # required for LINE image QR in prod
```

Webhook: `https://<host>/webhooks/line` · Header `X-Line-Signature`.

---

## Exit criteria

- [x] Foundation cards 29–32 done  
- [x] Flag-off: no Telegram impact  
- [x] Masked shop path via services  
- [x] Flex welcome/menu/order/payment  
- [x] PromptPay QR image host (`/media/line-qr/…`)  
- [x] Multi-OA brand map (`destination` + `LINE_OA_BRAND_MAP`)  
- [x] Redis session backend option  
- [x] Suite green (`test_line_card16.py`)  
- [ ] **Ops:** Live LINE channel secret/token + public HTTPS base for QR  

---

## Related

- [CARD-34](CARD-34-conversation-workflow-specifications.md) · [PACKAGE-line](../Specifications/flows/PACKAGE-line.md)  
- [CARD-33](../later/CARD-33-instagram-messaging-channel.md) · [CARD-40](../done/CARD-40-web-telegram-abstracted-feature-parity.md)  
