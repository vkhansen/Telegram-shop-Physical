"""Snus white-label demo seed + local media (tests/test-data images)."""

from bot.services.catalog_public import get_brand_public, get_store_menu
from bot.services.media_proxy import is_catalog_file_id, media_url_for, read_local_media_file
from bot.services.seed_snus_demo import NICOTINE_WARNING, list_test_data_images, seed_snus_demo


def test_test_data_has_images():
    files = list_test_data_images()
    assert len(files) >= 4, "expected images under tests/test-data"


def test_seed_snus_demo_and_catalog(db_engine, monkeypatch):
    monkeypatch.setenv("SEED_SNUS_COMMERCE_MODE", "portfolio")
    summary = seed_snus_demo(force=True)
    assert summary["slug"] == "snus-demo"
    assert summary["products"] >= 12
    assert summary.get("commerce_mode") == "portfolio"

    brand = get_brand_public("snus-demo")
    assert brand is not None
    assert brand["age_gate_enabled"] is True
    assert brand["min_age"] == 18
    assert brand["commerce_mode"] == "portfolio"
    compliance = brand["web"]["compliance"]
    warnings = compliance["footer_warnings"]
    assert any("nicotine" in w.lower() for w in warnings)
    assert NICOTINE_WARNING in warnings
    assert "addictive chemical" in NICOTINE_WARNING.lower()
    # Snus copy is seed data only — white-label shape is generic
    age = compliance["age_gate"]
    assert age["title"] == "Are you of legal age?"
    assert "nicotine" in age["body_md"].lower()
    assert age["confirm_label"] == "I am 18 or older"
    assert age["deny_label"] == "I am under 18"
    assert age.get("deny_redirect_url")
    assert NICOTINE_WARNING in (age.get("disclaimer_lines") or [])
    assert compliance.get("product_disclaimer_md")
    assert isinstance(compliance.get("disclaimers"), list)
    assert compliance.get("legal_note")
    assert brand["web"].get("nav")  # section labels are tenant config
    assert brand["logo_url"] and "/media/local/" in brand["logo_url"]
    # Capability mask is channel-agnostic switchboard (not Telegram-specific)
    assert brand.get("capabilities")
    assert brand["capabilities"].get("catalog") is True
    assert brand["capabilities"].get("checkout") is False  # portfolio web mask
    assert brand.get("channels", {}).get("web") is True
    assert brand.get("channel") == "web"
    # Every test-data jpg should be loadable
    files = list_test_data_images()
    assert len(files) >= 12
    for name in files:
        raw = read_local_media_file(name)
        assert raw is not None, name

    menu = get_store_menu("snus-demo", "bangkok")
    assert menu is not None
    items = [i for c in menu["categories"] for i in c["items"]]
    assert len(items) >= 12
    assert all(i["cta"] == "inquire" for i in items)
    # All lineup items should have local media from tests/test-data
    with_img = [i for i in items if i.get("image_url")]
    assert len(with_img) >= 12
    assert all("/media/local/" in (i["image_url"] or "") for i in with_img)
    assert any(i["name"] == "Cola Lime" for i in items)


def test_seed_snus_full_store_enables_checkout(db_engine, monkeypatch):
    """Local storefront commerce UI / Playwright uses SEED_SNUS_COMMERCE_MODE=full_store."""
    monkeypatch.setenv("SEED_SNUS_COMMERCE_MODE", "full_store")
    summary = seed_snus_demo(force=True)
    assert summary.get("commerce_mode") == "full_store"
    brand = get_brand_public("snus-demo")
    assert brand is not None
    assert brand["commerce_mode"] == "full_store"
    assert brand["capabilities"].get("checkout") is True
    assert brand["capabilities"].get("cart") is True
    menu = get_store_menu("snus-demo", "bangkok")
    assert menu is not None
    items = [i for c in menu["categories"] for i in c["items"]]
    assert any(i["cta"] == "order" for i in items)


def test_local_media_bytes():
    files = list_test_data_images()
    assert files
    data = read_local_media_file(files[0])
    assert data is not None
    raw, ctype = data
    assert len(raw) > 100
    assert "image" in ctype
    assert is_catalog_file_id(f"local:{files[0]}") is True
    url = media_url_for(f"local:{files[0]}")
    assert url and files[0] in url
