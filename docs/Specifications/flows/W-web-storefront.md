# W-01…W-03: Web storefront

> Spec status: `accepted` / linked · See [WEB-INSTAGRAM-STYLE-STOREFRONT.md](../WEB-INSTAGRAM-STYLE-STOREFRONT.md)  
> Commerce parity: same spine as Telegram **C-06 → C-08 → C-11–C-14 → C-17** via `commerce_api` + services.

| ID | Flow | Status |
|----|------|--------|
| W-01 | Brand → Store → Menu → Item | catalog API + storefront |
| W-02 | Shared item deep link | `/{brand}/{store}/i/{item}` |
| W-03 | Unavailable item | badges + no add-to-cart |
| W-04 | Cart (C-08) | `/{brand}/cart` → cart service |
| W-05 | Checkout (C-11–C-14) | `/{brand}/checkout` → delivery + cash/PromptPay |
| W-06 | Orders (C-17) | `/{brand}/orders` · `/{brand}/orders/{code}` |

Implementation: CARD-38 storefront + CARD-40 commerce API · `apps/storefront` · Playwright `e2e/commerce.spec.ts`.
