#!/usr/bin/env python3
"""Fuzzing seed generator for a test database.

Produces randomized-but-referentially-valid data — a varying number of brands,
each with a random number of stores/branches, categories, menu items (mixed
prepared/product), modifiers, staff, and per-branch inventory. The *shape* is
fuzzed (counts, types, optional fields, multi-store layouts); the *graph* is
always valid, and the generator self-checks with bot.database.integrity before
returning.

Deterministic: same ``--seed`` ⇒ same dataset. Re-runnable: ``--clean`` wipes
any previously generated fuzz data first (identified by the ``fuzz-`` brand-slug
prefix and a reserved fuzz user-id range).

Usage:
    python scripts/fuzz_seed.py --seed 42 --brands 5
    python scripts/fuzz_seed.py --clean-only
    python scripts/fuzz_seed.py --chaos          # inject broken configs, show validator catching them

For e2e tests, import generate_fuzz_data() / inject_chaos() and pass a session.
"""
from __future__ import annotations

import argparse
import logging
import os
import random
import sys

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from sqlalchemy.orm import Session

from bot.database.main import Database
from bot.database.integrity import check_integrity, summarize, Severity
from bot.database.models.main import (
    Brand, BotConfig, BranchInventory, BrandStaff, Categories, Goods, Role, Store, User,
)

FUZZ_SLUG_PREFIX = "fuzz-"
FUZZ_USER_BASE = 8_100_000_000
FUZZ_USER_SPAN = 1_000_000
FUZZ_TOKEN_PREFIX = "FUZZ:"

_CUISINES = ["Thai", "Afghan", "Italian", "Cafe", "Sushi", "Burger", "Vegan", "BBQ"]
_CATEGORY_WORDS = ["Starters", "Mains", "Curries", "Salads", "Drinks", "Desserts",
                   "Breakfast", "Sides", "Specials", "Grill"]
_ITEM_WORDS = ["Pad Thai", "Green Curry", "Mango Sticky Rice", "Iced Latte", "Spring Roll",
               "Tom Yum", "Fried Rice", "Lemonade", "Cheesecake", "Espresso", "Kebab", "Soup"]
_ROLES = ["admin", "kitchen", "rider"]


def _base_role_id(session: Session) -> int:
    """Return an existing role id, creating a minimal USER role if none exist."""
    row = session.query(Role.id).order_by(Role.id).first()
    if row:
        return row[0]
    role = Role(name="USER", permissions=0)
    session.add(role)
    session.flush()
    return role.id


def _maybe_modifiers(rng: random.Random) -> dict | None:
    if rng.random() > 0.3:
        return None
    return {
        "spice_level": {
            "label": "Spice Level", "type": "single", "required": True,
            "options": [
                {"id": "mild", "label": "Mild", "price": 0},
                {"id": "hot", "label": "Hot", "price": 0},
            ],
        }
    }


def generate_fuzz_data(session: Session, rng: random.Random, num_brands: int = 3) -> dict:
    """Create `num_brands` fully-valid fuzzed brands. Returns a counts summary."""
    role_id = _base_role_id(session)
    counts = {"brands": 0, "stores": 0, "categories": 0, "items": 0,
              "staff": 0, "branch_inventory": 0, "users": 0}
    cat_counter = item_counter = 0

    for b in range(num_brands):
        token = f"{rng.randrange(10**9):09d}"
        cuisine = rng.choice(_CUISINES)
        brand = Brand(
            name=f"Fuzz {cuisine} {b}-{token}",
            slug=f"{FUZZ_SLUG_PREFIX}{b}-{token}",
            description=f"Fuzz-generated {cuisine} brand",
            promptpay_id=f"0{rng.randrange(10**9):09d}",
            promptpay_name=f"Fuzz {cuisine} {b}",
        )
        session.add(brand)
        session.flush()  # assign brand.id
        counts["brands"] += 1

        session.add(BotConfig(
            brand_id=brand.id,
            bot_token=f"{FUZZ_TOKEN_PREFIX}{brand.id}:{token}",
            bot_username=f"fuzz_{brand.id}_bot",
            default_language=rng.choice(["th", "en"]),
            default_currency="THB",
            payments_enabled=rng.sample(["promptpay", "cash", "bitcoin"], k=rng.randint(1, 3)),
        ))

        # Stores / branches — exactly one default.
        num_stores = rng.randint(1, 4)
        stores: list[Store] = []
        for sidx in range(num_stores):
            store = Store(
                name=f"Branch {sidx + 1}",
                brand_id=brand.id,
                address=f"{rng.randint(1, 999)} Fuzz Rd",
                latitude=round(rng.uniform(13.6, 13.9), 6),
                longitude=round(rng.uniform(100.4, 100.7), 6),
                phone=f"0{rng.randrange(10**9):09d}",
                is_default=(sidx == 0),
            )
            session.add(store)
            stores.append(store)
        session.flush()
        counts["stores"] += num_stores

        # Categories + items (names are GLOBAL primary keys → keep globally unique).
        for _ in range(rng.randint(2, 5)):
            cat_name = f"{brand.slug}:{rng.choice(_CATEGORY_WORDS)}-{cat_counter}"
            cat_counter += 1
            session.add(Categories(
                name=cat_name, brand_id=brand.id, sort_order=rng.randint(0, 20),
                description="Fuzz category",
            ))
            session.flush()
            counts["categories"] += 1

            for _ in range(rng.randint(1, 6)):
                item_name = f"{brand.slug}:{rng.choice(_ITEM_WORDS)}-{item_counter}"
                item_counter += 1
                is_product = rng.random() < 0.4
                stock = rng.randint(0, 200) if is_product else 0
                reserved = rng.randint(0, stock) if stock else 0
                item = Goods(
                    name=item_name,
                    brand_id=brand.id,           # MUST match the category's brand
                    category_name=cat_name,
                    price=round(rng.uniform(20, 500), 2),
                    description="Fuzz item",
                    item_type="product" if is_product else "prepared",
                    stock_quantity=stock,
                    prep_time_minutes=rng.choice([None, 5, 10, 15, 20]),
                    daily_limit=rng.choice([None, None, 50]),
                    modifiers=_maybe_modifiers(rng),
                )
                item.reserved_quantity = reserved
                session.add(item)
                counts["items"] += 1

                # Per-branch inventory override for product items (same brand by construction).
                if is_product and rng.random() < 0.5:
                    bstore = rng.choice(stores)
                    bstock = rng.randint(0, 100)
                    session.add(BranchInventory(
                        store_id=bstore.id, item_name=item_name,
                        stock_quantity=bstock, reserved_quantity=rng.randint(0, bstock) if bstock else 0,
                    ))
                    counts["branch_inventory"] += 1

        # Staff: an owner plus a random subset of operational roles.
        owner_uid = FUZZ_USER_BASE + counts["users"]
        session.add(User(telegram_id=owner_uid, registration_date=_now(), role_id=role_id))
        session.flush()
        counts["users"] += 1
        session.add(BrandStaff(brand_id=brand.id, user_id=owner_uid, role="owner"))
        counts["staff"] += 1
        for role_name in rng.sample(_ROLES, k=rng.randint(0, len(_ROLES))):
            uid = FUZZ_USER_BASE + counts["users"]
            session.add(User(telegram_id=uid, registration_date=_now(), role_id=role_id))
            session.flush()
            counts["users"] += 1
            # Some staff are store-scoped (to that brand's own store).
            store_id = rng.choice(stores).id if rng.random() < 0.5 else None
            session.add(BrandStaff(brand_id=brand.id, user_id=uid, role=role_name, store_id=store_id))
            counts["staff"] += 1

    session.flush()
    return counts


def inject_chaos(session: Session, rng: random.Random) -> set[str]:
    """Deliberately break a few configs. Returns the set of integrity check names
    that SHOULD fire as a result — used to prove the validator catches them."""
    expected: set[str] = set()
    items = session.query(Goods).all()
    cats = session.query(Categories).all()
    brands = session.query(Brand).all()

    if items and len(brands) >= 2:
        other = next((b.id for b in brands if b.id != items[0].brand_id), None)
        if other is not None:
            items[0].brand_id = other  # cross-brand item vs its category
            expected.add("item_category_cross_brand")
    if cats:
        cats[0].brand_id = None        # unbranded category
        expected.add("unbranded")
    if len(items) > 1:
        items[1].price = 0             # bad price
        expected.add("item_bad_price")
    if brands:
        # second default store for a brand
        b0 = brands[0].id
        for s in session.query(Store).filter(Store.brand_id == b0).all():
            s.is_default = True
        if session.query(Store).filter(Store.brand_id == b0).count() > 1:
            expected.add("brand_multiple_default_stores")
    session.flush()
    return expected


def clean_fuzz_data(session: Session) -> dict:
    """Remove all previously generated fuzz data (idempotent)."""
    fuzz_brand_ids = [bid for (bid,) in session.query(Brand.id)
                      .filter(Brand.slug.like(f"{FUZZ_SLUG_PREFIX}%")).all()]
    fuzz_store_ids = []
    if fuzz_brand_ids:
        fuzz_store_ids = [sid for (sid,) in session.query(Store.id)
                          .filter(Store.brand_id.in_(fuzz_brand_ids)).all()]
    removed = {}

    def _del(model, cond):
        return session.query(model).filter(cond).delete(synchronize_session=False)

    if fuzz_store_ids:
        removed["branch_inventory"] = _del(BranchInventory, BranchInventory.store_id.in_(fuzz_store_ids))
    if fuzz_brand_ids:
        removed["items"] = _del(Goods, Goods.brand_id.in_(fuzz_brand_ids))
        removed["categories"] = _del(Categories, Categories.brand_id.in_(fuzz_brand_ids))
        removed["staff"] = _del(BrandStaff, BrandStaff.brand_id.in_(fuzz_brand_ids))
        removed["bot_configs"] = _del(BotConfig, BotConfig.brand_id.in_(fuzz_brand_ids))
        removed["stores"] = _del(Store, Store.brand_id.in_(fuzz_brand_ids))
        removed["brands"] = _del(Brand, Brand.id.in_(fuzz_brand_ids))
    removed["users"] = _del(
        User, User.telegram_id.between(FUZZ_USER_BASE, FUZZ_USER_BASE + FUZZ_USER_SPAN))
    session.flush()
    return removed


def _now():
    # Imported lazily so this module stays import-light.
    import datetime as _dt
    return _dt.datetime.now(_dt.timezone.utc)


def _run_cli(args) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    rng = random.Random(args.seed)
    with Database().session() as session:
        if args.clean or args.clean_only:
            removed = clean_fuzz_data(session)
            logging.info("Cleaned fuzz data: %s", {k: v for k, v in removed.items() if v})
            if args.clean_only:
                return 0
        counts = generate_fuzz_data(session, rng, num_brands=args.brands)
        logging.info("Generated: %s", counts)

        if args.chaos:
            expected = inject_chaos(session, rng)
            violations = check_integrity(session)
            caught = {v.check for v in violations}
            logging.warning("Chaos injected. Expected checks to fire: %s", sorted(expected))
            logging.warning("Validator reported: %s", summarize(violations))
            missed = expected - caught
            if missed:
                logging.error("Validator MISSED: %s", sorted(missed))
                return 1
            logging.info("Validator caught all injected violations ✅")
            # Roll back chaos so we don't persist broken data.
            session.rollback()
            return 0

        violations = check_integrity(session)
        s = summarize(violations)
        if s["errors"]:
            for v in violations:
                if v.severity is Severity.ERROR:
                    logging.error(str(v))
            logging.error("Fuzz data FAILED integrity: %s", s)
            session.rollback()
            return 1
        logging.info("Fuzz data passed integrity: %s", s)
        return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Fuzzing seed generator for a test database.")
    p.add_argument("--seed", type=int, default=1337, help="RNG seed (deterministic).")
    p.add_argument("--brands", type=int, default=3, help="Number of brands to generate.")
    p.add_argument("--clean", action="store_true", help="Wipe existing fuzz data first, then generate.")
    p.add_argument("--clean-only", action="store_true", help="Only wipe existing fuzz data; generate nothing.")
    p.add_argument("--chaos", action="store_true",
                   help="Inject broken configs and verify the validator catches them (rolled back).")
    return _run_cli(p.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
