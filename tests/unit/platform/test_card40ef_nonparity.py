"""CARD-40 Tier E+F — intentional non-parity harden + scorecard freeze.

E1 Web-only pack off TG by default
E2 Deep-link policy (URL only, no TG lead/book FSM)
E3 TG-ops pack out of customer web parity
E4 Enforcement: no TG lead/book handlers; API rejects ops impersonation
F  Scorecard machine checks (packs + shared caps + adapter wiring)
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from bot.platform.capabilities import (
    CHANNEL_DEFAULT_OFF,
    PLATFORM_CAPS,
    SHARED_PARITY_CAPS,
    TG_OPS_CAPS,
    WEB_ONLY_CAPS,
    can,
    cap_enabled,
    features_for,
    resolve_capabilities,
)
from bot.platform import deep_links
from bot.web import auth_api

REPO = Path(__file__).resolve().parents[3]
HANDLERS_USER = REPO / "bot" / "handlers" / "user"
HANDLERS_ROOT = REPO / "bot" / "handlers"


# ---------------------------------------------------------------------------
# E1 — Web-only pack
# ---------------------------------------------------------------------------


def test_e1_web_only_pack_off_telegram_default():
    tg = resolve_capabilities(
        commerce_mode="full_store",
        age_gate_enabled=True,
        web_profile=None,
        channel="telegram",
        role="customer",
    )
    for key in WEB_ONLY_CAPS:
        # maps_widget is not in TG PLATFORM_CAPS ceiling either
        assert tg.get(key) is False, f"TG default should hide web-only {key}"


def test_e1_web_only_pack_on_web_default():
    web = resolve_capabilities(
        commerce_mode="full_store",
        age_gate_enabled=True,
        web_profile=None,
        channel="web",
        role="customer",
    )
    # Core funnel + marketing expected ON for web (age_gate follows brand flag)
    for key in ("leads", "booking", "about", "faq", "auth", "maps_widget"):
        assert web[key] is True, f"web default should enable {key}"
    assert web["age_gate"] is True


def test_e1_channel_default_off_includes_funnel():
    tg_off = CHANNEL_DEFAULT_OFF["telegram"]
    assert "leads" in tg_off
    assert "booking" in tg_off
    assert "age_gate" in tg_off
    assert "auth" in tg_off


def test_e1_brand_mask_may_reenable_tg_leads_but_not_ops_on_web():
    tg = resolve_capabilities(
        commerce_mode="full_store",
        age_gate_enabled=False,
        web_profile={
            "channels": {
                "telegram": {"enabled": True, "mask": {"leads": True, "booking": True}},
            }
        },
        channel="telegram",
        role="customer",
    )
    assert tg["leads"] is True
    assert tg["booking"] is True
    # Still no ops on customer role
    for key in TG_OPS_CAPS:
        assert tg[key] is False


# ---------------------------------------------------------------------------
# E2 — Deep-link policy
# ---------------------------------------------------------------------------


def test_e2_storefront_paths_and_urls():
    assert deep_links.storefront_path("snus-demo", "inquire") == "/snus-demo/inquire"
    assert deep_links.storefront_path("snus-demo", "book") == "/snus-demo/book"
    assert deep_links.storefront_path("snus-demo", "contact") == "/snus-demo/contact"
    assert deep_links.storefront_path("snus-demo", "home") == "/snus-demo"
    url = deep_links.storefront_url("snus-demo", "inquire", base="https://shop.example")
    assert url == "https://shop.example/snus-demo/inquire"


def test_e2_funnel_url_button_is_link_only():
    btn = deep_links.funnel_url_button("acme", "book", base="https://x.test")
    assert btn["url"] == "https://x.test/acme/book"
    assert "text" in btn
    # No form fields — URL button contract only
    assert set(btn.keys()) == {"text", "url"}


def test_e2_required_cap_for_funnel():
    assert deep_links.required_cap_for_funnel("inquire") == "leads"
    assert deep_links.required_cap_for_funnel("book") == "booking"
    assert deep_links.required_cap_for_funnel("home") is None


def test_e2_unknown_page_raises():
    with pytest.raises(ValueError, match="unknown_funnel"):
        deep_links.storefront_path("x", "not-a-page")


# ---------------------------------------------------------------------------
# E3 — TG-ops pack out of customer web
# ---------------------------------------------------------------------------


def test_e3_web_platform_ceiling_excludes_ops():
    web_caps = PLATFORM_CAPS["web"]
    for key in TG_OPS_CAPS:
        assert key not in web_caps
    # delivery_chat also not customer-web parity
    assert "delivery_chat" not in web_caps


def test_e3_web_customer_resolved_ops_off():
    web = resolve_capabilities(
        commerce_mode="full_store",
        age_gate_enabled=False,
        web_profile={
            # Even if someone tries to re-enable via mask, platform ceiling wins
            "channels": {
                "web": {
                    "enabled": True,
                    "mask": {k: True for k in TG_OPS_CAPS},
                }
            }
        },
        channel="web",
        role="customer",
    )
    for key in TG_OPS_CAPS:
        assert web[key] is False
        assert can("web", key, role="customer") is False


def test_e3_telegram_admin_has_ops_not_customer():
    admin = features_for("telegram", "admin")
    assert "admin_console" in admin
    assert "broadcast" in admin
    customer = features_for("telegram", "customer")
    for key in TG_OPS_CAPS:
        assert key not in customer


# ---------------------------------------------------------------------------
# E4 — Enforcement
# ---------------------------------------------------------------------------


def test_e4_no_lead_or_booking_fsm_in_user_handlers():
    """TG customer package must not register lead/book form handlers."""
    forbidden_substrings = (
        "lead_handler",
        "leads_handler",
        "booking_handler",
        "book_handler",
        "create_lead",
        "create_booking",
        "LeadForm",
        "BookingForm",
        "age_gate_handler",
    )
    py_files = list(HANDLERS_USER.glob("*.py"))
    assert py_files, "expected user handlers"
    for path in py_files:
        text = path.read_text(encoding="utf-8")
        for needle in forbidden_substrings:
            assert needle not in text, f"{path.name} must not implement {needle}"


def test_e4_user_router_modules_exclude_funnel_fsm():
    init_src = (HANDLERS_USER / "__init__.py").read_text(encoding="utf-8")
    # Import graph should stay commerce/support/AI — no funnel FSM modules
    assert "lead" not in init_src.lower()
    assert "booking" not in init_src.lower()
    assert "age_gate" not in init_src.lower()


def test_e4_reject_ops_impersonation_helper():
    resp = auth_api._reject_ops_impersonation({"role": "admin", "name": "x"})
    assert resp is not None
    assert resp.status == 403

    resp2 = auth_api._reject_ops_impersonation({"admin_console": True})
    assert resp2 is not None
    assert resp2.status == 403

    assert auth_api._reject_ops_impersonation({"name": "ok", "consent": True}) is None


def test_e4_web_admin_role_cannot_unlock_ops_ceiling():
    """Even role=admin on web platform cannot grant TG-ops (no ops impersonation)."""
    for key in TG_OPS_CAPS:
        assert can("web", key, role="admin") is False
    assert features_for("web", "admin") == frozenset() or not (
        features_for("web", "admin") & TG_OPS_CAPS
    )


# ---------------------------------------------------------------------------
# F — Scorecard freeze (machine-checkable)
# ---------------------------------------------------------------------------


def test_f_shared_parity_caps_on_both_platforms():
    for key in SHARED_PARITY_CAPS:
        assert can("telegram", key, role="customer") is True, key
        assert can("web", key, role="customer") is True, key


def test_f_web_only_and_ops_packs_disjoint_from_shared():
    assert WEB_ONLY_CAPS.isdisjoint(SHARED_PARITY_CAPS)
    assert TG_OPS_CAPS.isdisjoint(SHARED_PARITY_CAPS)
    assert TG_OPS_CAPS.isdisjoint(WEB_ONLY_CAPS)


def test_f_scorecard_default_masks_snapshot():
    """Living scorecard: default customer masks for full_store."""
    web = resolve_capabilities(
        commerce_mode="full_store",
        age_gate_enabled=True,
        web_profile=None,
        channel="web",
        role="customer",
    )
    tg = resolve_capabilities(
        commerce_mode="full_store",
        age_gate_enabled=True,
        web_profile=None,
        channel="telegram",
        role="customer",
    )
    # Shared
    for key in SHARED_PARITY_CAPS:
        assert web[key] is True and tg[key] is True, key
    # Web-only N/A on TG
    assert tg["leads"] is False and web["leads"] is True
    assert tg["booking"] is False and web["booking"] is True
    # Ops N/A on both customer masks
    for key in TG_OPS_CAPS:
        assert web[key] is False and tg[key] is False


def test_f_auth_api_wires_cap_gates():
    """create_lead / create_booking source must reference capability checks."""
    src = inspect.getsource(auth_api.create_lead)
    assert "leads" in src
    assert "cap_enabled" in src or "leads_disabled" in src
    src_b = inspect.getsource(auth_api.create_booking)
    assert "booking" in src_b


def test_f_deep_links_module_documents_no_form_policy():
    src = Path(deep_links.__file__).read_text(encoding="utf-8")
    assert "must not" in src.lower() or "URL button" in src
    assert "inquire" in src and "book" in src


def test_f_pr_gate_doc_exists():
    scorecard = REPO / "docs" / "later" / "CARD-40-parity-scorecard.md"
    pr_tpl = REPO / ".github" / "PULL_REQUEST_TEMPLATE.md"
    assert scorecard.is_file(), "F1 scorecard doc required"
    assert pr_tpl.is_file(), "F2 PR template required"
    text = scorecard.read_text(encoding="utf-8")
    assert "SHARED_PARITY_CAPS" in text or "shared" in text.lower()
    assert "WEB_ONLY" in text or "web-only" in text.lower()
    pr = pr_tpl.read_text(encoding="utf-8")
    assert "CARD-40" in pr or "capability" in pr.lower()


def test_f_no_handler_domain_shortcuts_in_leads_path():
    """Lead/book HTTP path goes through services, not raw ORM in auth_api."""
    tree = ast.parse((REPO / "bot" / "web" / "auth_api.py").read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name)
    assert "bot.database.models.main" not in imported
    assert "bot.database.models" not in imported
