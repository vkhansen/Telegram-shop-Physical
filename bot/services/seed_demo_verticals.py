"""Multi-vertical white-label demo brands for end-to-end system fuzzing.

Seeds several independent brands with:
  - dummy branches (address / phone / geo)
  - prepared + product inventory (branch stock for products)
  - modifiers / allergens / prep times
  - clipart placeholders (``tests/test-data/ph-*.png``)
  - commerce modes for cart, inquire, age-gate flows

Verticals
---------
  food-demo     Thai kitchen (full_store) — also via seed_food_demo
  coffee-demo   Specialty coffee shop (full_store)
  herb-demo     Adult herb retail demo (age gate 21, hybrid)
  bakery-demo   Neighborhood bakery (full_store)
  grocery-demo  Mini-mart convenience (full_store, stock-heavy)

Snus stays in ``seed_snus_demo`` (editorial theme). Use ``seed_all_demos()``.
"""

from __future__ import annotations

import logging
from copy import deepcopy
from decimal import Decimal
from typing import Any

from bot.database.main import Database
from bot.database.models.main import BranchInventory, Brand, Categories, Goods, Role, Store
from bot.services.demo_placeholders import ensure_all_placeholders, local_ref
from bot.services.theme_contrast import enforce_theme_tokens

logger = logging.getLogger(__name__)

# ── shared modifiers ────────────────────────────────────────────────────────

SIZE_DRINK = {
    "size": {
        "label": "Size",
        "type": "single",
        "required": True,
        "options": [
            {"id": "s", "label": "Small", "price": 0},
            {"id": "m", "label": "Medium", "price": 15},
            {"id": "l", "label": "Large", "price": 30},
        ],
    }
}
MILK = {
    "milk": {
        "label": "Milk",
        "type": "single",
        "required": False,
        "options": [
            {"id": "dairy", "label": "Dairy", "price": 0},
            {"id": "oat", "label": "Oat", "price": 20},
            {"id": "almond", "label": "Almond", "price": 20},
            {"id": "soy", "label": "Soy", "price": 15},
        ],
    }
}
SPICE = {
    "spice_level": {
        "label": "🌶 Spice",
        "type": "single",
        "required": True,
        "options": [
            {"id": "mild", "label": "Mild", "price": 0},
            {"id": "medium", "label": "Medium", "price": 0},
            {"id": "hot", "label": "Hot", "price": 0},
        ],
    }
}
EXTRAS_FOOD = {
    "extras": {
        "label": "Extras",
        "type": "multi",
        "required": False,
        "options": [
            {"id": "egg", "label": "Fried egg", "price": 15},
            {"id": "rice", "label": "Extra rice", "price": 20},
        ],
    }
}
GRIND = {
    "grind": {
        "label": "Grind",
        "type": "single",
        "required": False,
        "options": [
            {"id": "whole", "label": "Whole bean", "price": 0},
            {"id": "filter", "label": "Filter", "price": 0},
            {"id": "espresso", "label": "Espresso", "price": 0},
        ],
    }
}
HERB_AMOUNT = {
    "amount": {
        "label": "Amount",
        "type": "single",
        "required": True,
        "options": [
            {"id": "1g", "label": "1 g", "price": 0},
            {"id": "3.5g", "label": "3.5 g", "price": 450},
            {"id": "7g", "label": "7 g", "price": 850},
        ],
    }
}

# item tuple: name, price, desc, itype, stock, prep, allergens, mods, image, featured
# stock: products use global stock; prepared use 0 = unlimited


def _theme_pack(
    *,
    mode: str,
    paper: str,
    ink: str,
    accent: str,
    sea: str,
    footer: str | None = None,
    paper_warm: str | None = None,
    sun: str | None = None,
) -> dict:
    """Build a high-contrast token pack.

    Semantics (enforced again in the storefront):
      paper  — page background
      ink    — body text on paper (must contrast paper)
      on_ink — text on solid ink surfaces
      sun/accent — CTA fills; on_accent — text on those fills
    """
    sun_c = sun or accent
    # Derive on_* from relative luminance (simple mid-point rule for seeds)
    def _on(bg: str) -> str:
        h = bg.lstrip("#")
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        try:
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        except ValueError:
            return "#14110a"
        # perceived luminance
        lum = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
        return "#14110a" if lum > 0.45 else "#f7f5f2"

    foot = footer or ("#14110a" if mode == "light" else "#050608")
    # Contrast law applied at generation time (also re-checked in storefront).
    raw = {
        "mode": mode,
        "colors": {
            "ink": ink,
            "sea": sea,
            "sea_deep": sea,
            "sun": sun_c,
            "paper": paper,
            "paper_warm": paper_warm or paper,
            "line": "rgba(255,255,255,.14)" if mode == "dark" else "rgba(20,17,10,.14)",
            "footer": foot,
            "accent": accent,
            "on_ink": _on(ink),
            "on_accent": _on(sun_c),
            "on_footer": _on(foot),
            "muted": (
                "rgba(247,245,242,.72)" if mode == "dark" else "rgba(20,17,10,.68)"
            ),
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
            "radius_gate": "12px",
            "container_max": "72rem",
            "section_pad_y": "2.5rem",
            "grid_catalog": "3",
            "card_aspect": "1/1",
            "can_tilt_deg": 0,
            "shadow": "none",
            "border_width": "1px",
        },
        "motion": {"ticker_seconds": 0, "hover_lift_px": 2, "hero_underline": False},
        "chrome": {
            "nav": "profile",
            "ticker": "static",
            "age_gate": "dark_full" if mode == "dark" else "paper_card",
            "benefits": "cards",
            "catalog": "ig_grid",
            "product_media": "photo",
            "logo": "image",
            "hero": "profile",
            "featured": "split",
        },
    }
    return enforce_theme_tokens(raw)


# Distinct high-contrast brand palettes (paper vs ink always opposite ends of luminance)
PALETTE_FOOD = _theme_pack(
    mode="dark",
    paper="#14110e",
    paper_warm="#1c1814",
    ink="#f5efe6",
    accent="#e8a838",
    sun="#f0b429",
    sea="#f0c674",
    footer="#0a0908",
)
PALETTE_COFFEE = _theme_pack(
    mode="light",
    paper="#f6efe6",
    paper_warm="#ebe0d2",
    ink="#1c120c",
    accent="#8b4513",
    sun="#c4782a",
    sea="#5c3317",
    footer="#1c120c",
)
PALETTE_HERB = _theme_pack(
    mode="dark",
    paper="#0b1610",
    paper_warm="#122018",
    ink="#e6f5ea",
    accent="#3dd68c",
    sun="#5eead4",
    sea="#86efac",
    footer="#06100a",
)
PALETTE_BAKERY = _theme_pack(
    mode="light",
    paper="#fff6ed",
    paper_warm="#ffe8d4",
    ink="#3b1f12",
    accent="#c2410c",
    sun="#ea580c",
    sea="#9a3412",
    footer="#3b1f12",
)
PALETTE_GROCERY = _theme_pack(
    mode="dark",
    paper="#0a1528",
    paper_warm="#122038",
    ink="#e8f1ff",
    accent="#38bdf8",
    sun="#7dd3fc",
    sea="#93c5fd",
    footer="#050d18",
)


def _base_web(
    *,
    theme_name: str,
    tokens: dict,
    tagline: str,
    nav_catalog: str,
    about_title: str,
    about_body: str,
    hero_headline: str,
    hero_subhead: str,
    featured_item: str,
    benefits: list[dict],
    faq: list[dict],
    compliance: dict,
    modules: dict | None = None,
    channels_web_mask: dict | None = None,
    ticker: str | None = None,
) -> dict:
    mask = {
        "checkout": True,
        "cart": True,
        "payment_cash": True,
        "payment_promptpay": True,
        "order_status": True,
        "portfolio": False,
        "leads": True,
        "booking": True,
    }
    if channels_web_mask:
        mask.update(channels_web_mask)
    return {
        "schema_version": 1,
        "web_enabled": True,
        "theme": theme_name,
        "theme_tokens": tokens,
        "tagline": tagline,
        "ticker": ticker,
        "nav": {
            "home": "Home",
            "catalog": nav_catalog,
            "about": about_title,
            "contact": "Contact",
            "inquire": "Inquire",
            "book": "Book",
            "support": "Support",
            "login": "Log in",
            "cart": "Cart",
            "orders": "Orders",
            "checkout": "Checkout",
        },
        "sections": {
            "featured_eyebrow": "Featured",
            "featured_badge": "POPULAR",
            "featured_cta": f"See full {nav_catalog.lower()}",
            "catalog_eyebrow": nav_catalog,
            "catalog_headline": f"Browse the {nav_catalog.lower()}.",
            "catalog_subline": "Demo catalog — prices and stock are sample data",
            "benefits_eyebrow": "Why us",
            "benefits_headline": "Built for demo checkouts.",
            "open_branch": "Open branch →",
        },
        "hero": {
            "headline": hero_headline,
            "subhead": hero_subhead,
            "eyebrow": "DEMO STORE",
            "featured_item": featured_item,
        },
        "about": {"title": about_title, "body_md": about_body},
        "faq": faq,
        "compliance": compliance,
        "modules": modules
        or {
            "show_about": True,
            "show_faq": True,
            "show_lead_form": True,
            "show_booking": True,
            "show_benefits": True,
            "show_featured": True,
            "show_ticker": bool(ticker),
            "show_tickets": True,
            "show_auth": True,
            "show_contact": True,
            "show_catalog": True,
        },
        "channels": {
            "web": {"enabled": True, "mask": mask},
            "telegram": {"enabled": True, "mask": {}},
            "line": {"enabled": False},
            "whatsapp": {"enabled": False},
            "instagram": {"enabled": False},
        },
        "benefits": benefits,
        "social": {"instagram": "https://instagram.com/", "line": "https://line.me/"},
        "cta": {
            "order": "Add to cart",
            "add_to_cart": "Add to cart",
            "inquire": "Send inquiry",
            "book": "Book",
        },
    }


# ── vertical definitions ────────────────────────────────────────────────────

def _coffee_spec() -> dict[str, Any]:
    return {
        "slug": "coffee-demo",
        "name": "Bean & Steam Demo",
        "legal_name": "Bean & Steam Demo Co., Ltd.",
        "dbd_number": "0105551111001",
        "support_email": "hello@coffee-demo.local",
        "support_phone": "+66821110001",
        "description": "Specialty coffee demo — espresso bar, cold brew, and beans by the bag.",
        "commerce_mode": "full_store",
        "age_gate_enabled": False,
        "min_age": None,
        "logo": "ph-coffee-logo.png",
        "web_profile": _base_web(
            theme_name="ig_default",
            tokens=PALETTE_COFFEE,
            tagline="Single-origin demos · flat whites · beans to go",
            nav_catalog="Menu",
            about_title="The bar",
            about_body=(
                "**Bean & Steam** is a multi-branch coffee demo for cart, modifiers "
                "(size/milk), and product stock (retail bags).\n\n"
                "Not a real café — white-label harness data only."
            ),
            hero_headline="Pull a shot. Grab a bag.",
            hero_subhead="Espresso drinks, cold brew, and retail beans with grind options.",
            featured_item="Café Flat White",
            benefits=[
                {"n": "01", "title": "Modifiers", "body": "Size + milk options on most drinks."},
                {"n": "02", "title": "Retail bags", "body": "Product stock tracked per branch."},
                {"n": "03", "title": "Prep times", "body": "Barista prep minutes on drinks."},
                {"n": "04", "title": "Three branches", "body": "Ari, Thonglor, and Siam kiosk."},
            ],
            faq=[
                {"q": "Do you do oat milk?", "a_md": "Yes — milk is a modifier on most drinks."},
                {"q": "Can I buy beans?", "a_md": "Retail bags are product SKUs with branch stock."},
            ],
            compliance={
                "footer_warnings": ["Demo café only. Sample prices and stock."],
                "legal_note": "White-label coffee vertical for flow testing.",
                "show_dbd_in_footer": True,
            },
        ),
        "stores": [
            {
                "name": "Ari Roastery",
                "slug": "ari",
                "address": "88/12 Phahonyothin Road, Soi Ari 4, Samsen Nai, Phaya Thai, Bangkok 10400",
                "phone": "+66821110001",
                "lat": 13.7796,
                "lng": 100.5446,
                "is_default": True,
            },
            {
                "name": "Thonglor Bar",
                "slug": "thonglor",
                "address": "55 Sukhumvit 55 (Thong Lo), Khlong Tan Nuea, Watthana, Bangkok 10110",
                "phone": "+66821110002",
                "lat": 13.7305,
                "lng": 100.5820,
                "is_default": False,
            },
            {
                "name": "Siam Paragon Kiosk",
                "slug": "siam",
                "address": "991 Rama I Road, Pathum Wan, Pathum Wan, Bangkok 10330",
                "phone": "+66821110003",
                "lat": 13.7466,
                "lng": 100.5347,
                "is_default": False,
            },
        ],
        # Goods.name is global PK — unique across verticals.
        "menu": {
            ("Coffee Drinks", 1): [
                ("Café Espresso", 65, "Double ristretto demo shot.", "prepared", 0, 3, None, {**SIZE_DRINK}, "ph-coffee-espresso.png", False),
                ("Café Flat White", 95, "Silky microfoam over double espresso.", "prepared", 0, 5, "dairy", {**SIZE_DRINK, **MILK}, "ph-coffee-latte.png", True),
                ("Café Oat Latte", 110, "Espresso + oat milk (default oat).", "prepared", 0, 5, None, {**SIZE_DRINK, **MILK}, "ph-coffee-latte.png", False),
                ("Café Cold Brew", 120, "12-hour steep, served over ice.", "prepared", 0, 2, None, {**SIZE_DRINK}, "ph-coffee-cold.png", False),
            ],
            ("Tea & Alt", 2): [
                ("Café Matcha Latte", 125, "Ceremonial-style matcha demo.", "prepared", 0, 6, "dairy", {**SIZE_DRINK, **MILK}, "ph-coffee-tea.png", False),
                ("Café Thai Iced Tea", 70, "Sweet tea demo (café style).", "prepared", 0, 4, "dairy", {**SIZE_DRINK}, "ph-coffee-tea.png", False),
            ],
            ("Pastry Case", 3): [
                ("Café Butter Croissant", 75, "Flaky demo croissant.", "product", 40, None, "gluten,dairy", None, "ph-coffee-pastry.png", False),
                ("Café Banana Bread", 65, "Slice of banana loaf.", "product", 25, None, "gluten,egg", None, "ph-coffee-pastry.png", False),
            ],
            ("Retail Beans", 4): [
                ("Café House Blend 250g", 320, "Medium roast demo bag.", "product", 80, None, None, {**GRIND}, "ph-coffee-logo.png", False),
                ("Café Single Origin 250g", 420, "Rotating origin demo bag.", "product", 40, None, None, {**GRIND}, "ph-coffee-logo.png", False),
            ],
        },
    }


def _herb_spec() -> dict[str, Any]:
    """Adult herb retail demo — age-gated hybrid (browse + inquire, limited web order)."""
    return {
        "slug": "herb-demo",
        "name": "Green Leaf Demo",
        "legal_name": "Green Leaf Demo Co., Ltd.",
        "dbd_number": "0105552222002",
        "support_email": "hello@herb-demo.local",
        "support_phone": "+66822220001",
        "description": (
            "Adult-use herb retail demo for age-gate, portfolio/hybrid CTAs, and inventory. "
            "Fictional products only — not a real dispensary."
        ),
        "commerce_mode": "hybrid",
        "age_gate_enabled": True,
        "min_age": 21,
        "logo": "ph-herb-logo.png",
        "web_profile": _base_web(
            theme_name="ig_default",
            tokens=PALETTE_HERB,
            tagline="Adults only demo · flower · pre-rolls · edibles (fictional SKUs)",
            nav_catalog="Menu",
            about_title="About this demo",
            about_body=(
                "**Green Leaf Demo** exercises age gates (21+), hybrid commerce "
                "(some items orderable, some inquire-only), and branch stock.\n\n"
                "All products are **fictional placeholders** for platform testing. "
                "Operators must ensure local legality before any real catalog."
            ),
            hero_headline="Demo dispensary flows.",
            hero_subhead="Age gate, compliance copy, stocked flower, and inquire-only specialty.",
            featured_item="Demo Citrus Haze 3.5g",
            benefits=[
                {"n": "01", "title": "Age gate 21+", "body": "Compliance age gate from brand flags."},
                {"n": "02", "title": "Hybrid CTAs", "body": "Order vs inquire per SKU."},
                {"n": "03", "title": "Stocked products", "body": "Flower and pre-rolls track inventory."},
                {"n": "04", "title": "Lead capture", "body": "Wholesale inquire flow for testing."},
            ],
            faq=[
                {"q": "Is this a real shop?", "a_md": "No — fictional demo catalog only."},
                {"q": "Why age gate?", "a_md": "Tests brand.age_gate_enabled + min_age + compliance copy."},
            ],
            compliance={
                "age_gate": {
                    "title": "Are you 21 or older?",
                    "body_md": (
                        "This **demo** storefront simulates an adult-only catalog. "
                        "You must be of legal age in your jurisdiction to continue. "
                        "Fictional products only."
                    ),
                    "confirm_label": "I am 21 or older",
                    "deny_label": "I am under 21",
                    "deny_redirect_url": "https://www.google.com",
                    "footer_note": "Adult demo catalog — not a real dispensary",
                    "disclaimer_lines": [
                        "For adults of legal age only. Demo data — not for sale.",
                    ],
                },
                "footer_warnings": [
                    "Adults only demo. Fictional products. Not medical advice. Not a real dispensary.",
                ],
                "product_disclaimer_title": "Adult product notice",
                "product_disclaimer_md": (
                    "Fictional herb retail SKUs for platform testing. "
                    "Sale and possession are regulated — operators must comply locally."
                ),
                "disclaimers": [
                    {
                        "id": "demo_herb",
                        "title": "Demo only",
                        "body": "No real controlled substances. Placeholder catalog.",
                        "placement": "footer",
                    }
                ],
                "legal_note": "White-label age-gate + hybrid commerce test vertical.",
                "show_dbd_in_footer": True,
            },
            modules=None,
            channels_web_mask={
                "checkout": True,
                "cart": True,
                "portfolio": True,
                "leads": True,
            },
            ticker="ADULTS 21+ · DEMO ONLY · FICTIONAL SKUS · NOT A REAL DISPENSARY",
        ),
        "stores": [
            {
                "name": "Sukhumvit Lounge",
                "slug": "sukhumvit",
                "address": "12/3 Sukhumvit Soi 33, Khlong Tan Nuea, Watthana, Bangkok 10110",
                "phone": "+66822220001",
                "lat": 13.7360,
                "lng": 100.5650,
                "is_default": True,
            },
            {
                "name": "Rama 9 Kiosk",
                "slug": "rama9",
                "address": "Central Rama 9, 9/9 Ratchadaphisek Road, Din Daeng, Bangkok 10310",
                "phone": "+66822220002",
                "lat": 13.7580,
                "lng": 100.5655,
                "is_default": False,
            },
            {
                "name": "Asok Counter",
                "slug": "asok",
                "address": "1 Asok Montri Road, Khlong Toei Nuea, Watthana, Bangkok 10110",
                "phone": "+66822220003",
                "lat": 13.7372,
                "lng": 100.5604,
                "is_default": False,
            },
        ],
        "menu": {
            ("Flower", 1): [
                (
                    "Demo Citrus Haze 3.5g",
                    590,
                    "Fictional citrus-forward flower jar. Demo SKU.",
                    "product",
                    50,
                    None,
                    None,
                    {**HERB_AMOUNT},
                    "ph-herb-flower.png",
                    True,
                ),
                (
                    "Demo Midnight Kush 3.5g",
                    620,
                    "Fictional dark berry flower jar.",
                    "product",
                    40,
                    None,
                    None,
                    {**HERB_AMOUNT},
                    "ph-herb-flower.png",
                    False,
                ),
            ],
            ("Pre-rolls", 2): [
                ("Demo Classic Pre-roll", 180, "Single demo pre-roll.", "product", 100, None, None, None, "ph-herb-preroll.png", False),
                ("Demo 5-Pack Pre-rolls", 750, "Five-pack demo bundle.", "product", 30, None, None, None, "ph-herb-preroll.png", False),
            ],
            ("Edibles", 3): [
                (
                    "Demo Gummies 10pc",
                    450,
                    "Fictional gummy pack — inquire for bulk.",
                    "product",
                    25,
                    None,
                    None,
                    None,
                    "ph-herb-edible.png",
                    False,
                ),
            ],
            ("Vapes & Gear", 4): [
                (
                    "Demo Disposable Vape",
                    890,
                    "Fictional disposable — demo product.",
                    "product",
                    20,
                    None,
                    None,
                    None,
                    "ph-herb-vape.png",
                    False,
                ),
                (
                    "Demo Glass Pipe",
                    350,
                    "Accessory — inquiry-only specialty in hybrid mode.",
                    "product",
                    15,
                    None,
                    None,
                    None,
                    "ph-herb-access.png",
                    False,
                ),
            ],
        },
        # item names that should be inquiry_only even in hybrid
        "inquiry_only_items": {"Demo Glass Pipe", "Demo Gummies 10pc"},
    }


def _bakery_spec() -> dict[str, Any]:
    return {
        "slug": "bakery-demo",
        "name": "Morning Crust Demo",
        "legal_name": "Morning Crust Demo Co., Ltd.",
        "dbd_number": "0105553333003",
        "support_email": "hello@bakery-demo.local",
        "support_phone": "+66823330001",
        "description": "Neighborhood bakery demo — bread, viennoiserie, cakes with daily limits.",
        "commerce_mode": "full_store",
        "age_gate_enabled": False,
        "min_age": None,
        "logo": "ph-bakery-logo.png",
        "web_profile": _base_web(
            theme_name="ig_default",
            tokens=PALETTE_BAKERY,
            tagline="Fresh loaves · demo croissants · preorder cakes",
            nav_catalog="Menu",
            about_title="The oven",
            about_body=(
                "Bakery vertical for **daily limits**, product stock (loaves), "
                "and prepared custom cakes.\n\nDemo only."
            ),
            hero_headline="Warm crust. Cold butter.",
            hero_subhead="Test daily_limit on pastries and stocked bread inventory.",
            featured_item="Bake Sourdough Loaf",
            benefits=[
                {"n": "01", "title": "Daily limits", "body": "Croissants cap daily sold count."},
                {"n": "02", "title": "Stocked bread", "body": "Loaves are product inventory."},
                {"n": "03", "title": "Cake preorder", "body": "Prepared cake with prep time."},
                {"n": "04", "title": "Three ovens", "body": "Ekkamai, Ari, and Charoen Krung branches."},
            ],
            faq=[{"q": "Same-day cakes?", "a_md": "Demo cake has prep_time_minutes for kitchen ETA tests."}],
            compliance={
                "footer_warnings": ["Demo bakery. Sample allergens on items."],
                "legal_note": "Bakery vertical harness.",
                "show_dbd_in_footer": True,
            },
        ),
        "stores": [
            {
                "name": "Ekkamai Oven",
                "slug": "ekkamai",
                "address": "20 Sukhumvit 63 (Ekkamai), Khlong Tan Nuea, Watthana, Bangkok 10110",
                "phone": "+66823330001",
                "lat": 13.7245,
                "lng": 100.5850,
                "is_default": True,
            },
            {
                "name": "Ari Bakehouse",
                "slug": "ari",
                "address": "14 Phahonyothin Soi 7, Samsen Nai, Phaya Thai, Bangkok 10400",
                "phone": "+66823330002",
                "lat": 13.7821,
                "lng": 100.5440,
                "is_default": False,
            },
            {
                "name": "Charoen Krung Loaf",
                "slug": "charoenkrung",
                "address": "1120 Charoen Krung Road, Bang Rak, Bang Rak, Bangkok 10500",
                "phone": "+66823330003",
                "lat": 13.7235,
                "lng": 100.5145,
                "is_default": False,
            },
        ],
        "menu": {
            ("Bread", 1): [
                ("Bake Sourdough Loaf", 120, "Country loaf demo.", "product", 30, None, "gluten", None, "ph-bakery-bread.png", True),
                ("Bake Multigrain Loaf", 110, "Seeded loaf demo.", "product", 25, None, "gluten", None, "ph-bakery-bread.png", False),
            ],
            ("Viennoiserie", 2): [
                ("Bake Butter Croissant", 55, "Classic croissant — daily cap.", "prepared", 0, 0, "gluten,dairy", None, "ph-bakery-croissant.png", False),
                ("Bake Pain au Chocolat", 65, "Chocolate stick demo.", "prepared", 0, 0, "gluten,dairy", None, "ph-bakery-croissant.png", False),
            ],
            ("Sweets", 3): [
                ("Bake Chocolate Cookie", 45, "Chunky cookie demo.", "product", 60, None, "gluten,egg,dairy", None, "ph-bakery-cookie.png", False),
                ("Bake Birthday Cake", 890, "6-inch demo cake (prep).", "prepared", 0, 90, "gluten,egg,dairy", None, "ph-bakery-cake.png", False),
            ],
        },
        "daily_limits": {"Bake Butter Croissant": 40, "Bake Pain au Chocolat": 30},
    }


def _grocery_spec() -> dict[str, Any]:
    return {
        "slug": "grocery-demo",
        "name": "Corner Mart Demo",
        "legal_name": "Corner Mart Demo Co., Ltd.",
        "dbd_number": "0105554444004",
        "support_email": "hello@grocery-demo.local",
        "support_phone": "+66824440001",
        "description": "Mini-mart demo focused on product inventory, multi-branch stock, and simple cart.",
        "commerce_mode": "full_store",
        "age_gate_enabled": False,
        "min_age": None,
        "logo": "ph-grocery-logo.png",
        "web_profile": _base_web(
            theme_name="ig_default",
            tokens=PALETTE_GROCERY,
            tagline="Water · snacks · dairy · produce — stocked for cart tests",
            nav_catalog="Aisles",
            about_title="The mart",
            about_body=(
                "Convenience store vertical for **branch inventory** isolation tests. "
                "All items are products with stock per store."
            ),
            hero_headline="Grab-and-go demo stock.",
            hero_subhead="Deplete branch inventory, then confirm sold-out badges.",
            featured_item="Demo Sparkling Water 500ml",
            benefits=[
                {"n": "01", "title": "Branch stock", "body": "Same SKU, different counts per store."},
                {"n": "02", "title": "Sold out path", "body": "Set stock low to test unavailable CTAs."},
                {"n": "03", "title": "No prep", "body": "Pure product cart/checkout path."},
                {"n": "04", "title": "Three stores", "body": "Silom, On Nut, and Ladprao stock splits."},
            ],
            faq=[{"q": "Why multiple stores?", "a_md": "Test branch inventory isolation in checkout."}],
            compliance={
                "footer_warnings": ["Demo mini-mart. Not a real retailer."],
                "legal_note": "Grocery inventory harness.",
                "show_dbd_in_footer": True,
            },
        ),
        "stores": [
            {
                "name": "Silom Corner",
                "slug": "silom",
                "address": "88/2 Silom Road, Suriyawong, Bang Rak, Bangkok 10500",
                "phone": "+66824440001",
                "lat": 13.7260,
                "lng": 100.5280,
                "is_default": True,
            },
            {
                "name": "On Nut Corner",
                "slug": "onnut",
                "address": "1 Sukhumvit Road (Soi 77), Phra Khanong, Suan Luang, Bangkok 10250",
                "phone": "+66824440002",
                "lat": 13.7055,
                "lng": 100.6010,
                "is_default": False,
            },
            {
                "name": "Ladprao Express",
                "slug": "ladprao",
                "address": "333 Ratchadaphisek Road, Chatuchak, Chatuchak, Bangkok 10900",
                "phone": "+66824440003",
                "lat": 13.8165,
                "lng": 100.5615,
                "is_default": False,
            },
        ],
        "menu": {
            ("Drinks", 1): [
                ("Demo Sparkling Water 500ml", 25, "Bottle demo.", "product", 200, None, None, None, "ph-grocery-water.png", True),
                ("Demo Cola Can", 20, "330ml demo can.", "product", 150, None, None, None, "ph-grocery-water.png", False),
            ],
            ("Snacks", 2): [
                ("Demo Potato Chips", 35, "Salted chips demo.", "product", 80, None, "gluten", None, "ph-grocery-snack.png", False),
                ("Demo Mixed Nuts", 55, "Snack tin demo.", "product", 40, None, "peanut", None, "ph-grocery-snack.png", False),
            ],
            ("Dairy", 3): [
                ("Demo Fresh Milk 1L", 45, "Chilled milk demo.", "product", 60, None, "dairy", None, "ph-grocery-dairy.png", False),
                ("Demo Yogurt Cup", 30, "Plain yogurt demo.", "product", 70, None, "dairy", None, "ph-grocery-dairy.png", False),
            ],
            ("Produce", 4): [
                ("Demo Banana Bunch", 40, "Produce demo.", "product", 35, None, None, None, "ph-grocery-produce.png", False),
                ("Demo Tomato Pack", 35, "Cherry tomato demo pack.", "product", 40, None, None, None, "ph-grocery-produce.png", False),
            ],
        },
        # optional per-store stock overrides: {store_slug: {item_name: qty}}
        "branch_stock": {
            "silom": {"Demo Sparkling Water 500ml": 5, "Demo Cola Can": 2},  # low for sold-out tests
            "onnut": {"Demo Sparkling Water 500ml": 120},
            "ladprao": {"Demo Sparkling Water 500ml": 80, "Demo Cola Can": 50},
        },
    }


def _food_kitchen_spec() -> dict[str, Any]:
    """Thai kitchen — mirrors seed_food_demo names so either seeder is safe."""
    return {
        "slug": "food-demo",
        "name": "Bangkok Kitchen Demo",
        "legal_name": "Bangkok Kitchen Demo Co., Ltd.",
        "dbd_number": "0105559876543",
        "support_email": "hello@food-demo.local",
        "support_phone": "+66820000001",
        "description": (
            "Multi-branch Thai restaurant demo for white-label full-store testing. "
            "Menu and copy come from the database."
        ),
        "commerce_mode": "full_store",
        "age_gate_enabled": False,
        "min_age": None,
        "logo": "ph-food-logo.png",
        "web_profile": _base_web(
            theme_name="ig_default",
            tokens=PALETTE_FOOD,
            tagline="Everyday Thai comfort food — kitchen-fresh, branch delivery ready",
            nav_catalog="Menu",
            about_title="Our kitchen",
            about_body=(
                "Generic **food-store** template with spice modifiers, prepared dishes, "
                "and packaged drink inventory."
            ),
            hero_headline="Hot wok. Cold drinks. Fast riders.",
            hero_subhead="Full-store Thai kitchen demo for cart + delivery flows.",
            featured_item="Demo Pad Thai",
            benefits=[
                {"n": "01", "title": "Wok mains", "body": "Prepared dishes, unlimited stock."},
                {"n": "02", "title": "Modifiers", "body": "Spice + extras on many dishes."},
                {"n": "03", "title": "Drink stock", "body": "Products track branch inventory."},
                {"n": "04", "title": "Three kitchens", "body": "Sukhumvit, Silom, and Thonglor."},
            ],
            faq=[
                {"q": "Delivery?", "a_md": "Enable delivery caps on the brand channel to test."},
                {"q": "Spice levels?", "a_md": "Stored on Goods.modifiers JSON."},
            ],
            compliance={
                "footer_warnings": ["Demo restaurant catalog only."],
                "product_disclaimer_md": "Allergens listed per item. Demo only.",
                "legal_note": "Food vertical harness.",
                "show_dbd_in_footer": True,
            },
        ),
        "stores": [
            {
                "name": "Sukhumvit Kitchen",
                "slug": "sukhumvit",
                "address": "42/8 Sukhumvit Soi 22, Khlong Tan, Khlong Toei, Bangkok 10110",
                "phone": "+66820000001",
                "lat": 13.7383,
                "lng": 100.5601,
                "is_default": True,
            },
            {
                "name": "Silom Kitchen",
                "slug": "silom",
                "address": "130/5 Silom Road, Suriyawong, Bang Rak, Bangkok 10500",
                "phone": "+66820000002",
                "lat": 13.7280,
                "lng": 100.5340,
                "is_default": False,
            },
            {
                "name": "Thonglor Kitchen",
                "slug": "thonglor",
                "address": "9 Sukhumvit 55 (Thong Lo), Khlong Tan Nuea, Watthana, Bangkok 10110",
                "phone": "+66820000003",
                "lat": 13.7330,
                "lng": 100.5820,
                "is_default": False,
            },
        ],
        "menu": {
            ("Food Starters", 1): [
                ("Demo Spring Rolls", 80, "Crispy vegetable rolls.", "prepared", 0, 8, "gluten", None, "ph-food-salad.png", False),
                ("Demo Papaya Salad", 90, "Som tam style demo.", "prepared", 0, 7, "fish,peanut", {**SPICE}, "ph-food-salad.png", False),
            ],
            ("Food Mains", 2): [
                ("Demo Pad Thai", 120, "Stir-fried noodles demo.", "prepared", 0, 12, "shellfish,peanut,egg", {**SPICE, **EXTRAS_FOOD}, "ph-food-padthai.png", True),
                ("Demo Basil Chicken Rice", 130, "Pad krapow style demo.", "prepared", 0, 10, None, {**SPICE, **EXTRAS_FOOD}, "ph-food-rice.png", False),
                ("Demo Green Curry", 150, "Coconut curry demo.", "prepared", 0, 15, "fish", {**SPICE}, "ph-food-curry.png", False),
            ],
            ("Food Drinks", 3): [
                ("Demo Thai Iced Tea", 60, "Sweet tea demo.", "prepared", 0, 4, "dairy", None, "ph-food-drink.png", False),
                ("Demo Coconut Water", 55, "Packaged coconut water.", "product", 120, None, None, None, "ph-food-drink.png", False),
                ("Demo Bottled Water", 25, "Still water 500ml.", "product", 300, None, None, None, "ph-food-drink.png", False),
            ],
            ("Food Desserts", 4): [
                ("Demo Mango Sticky Rice", 95, "Sweet rice demo.", "prepared", 0, 6, None, None, "ph-food-dessert.png", False),
                ("Demo Coconut Ice Cream", 70, "Scoop demo product.", "product", 80, None, "dairy", None, "ph-food-dessert.png", False),
            ],
        },
    }


VERTICAL_BUILDERS = {
    "food": _food_kitchen_spec,
    "coffee": _coffee_spec,
    "herb": _herb_spec,
    "bakery": _bakery_spec,
    "grocery": _grocery_spec,
}

VERTICAL_SLUGS = {
    "food": "food-demo",
    "coffee": "coffee-demo",
    "herb": "herb-demo",
    "bakery": "bakery-demo",
    "grocery": "grocery-demo",
}


def _ensure_role(session) -> None:
    if session.query(Role).filter_by(name="USER").first() is None:
        session.add(Role(name="USER", permissions=1))
        session.flush()


def seed_vertical(spec: dict[str, Any], *, force: bool = False) -> dict[str, Any]:
    """Upsert one vertical brand from a spec dict."""
    ensure_all_placeholders(force=False)
    slug = spec["slug"]
    inquiry_only = set(spec.get("inquiry_only_items") or [])
    daily_limits = dict(spec.get("daily_limits") or {})
    branch_stock = dict(spec.get("branch_stock") or {})
    # Always store contrast-safe theme tokens
    web_profile = deepcopy(spec["web_profile"])
    if isinstance(web_profile.get("theme_tokens"), dict):
        web_profile["theme_tokens"] = enforce_theme_tokens(web_profile["theme_tokens"])

    with Database().session() as s:
        _ensure_role(s)
        brand = s.query(Brand).filter_by(slug=slug).one_or_none()
        if brand and not force:
            n_goods = s.query(Goods).filter_by(brand_id=brand.id).count()
            n_stores = s.query(Store).filter_by(brand_id=brand.id).count()
            if n_goods and n_stores:
                brand.web_profile = web_profile
                brand.commerce_mode = spec["commerce_mode"]
                brand.age_gate_enabled = bool(spec["age_gate_enabled"])
                brand.min_age = spec.get("min_age")
                s.commit()
                return {
                    "slug": slug,
                    "products": n_goods,
                    "stores": n_stores,
                    "skipped": True,
                    "commerce_mode": spec["commerce_mode"],
                    "template": slug,
                }

        logo = local_ref(spec["logo"]) if spec.get("logo") else None
        if brand is None:
            brand = Brand(
                name=spec["name"],
                slug=slug,
                description=spec.get("description"),
                legal_name=spec.get("legal_name"),
                dbd_number=spec.get("dbd_number"),
                support_email=spec.get("support_email"),
                support_phone=spec.get("support_phone"),
                commerce_mode=spec["commerce_mode"],
                age_gate_enabled=bool(spec["age_gate_enabled"]),
                min_age=spec.get("min_age"),
                timezone="Asia/Bangkok",
                web_profile=web_profile,
                logo_file_id=logo,
            )
            s.add(brand)
            s.flush()
        else:
            brand.name = spec["name"]
            brand.description = spec.get("description")
            brand.legal_name = spec.get("legal_name") or brand.legal_name
            brand.dbd_number = spec.get("dbd_number") or brand.dbd_number
            brand.support_email = spec.get("support_email") or brand.support_email
            brand.support_phone = spec.get("support_phone") or brand.support_phone
            brand.commerce_mode = spec["commerce_mode"]
            brand.age_gate_enabled = bool(spec["age_gate_enabled"])
            brand.min_age = spec.get("min_age")
            brand.web_profile = web_profile
            if logo:
                brand.logo_file_id = logo
            brand.timezone = brand.timezone or "Asia/Bangkok"

        stores: list[Store] = []
        for st_def in spec["stores"]:
            st = s.query(Store).filter_by(brand_id=brand.id, slug=st_def["slug"]).one_or_none()
            if st is None:
                st = s.query(Store).filter_by(brand_id=brand.id, name=st_def["name"]).one_or_none()
            if st is None:
                st = Store(
                    name=st_def["name"],
                    slug=st_def["slug"],
                    brand_id=brand.id,
                    address=st_def.get("address"),
                    phone=st_def.get("phone"),
                    latitude=st_def.get("lat"),
                    longitude=st_def.get("lng"),
                    is_default=bool(st_def.get("is_default")),
                    is_active=True,
                    web_profile={
                        "schema_version": 1,
                        "about_md": f"Demo branch: {st_def['name']}.\n\n{st_def.get('address') or ''}",
                        "amenities": ["pickup", "demo"],
                        "pickup_notes_md": f"**Address:** {st_def.get('address') or '—'}\n\n**Phone:** {st_def.get('phone') or '—'}",
                    },
                )
                s.add(st)
            else:
                st.slug = st_def["slug"]
                st.name = st_def["name"]
                st.address = st_def.get("address")
                st.phone = st_def.get("phone")
                st.latitude = st_def.get("lat")
                st.longitude = st_def.get("lng")
                st.is_default = bool(st_def.get("is_default"))
                st.is_active = True
                st.web_profile = {
                    "schema_version": 1,
                    "about_md": f"Demo branch: {st_def['name']}.\n\n{st_def.get('address') or ''}",
                    "amenities": ["pickup", "demo"],
                    "pickup_notes_md": f"**Address:** {st_def.get('address') or '—'}\n\n**Phone:** {st_def.get('phone') or '—'}",
                }
            stores.append(st)
        s.flush()

        product_names: list[str] = []
        created = 0
        for (cat_name, sort_order), items in spec["menu"].items():
            cat = s.query(Categories).filter_by(name=cat_name).one_or_none()
            if cat is None:
                s.add(
                    Categories(
                        name=cat_name,
                        brand_id=brand.id,
                        sort_order=sort_order,
                        description=f"Demo: {cat_name}",
                    )
                )
            else:
                cat.brand_id = brand.id
                cat.sort_order = sort_order

            for row in items:
                name, price, desc, itype, stock, prep, allergens, mods, image, _featured = row
                existing = s.query(Goods).filter_by(name=name).one_or_none()
                img_ref = local_ref(image) if image else None
                is_inq = name in inquiry_only
                # hybrid + inquiry_only → not web_orderable
                web_orderable = not is_inq
                if existing:
                    g = existing
                    g.brand_id = brand.id
                    g.category_name = cat_name
                    g.price = Decimal(str(price))
                    g.description = desc
                    g.item_type = itype
                    g.stock_quantity = stock
                    g.prep_time_minutes = prep
                    g.allergens = allergens
                    g.modifiers = mods
                    g.is_active = True
                    g.web_listable = True
                    g.web_orderable = web_orderable
                    g.inquiry_only = is_inq
                    if img_ref:
                        g.image_file_id = img_ref
                    if name in daily_limits:
                        g.daily_limit = daily_limits[name]
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
                        image_file_id=img_ref,
                        daily_limit=daily_limits.get(name),
                    )
                    g.web_listable = True
                    g.web_orderable = web_orderable
                    g.inquiry_only = is_inq
                    s.add(g)
                    created += 1
                if itype == "product":
                    product_names.append(name)
        s.flush()

        inv_created = 0
        for item_name in product_names:
            for st in stores:
                inv = (
                    s.query(BranchInventory)
                    .filter_by(store_id=st.id, item_name=item_name)
                    .one_or_none()
                )
                qty = 100
                overrides = branch_stock.get(st.slug) or {}
                if item_name in overrides:
                    qty = int(overrides[item_name])
                if inv is None:
                    s.add(
                        BranchInventory(
                            store_id=st.id,
                            item_name=item_name,
                            stock_quantity=qty,
                            reserved_quantity=0,
                        )
                    )
                    inv_created += 1
                elif force:
                    inv.stock_quantity = qty

        s.commit()
        total = s.query(Goods).filter_by(brand_id=brand.id).count()
        n_stores = s.query(Store).filter_by(brand_id=brand.id).count()
        logger.info(
            "Vertical ready slug=%s products=%s stores=%s created=%s inv=%s",
            slug,
            total,
            n_stores,
            created,
            inv_created,
        )
        return {
            "slug": slug,
            "products": total,
            "stores": n_stores,
            "created": created,
            "branch_inventory": inv_created,
            "commerce_mode": spec["commerce_mode"],
            "template": slug,
            "age_gate": bool(spec["age_gate_enabled"]),
        }


def seed_named_vertical(name: str, *, force: bool = False) -> dict[str, Any]:
    key = name.strip().lower().replace("_demo", "").replace("-demo", "")
    # allow slug form coffee-demo
    for k, slug in VERTICAL_SLUGS.items():
        if key in (k, slug, slug.replace("-demo", "")):
            return seed_vertical(VERTICAL_BUILDERS[k](), force=force)
    raise ValueError(f"unknown vertical: {name!r} (choose {list(VERTICAL_BUILDERS)})")


def seed_all_verticals(*, force: bool = False) -> list[dict[str, Any]]:
    ensure_all_placeholders(force=False)
    results = []
    for key in VERTICAL_BUILDERS:
        results.append(seed_vertical(VERTICAL_BUILDERS[key](), force=force))
    return results


def seed_all_demos(*, force: bool = False, snus: bool = True) -> list[dict[str, Any]]:
    """Snus editorial + all commerce verticals."""
    out: list[dict[str, Any]] = []
    if snus:
        from bot.services.seed_snus_demo import seed_snus_demo

        out.append(seed_snus_demo(force=force))
    out.extend(seed_all_verticals(force=force))
    return out
