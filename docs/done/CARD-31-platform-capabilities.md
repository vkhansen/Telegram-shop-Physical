# Card 31: Platform Capabilities & Feature Mask

## Implementation Status

> **✅ DONE** | `████████████████████` | Platform×role matrix + `features_for`/`can` in `bot/platform/capabilities.py` (2026-07-17). Residual: more TG handler mask churn optional. Moved to `docs/done/`.

**Tier:** T0 — Multi-Channel Foundation  
**Phase:** M3 — Multi-Platform Growth  
**Priority:** High (masks are law for every adapter)  
**Effort:** Low (0.5–1 day remaining)  
**Dependencies:** Align with [UNIFIED-BACKEND-CHANNEL-INTERFACE](../Specifications/UNIFIED-BACKEND-CHANNEL-INTERFACE.md)  
**Plan:** [`MULTI-CHANNEL-TIERED-PLAN.md`](../later/MULTI-CHANNEL-TIERED-PLAN.md)  
**Code (partial):** `bot/platform/capabilities.py`, `bot/platform/channels.py` · public brand DTO `capabilities` / `channels`

---

## Why

Without an explicit capability matrix, secondary channels (Instagram first) tend to grow toward full Telegram parity — live location, admin console, dispatch — which those platforms cannot support cleanly.

This card defines **what each platform may expose**, intersected with **role privilege**, so CARD-33 and later channels implement a **masked subset** by policy.

---

## Scope

**Prefer extending existing module (do not invent a second matrix):**

```
bot/platform/capabilities.py   # already: resolve_capabilities(brand, channel)
bot/platform/channels.py
```

Optional legacy path name from original design (merge, don’t duplicate):

```
bot/ports/capabilities.py  → re-export from bot.platform.capabilities
```

```python
Platform = Literal["telegram", "instagram", "line", "whatsapp", "web"]

PLATFORM_CAPS: dict[str, frozenset[str]] = {
    "telegram": frozenset({
        "shop_browse", "cart", "modifiers_full", "checkout",
        "location_once", "location_live", "delivery_chat",
        "payment_promptpay", "payment_crypto", "payment_cash",
        "order_status", "tickets", "ai_customer",
        "admin_console", "kitchen_ops", "driver_dispatch",
        "broadcast", "referrals", "reviews",
    }),
    "instagram": frozenset({
        "shop_browse_limited", "cart", "modifiers_basic", "checkout",
        "location_once",  # no location_live
        "payment_promptpay", "payment_crypto", "payment_cash",
        "order_status", "tickets",
        # intentionally no: admin_console, kitchen_ops, driver_dispatch,
        # location_live, delivery_chat, broadcast (default)
    }),
    "line": frozenset({
        "shop_browse", "cart", "modifiers_full", "checkout",
        "location_once", "payment_promptpay", "payment_crypto", "payment_cash",
        "order_status", "tickets", "ai_customer",
    }),
    "web": frozenset({
        "shop_browse", "cart", "modifiers_full", "checkout",
        "location_once", "location_live", "payment_promptpay", "payment_crypto",
        "payment_cash", "order_status", "tickets", "ai_customer", "maps_widget",
    }),
    "whatsapp": frozenset({
        "shop_browse_limited", "cart", "checkout", "location_once",
        "payment_promptpay", "payment_cash", "order_status", "tickets",
    }),
}

ROLE_FEATURES: dict[str, frozenset[str]] = {
    "customer": frozenset({
        "shop_browse", "shop_browse_limited", "cart", "modifiers_full",
        "modifiers_basic", "checkout", "location_once", "location_live",
        "delivery_chat", "payment_promptpay", "payment_crypto", "payment_cash",
        "order_status", "tickets", "ai_customer", "referrals", "reviews",
        "maps_widget",
    }),
    "admin": frozenset({"admin_console", "broadcast", "kitchen_ops"}),
    "driver": frozenset({"driver_dispatch", "location_live"}),
    "kitchen": frozenset({"kitchen_ops"}),
}

def features_for(platform: str, role: str = "customer") -> frozenset[str]:
    return PLATFORM_CAPS.get(platform, frozenset()) & ROLE_FEATURES.get(role, frozenset())

def can(platform: str, feature: str, role: str = "customer") -> bool:
    return feature in features_for(platform, role)
```

Optional: brand-level override via `BotSettings` key `channel_features_json` (later).

### Docs

- Table in `MULTI-CHANNEL-TIERED-PLAN.md` stays source of product policy; this module is the machine-readable form.
- PR checklist for channel work: new IG flow must call `can("instagram", feature)`.

### Telegram

- **No runtime enforcement required in Telegram handlers** for T0 (avoid churn).
- Enforcement is mandatory at Instagram adapter boundary (CARD-33).

---

## Tests

- `features_for("telegram", "customer")` includes live location  
- `features_for("instagram", "customer")` excludes admin / live location / driver  
- `features_for("instagram", "admin")` does not grant admin_console if admin role features ∩ IG caps is empty (or document that admin role is Telegram-only)

---

## Exit criteria

- [x] Brand + channel resolve landed (`bot/platform/capabilities`) + unit tests  
- [x] Public API exposes `capabilities` / `channels`  
- [x] Storefront gates UI via mask  
- [x] Full platform×role matrix (`PLATFORM_CAPS` ∩ `ROLE_FEATURES`) merged  
- [x] Adapter enforcement helpers (`can`, `features_for`, `cap_enabled`) + docs for CARD-33 / handlers  
- [x] Referenced from CARD-33 and tier plan ✅  
- [x] CARD-40 Tier A default channel OFF masks + parity matrix doc

---

## Effort

**0.5–1 day**
