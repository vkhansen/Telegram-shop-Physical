"""Food kitchen white-label demo seed (generic full_store vertical)."""

from bot.services.catalog_public import get_brand_public, get_store_menu
from bot.services.seed_food_demo import BRAND_SLUG, DEFAULT_STORE_SLUG, seed_food_demo


def test_seed_food_demo_and_catalog(db_engine):
    summary = seed_food_demo(force=True)
    assert summary["slug"] == BRAND_SLUG
    assert summary["products"] >= 10
    assert summary["stores"] >= 2
    assert summary.get("commerce_mode") == "full_store"
    assert summary.get("template") == "food_kitchen"

    brand = get_brand_public(BRAND_SLUG)
    assert brand is not None
    assert brand["age_gate_enabled"] is False
    assert brand["commerce_mode"] == "full_store"
    assert brand["capabilities"].get("checkout") is True
    assert brand["capabilities"].get("cart") is True
    web = brand["web"]
    assert web.get("theme") == "ig_default"
    assert web.get("nav", {}).get("catalog") == "Menu"
    assert "nicotine" not in (web.get("tagline") or "").lower()
    assert "kitchen" in (brand.get("name") or "").lower() or "kitchen" in (web.get("about") or {}).get(
        "body_md", ""
    ).lower()

    menu = get_store_menu(BRAND_SLUG, DEFAULT_STORE_SLUG)
    assert menu is not None
    items = [i for c in menu["categories"] for i in c["items"]]
    assert len(items) >= 10
    assert any(i["name"] == "Demo Pad Thai" for i in items)
    assert any(i["cta"] == "order" for i in items)
    # Food template does not require vector visual DNA / strength pips
    pad = next(i for i in items if i["name"] == "Demo Pad Thai")
    assert pad["web_orderable"] is True
    assert pad.get("strength") in (None, 0) or pad.get("strength") is None


def test_seed_food_is_idempotent(db_engine):
    first = seed_food_demo(force=True)
    second = seed_food_demo(force=False)
    assert second.get("skipped") is True
    assert second["products"] == first["products"]
