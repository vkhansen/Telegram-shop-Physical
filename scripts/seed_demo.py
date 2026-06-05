#!/usr/bin/env python3
"""Populate a deployment with a realistic, valid menu + multi-branch tree.

Unlike scripts/fuzz_seed.py (random data for testing), this seeds a coherent
demo restaurant: one brand with three named branches and a full Thai menu
(categories, prepared dishes, packaged drinks with stock, modifiers, allergens,
per-branch inventory).

Targets brand_id=1 by default — the brand single-bot mode (MULTI_BOT_ENABLED=
false) injects into every handler, so the running bot will actually show this
menu. Idempotent: existing categories/items/branches (matched by name) are left
untouched, so it is safe to re-run. Validates integrity before committing.

    python scripts/seed_demo.py            # seed brand 1
    python scripts/seed_demo.py --brand-id 5
"""

import argparse
import logging
import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from bot.database.integrity import Severity, check_integrity, summarize  # noqa: E402
from bot.database.main import Database  # noqa: E402
from bot.database.models.main import BranchInventory, Brand, Categories, Goods, Store  # noqa: E402

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

# (category, sort_order) -> list of items
# item: (name, price, description, type, stock, prep, allergens, modifiers)
BRANCHES = [
    ("Sukhumvit Branch", 13.7383, 100.5601, "0820000001", True),
    ("Silom Branch", 13.7280, 100.5340, "0820000002", False),
    ("Thonglor Branch", 13.7330, 100.5820, "0820000003", False),
]

MENU = {
    ("Starters", 1): [
        ("Spring Rolls", 80, "Crispy vegetable spring rolls (4 pcs)", "prepared", 0, 8, "gluten", None),
        ("Chicken Satay", 120, "Grilled chicken skewers with peanut sauce", "prepared", 0, 12, "peanut", None),
        ("Papaya Salad", 90, "Som tam with lime and chili", "prepared", 0, 7, "fish,peanut", {**SPICE}),
    ],
    ("Main Dishes", 2): [
        (
            "Pad Thai",
            120,
            "Stir-fried rice noodles with shrimp",
            "prepared",
            0,
            12,
            "shellfish,peanut,egg",
            {**SPICE, **EXTRAS},
        ),
        ("Pad See Ew", 110, "Wide noodles in sweet soy with chicken", "prepared", 0, 12, "gluten,egg", {**EXTRAS}),
        (
            "Basil Chicken Rice",
            130,
            "Stir-fried minced chicken with holy basil",
            "prepared",
            0,
            10,
            None,
            {**SPICE, **EXTRAS},
        ),
    ],
    ("Curries", 3): [
        ("Green Curry", 150, "Coconut green curry with chicken", "prepared", 0, 15, "fish", {**SPICE}),
        ("Massaman Curry", 160, "Rich peanut curry with beef and potato", "prepared", 0, 18, "peanut", {**SPICE}),
        ("Red Curry", 150, "Coconut red curry with vegetables", "prepared", 0, 15, "fish", {**SPICE}),
    ],
    ("Drinks", 4): [
        ("Thai Iced Tea", 60, "Sweet creamy iced tea", "prepared", 0, 4, "dairy", None),
        ("Coconut Water", 55, "Fresh young coconut water", "product", 120, None, None, None),
        ("Singha Beer", 90, "Bottled lager 330ml", "product", 200, None, "gluten", None),
        ("Bottled Water", 25, "Still water 500ml", "product", 300, None, None, None),
    ],
    ("Desserts", 5): [
        ("Mango Sticky Rice", 95, "Sweet sticky rice with fresh mango", "prepared", 0, 6, None, None),
        ("Coconut Ice Cream", 70, "Homemade coconut ice cream", "product", 80, None, "dairy", None),
    ],
}


def seed_demo(session, brand_id: int) -> dict:
    brand = session.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise SystemExit(f"Brand id={brand_id} does not exist — run the bot once to create the default brand.")

    counts = {"branches": 0, "categories": 0, "items": 0, "branch_inventory": 0, "skipped": 0}

    # Branches
    stores: list[Store] = []
    for name, lat, lng, phone, is_default in BRANCHES:
        existing = session.query(Store).filter_by(brand_id=brand_id, name=name).first()
        if existing:
            stores.append(existing)
            counts["skipped"] += 1
            continue
        store = Store(
            name=name,
            brand_id=brand_id,
            latitude=lat,
            longitude=lng,
            phone=phone,
            is_default=is_default,
            address=f"{name}, Bangkok",
        )
        session.add(store)
        stores.append(store)
        counts["branches"] += 1
    session.flush()

    # Categories + items
    product_items: list[str] = []
    for (cat_name, sort_order), items in MENU.items():
        if not session.query(Categories).filter_by(name=cat_name).first():
            session.add(Categories(name=cat_name, brand_id=brand_id, sort_order=sort_order))
            counts["categories"] += 1
        for name, price, desc, itype, stock, prep, allergens, mods in items:
            if session.query(Goods).filter_by(name=name).first():
                counts["skipped"] += 1
                if itype == "product":
                    product_items.append(name)
                continue
            g = Goods(
                name=name,
                brand_id=brand_id,
                category_name=cat_name,
                price=price,
                description=desc,
                item_type=itype,
                stock_quantity=stock,
                prep_time_minutes=prep,
                allergens=allergens,
                modifiers=mods,
            )
            session.add(g)
            counts["items"] += 1
            if itype == "product":
                product_items.append(name)
    session.flush()

    # Per-branch inventory for packaged products
    for item_name in product_items:
        for store in stores:
            if session.query(BranchInventory).filter_by(store_id=store.id, item_name=item_name).first():
                continue
            session.add(
                BranchInventory(store_id=store.id, item_name=item_name, stock_quantity=100, reserved_quantity=0)
            )
            counts["branch_inventory"] += 1
    session.flush()
    return counts


def main() -> int:
    p = argparse.ArgumentParser(description="Seed a realistic demo menu + branches.")
    p.add_argument("--brand-id", type=int, default=1, help="Target brand id (default 1 = single-bot brand).")
    args = p.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    with Database().session() as session:
        counts = seed_demo(session, args.brand_id)
        violations = check_integrity(session)
        errs = [v for v in violations if v.severity is Severity.ERROR]
        if errs:
            for v in errs:
                logging.error(str(v))
            logging.error("Seed produced integrity errors — rolling back.")
            session.rollback()
            return 1
        logging.info("Seeded demo data: %s", counts)
        logging.info("Integrity after seed: %s", summarize(violations))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
