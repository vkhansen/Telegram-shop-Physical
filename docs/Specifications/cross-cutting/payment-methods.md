# Payment methods

> Spec status: `accepted` · Mode: `as-built` · CARD-34
> Services: `bot/services/checkout.py` · PromptPay: `bot/payments/promptpay.py`

## Methods

| Method | Capability | Surfaces |
|--------|------------|----------|
| Cash / COD | `payment_cash` | TG · LINE/IG simplified · web mode-gated |
| PromptPay QR + slip | `payment_promptpay` | TG full · LINE hosted QR · IG · web QR |
| Crypto | `payment_crypto` + flags | **Telegram primary**; LINE/IG off v1 |

## Shared rules

1. Checkout service creates pending order + reserves inventory.
2. CARD-23: no DB session across network I/O.
3. CARD-24: dup-slip reject + refund audit trail.
4. Resolve PromptPay target: store → brand → global.

## LINE QR host

PNG cached and served at `/media/line-qr/{token}.png` (needs `PUBLIC_MEDIA_BASE_URL` HTTPS in prod).
