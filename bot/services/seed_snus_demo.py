"""Seed a NOVA-inspired snus demo brand using tests/test-data images (CARD-38).

Images are referenced as ``local:<filename>`` and served by the media proxy
from ``tests/test-data/`` (no Telegram upload required for local/demo).
"""

from __future__ import annotations

import logging
from decimal import Decimal
from pathlib import Path

from bot.database.main import Database
from bot.database.models.main import Brand, Categories, Goods, Role, Store

logger = logging.getLogger(__name__)

# Project root: bot/services/../../
_ROOT = Path(__file__).resolve().parents[2]
TEST_DATA = _ROOT / "tests" / "test-data"

# Map demo SKUs → images in tests/test-data (15 files available)
SNUS_LINEUP: list[tuple[str, str, str, str, int]] = [
    # name, price, flavor desc, image filename, strength 1-7
    ("Mint Glacier", "299", "Sharp mint lift with a cool, dry finish. Everyday strength.", "1000045254.jpg", 3),
    ("Berries Storm", "319", "Bright berry ice with a long clean finish — pocket-ready slim pouches.", "1000045255.jpg", 4),
    ("Cola Lime", "329", "Dark cola zest and lime ice — late-night storm energy. Limited · new release.", "1000045258.jpg", 5),
    ("Citrus Pulse", "289", "Citrus peel and light sweetness — bright daytime option.", "1000045260.jpg", 2),
    ("Coffee Ember", "309", "Roasted coffee notes with a warm finish — evening ritual.", "1000045262.jpg", 4),
    ("Tropic Heat", "319", "Tropical fruit with a mild warm spice edge.", "1000045264.jpg", 4),
    ("Iceberg Spearmint", "299", "Classic spearmint freeze for all-day discreet use.", "1000045268.jpg", 3),
    ("Watermelon Chill", "309", "Sweet melon body with a cold mint close.", "1000045270.jpg", 3),
    ("Grape Night", "319", "Dark grape and soft ice — after-hours lineup.", "1000045271.jpg", 4),
    ("Apple Frost", "299", "Crisp green apple with a clean frost finish.", "1000045272.jpg", 3),
    ("Mango Storm", "329", "Ripe mango heat-wave with long-lasting flavor.", "1000045273.jpg", 5),
    ("Peppermint Zero", "279", "Clean peppermint for lighter adult sessions.", "1000045274.jpg", 2),
    ("Cherry Blizzard", "319", "Sour cherry ice with a sharp cold finish.", "1000045275.jpg", 4),
    ("Lemon Thunder", "309", "Electric lemon zest and soft mint undercurrent.", "1000045276.jpg", 3),
    ("Vanilla Smoke", "329", "Soft vanilla body with a dark spice close — demo limited.", "1000045277.jpg", 5),
]

NICOTINE_WARNING = (
    "Warning: This product contains nicotine. Nicotine is an addictive chemical. "
    "For sale to adults of legal age only."
)

AGE_GATE_BODY = (
    "This product contains nicotine — a highly addictive substance. "
    "You must be of legal age in your country to enter this site."
)

# Snus-specific marketing + legal prose lives ONLY in this demo seed.
# The storefront template is product-agnostic and reads web_profile.compliance / nav / sections.
SNUS_WEB_PROFILE = {
    "schema_version": 1,
    "web_enabled": True,
    "theme": "landing_gallery",
    "tagline": "Clean Kicks for Thailand — Tobacco-Free, Flavor-Focused, Pocket-Ready",
    # Single ticker source (also readable via compliance.ticker)
    "ticker": "Nicotine pouches · Sweden snus · Tobacco free · All white slim format · Adults only",
    "nav": {
        "home": "Home",
        "catalog": "Flavors",
        "about": "Heritage",
        "contact": "Contact",
        "inquire": "Inquire",
        "book": "Book meeting",
        "support": "Support",
        "login": "Log in",
    },
    "sections": {
        "featured_eyebrow": "Featured storm",
        "featured_badge": "LIMITED · NEW RELEASE",
        "featured_cta": "See all flavors",
        "catalog_eyebrow": "02 · The lineup",
        "catalog_headline": "Pick your weather.",
        "catalog_subline": "Tap a can for details",
        "benefits_eyebrow": "01 · Built for the kick",
        "benefits_headline": "Four things that hit different.",
        "open_branch": "Open branch →",
    },
    "hero": {
        "headline": "A Storm of Flavor in Every Pouch",
        "subhead": "Fifteen all-white nicotine pouches built for clean kicks and loud flavor.",
        "eyebrow": "RESTRICTED · 18+",
        # Name must match a Goods.name in the catalog (featured resolves from DB images)
        "featured_item": "Cola Lime",
    },
    "about": {
        "title": "Heritage",
        "body_md": (
            "Snus is a 200-year Swedish ritual. This demo lineup is a bolder, brighter cousin — "
            "built for adults who want the lift without the smoke.\n\n"
            "Slim pouches, discreet use, and climate-aware storage notes for Thailand heat. "
            "This is a **white-label demo** seeded from `tests/test-data` product photos."
        ),
    },
    "faq": [
        {
            "q": "What is a nicotine pouch?",
            "a_md": "A small white pouch placed under the upper lip. Demo copy only — not medical advice.",
        },
        {
            "q": "How do I order?",
            "a_md": "This demo supports inquire / book meeting flows. Full checkout stays on private channels when configured.",
        },
        {
            "q": "Age restriction?",
            "a_md": "Adults of legal age only. You must pass the age gate to browse.",
        },
    ],
    "compliance": {
        "age_gate": {
            "title": "Are you of legal age?",
            "body_md": AGE_GATE_BODY,
            "confirm_label": "I am 18 or older",
            "deny_label": "I am under 18",
            "deny_redirect_url": "https://www.google.com",
            "footer_note": "For adult nicotine users only",
            # Shown under gate buttons (tenant legal strips)
            "disclaimer_lines": [NICOTINE_WARNING],
        },
        "footer_warnings": [NICOTINE_WARNING],
        "product_disclaimer_title": "Nicotine product notice",
        "product_disclaimer_md": (
            f"{NICOTINE_WARNING}\n\n"
            "Demo catalog only. Not medical advice. Sale and use are restricted to adults of legal age "
            "where permitted. Operators must ensure local compliance before publishing."
        ),
        "disclaimers": [
            {
                "id": "demo",
                "title": "White-label demo",
                "body": (
                    "This site is a platform demo. Images and prices are sample data. "
                    "Real brands configure their own warnings, age gates, and catalog."
                ),
                "placement": "footer",
            },
            {
                "id": "not_medical",
                "title": "Not medical advice",
                "body": (
                    "Nothing on this demo is a health claim or medical recommendation. "
                    "Nicotine is addictive. Consult local regulations."
                ),
                "placement": "page",
            },
        ],
        "legal_note": (
            "Content and offers are provided by the brand operator. Availability, pricing, and legality "
            "vary by location. This white-label template only displays configured notices."
        ),
        "show_dbd_in_footer": True,
    },
    "modules": {
        "show_about": True,
        "show_faq": True,
        "show_lead_form": True,
        "show_booking": True,
        "show_benefits": True,
        "show_featured": True,
        "show_ticker": True,
        "show_tickets": True,
        "show_auth": True,
        "show_contact": True,
        "show_catalog": True,
    },
    # Per-channel surface masks (DRY reconfiguration without code deploys)
    "channels": {
        "web": {
            "enabled": True,
            # Portfolio demo: no web checkout; inquire / book instead
            "mask": {"checkout": False, "portfolio": True},
        },
        "telegram": {
            "enabled": True,
            "mask": {"booking": False},  # example subset on bot vs web
        },
        "line": {"enabled": False},
        "whatsapp": {"enabled": False},
        "instagram": {"enabled": False},
    },
    "benefits": [
        {
            "n": "01",
            "title": "Tobacco free",
            "body": "All-white pouches. No staining, no smoke — plant fiber and nicotine.",
        },
        {
            "n": "02",
            "title": "Ice-locked flavor",
            "body": "Flavor that hits fast and rides for a long session.",
        },
        {
            "n": "03",
            "title": "Discreet in the heat",
            "body": "Pocket-ready format suited to discreet adult use in Thailand.",
        },
        {
            "n": "04",
            "title": "20 pouches",
            "body": "Every can carries twenty slim pouches. Demo packaging copy.",
        },
    ],
    "social": {
        "instagram": "https://instagram.com/",
        "line": "https://line.me/",
        "whatsapp_e164": "66812345678",
    },
}


def local_file_id(filename: str) -> str:
    return f"local:{filename}"


def list_test_data_images() -> list[str]:
    """Filenames of demo product photos under tests/test-data (not a pytest test)."""
    if not TEST_DATA.is_dir():
        return []
    return sorted(p.name for p in TEST_DATA.glob("*.jpg"))


# Back-compat alias (avoid pytest collecting this as a test when imported).
test_data_filenames = list_test_data_images


def seed_snus_demo(*, force: bool = False) -> dict:
    """
    Create or refresh the ``snus-demo`` brand with lineup images from tests/test-data.

    Returns summary dict with brand slug and product count.
    """
    images = list_test_data_images()
    if not images:
        logger.warning("No images in %s — seeding without local media", TEST_DATA)
    # Map lineup to available images (cycle if fewer files)
    with Database().session() as s:
        if s.query(Role).filter_by(name="USER").first() is None:
            s.add(Role(name="USER", permissions=1))
            s.flush()

        brand = s.query(Brand).filter_by(slug="snus-demo").one_or_none()
        if brand and not force:
            # Still ensure store + goods exist
            store = s.query(Store).filter_by(brand_id=brand.id, slug="bangkok").one_or_none()
            n_goods = s.query(Goods).filter_by(brand_id=brand.id).count()
            if store and n_goods > 0:
                return {"slug": "snus-demo", "products": n_goods, "skipped": True}

        if brand is None:
            brand = Brand(
                name="NOVA Storm Demo",
                slug="snus-demo",
                description=(
                    "Fifteen all-white nicotine pouches built for clean kicks and loud flavor. "
                    "Adults only — demo white-label storefront."
                ),
                legal_name="NOVA Storm Demo Co., Ltd.",
                dbd_number="0105551234567",
                support_email="hello@snus-demo.local",
                support_phone="+66812345678",
                commerce_mode="portfolio",
                age_gate_enabled=True,
                min_age=18,
                timezone="Asia/Bangkok",
                web_profile=SNUS_WEB_PROFILE,
            )
            # logo from first image if present
            if images:
                brand.logo_file_id = local_file_id(images[0])
            s.add(brand)
            s.flush()
        else:
            brand.age_gate_enabled = True
            brand.min_age = 18
            brand.commerce_mode = "portfolio"
            brand.web_profile = SNUS_WEB_PROFILE
            brand.description = (
                "Fifteen all-white nicotine pouches built for clean kicks and loud flavor. "
                "Adults only — demo white-label storefront."
            )
            brand.legal_name = brand.legal_name or "NOVA Storm Demo Co., Ltd."
            brand.dbd_number = brand.dbd_number or "0105551234567"
            if images:
                brand.logo_file_id = local_file_id(images[0])

        store = s.query(Store).filter_by(brand_id=brand.id, slug="bangkok").one_or_none()
        if store is None:
            store = Store(
                name="Bangkok Flagship",
                slug="bangkok",
                brand_id=brand.id,
                address="Sukhumvit Soi Demo, Khlong Toei, Bangkok 10110",
                phone="+66812345678",
                latitude=13.7367,
                longitude=100.5600,
                is_default=True,
                is_active=True,
                menu_image_file_id=local_file_id(images[1]) if len(images) > 1 else None,
                web_profile={
                    "schema_version": 1,
                    "about_md": "Flagship demo branch for white-label previews.",
                },
            )
            s.add(store)
        else:
            store.is_active = True
            store.is_default = True
            if images and len(images) > 1:
                store.menu_image_file_id = local_file_id(images[1])

        cat = s.query(Categories).filter_by(name="The Lineup", brand_id=brand.id).one_or_none()
        if cat is None:
            # Categories.name is PK globally — may exist; try without brand filter
            cat = s.query(Categories).filter_by(name="The Lineup").one_or_none()
            if cat is None:
                s.add(
                    Categories(
                        name="The Lineup",
                        brand_id=brand.id,
                        sort_order=1,
                        description="Pick your weather — flavor storms for adult users.",
                        image_file_id=local_file_id(images[2]) if len(images) > 2 else None,
                    )
                )
            else:
                cat.brand_id = brand.id
                cat.description = cat.description or "Pick your weather."
        s.flush()

        created = 0
        for i, (name, price, desc, img, strength) in enumerate(SNUS_LINEUP):
            # Prefer mapped image; fall back to cycling available files
            img_name = img if (TEST_DATA / img).exists() else (images[i % len(images)] if images else None)
            existing = s.query(Goods).filter_by(name=name).one_or_none()
            if existing:
                existing.brand_id = brand.id
                existing.category_name = "The Lineup"
                existing.price = Decimal(price)
                existing.description = f"{desc}\n\nStrength {strength}/7 · Slim format · Demo SKU."
                existing.is_active = True
                existing.web_listable = True
                existing.web_orderable = False
                existing.inquiry_only = True
                existing.item_type = "product"
                if img_name:
                    existing.image_file_id = local_file_id(img_name)
                continue
            g = Goods(
                name=name,
                price=Decimal(price),
                description=f"{desc}\n\nStrength {strength}/7 · Slim format · Demo SKU.",
                category_name="The Lineup",
                brand_id=brand.id,
                item_type="product",
                stock_quantity=0,  # portfolio — not branch stock
                is_active=True,
            )
            g.web_listable = True
            g.web_orderable = False
            g.inquiry_only = True
            if img_name:
                g.image_file_id = local_file_id(img_name)
            s.add(g)
            created += 1

        s.commit()
        total = s.query(Goods).filter_by(brand_id=brand.id).count()
        logger.info("Snus demo ready slug=snus-demo products=%s created=%s images_dir=%s", total, created, TEST_DATA)
        return {"slug": "snus-demo", "products": total, "created": created, "images": len(images)}
