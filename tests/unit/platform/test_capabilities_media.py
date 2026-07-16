"""Platform contracts: capabilities masks + media refs (channel-agnostic)."""

from bot.platform.capabilities import (
    CAPABILITY_KEYS,
    can,
    cap_enabled,
    features_for,
    resolve_capabilities,
    channel_status,
)
from bot.platform.media_ref import media_url_for_ref, normalize_media_ref, parse_media_ref


def test_parse_media_ref_schemes():
    assert parse_media_ref("local:a.jpg").scheme == "local"
    assert parse_media_ref("local:a.jpg").value == "a.jpg"
    assert parse_media_ref("tg:ABC123").scheme == "tg"
    # Legacy bare telegram id
    assert parse_media_ref("AgACAgI").scheme == "tg"
    assert parse_media_ref("https://cdn.example/x.jpg").scheme == "https"
    assert normalize_media_ref("local:x.jpg") == "local:x.jpg"


def test_local_media_url():
    url = media_url_for_ref("local:1000045254.jpg")
    assert url is not None
    assert "/media/local/1000045254.jpg" in url


# --- CARD-31 platform × role matrix ---


def test_features_for_telegram_customer_includes_live_location():
    caps = features_for("telegram", "customer")
    assert "location_live" in caps
    assert "location_once" in caps
    assert "catalog" in caps
    assert "checkout" in caps
    assert "delivery_chat" in caps
    assert "admin_console" not in caps  # ops role only


def test_features_for_instagram_customer_excludes_ops_and_live():
    caps = features_for("instagram", "customer")
    assert "catalog" in caps
    assert "checkout" in caps
    assert "location_once" in caps
    assert "location_live" not in caps
    assert "admin_console" not in caps
    assert "driver_dispatch" not in caps
    assert "delivery_chat" not in caps
    assert "broadcast" not in caps


def test_features_for_instagram_admin_no_admin_console():
    # admin role features ∩ IG platform caps is empty for admin_console
    caps = features_for("instagram", "admin")
    assert "admin_console" not in caps
    assert caps == frozenset() or "admin_console" not in caps


def test_features_for_telegram_admin_ops_only():
    caps = features_for("telegram", "admin")
    assert "admin_console" in caps
    assert "broadcast" in caps
    assert "kitchen_ops" in caps
    assert "checkout" not in caps  # narrow role; multi-role callers union


def test_can_alias_shop_browse():
    assert can("telegram", "shop_browse", role="customer") is True
    assert can("instagram", "admin_console", role="customer") is False
    assert can("web", "maps_widget", role="customer") is True


def test_web_platform_excludes_ops():
    caps = features_for("web", "customer")
    assert "catalog" in caps
    assert "leads" in caps
    assert "booking" in caps
    assert "auth" in caps
    assert "admin_console" not in caps
    assert "kitchen_ops" not in caps
    assert "driver_dispatch" not in caps


# --- CARD-40 Tier A default masks + brand override ---


def test_capabilities_portfolio_web_mask():
    web = {
        "modules": {"show_booking": True, "show_lead_form": True},
        "channels": {
            "web": {"enabled": True, "mask": {"checkout": False}},
            "telegram": {"enabled": True, "mask": {"booking": False}},
        },
    }
    web_caps = resolve_capabilities(
        commerce_mode="portfolio",
        age_gate_enabled=True,
        web_profile=web,
        channel="web",
    )
    assert web_caps["age_gate"] is True
    assert web_caps["checkout"] is False
    assert web_caps["cart"] is False
    assert web_caps["portfolio"] is True
    assert web_caps["leads"] is True
    assert web_caps["booking"] is True
    assert web_caps["catalog"] is True
    assert web_caps["auth"] is True
    # Web customer: ops stay off
    assert web_caps["admin_console"] is False
    assert web_caps["delivery_chat"] is False

    tg = resolve_capabilities(
        commerce_mode="portfolio",
        age_gate_enabled=True,
        web_profile=web,
        channel="telegram",
    )
    assert tg["booking"] is False
    # CARD-40 default: leads off on TG unless brand re-enables
    assert tg["leads"] is False
    assert tg["age_gate"] is False
    assert tg["auth"] is False
    assert tg["about"] is False
    assert tg["catalog"] is True
    assert tg["tickets"] is True
    assert tg["ai_customer"] is True
    assert tg["location_live"] is True


def test_telegram_brand_can_reenable_leads():
    """Brand channel.mask may turn leads on for TG when platform allows (A4)."""
    web = {
        "modules": {"show_lead_form": True},
        "channels": {
            "telegram": {"enabled": True, "mask": {"leads": True, "booking": True}},
        },
    }
    tg = resolve_capabilities(
        commerce_mode="full_store",
        age_gate_enabled=False,
        web_profile=web,
        channel="telegram",
        role="customer",
    )
    assert tg["leads"] is True
    assert tg["booking"] is True
    assert tg["checkout"] is True
    assert tg["cart"] is True
    assert tg["auth"] is False  # still default-off; not in mask


def test_full_store_commerce_payments_follow_checkout():
    caps = resolve_capabilities(
        commerce_mode="full_store",
        age_gate_enabled=False,
        web_profile=None,
        channel="web",
    )
    assert caps["checkout"] is True
    assert caps["cart"] is True
    assert caps["payment_promptpay"] is True
    assert caps["order_status"] is True


def test_disabled_channel_all_false():
    web = {"channels": {"line": {"enabled": False}}}
    caps = resolve_capabilities(
        commerce_mode="full_store",
        age_gate_enabled=False,
        web_profile=web,
        channel="line",
    )
    assert caps["catalog"] is False
    assert not any(caps.values())
    assert set(caps) == set(CAPABILITY_KEYS)


def test_channel_status_defaults():
    st = channel_status(None)
    assert st["web"] is True
    assert st["telegram"] is True
    assert st["line"] is False


def test_cap_enabled_helper():
    caps = {"catalog": True, "leads": False}
    assert cap_enabled(caps, "catalog") is True
    assert cap_enabled(caps, "shop_browse") is True  # alias
    assert cap_enabled(caps, "leads") is False
    assert cap_enabled(caps, "missing") is False
