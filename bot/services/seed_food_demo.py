"""Seed a generic Thai food restaurant brand for white-label harness tests.

Complements ``seed_snus_demo`` (NOVA-style nicotine portfolio/full_store).
Uses the same product-agnostic storefront shell — all copy/theme/menu comes
from Brand columns + ``web_profile`` + Goods rows (not Astro hardcoding).
"""

from __future__ import annotations

import logging
from decimal import Decimal

from bot.database.main import Database
from bot.database.models.main import BranchInventory, Brand, Categories, Goods, Role, Store

logger = logging.getLogger(__name__)

BRAND_SLUG = "food-demo"
DEFAULT_STORE_SLUG = "sukhumvit"

# Dark kitchen / restaurant chrome — high contrast (light text on dark paper).
FOOD_THEME_TOKENS = {
    "mode": "dark",
    "colors": {
        "ink": "#f5efe6",
        "sea": "#f0c674",
        "sea_deep": "#e8a838",
        "sun": "#f0b429",
        "paper": "#14110e",
        "paper_warm": "#1c1814",
        "line": "rgba(255,255,255,.14)",
        "footer": "#0a0908",
        "accent": "#e8a838",
        "on_ink": "#14110e",
        "on_accent": "#14110a",
        "on_footer": "#f5efe6",
        "muted": "rgba(245,239,230,.72)",
    },
    "type": {
        "display": "system-ui",
        "body": "system-ui",
        "mono": "ui-monospace",
        "display_scale": "normal",
        "text_transform_display": "none",
        "letter_spacing_display": "-0.01em",
        "line_height_display": "1.05",
    },
    "geometry": {
        "radius_card": "1rem",
        "radius_pill": "999px",
        "radius_gate": "0",
        "container_max": "72rem",
        "section_pad_y": "2.5rem",
        "grid_catalog": "3",
        "card_aspect": "1/1",
        "can_tilt_deg": 0,
        "shadow": "none",
        "border_width": "1px",
    },
    "motion": {
        "ticker_seconds": 0,
        "hover_lift_px": 2,
        "hero_underline": False,
    },
    "chrome": {
        "nav": "profile",
        "ticker": "static",
        "age_gate": "dark_full",
        "benefits": "cards",
        "catalog": "ig_grid",
        "product_media": "photo",
        "logo": "image",
        "hero": "profile",
        "featured": "split",
    },
}

SPICE = {
    "spice_level": {
        "label": "🌶 Spice Level",
        "type": "single",
        "required": True,
        "options": [
            {"id": "mild", "label": "Mild", "price": 0},
            {"id": "medium", "label": "Medium", "price": 0},
            {"id": "thai_hot", "label": "Thai Hot 🔥", "price": 0},
        ],
    }
}
EXTRAS = {
    "extras": {
        "label": "➕ Extras",
        "type": "multi",
        "required": False,
        "options": [
            {"id": "extra_rice", "label": "Extra Rice", "price": 20},
            {"id": "fried_egg", "label": "Fried Egg", "price": 15},
        ],
    }
}

# Distinct names (Goods.name is global PK) so food coexists with snus lineup.
# item: (name, price, desc, type, stock, prep, allergens, modifiers)
FOOD_MENU: dict[tuple[str, int], list[tuple]] = {
    ("Food Starters", 1): [
        ("Demo Spring Rolls", 80, "Crispy vegetable spring rolls (4 pcs)", "prepared", 0, 8, "gluten", None),
        ("Demo Chicken Satay", 120, "Grilled chicken skewers with peanut sauce", "prepared", 0, 12, "peanut", None),
        ("Demo Papaya Salad", 90, "Som tam with lime and chili", "prepared", 0, 7, "fish,peanut", {**SPICE}),
    ],
    ("Food Mains", 2): [
        (
            "Demo Pad Thai",
            120,
            "Stir-fried rice noodles with shrimp",
            "prepared",
            0,
            12,
            "shellfish,peanut,egg",
            {**SPICE, **EXTRAS},
        ),
        ("Demo Pad See Ew", 110, "Wide noodles in sweet soy with chicken", "prepared", 0, 12, "gluten,egg", {**EXTRAS}),
        (
            "Demo Basil Chicken Rice",
            130,
            "Stir-fried minced chicken with holy basil",
            "prepared",
            0,
            10,
            None,
            {**SPICE, **EXTRAS},
        ),
    ],
    ("Food Curries", 3): [
        ("Demo Green Curry", 150, "Coconut green curry with chicken", "prepared", 0, 15, "fish", {**SPICE}),
        ("Demo Massaman Curry", 160, "Rich peanut curry with beef and potato", "prepared", 0, 18, "peanut", {**SPICE}),
        ("Demo Red Curry", 150, "Coconut red curry with vegetables", "prepared", 0, 15, "fish", {**SPICE}),
    ],
    ("Food Drinks", 4): [
        ("Demo Thai Iced Tea", 60, "Sweet creamy iced tea", "prepared", 0, 4, "dairy", None),
        ("Demo Coconut Water", 55, "Fresh young coconut water", "product", 120, None, None, None),
        ("Demo Bottled Water", 25, "Still water 500ml", "product", 300, None, None, None),
    ],
    ("Food Desserts", 5): [
        ("Demo Mango Sticky Rice", 95, "Sweet sticky rice with fresh mango", "prepared", 0, 6, None, None),
        ("Demo Coconut Ice Cream", 70, "Homemade coconut ice cream", "product", 80, None, "dairy", None),
    ],
}

BRANCHES = [
    # (name, slug, lat, lng, phone, is_default, address)
    (
        "Sukhumvit Kitchen",
        "sukhumvit",
        13.7383,
        100.5601,
        "+66820000001",
        True,
        "42/8 Sukhumvit Soi 22, Khlong Tan, Khlong Toei, Bangkok 10110",
    ),
    (
        "Silom Kitchen",
        "silom",
        13.7280,
        100.5340,
        "+66820000002",
        False,
        "130/5 Silom Road, Suriyawong, Bang Rak, Bangkok 10500",
    ),
    (
        "Thonglor Kitchen",
        "thonglor",
        13.7330,
        100.5820,
        "+66820000003",
        False,
        "9 Sukhumvit 55 (Thong Lo), Khlong Tan Nuea, Watthana, Bangkok 10110",
    ),
]

FOOD_WEB_PROFILE = {
    "schema_version": 1,
    "web_enabled": True,
    "theme": "ig_default",
    "theme_tokens": FOOD_THEME_TOKENS,
    "tagline": "Everyday Thai comfort food — kitchen-fresh, branch delivery ready",
    "ticker": None,
    "nav": {
        "home": "Home",
        "catalog": "Menu",
        "about": "Our kitchen",
        "contact": "Contact",
        "inquire": "Catering",
        "book": "Reserve table",
        "support": "Support",
        "login": "Log in",
        "cart": "Cart",
        "orders": "Orders",
        "checkout": "Checkout",
    },
    "sections": {
        "featured_eyebrow": "Chef's pick",
        "featured_badge": "POPULAR",
        "featured_cta": "See full menu",
        "catalog_eyebrow": "Menu",
        "catalog_headline": "Order from the kitchen.",
        "catalog_subline": "Modifiers and spice levels available on many dishes",
        "benefits_eyebrow": "Why us",
        "benefits_headline": "Built for Bangkok delivery nights.",
        "open_branch": "Open branch →",
    },
    "hero": {
        "headline": "Hot wok. Cold drinks. Fast riders.",
        "subhead": "A multi-branch Thai kitchen demo for white-label full-store checkout.",
        "eyebrow": "OPEN LATE",
        "featured_item": "Demo Pad Thai",
    },
    "about": {
        "title": "Our kitchen",
        "body_md": (
            "This is a **generic food-store template** for harness tests. "
            "Menu, prices, branch addresses, and copy live in the database — "
            "the Astro shell only renders API payloads.\n\n"
            "Prepared dishes use unlimited stock; packaged drinks track inventory per branch."
        ),
    },
    "faq": [
        {
            "q": "Do you deliver?",
            "a_md": "Yes when checkout + delivery capabilities are enabled for the brand channel.",
        },
        {
            "q": "Can I change spice level?",
            "a_md": "Many mains expose spice and extras modifiers stored on the Goods row.",
        },
        {
            "q": "Is this a real restaurant?",
            "a_md": "No — demo data for platform testing only.",
        },
    ],
    "compliance": {
        "footer_warnings": [
            "Demo restaurant catalog only. Prices and availability are sample data.",
        ],
        "product_disclaimer_title": "Allergen notice",
        "product_disclaimer_md": (
            "Dishes may contain allergens listed on each item. "
            "Inform staff of severe allergies before ordering. Demo copy only."
        ),
        "disclaimers": [
            {
                "id": "demo_food",
                "title": "Food demo brand",
                "body": "White-label template for full-store food vertical testing.",
                "placement": "footer",
            }
        ],
        "legal_note": "Operator configures real kitchen policies before production publish.",
        "show_dbd_in_footer": True,
    },
    "modules": {
        "show_about": True,
        "show_faq": True,
        "show_lead_form": True,
        "show_booking": True,
        "show_benefits": True,
        "show_featured": True,
        "show_ticker": False,
        "show_tickets": True,
        "show_auth": True,
        "show_contact": True,
        "show_catalog": True,
    },
    "channels": {
        "web": {
            "enabled": True,
            "mask": {
                "checkout": True,
                "cart": True,
                "payment_cash": True,
                "payment_promptpay": True,
                "order_status": True,
                "portfolio": False,
                "leads": True,
                "booking": True,
            },
        },
        "telegram": {"enabled": True, "mask": {}},
        "line": {"enabled": False},
        "whatsapp": {"enabled": False},
        "instagram": {"enabled": False},
    },
    "benefits": [
        {
            "n": "01",
            "title": "Wok-fired mains",
            "body": "Pad Thai, basil rice, and curries prepped to order.",
        },
        {
            "n": "02",
            "title": "Branch inventory",
            "body": "Packaged drinks track stock per kitchen branch.",
        },
        {
            "n": "03",
            "title": "Modifiers",
            "body": "Spice level and extras live on the Goods row, not the template.",
        },
        {
            "n": "04",
            "title": "Full-store web",
            "body": "Cart and checkout on when commerce_mode is full_store.",
        },
    ],
    "social": {
        "instagram": "https://instagram.com/",
        "line": "https://line.me/",
        "whatsapp_e164": "66820000001",
    },
    "cta": {
        "order": "Add to cart",
        "add_to_cart": "Add to cart",
        "inquire": "Catering inquiry",
        "book": "Reserve table",
    },
}


def seed_food_demo(*, force: bool = False) -> dict:
    """Create or refresh the ``food-demo`` brand (multi-branch Thai kitchen)."""
    with Database().session() as s:
        if s.query(Role).filter_by(name="USER").first() is None:
            s.add(Role(name="USER", permissions=1))
            s.flush()

        brand = s.query(Brand).filter_by(slug=BRAND_SLUG).one_or_none()
        if brand and not force:
            n_goods = s.query(Goods).filter_by(brand_id=brand.id).count()
            n_stores = s.query(Store).filter_by(brand_id=brand.id).count()
            if n_goods > 0 and n_stores > 0:
                brand.web_profile = dict(FOOD_WEB_PROFILE)
                brand.commerce_mode = "full_store"
                brand.age_gate_enabled = False
                brand.min_age = None
                s.commit()
                return {
                    "slug": BRAND_SLUG,
                    "products": n_goods,
                    "stores": n_stores,
                    "skipped": True,
                    "refreshed_theme": True,
                    "commerce_mode": "full_store",
                    "template": "food_kitchen",
                }

        if brand is None:
            brand = Brand(
                name="Bangkok Kitchen Demo",
                slug=BRAND_SLUG,
                description=(
                    "Multi-branch Thai restaurant demo for white-label full-store testing. "
                    "Menu and copy come from the database."
                ),
                legal_name="Bangkok Kitchen Demo Co., Ltd.",
                dbd_number="0105559876543",
                support_email="hello@food-demo.local",
                support_phone="+66820000001",
                commerce_mode="full_store",
                age_gate_enabled=False,
                min_age=None,
                timezone="Asia/Bangkok",
                web_profile=dict(FOOD_WEB_PROFILE),
            )
            s.add(brand)
            s.flush()
        else:
            brand.name = "Bangkok Kitchen Demo"
            brand.description = (
                "Multi-branch Thai restaurant demo for white-label full-store testing. "
                "Menu and copy come from the database."
            )
            brand.legal_name = brand.legal_name or "Bangkok Kitchen Demo Co., Ltd."
            brand.dbd_number = brand.dbd_number or "0105559876543"
            brand.support_email = brand.support_email or "hello@food-demo.local"
            brand.support_phone = brand.support_phone or "+66820000001"
            brand.commerce_mode = "full_store"
            brand.age_gate_enabled = False
            brand.min_age = None
            brand.web_profile = dict(FOOD_WEB_PROFILE)
            brand.timezone = brand.timezone or "Asia/Bangkok"

        stores: list[Store] = []
        for name, slug, lat, lng, phone, is_default, address in BRANCHES:
            st = s.query(Store).filter_by(brand_id=brand.id, slug=slug).one_or_none()
            if st is None:
                st = (
                    s.query(Store)
                    .filter_by(brand_id=brand.id, name=name)
                    .one_or_none()
                )
            if st is None:
                st = Store(
                    name=name,
                    slug=slug,
                    brand_id=brand.id,
                    address=address,
                    phone=phone,
                    latitude=lat,
                    longitude=lng,
                    is_default=is_default,
                    is_active=True,
                    web_profile={
                        "schema_version": 1,
                        "about_md": f"Demo kitchen branch: {name}.",
                        "amenities": ["delivery", "pickup", "aircon"],
                    },
                )
                s.add(st)
            else:
                st.slug = slug
                st.address = address
                st.phone = phone
                st.latitude = lat
                st.longitude = lng
                st.is_default = is_default
                st.is_active = True
            stores.append(st)
        s.flush()

        product_names: list[str] = []
        created = 0
        for (cat_name, sort_order), items in FOOD_MENU.items():
            cat = s.query(Categories).filter_by(name=cat_name).one_or_none()
            if cat is None:
                s.add(
                    Categories(
                        name=cat_name,
                        brand_id=brand.id,
                        sort_order=sort_order,
                        description=f"Demo category: {cat_name}",
                    )
                )
            else:
                cat.brand_id = brand.id
                cat.sort_order = sort_order
            for name, price, desc, itype, stock, prep, allergens, mods in items:
                existing = s.query(Goods).filter_by(name=name).one_or_none()
                if existing:
                    existing.brand_id = brand.id
                    existing.category_name = cat_name
                    existing.price = Decimal(str(price))
                    existing.description = desc
                    existing.item_type = itype
                    existing.stock_quantity = stock
                    existing.prep_time_minutes = prep
                    existing.allergens = allergens
                    existing.modifiers = mods
                    existing.is_active = True
                    existing.web_listable = True
                    existing.web_orderable = True
                    existing.inquiry_only = False
                else:
                    g = Goods(
                        name=name,
                        brand_id=brand.id,
                        category_name=cat_name,
                        price=Decimal(str(price)),
                        description=desc,
                        item_type=itype,
                        stock_quantity=stock,
                        prep_time_minutes=prep,
                        allergens=allergens,
                        modifiers=mods,
                        is_active=True,
                    )
                    g.web_listable = True
                    g.web_orderable = True
                    g.inquiry_only = False
                    s.add(g)
                    created += 1
                if itype == "product":
                    product_names.append(name)
        s.flush()

        inv_created = 0
        for item_name in product_names:
            for st in stores:
                if (
                    s.query(BranchInventory)
                    .filter_by(store_id=st.id, item_name=item_name)
                    .first()
                ):
                    continue
                s.add(
                    BranchInventory(
                        store_id=st.id,
                        item_name=item_name,
                        stock_quantity=100,
                        reserved_quantity=0,
                    )
                )
                inv_created += 1

        s.commit()
        total = s.query(Goods).filter_by(brand_id=brand.id).count()
        n_stores = s.query(Store).filter_by(brand_id=brand.id).count()
        logger.info(
            "Food demo ready slug=%s products=%s stores=%s created=%s inv=%s",
            BRAND_SLUG,
            total,
            n_stores,
            created,
            inv_created,
        )
        return {
            "slug": BRAND_SLUG,
            "products": total,
            "stores": n_stores,
            "created": created,
            "branch_inventory": inv_created,
            "commerce_mode": "full_store",
            "template": "food_kitchen",
        }
