# LINE package (CARD-16)

> Status: **accepted** for gating · 2026-07-17

## In

C-01, C-04, C-05 (`LINE_DEFAULT_BRAND_ID` / `LINE_OA_BRAND_MAP`), C-06 (Flex menu), C-08 basic, C-10–C-14 (phone/address text; PromptPay QR host), C-17, C-18, C-22

## Out

Same as Instagram for ops/GPS/crypto/referrals.

## Config

```bash
LINE_CHANNEL_ENABLED=false
LINE_CHANNEL_ACCESS_TOKEN=
LINE_CHANNEL_SECRET=
LINE_DEFAULT_BRAND_ID=
LINE_OA_BRAND_MAP=UoaBotId1:1,UoaBotId2:2
LINE_SESSION_BACKEND=memory   # or redis
LINE_USE_FLEX=true
PUBLIC_MEDIA_BASE_URL=https://your.public.host
```

## Code

`bot/channels/line/*` · webhook `/webhooks/line` · QR `/media/line-qr/{token}.png`
