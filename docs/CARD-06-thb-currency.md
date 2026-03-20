# Card 6: THB Currency + Thai Number Formatting

**Phase:** 2 — Thailand Localization
**Priority:** Medium
**Effort:** Low (2-3 hours)
**Dependencies:** None

---

## Why

The default currency is RUB/USD. Thailand uses Thai Baht (THB). All prices, totals, receipts, and admin stats must display in THB with the correct symbol and formatting for Thai users.

## Scope

- Set THB as default currency
- Add currency formatting helper with Baht symbol
- Update all price display points
- Thai number formatting (comma separators)

## Files to Modify

| File | Changes |
|------|---------|
| `bot/config/env.py` | Change `PAY_CURRENCY` default to `"THB"` |
| `.env.example` | Update example to `PAY_CURRENCY=THB` |
| `bot/i18n/strings.py` | Update currency format strings, add `฿` symbol |
| `bot/handlers/user/order_handler.py` | Price displays use THB format |
| `bot/handlers/user/cart_handler.py` | Cart total in THB |
| `bot/handlers/user/shop_and_goods.py` | Product prices in THB |
| `bot/handlers/user/referral_system.py` | Bonus amounts in THB |
| `bot_cli.py` | All CLI price outputs in THB |
| `bot/export/customer_csv.py` | Export headers/values in THB |

## Implementation Details

### Currency Formatting Helper
```python
from decimal import Decimal

def format_thb(amount: Decimal) -> str:
    """Format amount as Thai Baht: ฿1,234.00"""
    return f"฿{amount:,.2f}"
```

### Config Change
```env
PAY_CURRENCY=THB
```

## Acceptance Criteria

- [ ] All prices display with ฿ symbol
- [ ] Comma-separated thousands (฿1,234.00)
- [ ] Cart totals, order summaries, receipts all in THB
- [ ] Admin stats and CLI in THB
- [ ] CSV exports show THB

## Test Plan

| Test File | Tests | What to Assert |
|-----------|-------|----------------|
| `tests/unit/utils/test_currency.py` | `test_format_thb_basic` | `format_thb(Decimal("1234.5"))` returns `"฿1,234.50"` |
| | `test_format_thb_zero` | `format_thb(Decimal("0"))` returns `"฿0.00"` |
| | `test_format_thb_large` | `format_thb(Decimal("1000000"))` returns `"฿1,000,000.00"` |
| | `test_format_thb_decimal_rounding` | Two decimal places always shown |
