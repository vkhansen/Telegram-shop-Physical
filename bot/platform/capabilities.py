"""Brand feature capabilities + per-channel masks + platform×role matrix.

Capabilities are the single switchboard for UI, public API modules, and
messaging surfaces. Resolution law (CARD-31 + CARD-40)::

    effective_caps(brand, channel, role) =
        PLATFORM_CAPS[channel]
      ∩ ROLE_FEATURES[role]
      ∩ brand base (commerce_mode · modules · age_gate)
      ∩ CHANNEL_DEFAULT_OFF[channel]   # then brand channel.mask may re-enable
      ∩ brand channel.mask

Operators configure:

  web_profile.modules      — coarse show_* toggles (legacy + friendly)
  web_profile.channels     — per-channel enable + capability mask
  brand.commerce_mode      — full_store | portfolio | hybrid
  brand.age_gate_enabled   — age gate flag

Public clients should prefer the resolved ``capabilities`` object on brand DTOs
rather than re-interpreting modules / commerce_mode themselves.

Adapter enforcement (CARD-33 / handlers)::

    from bot.platform.capabilities import can, cap_enabled, resolve_capabilities

    if not can("instagram", "checkout", role="customer"):
        ...
    if not cap_enabled(caps, "leads"):
        ...
"""

from __future__ import annotations

from typing import Any

from bot.platform.channels import DEFAULT_CHANNEL_ENABLED, normalize_channel
from bot.services.web_profile import normalize_commerce_mode

# ---------------------------------------------------------------------------
# Unified capability catalog (CARD-31 + CARD-40)
# Additive only — never rename without a migration path.
# ---------------------------------------------------------------------------

CAPABILITY_KEYS: tuple[str, ...] = (
    # Shared commerce
    "catalog",
    "item_detail",
    "cart",
    "modifiers_full",
    "modifiers_basic",
    "checkout",
    "portfolio",
    "payment_promptpay",
    "payment_crypto",
    "payment_cash",
    "order_status",
    "media",
    # Support / identity / AI
    "tickets",
    "auth",
    "ai_customer",
    "referrals",
    "reviews",
    # Location / delivery (channel-native)
    "location_once",
    "location_live",
    "delivery_chat",
    "maps_widget",
    # Web funnel / marketing
    "leads",
    "booking",
    "age_gate",
    "about",
    "faq",
    "benefits",
    "featured",
    "ticker",
    "contact",
    "social_links",
    # Ops (Telegram-first; not web customer)
    "admin_console",
    "kitchen_ops",
    "driver_dispatch",
    "broadcast",
)

# Legacy / CARD-31 names → canonical keys (accepted by can / features_for checks)
CAPABILITY_ALIASES: dict[str, str] = {
    "shop_browse": "catalog",
    "shop_browse_limited": "catalog",
}

# modules key → capability (DRY mapping from legacy web_profile.modules)
_MODULE_TO_CAP: dict[str, str] = {
    "show_about": "about",
    "show_faq": "faq",
    "show_lead_form": "leads",
    "show_booking": "booking",
    "show_benefits": "benefits",
    "show_featured": "featured",
    "show_ticker": "ticker",
    "show_tickets": "tickets",
    "show_auth": "auth",
    "show_contact": "contact",
    "show_catalog": "catalog",
}

# ---------------------------------------------------------------------------
# Platform ceiling (what the surface *can* support)
# ---------------------------------------------------------------------------

PLATFORM_CAPS: dict[str, frozenset[str]] = {
    "telegram": frozenset(
        {
            "catalog",
            "item_detail",
            "media",
            "cart",
            "modifiers_full",
            "checkout",
            "portfolio",
            "location_once",
            "location_live",
            "delivery_chat",
            "payment_promptpay",
            "payment_crypto",
            "payment_cash",
            "order_status",
            "tickets",
            "ai_customer",
            "admin_console",
            "kitchen_ops",
            "driver_dispatch",
            "broadcast",
            "referrals",
            "reviews",
            # Optional if brand re-enables via channels.telegram.mask
            "leads",
            "booking",
            "age_gate",
            "about",
            "faq",
            "benefits",
            "featured",
            "ticker",
            "contact",
            "social_links",
            # no OAuth auth adapter
        }
    ),
    "web": frozenset(
        {
            "catalog",
            "item_detail",
            "media",
            "cart",
            "modifiers_full",
            "checkout",
            "portfolio",
            "payment_promptpay",
            "payment_crypto",
            "payment_cash",
            "order_status",
            "tickets",
            "ai_customer",
            "maps_widget",
            "leads",
            "booking",
            "age_gate",
            "about",
            "faq",
            "benefits",
            "featured",
            "ticker",
            "contact",
            "social_links",
            "auth",
            "referrals",
            "reviews",
            "location_once",
            "location_live",  # optional web track
            # no admin_console / kitchen_ops / driver_dispatch / broadcast / delivery_chat
        }
    ),
    "instagram": frozenset(
        {
            "catalog",
            "item_detail",
            "media",
            "cart",
            "modifiers_basic",
            "checkout",
            "location_once",  # no location_live
            "payment_promptpay",
            "payment_crypto",
            "payment_cash",
            "order_status",
            "tickets",
            "leads",
            "booking",
            # intentionally no: admin_console, kitchen_ops, driver_dispatch,
            # location_live, delivery_chat, broadcast (default)
        }
    ),
    "line": frozenset(
        {
            "catalog",
            "item_detail",
            "media",
            "cart",
            "modifiers_full",
            "checkout",
            "location_once",
            "payment_promptpay",
            "payment_crypto",
            "payment_cash",
            "order_status",
            "tickets",
            "ai_customer",
            "leads",
            "booking",
        }
    ),
    "whatsapp": frozenset(
        {
            "catalog",
            "item_detail",
            "media",
            "cart",
            "checkout",
            "location_once",
            "payment_promptpay",
            "payment_cash",
            "order_status",
            "tickets",
            "leads",
        }
    ),
}

# ---------------------------------------------------------------------------
# Role privilege (intersected with platform)
# ---------------------------------------------------------------------------

ROLE_FEATURES: dict[str, frozenset[str]] = {
    "customer": frozenset(
        {
            "catalog",
            "item_detail",
            "media",
            "cart",
            "modifiers_full",
            "modifiers_basic",
            "checkout",
            "portfolio",
            "payment_promptpay",
            "payment_crypto",
            "payment_cash",
            "order_status",
            "tickets",
            "ai_customer",
            "referrals",
            "reviews",
            "location_once",
            "location_live",
            "delivery_chat",
            "maps_widget",
            "leads",
            "booking",
            "age_gate",
            "about",
            "faq",
            "benefits",
            "featured",
            "ticker",
            "contact",
            "social_links",
            "auth",
        }
    ),
    # Ops roles are narrow by design; multi-role callers should union features_for.
    "admin": frozenset({"admin_console", "broadcast", "kitchen_ops"}),
    "driver": frozenset({"driver_dispatch", "location_live"}),
    "kitchen": frozenset({"kitchen_ops"}),
}

# ---------------------------------------------------------------------------
# Intentional non-parity packs (CARD-40 Tier E)
# These are product policy, not debt. Tests and PR gate freeze them.
# ---------------------------------------------------------------------------

# Web funnel + marketing: default ON for web customer, OFF for TG customer.
WEB_ONLY_CAPS: frozenset[str] = frozenset(
    {
        "leads",
        "booking",
        "age_gate",
        "about",
        "faq",
        "benefits",
        "featured",
        "ticker",
        "contact",
        "social_links",
        "maps_widget",
        "auth",  # OAuth adapter is web; TG uses implicit identity
    }
)

# Ops surfaces: Telegram (or future ops web) only — never customer web parity.
TG_OPS_CAPS: frozenset[str] = frozenset(
    {
        "admin_console",
        "kitchen_ops",
        "driver_dispatch",
        "broadcast",
    }
)

# Shared commerce / support keys that *must* share services when both masks ON.
SHARED_PARITY_CAPS: frozenset[str] = frozenset(
    {
        "catalog",
        "item_detail",
        "media",
        "cart",
        "checkout",
        "payment_promptpay",
        "payment_crypto",
        "payment_cash",
        "order_status",
        "tickets",
    }
)

# ---------------------------------------------------------------------------
# Channel default OFF (CARD-40 A2) — brand channel.mask may re-enable
# within PLATFORM_CAPS × ROLE_FEATURES.
# ---------------------------------------------------------------------------

CHANNEL_DEFAULT_OFF: dict[str, frozenset[str]] = {
    # TG customer: shop + tickets + AI; no web funnel / OAuth / marketing by default
    "telegram": frozenset(
        {
            "leads",
            "booking",
            "age_gate",
            "about",
            "faq",
            "benefits",
            "featured",
            "ticker",
            "contact",
            "social_links",
            "auth",
        }
    ),
    # Web customer: ops and channel-native delivery chat stay off (platform ceiling
    # already omits most ops; keep explicit for honesty).
    "web": frozenset(
        {
            "admin_console",
            "kitchen_ops",
            "driver_dispatch",
            "broadcast",
            "delivery_chat",
        }
    ),
    "instagram": frozenset({"leads", "booking", "admin_console", "kitchen_ops", "driver_dispatch"}),
    "line": frozenset({"leads", "booking", "admin_console", "kitchen_ops", "driver_dispatch"}),
    "whatsapp": frozenset({"leads", "admin_console", "kitchen_ops", "driver_dispatch"}),
}


def _canonical(feature: str) -> str:
    return CAPABILITY_ALIASES.get(feature, feature)


def features_for(platform: str, role: str = "customer") -> frozenset[str]:
    """Platform ceiling ∩ role privilege (CARD-31)."""
    ch = normalize_channel(platform)
    return PLATFORM_CAPS.get(ch, frozenset()) & ROLE_FEATURES.get(role, frozenset())


def can(platform: str, feature: str, role: str = "customer") -> bool:
    """True if *feature* is allowed for platform×role (ignores brand mask)."""
    return _canonical(feature) in features_for(platform, role)


def _as_dict(v: Any) -> dict[str, Any]:
    return v if isinstance(v, dict) else {}


def _truthy(v: Any, default: bool = True) -> bool:
    if v is None:
        return default
    return bool(v)


def base_capabilities_from_brand(
    *,
    commerce_mode: str | None,
    age_gate_enabled: bool,
    web_profile: dict[str, Any] | None,
) -> dict[str, bool]:
    """Channel-agnostic base mask from brand columns + modules."""
    mode = normalize_commerce_mode(commerce_mode)
    web = _as_dict(web_profile)
    modules = _as_dict(web.get("modules"))

    caps: dict[str, bool] = {k: True for k in CAPABILITY_KEYS}
    caps["age_gate"] = bool(age_gate_enabled)
    caps["checkout"] = mode in ("full_store", "hybrid")
    caps["portfolio"] = mode in ("portfolio", "hybrid")
    # Portfolio-first: still show catalog but not checkout when pure portfolio
    if mode == "portfolio":
        caps["checkout"] = False

    # Cart + payments follow checkout for brand base
    caps["cart"] = caps["checkout"]
    for pay in ("payment_promptpay", "payment_crypto", "payment_cash"):
        caps[pay] = caps["checkout"]

    for mod_key, cap_key in _MODULE_TO_CAP.items():
        if mod_key in modules:
            caps[cap_key] = _truthy(modules[mod_key], caps[cap_key])

    # Explicit capabilities block overrides modules when present
    explicit = _as_dict(web.get("capabilities"))
    for k, v in explicit.items():
        ck = _canonical(k)
        if ck in caps:
            caps[ck] = bool(v)
            if ck == "checkout":
                caps["cart"] = caps["checkout"]
                for pay in ("payment_promptpay", "payment_crypto", "payment_cash"):
                    caps[pay] = caps["checkout"]

    return caps


def resolve_capabilities(
    *,
    commerce_mode: str | None,
    age_gate_enabled: bool,
    web_profile: dict[str, Any] | None,
    channel: str = "web",
    role: str = "customer",
) -> dict[str, bool]:
    """
    Resolve effective capability mask for a brand on a given channel × role.

    web_profile.channels example::

        {
          "web": {"enabled": true, "mask": {"checkout": false, "tickets": true}},
          "telegram": {"enabled": true, "mask": {"booking": true, "leads": true}},
          "line": {"enabled": false}
        }
    """
    ch = normalize_channel(channel)
    web = _as_dict(web_profile)
    channels = _as_dict(web.get("channels"))
    ch_cfg = _as_dict(channels.get(ch))

    # Channel disabled → all off (surface should 404 or hide brand)
    enabled_default = DEFAULT_CHANNEL_ENABLED.get(ch, False)
    if channels:
        # If channels block exists, missing channel key => default table
        if ch not in channels:
            channel_on = enabled_default
        else:
            channel_on = _truthy(ch_cfg.get("enabled"), True)
    else:
        channel_on = enabled_default

    if not channel_on:
        return {k: False for k in CAPABILITY_KEYS}

    allowed = features_for(ch, role)
    brand = base_capabilities_from_brand(
        commerce_mode=commerce_mode,
        age_gate_enabled=age_gate_enabled,
        web_profile=web,
    )

    # platform×role ∩ brand base
    caps: dict[str, bool] = {}
    for k in CAPABILITY_KEYS:
        if k not in allowed:
            caps[k] = False
        else:
            caps[k] = bool(brand.get(k, True))

    # Channel defaults OFF (CARD-40) — brand mask may re-enable below
    for k in CHANNEL_DEFAULT_OFF.get(ch, frozenset()):
        if k in caps:
            caps[k] = False

    # Per-channel mask (also accept "capabilities" alias)
    mask = _as_dict(ch_cfg.get("mask")) or _as_dict(ch_cfg.get("capabilities"))
    for k, v in mask.items():
        ck = _canonical(k)
        if ck not in caps:
            continue
        if bool(v):
            # Re-enable only within platform×role ceiling
            caps[ck] = ck in allowed
        else:
            caps[ck] = False

    return caps


def channel_status(web_profile: dict[str, Any] | None) -> dict[str, bool]:
    """Which channels are enabled for this brand (for admin/API discovery)."""
    web = _as_dict(web_profile)
    channels = _as_dict(web.get("channels"))
    out: dict[str, bool] = {}
    for ch, default in DEFAULT_CHANNEL_ENABLED.items():
        if not channels:
            out[ch] = default
            continue
        if ch not in channels:
            out[ch] = default
            continue
        cfg = _as_dict(channels.get(ch))
        out[ch] = _truthy(cfg.get("enabled"), True)
    return out


def cap_enabled(caps: dict[str, bool], key: str) -> bool:
    """Adapter helper: is a resolved mask key on?"""
    return bool(caps.get(_canonical(key), False))
