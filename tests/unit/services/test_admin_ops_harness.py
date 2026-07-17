"""Golden harness: admin-facing store + lead/booking ops flows.

Covers what operators need after a site is auto-generated:
  - list / create / edit / toggle / set-default stores
  - create lead → list inbox → status transitions
  - create booking → list → confirm
"""

from __future__ import annotations

import pytest

from bot.services import leads_bookings, store_admin
from bot.services.catalog_public import get_brand_public, get_store_menu
from bot.services.seed_food_demo import seed_food_demo
from bot.services.seed_snus_demo import seed_snus_demo


@pytest.fixture
def food_brand(db_engine):
    return seed_food_demo(force=True)


@pytest.fixture
def snus_brand(db_engine, monkeypatch):
    monkeypatch.setenv("SEED_SNUS_COMMERCE_MODE", "portfolio")
    return seed_snus_demo(force=True)


# ── Store admin ──────────────────────────────────────────────────────────────


def test_list_and_edit_store(food_brand):
    stores = store_admin.list_stores(brand_slug="food-demo")
    assert len(stores) >= 2
    default = next(s for s in stores if s["is_default"])
    assert default["slug"] == "sukhumvit"

    patched = store_admin.update_store(
        default["id"],
        address="99 Admin Edit Rd, Bangkok",
        phone="+66811112222",
        web_profile={"schema_version": 1, "about_md": "Updated by admin harness."},
    )
    assert patched["address"] == "99 Admin Edit Rd, Bangkok"
    assert patched["web_profile"]["about_md"].startswith("Updated by admin")

    menu = get_store_menu("food-demo", "sukhumvit")
    assert menu["store"]["address"] == "99 Admin Edit Rd, Bangkok"


def test_toggle_and_set_default_store(food_brand):
    stores = store_admin.list_stores(brand_slug="food-demo")
    silom = next(s for s in stores if s["slug"] == "silom")
    assert silom["is_default"] is False

    # Deactivate silom → not listed as active on public brand page
    off = store_admin.toggle_store(silom["id"], is_active=False)
    assert off["is_active"] is False
    brand = get_brand_public("food-demo")
    active_slugs = {s["slug"] for s in brand["stores"]}
    assert "silom" not in active_slugs
    assert "sukhumvit" in active_slugs

    # Reactivate + make default
    store_admin.toggle_store(silom["id"], is_active=True)
    now_default = store_admin.set_default_store(silom["id"])
    assert now_default["is_default"] is True
    stores2 = store_admin.list_stores(brand_slug="food-demo")
    defaults = [s for s in stores2 if s["is_default"]]
    assert len(defaults) == 1
    assert defaults[0]["slug"] == "silom"


def test_create_store_appears_on_brand(food_brand):
    created = store_admin.create_store(
        brand_slug="food-demo",
        name="Thonglor Pop-up",
        slug="thonglor",
        address="Thonglor Soi 10",
        phone="+66833334444",
        latitude=13.73,
        longitude=100.58,
    )
    assert created["slug"] == "thonglor"
    brand = get_brand_public("food-demo")
    assert any(s["slug"] == "thonglor" for s in brand["stores"])
    menu = get_store_menu("food-demo", "thonglor")
    assert menu is not None
    assert menu["store"]["name"] == "Thonglor Pop-up"


def test_create_store_duplicate_name_fails(food_brand):
    with pytest.raises(ValueError, match="name_exists"):
        store_admin.create_store(brand_slug="food-demo", name="Sukhumvit Kitchen")


# ── Leads inbox ──────────────────────────────────────────────────────────────


def test_lead_create_list_status_flow(snus_brand):
    lead = leads_bookings.create_lead(
        brand_slug="snus-demo",
        name="Wholesale Buyer",
        phone="+66855556666",
        preferred_channel="line",
        channel_handle="@buyer",
        item_slug="cola-lime",
        message="Need 50 cans",
        consent=True,
        age_confirmed=True,
        source="web_site",
        utm={"utm_source": "instagram", "utm_campaign": "reel-test"},
    )
    assert lead["status"] == "new"
    lead_id = lead["id"]

    inbox = leads_bookings.list_leads(brand_slug="snus-demo")
    assert any(row["id"] == lead_id for row in inbox)
    row = next(r for r in inbox if r["id"] == lead_id)
    assert row["name"] == "Wholesale Buyer"
    assert row["item_slug"] == "cola-lime"
    assert row["preferred_channel"] == "line"
    assert row["status"] == "new"

    contacted = leads_bookings.update_lead_status(lead_id, "contacted")
    assert contacted["status"] == "contacted"
    qualified = leads_bookings.update_lead_status(lead_id, "qualified")
    assert qualified["status"] == "qualified"

    only_new = leads_bookings.list_leads(brand_slug="snus-demo", status="new")
    assert all(r["id"] != lead_id for r in only_new)
    only_q = leads_bookings.list_leads(brand_slug="snus-demo", status="qualified")
    assert any(r["id"] == lead_id for r in only_q)

    got = leads_bookings.get_lead(lead_id)
    assert got is not None
    assert got["status"] == "qualified"
    assert got["brand_slug"] == "snus-demo"


def test_lead_status_invalid(snus_brand):
    lead = leads_bookings.create_lead(
        brand_slug="snus-demo",
        name="X",
        email="x@example.com",
        consent=True,
    )
    with pytest.raises(ValueError, match="invalid_status"):
        leads_bookings.update_lead_status(lead["id"], "not_a_status")


def test_leads_isolated_by_brand(food_brand, snus_brand):
    a = leads_bookings.create_lead(
        brand_slug="snus-demo",
        name="Snus Lead",
        phone="+66810000001",
        consent=True,
    )
    b = leads_bookings.create_lead(
        brand_slug="food-demo",
        name="Food Lead",
        phone="+66810000002",
        consent=True,
        message="Catering for 40",
    )
    snus_inbox = leads_bookings.list_leads(brand_slug="snus-demo")
    food_inbox = leads_bookings.list_leads(brand_slug="food-demo")
    assert any(r["id"] == a["id"] for r in snus_inbox)
    assert all(r["id"] != b["id"] for r in snus_inbox)
    assert any(r["id"] == b["id"] for r in food_inbox)
    assert all(r["id"] != a["id"] for r in food_inbox)


# ── Bookings ─────────────────────────────────────────────────────────────────


def test_booking_list_and_confirm(food_brand):
    booking = leads_bookings.create_booking(
        brand_slug="food-demo",
        name="Table Guest",
        meeting_type="in_person",
        phone="+66877778888",
        store_slug="sukhumvit",
        preferred_when="2026-09-01T19:00",
        notes="Party of 4",
        consent=True,
    )
    assert booking["status"] == "requested"
    listed = leads_bookings.list_bookings(brand_slug="food-demo")
    assert any(r["id"] == booking["id"] for r in listed)
    confirmed = leads_bookings.update_booking_status(booking["id"], "confirmed")
    assert confirmed["status"] == "confirmed"
