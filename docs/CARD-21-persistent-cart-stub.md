# CARD-21: Persistent Cart Stub on Menu Navigation

## Status: Planned

## Problem

When a customer adds items to their cart, there is **no visible indicator** on subsequent menu screens. The cart exists silently in the background, forcing users to navigate back through multiple menus to find and manage it. This creates friction:

- Users forget they have items in cart
- No context about which brand/store they're shopping from
- Switching brands silently orphans cart items
- Abandoned carts persist indefinitely with no cleanup

## Specification

### 1. Cart Stub Banner on Every Menu Refresh

Once a user has **at least one item** in their `ShoppingCart`, every menu message edit/send must prepend a **cart stub** — a compact, single-line summary above the normal menu content.

**Stub format:**
```
🛒 [BrandName] · [StoreName] · ฿[Total]
```

Example:
```
🛒 SomChai · Silom Branch · ฿450
```

**Where it appears:**
- Brand picker (if cart already has items from another brand — see section 3)
- Store/branch selector
- Category list
- Item list (paginated)
- Item detail view
- Modifier selection screens
- Any menu refresh via `safe_edit_text()` or `send_or_edit()`

**Where it does NOT appear:**
- Main menu (`/start`)
- Cart view itself (redundant)
- Checkout flow (already cart-aware)
- Admin screens
- Profile, rules, privacy, tickets screens

### 2. Flash Animation on Item Add

When an item is successfully added to cart, the stub should **briefly flash** the added item before settling to the summary view:

**Step 1 — Flash (shown for ~1.5s):**
```
🛒 ✨ Added: [ItemName] x[Qty] — ฿[ItemTotal]
```

**Step 2 — Settle to standard stub:**
```
🛒 [BrandName] · [StoreName] · ฿[NewTotal]
```

Implementation: Two sequential `safe_edit_text()` calls with an `asyncio.sleep(1.5)` between them. The flash edit updates the message text; the settle edit restores the normal stub + current menu content.

### 3. Brand Switching — Save or Delete Prompt

**Trigger:** User taps a different brand (`select_brand_{id}`) while their cart contains items from another brand.

**Behavior:** Intercept the brand selection callback and show:

```
⚠️ You have [N] items (฿[Total]) in your cart from [CurrentBrand].

Switching to [NewBrand] requires a new cart.

[ 💾 Save & Clear Cart ]  [ 🗑 Delete Cart ]  [ ↩️ Stay ]
```

- **Save & Clear Cart** — Creates a `SavedCart` record (new model, see Data Model below) with all current items serialized as JSON, then clears the active cart and proceeds to the new brand.
- **Delete Cart** — Clears the cart immediately and proceeds to the new brand.
- **Stay** — Returns to the previous brand's category listing. No changes.

Saved carts can be restored from the Profile menu (future enhancement, out of scope for this card).

### 4. Location Switching Within Same Brand

**Trigger:** User taps a different store (`select_branch_{id}`) within the same brand while cart has items.

**Behavior:** Check if all items in the current cart exist in the new store's `BranchInventory` with sufficient stock.

- **All items available** — Silently update `ShoppingCart.store_id` for all cart items to the new store. Show flash:
  ```
  🛒 📍 Switched to [NewStoreName] · ฿[Total]
  ```
- **Some items unavailable** — Show warning:
  ```
  ⚠️ [N] item(s) not available at [NewStoreName]:
  • [ItemName1]
  • [ItemName2]

  [ 🔄 Switch & Remove Unavailable ]  [ ↩️ Stay at [CurrentStore] ]
  ```

### 5. Cart Staleness & Timeout

**New field:** `ShoppingCart.expires_at` (nullable DateTime)

**Rules:**
- When the first item is added to an empty cart, set `expires_at = now + CART_TTL` (configurable, default **2 hours**)
- Each subsequent add-to-cart **resets** the timer: `expires_at = now + CART_TTL`
- Viewing the cart resets the timer
- Starting checkout clears `expires_at` (order takes over with its own `reserved_until`)

**Enforcement — Two layers:**

1. **Lazy check:** Before any cart read (`get_cart_items`, `calculate_cart_total`, cart stub generation), if `expires_at < now`, auto-clear the cart and return empty. Show a one-time notice:
   ```
   🕐 Your cart expired after [TTL] of inactivity and has been cleared.
   ```

2. **Background cleanup (optional):** Periodic task that bulk-deletes expired carts. Not required for MVP — lazy check is sufficient.

### 6. Cart Stub Visibility Rules Summary

| Condition | Stub Visible? | Content |
|-----------|:---:|---------|
| Cart empty | No | Normal menu only |
| Cart has items, browsing same brand | Yes | Brand · Store · Total |
| Cart has items, viewing different brand | Yes | Brand · Store · Total (acts as reminder) |
| Item just added | Yes | Flash item name, then settle to summary |
| Cart expired | No | One-time expiry notice shown |
| After checkout complete | No | Cart cleared |
| After explicit cart clear/delete | No | Cart cleared |

## Data Model Changes

### Modify: `ShoppingCart`
```python
# Add to ShoppingCart model
expires_at = Column(DateTime(timezone=True), nullable=True, index=True)
```

### New: `SavedCart` (for brand-switch save)
```python
class SavedCart(Base):
    __tablename__ = "saved_carts"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    brand_id = Column(Integer, ForeignKey("brands.id"), nullable=False)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=True)
    items_json = Column(JSON, nullable=False)  # Serialized cart items + modifiers
    original_total = Column(Numeric(12, 2), nullable=False)
    saved_at = Column(DateTime(timezone=True), server_default=func.now())
```

## Implementation Plan

### Phase 1: Cart Stub Infrastructure
1. Create `build_cart_stub(user_id, session)` utility in `bot/utils/cart_stub.py`
   - Fetches cart items, brand name, store name, total
   - Returns formatted stub string or empty string if cart is empty
   - Handles expired cart detection and cleanup
2. Create `inject_cart_stub(text, stub)` helper that prepends stub + separator to menu text
3. Modify `safe_edit_text()` in `message_utils.py` to accept optional `cart_stub` param

### Phase 2: Hook Into Navigation
4. Update `shop_and_goods.py` handlers to call `build_cart_stub()` and prepend to every menu message:
   - `show_categories()`
   - `show_goods_page()` / lazy paginator renders
   - `show_item_info()`
   - Brand picker, store selector
5. Update modifier selection screens in `cart_handler.py`

### Phase 3: Item Add Flash
6. In `add_to_cart` success path, perform two-step edit: flash → settle
7. Ensure flash doesn't break modifier flow or pagination state

### Phase 4: Brand Switch Guard
8. Add intercept in `select_brand` handler — check if cart has items from different brand
9. Implement save/delete/stay callback handlers
10. Add `SavedCart` model + migration

### Phase 5: Location Switch Logic
11. Add intercept in `select_branch` handler — check cart item availability at new store
12. Implement silent switch vs. unavailable-items prompt
13. Bulk-update `store_id` on cart items

### Phase 6: Cart Expiry
14. Add `expires_at` column + migration
15. Update `add_to_cart()` to set/reset `expires_at`
16. Add lazy expiry check in `get_cart_items()` and `build_cart_stub()`
17. Add config `CART_TTL_MINUTES` to env/config (default 120)

## Files to Modify

| File | Changes |
|------|---------|
| `bot/database/models/main.py` | Add `expires_at` to ShoppingCart, add `SavedCart` model |
| `bot/database/methods/create.py` | Set/reset `expires_at` on add_to_cart |
| `bot/database/methods/read.py` | Expiry check in `get_cart_items()`, new `get_cart_stub_data()` |
| `bot/database/methods/delete.py` | Expire-and-clear logic |
| `bot/utils/cart_stub.py` | **New** — `build_cart_stub()`, `inject_cart_stub()` |
| `bot/utils/message_utils.py` | Optional stub injection in `safe_edit_text()` |
| `bot/handlers/user/shop_and_goods.py` | Prepend stub to all menu edits |
| `bot/handlers/user/cart_handler.py` | Flash animation on add, stub on modifier screens |
| `bot/handlers/user/store_selection.py` | Brand switch guard, location switch logic |
| `bot/keyboards/inline.py` | Save/Delete/Stay keyboard for brand switch prompt |
| `bot/states/shop_state.py` | New state for brand-switch confirmation if needed |
| `alembic/versions/xxx_cart_stub.py` | Migration for `expires_at` + `saved_carts` table |

## Config

| Env Variable | Default | Description |
|---|---|---|
| `CART_TTL_MINUTES` | `120` | Minutes before an idle cart expires |
| `CART_FLASH_SECONDS` | `1.5` | Duration of "item added" flash display |

## Edge Cases

- **Race condition on flash:** If user taps another button during the 1.5s flash sleep, the settle edit may conflict. Mitigation: wrap settle edit in try/except and skip if message was already changed.
- **Multiple tabs/devices:** Telegram syncs state, so cart stub will appear on next interaction regardless of device.
- **Cart with deleted items:** If a `Goods` item is deleted by admin while in cart, `build_cart_stub()` should handle missing joins gracefully (skip item, show reduced total).
- **Brand with single store:** Skip location switch logic entirely — no prompt needed.
- **Empty cart after expiry during modifier flow:** If cart expires mid-modifier-selection, the new item add should still succeed (it creates a fresh cart with new `expires_at`).
