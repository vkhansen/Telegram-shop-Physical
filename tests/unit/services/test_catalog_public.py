"""CARD-38 Phase A — public catalog service tests."""

from decimal import Decimal

import pytest

from bot.database.models.main import BranchInventory, Brand, Categories, Goods, Store
from bot.services.catalog_public import (
    get_brand_public,
    get_store_item,
    get_store_menu,
    item_available,
    list_active_brands,
    resolve_item_cta,
    slugify,
)
from bot.services.web_profile import normalize_commerce_mode, validate_brand_web_profile


@pytest.fixture
def two_brands(db_engine):
    """Seed two brands with stores and goods."""
    from bot.database.main import Database

    with Database().session() as s:
        b1 = Brand(
            name="Alpha Cafe",
            slug="alpha-cafe",
            description="Coffee brand",
            legal_name="Alpha Cafe Co., Ltd.",
            dbd_number="0105559999999",
            commerce_mode="full_store",
            age_gate_enabled=False,
            web_profile={
                "schema_version": 1,
                "about": {"title": "About Alpha", "body_md": "We brew."},
                "modules": {"show_lead_form": True},
            },
        )
        b2 = Brand(
            name="Beta Portfolio",
            slug="beta-portfolio",
            description="Showcase only",
            commerce_mode="portfolio",
            age_gate_enabled=True,
            min_age=18,
            web_profile={
                "schema_version": 1,
                "compliance": {"footer_warnings": ["Adults only."]},
            },
        )
        s.add_all([b1, b2])
        s.flush()

        s1 = Store(
            name="Sukhumvit",
            slug="sukhumvit",
            brand_id=b1.id,
            address="123 Sukhumvit Rd",
            phone="+66811111111",
            latitude=13.74,
            longitude=100.56,
            is_default=True,
            is_active=True,
        )
        s2 = Store(
            name="Showroom",
            slug="showroom",
            brand_id=b2.id,
            address="99 Demo St",
            phone="+66822222222",
            is_active=True,
        )
        s.add_all([s1, s2])
        s.flush()

        s.add(Categories(name="Drinks", brand_id=b1.id, sort_order=1))
        s.add(Categories(name="Lineup", brand_id=b2.id, sort_order=1))
        s.flush()

        g1 = Goods(
            name="Latte",
            price=Decimal("85.00"),
            description="Milk coffee",
            category_name="Drinks",
            brand_id=b1.id,
            item_type="prepared",
            stock_quantity=0,
            is_active=True,
        )
        g2 = Goods(
            name="Berry Storm",
            price=Decimal("350.00"),
            description="Showcase item",
            category_name="Lineup",
            brand_id=b2.id,
            item_type="product",
            stock_quantity=0,
            is_active=True,
        )
        g2.media = [
            {
                "type": "web_visual",
                "accent_hex": "#c23b6e",
                "accent_hex_2": "#4a0a28",
                "strength": 4,
                "tag": "BERRY · ICE",
                "visual_motif": "berry",
                "featured_xl": False,
            }
        ]
        g_hidden = Goods(
            name="Secret",
            price=Decimal("1.00"),
            description="Not on web",
            category_name="Drinks",
            brand_id=b1.id,
            item_type="prepared",
        )
        g_hidden.web_listable = False
        g2.inquiry_only = True
        g2.web_orderable = False
        s.add_all([g1, g2, g_hidden])
        s.commit()
        return {"b1": b1.slug, "b2": b2.slug, "s1": s1.slug, "s2": s2.slug}


def test_slugify():
    assert slugify("Berry Storm!") == "berry-storm"
    assert slugify("") == "item"


def test_commerce_mode_normalize():
    assert normalize_commerce_mode("PORTFOLIO") == "portfolio"
    assert normalize_commerce_mode("nope") == "full_store"


def test_resolve_cta():
    assert resolve_item_cta(commerce_mode="portfolio", web_orderable=True, inquiry_only=False) == "inquire"
    assert resolve_item_cta(commerce_mode="full_store", web_orderable=True, inquiry_only=False) == "order"
    assert resolve_item_cta(commerce_mode="hybrid", web_orderable=False, inquiry_only=False) == "inquire"
    assert resolve_item_cta(commerce_mode="full_store", web_orderable=True, inquiry_only=True) == "inquire"


def test_web_profile_validate():
    out = validate_brand_web_profile({"about": {"title": "Hi"}, "schema_version": 1})
    assert out["schema_version"] == 1
    assert out["about"]["title"] == "Hi"


def test_web_profile_theme_tokens():
    out = validate_brand_web_profile(
        {
            "schema_version": 1,
            "theme": "landing_editorial",
            "theme_tokens": {
                "mode": "light",
                "colors": {"ink": "#06122e", "sun": "#ffd60a"},
                "chrome": {"catalog": "flavor_tiles", "product_media": "vector_only"},
            },
        }
    )
    assert out["theme"] == "landing_editorial"
    assert out["theme_tokens"]["mode"] == "light"
    assert out["theme_tokens"]["chrome"]["catalog"] == "flavor_tiles"


def test_list_brands(two_brands):
    brands = list_active_brands()
    slugs = {b["slug"] for b in brands}
    assert "alpha-cafe" in slugs
    assert "beta-portfolio" in slugs


def test_get_brand_public(two_brands):
    data = get_brand_public("alpha-cafe")
    assert data is not None
    assert data["name"] == "Alpha Cafe"
    assert data["legal"]["dbd_number"] == "0105559999999"
    assert data["web"]["about"]["title"] == "About Alpha"
    assert len(data["stores"]) == 1
    assert data["stores"][0]["slug"] == "sukhumvit"
    assert data["stores"][0]["address"] == "123 Sukhumvit Rd"

    assert get_brand_public("missing") is None


def test_inactive_brand_404(two_brands):
    from bot.database.main import Database
    from bot.database.models.main import Brand

    with Database().session() as s:
        b = s.query(Brand).filter_by(slug="alpha-cafe").one()
        b.is_active = False
        s.commit()
    assert get_brand_public("alpha-cafe") is None


def test_store_menu_full_store(two_brands):
    menu = get_store_menu("alpha-cafe", "sukhumvit")
    assert menu is not None
    assert menu["store"]["phone"] == "+66811111111"
    assert menu["brand"]["commerce_mode"] == "full_store"
    names = [i["name"] for c in menu["categories"] for i in c["items"]]
    assert "Latte" in names
    assert "Secret" not in names  # web_listable=False
    latte = next(i for c in menu["categories"] for i in c["items"] if i["name"] == "Latte")
    assert latte["cta"] == "order"
    assert latte["available"] is True


def test_store_menu_portfolio_cta(two_brands):
    menu = get_store_menu("beta-portfolio", "showroom")
    assert menu is not None
    assert menu["brand"]["commerce_mode"] == "portfolio"
    assert menu["brand"]["age_gate_enabled"] is True
    item = menu["categories"][0]["items"][0]
    assert item["cta"] == "inquire"
    assert item["name"] == "Berry Storm"
    # web_visual DNA from goods.media
    assert item["accent_hex"] == "#c23b6e"
    assert item["strength"] == 4
    assert item["visual_motif"] == "berry"
    assert item["tag"] == "BERRY · ICE"


def test_get_item_detail(two_brands):
    item = get_store_item("alpha-cafe", "sukhumvit", "latte")
    assert item is not None
    assert item["description"] == "Milk coffee"
    assert item["brand_slug"] == "alpha-cafe"


def test_product_out_of_stock_with_branch_inv(two_brands):
    from bot.database.main import Database

    with Database().session() as s:
        brand = s.query(Brand).filter_by(slug="alpha-cafe").one()
        store = s.query(Store).filter_by(slug="sukhumvit").one()
        s.add(Categories(name="Packaged", brand_id=brand.id, sort_order=2))
        s.flush()
        g = Goods(
            name="Bottle Water",
            price=Decimal("20"),
            description="Water",
            category_name="Packaged",
            brand_id=brand.id,
            item_type="product",
            stock_quantity=10,
            is_active=True,
        )
        s.add(g)
        s.flush()
        s.add(
            BranchInventory(
                store_id=store.id,
                item_name="Bottle Water",
                stock_quantity=0,
                reserved_quantity=0,
            )
        )
        s.commit()

    menu = get_store_menu("alpha-cafe", "sukhumvit")
    water = next(i for c in menu["categories"] for i in c["items"] if i["name"] == "Bottle Water")
    assert water["available"] is False
    assert "out_of_stock" in water["badges"]


def test_item_available_sold_out():
    g = Goods(
        name="X",
        price=Decimal("1"),
        description="d",
        category_name="Drinks",
        sold_out_today=True,
        is_active=True,
        item_type="prepared",
    )
    # Goods needs is_active etc. — sold_out set after
    g.sold_out_today = True
    ok, badges = item_available(g, now_hhmm="12:00")
    assert ok is False
    assert "sold_out" in badges
