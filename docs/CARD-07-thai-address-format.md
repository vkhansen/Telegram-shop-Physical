# Card 7: Thai Address Format Fields

**Phase:** 2 — Thailand Localization
**Priority:** Medium
**Effort:** Low (2-3 hours)
**Dependencies:** Card 2 (GPS is primary, this is supplementary)

---

## Why

Thai addresses follow a specific format: House no. → Soi → Road → Sub-district (Khwaeng) → District (Khet) → Province → Postal code. While GPS (Card 2) is the primary delivery method, structured address fields help riders with last-mile navigation and create proper receipts.

## Scope

- Extend CustomerInfo and Order with structured Thai address fields (JSON column)
- Optional structured input during checkout (GPS is primary)
- Display formatted Thai address in orders and CLI

## Files to Modify

| File | Changes |
|------|---------|
| `bot/database/models/main.py` | Add `address_structured` (JSON) to `CustomerInfo` and `Order` |
| `bot/handlers/user/order_handler.py` | After free-text address: optionally parse or ask for structured fields. Keep simple. |
| `bot_cli.py` | Format Thai address in order display |
| `bot/i18n/strings.py` | Thai address field labels |

## Implementation Details

### JSON Column (not separate columns — simpler, flexible)
```python
address_structured = Column(JSON, nullable=True)
# Example value:
# {
#   "house": "123/45",
#   "soi": "สุขุมวิท 23",
#   "road": "ถ.สุขุมวิท",
#   "subdistrict": "คลองเตยเหนือ",
#   "district": "วัฒนา",
#   "province": "กรุงเทพมหานคร",
#   "postal_code": "10110"
# }
```

### Checkout Flow (simple approach)
- Keep single text field for address (current behavior)
- GPS location is primary (Card 2)
- Structured fields are optional enhancement for receipt formatting
- Can be populated from Google Maps reverse geocoding (future)

## Acceptance Criteria

- [ ] JSON address field available on Order and CustomerInfo
- [ ] Free-text address still works (backward compatible)
- [ ] Structured address displayed in formatted Thai style
- [ ] GPS coordinates remain primary delivery method

## Test Plan

| Test File | Tests | What to Assert |
|-----------|-------|----------------|
| `tests/unit/database/test_models.py` | `test_order_address_structured_json` | JSON column stores/retrieves Thai address dict correctly |
| | `test_customer_info_address_structured` | CustomerInfo saves structured address for reuse |
| `tests/unit/utils/test_validators.py` | `test_validate_thai_address_schema` | Validate required keys: house, soi, road, subdistrict, district, province, postal_code |
| | `test_validate_postal_code_format` | Thai postal codes are 5 digits |
