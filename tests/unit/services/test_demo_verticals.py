"""Multi-vertical demo seeds + placeholders for system fuzzing."""

from pathlib import Path

from bot.services.catalog_public import get_brand_public, get_store_menu, list_active_brands
from bot.services.demo_placeholders import TEST_DATA, ensure_all_placeholders, local_ref
from bot.services.media_proxy import is_catalog_file_id, read_local_media_file
from bot.services.seed_demo_verticals import (
    VERTICAL_BUILDERS,
    seed_all_demos,
    seed_all_verticals,
    seed_named_vertical,
)


def test_placeholders_generated():
    names = ensure_all_placeholders(force=False)
    assert len(names) >= 20
    for n in names[:5]:
        path = TEST_DATA / n
        assert path.is_file()
        raw = read_local_media_file(n)
        assert raw is not None
        data, ctype = raw
        assert len(data) > 200
        assert "image" in ctype
        assert is_catalog_file_id(local_ref(n)) is True


def test_seed_all_verticals(db_engine, monkeypatch):
    monkeypatch.setenv("SEED_SNUS_COMMERCE_MODE", "full_store")
    results = seed_all_demos(force=True, snus=True)
    slugs = {r["slug"] for r in results}
    assert "snus-demo" in slugs
    for key in VERTICAL_BUILDERS:
        assert f"{key}-demo" if key != "herb" else "herb-demo" in slugs or any(
            r["slug"].endswith("-demo") for r in results
        )
    # explicit expected set
    expected = {"snus-demo", "food-demo", "coffee-demo", "herb-demo", "bakery-demo", "grocery-demo"}
    assert expected <= slugs

    brands = {b["slug"] for b in list_active_brands()}
    assert expected <= brands


def test_coffee_modifiers_and_stock(db_engine):
    seed_named_vertical("coffee", force=True)
    brand = get_brand_public("coffee-demo")
    assert brand is not None
    assert brand["age_gate_enabled"] is False
    assert brand["capabilities"].get("checkout") is True
    menu = get_store_menu("coffee-demo", "ari")
    assert menu is not None
    items = [i for c in menu["categories"] for i in c["items"]]
    flat = next(i for i in items if i["name"] == "Café Flat White")
    assert flat["cta"] == "order"
    assert flat.get("image_url") and "/media/local/" in flat["image_url"]
    beans = next(i for i in items if "House Blend" in i["name"])
    assert beans["item_type"] == "product"


def test_herb_age_gate_and_hybrid(db_engine):
    seed_named_vertical("herb", force=True)
    brand = get_brand_public("herb-demo")
    assert brand is not None
    assert brand["age_gate_enabled"] is True
    assert brand["min_age"] == 21
    age = brand["web"]["compliance"]["age_gate"]
    assert "21" in age["title"] or "21" in age["confirm_label"]
    menu = get_store_menu("herb-demo", "sukhumvit")
    items = [i for c in menu["categories"] for i in c["items"]]
    # inquiry-only specialty
    pipe = next(i for i in items if i["name"] == "Demo Glass Pipe")
    assert pipe["cta"] == "inquire"
    # orderable flower
    flower = next(i for i in items if "Citrus Haze" in i["name"])
    assert flower["cta"] == "order"


def test_grocery_low_stock_branch(db_engine):
    seed_named_vertical("grocery", force=True)
    silom = get_store_menu("grocery-demo", "silom")
    assert silom is not None
    water = next(
        i
        for c in silom["categories"]
        for i in c["items"]
        if i["name"] == "Demo Sparkling Water 500ml"
    )
    # still available at low stock (5), but present
    assert water["available"] is True
    assert water["cta"] == "order"


def test_bakery_daily_limit_field(db_engine):
    from bot.database.main import Database
    from bot.database.models.main import Goods

    seed_named_vertical("bakery", force=True)
    with Database().session() as s:
        cro = s.query(Goods).filter_by(name="Bake Butter Croissant").one()
        assert cro.daily_limit == 40


def test_verticals_have_multiple_branches_with_addresses(db_engine):
    """Every vertical brand exposes 2+ branches with full Bangkok-style addresses."""
    for key in ("coffee", "herb", "bakery", "grocery", "food"):
        seed_named_vertical(key, force=True)

    expectations = {
        "coffee-demo": 3,
        "herb-demo": 3,
        "bakery-demo": 3,
        "grocery-demo": 3,
        "food-demo": 3,
    }
    for slug, min_n in expectations.items():
        brand = get_brand_public(slug)
        assert brand is not None, slug
        stores = brand["stores"]
        assert len(stores) >= min_n, f"{slug} expected >={min_n} stores, got {len(stores)}"
        for st in stores:
            addr = st.get("address") or ""
            assert "Bangkok" in addr, f"{slug}/{st.get('slug')}: address missing Bangkok: {addr!r}"
            assert st.get("phone")
            assert st.get("latitude") is not None
            assert st.get("longitude") is not None
            # street-level detail (not just a district name)
            assert len(addr) >= 30, f"{slug}/{st.get('slug')}: address too short: {addr!r}"
            assert any(ch.isdigit() for ch in addr), f"{slug}/{st.get('slug')}: no house/road number: {addr!r}"


def test_snus_has_multiple_branches(db_engine, monkeypatch):
    monkeypatch.setenv("SEED_SNUS_COMMERCE_MODE", "full_store")
    from bot.services.seed_snus_demo import seed_snus_demo

    seed_snus_demo(force=True)
    brand = get_brand_public("snus-demo")
    assert brand is not None
    assert len(brand["stores"]) >= 3
    slugs = {s["slug"] for s in brand["stores"]}
    assert "bangkok" in slugs
    assert "siam" in slugs
    for st in brand["stores"]:
        assert "Bangkok" in (st.get("address") or "")
        assert st.get("phone")
        assert st.get("latitude") is not None
