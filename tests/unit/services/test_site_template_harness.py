"""Golden harness: two vertical templates share one storefront spine.

Proves white-label sites are fully data-driven:
  - snus-demo → landing_editorial + age gate + nicotine compliance + flavor tiles DNA
  - food-demo → ig_default full_store kitchen + multi-branch + no age gate

No product names / legal copy are hard-coded in Astro (checked by grepping
that public DTOs differ only by seed data).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from bot.services.catalog_public import get_brand_public, get_store_menu, list_active_brands
from bot.services.seed_food_demo import seed_food_demo
from bot.services.seed_snus_demo import NICOTINE_WARNING, seed_snus_demo
from bot.services.store_admin import update_store

STOREFRONT_SRC = Path(__file__).resolve().parents[3] / "apps" / "storefront" / "src"


@pytest.fixture
def both_templates(db_engine, monkeypatch):
    monkeypatch.setenv("SEED_SNUS_COMMERCE_MODE", "full_store")
    snus = seed_snus_demo(force=True)
    food = seed_food_demo(force=True)
    return snus, food


def test_storefront_src_has_no_vertical_product_copy():
    """Astro shell must not hardcode snus or food product marketing strings."""
    # Product / brand marketing must never live in the Astro shell.
    # Generic UI fallbacks (e.g. default age-gate title) are OK — seeds override them.
    banned = (
        "Mint Glacier",
        "Cola Lime",
        "NOVA Storm",
        "nicotine pouches",
        "Demo Pad Thai",
        "Bangkok Kitchen Demo",
        "Pick your weather",
        "Tobacco free",
        "Wok-fired mains",
        "snus-demo",
        "food-demo",
    )
    hits: list[str] = []
    for path in STOREFRONT_SRC.rglob("*"):
        if path.suffix not in {".astro", ".ts", ".css"}:
            continue
        # Skip pure comments-only mention of "snus-style" in VectorCan geometry
        text = path.read_text(encoding="utf-8")
        for b in banned:
            if b in text:
                hits.append(f"{path.relative_to(STOREFRONT_SRC)}: {b}")
    assert hits == [], f"static vertical copy in storefront:\n" + "\n".join(hits)


def test_both_brands_listed_and_isolated(both_templates):
    brands = list_active_brands()
    slugs = {b["slug"] for b in brands}
    assert "snus-demo" in slugs
    assert "food-demo" in slugs

    snus = get_brand_public("snus-demo")
    food = get_brand_public("food-demo")
    assert snus and food
    assert snus["name"] != food["name"]
    assert snus["web"]["theme"] == "landing_editorial"
    assert food["web"]["theme"] == "ig_default"
    assert snus["age_gate_enabled"] is True
    assert food["age_gate_enabled"] is False
    # Snus legal prose is seed-only
    assert NICOTINE_WARNING in snus["web"]["compliance"]["footer_warnings"]
    food_warnings = " ".join(food["web"]["compliance"].get("footer_warnings") or []).lower()
    assert "nicotine" not in food_warnings
    assert "demo" in food_warnings


def test_catalogs_differ_by_seed_data(both_templates):
    snus_menu = get_store_menu("snus-demo", "bangkok")
    food_menu = get_store_menu("food-demo", "sukhumvit")
    assert snus_menu and food_menu
    snus_names = {i["name"] for c in snus_menu["categories"] for i in c["items"]}
    food_names = {i["name"] for c in food_menu["categories"] for i in c["items"]}
    assert snus_names & food_names == set()
    assert "Cola Lime" in snus_names
    assert "Demo Pad Thai" in food_names
    # Snus items carry visual DNA for vector cans
    cola = next(i for c in snus_menu["categories"] for i in c["items"] if i["name"] == "Cola Lime")
    assert cola.get("accent_hex")
    assert cola.get("visual_motif")
    assert cola.get("strength")
    # Food items are prepared dishes without strength pips
    pad = next(i for c in food_menu["categories"] for i in c["items"] if i["name"] == "Demo Pad Thai")
    assert pad.get("item_type") == "prepared"
    assert pad["cta"] == "order"


def test_nav_labels_come_from_web_profile(both_templates):
    snus = get_brand_public("snus-demo")
    food = get_brand_public("food-demo")
    assert snus["web"]["nav"]["catalog"] == "Flavors"
    assert food["web"]["nav"]["catalog"] == "Menu"
    assert snus["web"]["nav"]["about"] == "Heritage"
    assert food["web"]["nav"]["about"] == "Our kitchen"
    assert snus["web"]["sections"]["catalog_headline"] == "Pick your weather."
    assert "kitchen" in food["web"]["sections"]["catalog_headline"].lower() or "menu" in food["web"][
        "sections"
    ]["catalog_headline"].lower()


def test_store_edit_reflects_in_public_catalog(both_templates):
    """Admin edits store address/phone → public menu DTO updates (DRY)."""
    menu_before = get_store_menu("food-demo", "sukhumvit")
    assert menu_before is not None
    store_id = menu_before["store"]["id"] if "id" in menu_before["store"] else None
    # catalog may not expose store id — resolve via admin service
    from bot.services.store_admin import get_store_by_slug

    st = get_store_by_slug("food-demo", "sukhumvit")
    assert st is not None
    store_id = st["id"]

    updated = update_store(
        store_id,
        address="Edited Soi for Harness, Bangkok 10110",
        phone="+66998887766",
    )
    assert updated["address"].startswith("Edited Soi")
    assert updated["phone"] == "+66998887766"

    menu_after = get_store_menu("food-demo", "sukhumvit")
    assert menu_after is not None
    assert menu_after["store"]["address"] == "Edited Soi for Harness, Bangkok 10110"
    assert menu_after["store"]["phone"] == "+66998887766"

    brand = get_brand_public("food-demo")
    store_sum = next(s for s in brand["stores"] if s["slug"] == "sukhumvit")
    assert store_sum["address"] == "Edited Soi for Harness, Bangkok 10110"


def test_theme_tokens_differ(both_templates):
    snus = get_brand_public("snus-demo")
    food = get_brand_public("food-demo")
    snus_tokens = snus["web"].get("theme_tokens") or {}
    food_tokens = food["web"].get("theme_tokens") or {}
    assert snus_tokens.get("mode") == "light"
    assert food_tokens.get("mode") == "dark"
    assert snus_tokens.get("chrome", {}).get("catalog") == "flavor_tiles"
    assert food_tokens.get("chrome", {}).get("catalog") == "ig_grid"
    assert snus_tokens.get("chrome", {}).get("product_media") == "vector_only"
    assert food_tokens.get("chrome", {}).get("product_media") == "photo"
