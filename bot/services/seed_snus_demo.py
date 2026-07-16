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

# Map demo SKUs → images + vector visual DNA (accent / strength / motif).
# Photos are optional; storefront editorial theme draws SVG cans from visual fields.
# tuple: name, price, desc, image, strength, accent, accent2, tag, motif, featured_xl
SNUS_LINEUP: list[tuple[str, str, str, str, int, str, str, str, str, bool]] = [
    ("Mint Glacier", "299", "Sharp mint lift with a cool, dry finish. Everyday strength.", "1000045254.jpg", 3, "#3ecf8e", "#0a4d3c", "MINT · ICE", "ice", False),
    ("Berries Storm", "319", "Bright berry ice with a long clean finish — pocket-ready slim pouches.", "1000045255.jpg", 4, "#c23b6e", "#4a0a28", "BERRY · ICE", "berry", False),
    ("Cola Lime", "329", "Dark cola zest and lime ice — late-night storm energy. Limited · new release.", "1000045258.jpg", 5, "#b86a3a", "#2a1508", "FIZZ · ZEST", "cola", True),
    ("Citrus Pulse", "289", "Citrus peel and light sweetness — bright daytime option.", "1000045260.jpg", 2, "#f0b429", "#6b4a00", "CITRUS · DAY", "citrus", False),
    ("Coffee Ember", "309", "Roasted coffee notes with a warm finish — evening ritual.", "1000045262.jpg", 4, "#6b3f2a", "#1f1008", "ROAST · WARM", "coffee", False),
    ("Tropic Heat", "319", "Tropical fruit with a mild warm spice edge.", "1000045264.jpg", 4, "#e85d04", "#5c1a00", "TROPIC · HEAT", "storm", False),
    ("Iceberg Spearmint", "299", "Classic spearmint freeze for all-day discreet use.", "1000045268.jpg", 3, "#5ecfcf", "#0a3d3d", "SPEARMINT · ICE", "ice", False),
    ("Watermelon Chill", "309", "Sweet melon body with a cold mint close.", "1000045270.jpg", 3, "#e85a7a", "#5c1028", "MELON · CHILL", "berry", False),
    ("Grape Night", "319", "Dark grape and soft ice — after-hours lineup.", "1000045271.jpg", 4, "#7b3fa0", "#1a0a28", "GRAPE · NIGHT", "night", False),
    ("Apple Frost", "299", "Crisp green apple with a clean frost finish.", "1000045272.jpg", 3, "#7cbc3d", "#1e3d0a", "APPLE · FROST", "ice", False),
    ("Mango Storm", "329", "Ripe mango heat-wave with long-lasting flavor.", "1000045273.jpg", 5, "#ff9f1c", "#5c3000", "MANGO · STORM", "storm", False),
    ("Peppermint Zero", "279", "Clean peppermint for lighter adult sessions.", "1000045274.jpg", 2, "#a8e6cf", "#1a4d3c", "PEPPERMINT · LIGHT", "ice", False),
    ("Cherry Blizzard", "319", "Sour cherry ice with a sharp cold finish.", "1000045275.jpg", 4, "#d62828", "#4a0a0a", "CHERRY · ICE", "berry", False),
    ("Lemon Thunder", "309", "Electric lemon zest and soft mint undercurrent.", "1000045276.jpg", 3, "#f4d35e", "#5c4a00", "LEMON · ZEST", "citrus", False),
    ("Vanilla Smoke", "329", "Soft vanilla body with a dark spice close — demo limited.", "1000045277.jpg", 5, "#d4a574", "#3d2814", "VANILLA · SPICE", "night", False),
]

# Editorial theme pack: paper/ink/sea/sun tokens + chrome enums (no image assets).
SNUS_THEME_TOKENS = {
    "mode": "light",
    "colors": {
        "ink": "#06122e",
        "sea": "#0a4ea2",
        "sea_deep": "#062f63",
        "sun": "#ffd60a",
        "paper": "#fbf8f3",
        "paper_warm": "#f3ecdf",
        "line": "rgba(6,18,46,.12)",
        "footer": "#02091b",
        "accent": "#ffd60a",
        "on_ink": "#fbf8f3",
        "muted": "rgba(6,18,46,.55)",
    },
    "type": {
        "display": "Archivo Black",
        "body": "Inter",
        "mono": "JetBrains Mono",
        "display_scale": "hero_xl",
        "text_transform_display": "uppercase",
        "letter_spacing_display": "-0.02em",
        "line_height_display": "0.88",
    },
    "geometry": {
        "radius_card": "20px",
        "radius_pill": "999px",
        "radius_gate": "24px",
        "container_max": "1280px",
        "section_pad_y": "5rem",
        "grid_catalog": "3",
        "card_aspect": "4/5",
        "can_tilt_deg": 8,
        "shadow": "0 30px 60px -30px rgba(6,18,46,.35)",
        "border_width": "1.5px",
    },
    "motion": {
        "ticker_seconds": 28,
        "hover_lift_px": 6,
        "hero_underline": True,
    },
    "chrome": {
        "nav": "sticky_full",
        "ticker": "marquee",
        "age_gate": "paper_card",
        "benefits": "ink_strip_numbers",
        "catalog": "flavor_tiles",
        "product_media": "vector_only",
        "logo": "wordmark_svg",
        "hero": "editorial_display",
        "featured": "spotlight",
    },
}


def web_visual(
    *,
    accent: str,
    accent2: str,
    strength: int,
    tag: str,
    motif: str,
    featured_xl: bool = False,
) -> dict:
    """Structured product visual DNA (geometry) stored on goods.media."""
    return {
        "type": "web_visual",
        "accent_hex": accent,
        "accent_hex_2": accent2,
        "strength": strength,
        "tag": tag,
        "visual_motif": motif,
        "featured_xl": featured_xl,
    }

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
    # landing_editorial = paper/sea/sun + vector cans (per-brand theme_tokens)
    "theme": "landing_editorial",
    "theme_tokens": SNUS_THEME_TOKENS,
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
                # Refresh theme tokens + product visual DNA without full recreate
                brand.web_profile = SNUS_WEB_PROFILE
                brand.age_gate_enabled = True
                brand.min_age = 18
                for name, _price, desc, _img, strength, accent, accent2, tag, motif, featured_xl in SNUS_LINEUP:
                    g = s.query(Goods).filter_by(name=name).one_or_none()
                    if not g:
                        continue
                    g.media = [
                        web_visual(
                            accent=accent,
                            accent2=accent2,
                            strength=strength,
                            tag=tag,
                            motif=motif,
                            featured_xl=featured_xl,
                        )
                    ]
                    g.description = f"{desc}\n\nStrength {strength}/7 · Slim format · Demo SKU."
                s.commit()
                return {"slug": "snus-demo", "products": n_goods, "skipped": True, "refreshed_theme": True}

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
        for i, (name, price, desc, img, strength, accent, accent2, tag, motif, featured_xl) in enumerate(
            SNUS_LINEUP
        ):
            # Prefer mapped image; fall back to cycling available files
            img_name = img if (TEST_DATA / img).exists() else (images[i % len(images)] if images else None)
            visual = web_visual(
                accent=accent,
                accent2=accent2,
                strength=strength,
                tag=tag,
                motif=motif,
                featured_xl=featured_xl,
            )
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
                existing.media = [visual]
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
            g.media = [visual]
            if img_name:
                g.image_file_id = local_file_id(img_name)
            s.add(g)
            created += 1

        s.commit()
        total = s.query(Goods).filter_by(brand_id=brand.id).count()
        logger.info("Snus demo ready slug=snus-demo products=%s created=%s images_dir=%s", total, created, TEST_DATA)
        return {"slug": "snus-demo", "products": total, "created": created, "images": len(images)}
