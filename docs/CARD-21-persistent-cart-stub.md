# CARD-21: Persistent Cart Stub on Menu Navigation

## Status: Phases 2/3/6 shipped — Phases 4/5 pending

## Progress Log

### 2026-04-13 — Pass 1 (commit `c3cad02`)
Phases **2** (banner injection) + **6** (cart expiry) landed.

- `bot/utils/cart_stub.py` — `build_cart_stub`, `inject_cart_stub`, `format_cart_stub`, `format_flash_stub`, `get_cart_stub_data`, `_as_aware_utc` (tz-safe helper — SQLite strips tzinfo on `DateTime(timezone=True)` round-trip, so Python-side comparisons must normalize).
- `bot/database/methods/create.py::add_to_cart` — sets `expires_at` on new rows AND bulk-resets `expires_at` across the entire user cart on every subsequent add (one TTL governs the whole cart).
- `bot/database/methods/read.py::get_cart_items` — lazy expiry sweep: if any row's `expires_at < now`, delete the whole user cart and return `[]`. Comparison is SQL-side for backend safety.
- Banner injection at 7 menu sites: `shop_and_goods.py` (`show_brand_categories`, `navigate_categories`, `items_list_callback_handler`, `navigate_goods`, `item_info_callback_handler` — caption branch covers both photo and text paths) and `store_selection.py` (`brand_picker`, `_select_branch_or_proceed`).
- **18 regression tests** in `tests/unit/test_cart_stub_card21.py`.
- `cart_stub.py` coverage: 0% → 85%.

### 2026-04-13 — Pass 2 Phase 3 (commit `5a11da0`)
Phase **3** (flash animation on add) landed.

- `bot/utils/cart_stub.py::flash_cart_added` — two-step async helper: flash line → `asyncio.sleep(CART_FLASH_SECONDS)` → settle. Wraps settle edit in try/except so a concurrent tap can't crash the handler.
- `cart_handler.py::add_to_cart_handler` (no-modifier direct add) — runs flash only for text messages. Photo item-detail screens (`item.image_file_id` set) fall back to the existing `call.answer` toast because `edit_text` can't update a caption. Settle text re-injects `build_cart_stub(user_id)` into the current message text with the same reply markup.
- `cart_handler.py::_finish_modifier_selection` — replaces the static `edit_text` success screen with a flash that settles to the stub-injected success text + `back_to_menu` keyboard. Uses `calculate_item_price` for the modifier-priced total.
- **3 new async tests** in `TestFlashCartAdded`: two-step edit + sleep + settle, settle-error swallow, flash-error swallow. Monkeypatches `bot.utils.message_utils.safe_edit_text` and `bot.utils.cart_stub.asyncio.sleep`.
- Full suite: **1275 passing**, overall coverage **44.01%**, `cart_stub.py` at **92%**.

### Still pending
- **Phase 4** — brand-switch Save/Delete/Stay (see Phase 4 Implementation Notes below).
- **Phase 5** — store-switch availability check (see Phase 5 Implementation Notes below).
- Handler-level tests for `shop_and_goods.py` (still 10%) and `store_selection.py` (still 21%) — need the fake-Telegram harness from Session C.

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

## Phase 4 Implementation Notes (pending — brand-switch Save/Delete/Stay)

**Everything needed already exists:**
- `SavedCart` model — `bot/database/models/main.py:1079-1103` (id, user_id, brand_id, store_id, items_json, original_total, saved_at)
- `EnvKeys.CART_TTL_MINUTES` + `CART_FLASH_SECONDS` — `bot/config/env.py:94-95`
- Cart banner already injected into `brand_picker` (so the user already sees the stub when switching)

**Intercept point:** `bot/handlers/user/store_selection.py::select_brand` — the handler that fires on `select_brand_{id}` callbacks. Look for the line that commits the brand via `state.update_data(...)` (around line 73–83 per the resume memo). Before that commit, call `get_cart_stub_data(user_id)` and compare `data['brand_id']` against the incoming brand id. If different and nonzero items, show the confirmation prompt instead of proceeding.

**Bug-hunting rule reminder:** when you add the cart-has-items check in `select_brand`, grep every other handler that can cross brands (pagination back-links, deep-links, `/start` with a brand arg, admin impersonation) and apply the same guard — otherwise the brand switch silently orphans items through a side path.

**New FSM state:** add `confirming_brand_switch` to `bot/states/shop_state.py::ShopStates`. Store `pending_brand_id` in FSM data so the save/delete/stay callbacks know where to go after confirmation.

**New keyboard:** `brand_switch_confirm_keyboard(pending_brand_id)` in `bot/keyboards/inline.py` with three buttons — callback data `save_cart:{brand_id}`, `delete_cart:{brand_id}`, `stay_brand`. Use `:` separator consistent with `mod_sel:` pattern.

**New callback handlers** (in `store_selection.py` or `cart_handler.py`):
1. `save_cart:{brand_id}` — serialize current cart to `items_json` (include: item_name, quantity, selected_modifiers, unit_price at save time), compute `original_total`, insert a `SavedCart` row, clear `ShoppingCart` for this user, then call the existing brand-switch completion path with the pending brand id.
2. `delete_cart:{brand_id}` — `clear_cart(user_id)` then proceed with brand switch.
3. `stay_brand` — clear FSM state, re-render the previous brand's category listing (call `show_brand_categories` with the old brand id from `get_cart_stub_data`).

**Serialization schema for `items_json`:** keep it forward-compatible — `{"items": [{"name": ..., "quantity": ..., "modifiers": {...}, "unit_price": "..."}]}`. Store prices as strings to avoid Decimal→JSON float lossiness. Include a `"schema_version": 1` key.

**Locale strings to add** (in `locales/*.yml`):
- `shop.brand_switch.warning` — "You have {n} items (฿{total}) in your cart from {current_brand}. Switching to {new_brand} requires a new cart."
- `btn.save_cart` — "💾 Save & Clear"
- `btn.delete_cart` — "🗑 Delete Cart"
- `btn.stay` — "↩️ Stay"
- `shop.brand_switch.saved` — "Cart saved. You can restore it from Profile later."
- `shop.brand_switch.deleted` — "Cart cleared."

**Tests to add** (extend `test_cart_stub_card21.py` or new `test_brand_switch_card21.py`):
- Switching within the same brand skips the prompt entirely (no FSM transition).
- Empty cart + brand switch skips the prompt.
- Save path creates a `SavedCart` row with correct `items_json` and `original_total`, then empties the `ShoppingCart`.
- Delete path clears the cart without creating a `SavedCart`.
- Stay path leaves both the cart and the current brand untouched.
- Bug-hunting: multi-item modifier carts serialize correctly (dict selection, list multi-select).

**Out of scope:** restoring a `SavedCart` from the Profile menu — explicitly noted in spec section 3 as future enhancement.

## Phase 5 Implementation Notes (pending — store-switch availability)

**Intercept point:** `bot/handlers/user/store_selection.py::select_branch` (or `_select_branch_or_proceed`) — fires on `select_branch_{id}`. The handler already has `brand_id` in context; same-brand is guaranteed when this runs (brand switch is Phase 4's concern).

**Check logic:**
```python
cart_items = await get_cart_items(user_id)
if not cart_items or cart_items[0]['store_id'] == new_store_id:
    # Silent proceed — no cart or already at this store
    ...
else:
    # Query BranchInventory for each item at new_store_id
    # BranchInventory model is at bot/database/models/main.py (search for it)
    unavailable = []
    for ci in cart_items:
        inv = session.query(BranchInventory).filter_by(
            store_id=new_store_id, goods_name=ci['item_name']
        ).first()
        if not inv or inv.stock_quantity < ci['quantity']:
            # 'prepared' items (stock_quantity=0 = unlimited per CLAUDE.md)
            # must not be flagged — check item_type first
            good = session.query(Goods).filter_by(name=ci['item_name']).first()
            if good and good.item_type == 'prepared':
                continue  # unlimited stock — always available
            unavailable.append(ci['item_name'])
```

**CRITICAL per CLAUDE.md:** `prepared` items have `stock_quantity=0` meaning **unlimited**, so they must never appear in the unavailable list. `product` items are inventory-tracked and need the real check. Miss this and every prepared-items cart will show a false unavailability warning on every store switch.

**Two branches:**
1. **All available** — bulk-update `ShoppingCart.store_id` for this user to `new_store_id`, then show a flash using `flash_cart_added`-style two-step edit: flash `"🛒 📍 Switched to {store_name} · ฿{total}"` → settle to the normal store selection result screen. Consider generalizing `flash_cart_added` into `flash_stub_line(message, flash_text, settle_text, settle_markup)` — the current helper is item-specific but the mechanics are identical.
2. **Some unavailable** — render warning with `shop.store_switch.unavailable` locale string listing item names, with buttons `switch_and_remove:{store_id}` and `stay_store`. On `switch_and_remove`: delete unavailable rows from `ShoppingCart`, bulk-update `store_id` on the rest, then render the same flash.

**Bug-hunting rule reminder:** the `prepared` vs `product` distinction matters everywhere stock is checked. Grep for `stock_quantity` comparisons across the codebase when touching this — any `stock_quantity < X` check that doesn't first exclude `item_type == 'prepared'` is the same bug.

**New FSM state:** `confirming_store_switch` in `ShopStates`, storing `pending_store_id` + `unavailable_items` list.

**New keyboard:** `store_switch_confirm_keyboard(pending_store_id)` in `inline.py`.

**Locale strings to add:**
- `shop.store_switch.unavailable` — "⚠️ {n} item(s) not available at {store_name}:\n{items}"
- `shop.store_switch.flash` — "🛒 📍 Switched to {store_name} · ฿{total}"
- `btn.switch_and_remove` — "🔄 Switch & Remove Unavailable"
- `btn.stay_store` — "↩️ Stay at {store_name}"

**Edge case:** single-store brand — skip the whole flow (no-op). Check `len(stores) == 1` before even showing the store picker.

**Tests to add:**
- Same-store reselect is a no-op (no DB writes).
- All-available path bulk-updates `store_id` on every cart row for that user.
- Unavailable-items path lists only `product`-type items with insufficient stock; `prepared` items never appear.
- Switch-and-remove deletes exactly the unavailable rows, leaves the rest, and sets their `store_id` to the new store.
- Stay-store leaves cart untouched.

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
