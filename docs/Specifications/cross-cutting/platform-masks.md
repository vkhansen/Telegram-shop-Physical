# Platform masks (customer flows × channel)

> Spec status: `accepted` · CARD-34 / CARD-31 / CARD-40
> Code: `bot/platform/capabilities.py`

## Legend

| Mark | Meaning |
|------|---------|
| F | Full |
| S | Simplified |
| W | Web |
| — | Off |

## Matrix

| ID | Flow | TG | IG | LINE | Web |
|----|------|----|----|------|-----|
| C-01 | Start / home | F | S | S | W |
| C-02 | Language | F | — | — | — |
| C-03 | Privacy | F | — | — | compliance |
| C-04 | Help | F | S | S | FAQ |
| C-05 | Store/brand | F | S | S (OA map) | slug |
| C-06 | Browse | F | S | S Flex | catalog |
| C-07 | Search | F | — | — | UI |
| C-08 | Cart | F | S | S | API |
| C-09 | Saved carts | F | — | — | — |
| C-10–12 | Checkout profile | F | S | S | API |
| C-13 | Cash | F | S | S | mode |
| C-14 | PromptPay | F | S | S QR host | QR |
| C-15 | Crypto | F | — | — | optional |
| C-16 | Bonus | F | — | — | — |
| C-17 | Orders | F | S | S | API |
| C-18 | Status push | F | S | S | optional |
| C-19 | Delivery chat/GPS | F | — | — | — |
| C-20 | Reviews | F | — | — | — |
| C-21 | Referrals | F | — | — | — |
| C-22 | Tickets | F | S | S | OAuth portal |
| C-23 | Customer AI | F | optional | optional | optional |
| C-24 | Coupons | F | — | — | — |

## Ops / driver

All A-* and D-*: **Telegram only**.

## Instagram In package (CARD-33)

**In:** C-01, C-04, C-05(default), C-06–C-08, C-10–C-14, C-17–C-18, C-22  
**Out:** C-02, C-03, C-09, C-15–C-16, C-19–C-21, C-23–C-24, all A/D

## LINE In package (CARD-16)

**In:** same as IG plus Flex menu + hosted PromptPay QR  
**Flags:** `LINE_CHANNEL_ENABLED`, `LINE_USE_FLEX`, `LINE_SESSION_BACKEND`, `LINE_OA_BRAND_MAP`  
**Out:** ops, live GPS chat, crypto v1
