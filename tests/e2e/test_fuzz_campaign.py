"""Fuzzing campaign: generate many labeled multi-brand / multi-branch configs and
hunt edge cases — focusing on BRAND/BRANCH ISOLATION (no cross-contamination)
plus availability/inventory/currency invariants.

Run with:  pytest tests/e2e/test_fuzz_campaign.py --run-e2e -s
"""

import datetime as dt
import random
from decimal import Decimal

import pytest

from bot.database.brand_scope import brand_query
from bot.database.integrity import Severity, check_integrity
from bot.database.methods.inventory import release_reservation, reserve_inventory
from bot.database.models.main import (
    BranchInventory,
    Brand,
    BrandStaff,
    Categories,
    Goods,
    Order,
    OrderItem,
    Store,
)
from bot.utils.currency import format_currency
from scripts.fuzz_seed import generate_fuzz_data

pytestmark = [pytest.mark.e2e]

BRAND_SCOPED = (Goods, Categories, Store, BrandStaff)
# Brand-relevant tables that LACK a brand_id column → brand_query cannot filter them;
# isolation must flow through their parent (order/store). The campaign verifies that.
NO_BRAND_COLUMN = (OrderItem, BranchInventory)


def _now():
    return dt.datetime.now(dt.UTC)


# --------------------------------------------------------------------------- #
# 1. Brand / branch isolation — the core "no cross-contamination" guarantee.
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("seed", [3, 11, 77, 2024])
def test_brand_query_never_leaks_foreign_brand(db_session, seed):
    generate_fuzz_data(db_session, random.Random(seed), num_brands=6)
    brands = db_session.query(Brand).filter(Brand.slug.like("fuzz-%")).all()
    assert len(brands) == 6

    for b in brands:
        for model in BRAND_SCOPED:
            rows = brand_query(db_session, model, b.id).all()
            # No row from any other brand may appear in a brand-scoped query.
            foreign = [r for r in rows if r.brand_id != b.id]
            assert not foreign, f"{model.__name__} leaked foreign brand into brand {b.id}: {foreign}"
        # Data is *labeled* per brand (names carry the brand slug) — a leak would
        # surface as a mismatched label even if brand_id were wrong.
        for g in brand_query(db_session, Goods, b.id).all():
            assert g.name.startswith(b.slug + ":"), f"item {g.name!r} not labeled for brand {b.slug}"
        for c in brand_query(db_session, Categories, b.id).all():
            assert c.name.startswith(b.slug + ":")


def test_items_partition_cleanly_across_brands(db_session):
    generate_fuzz_data(db_session, random.Random(5), num_brands=5)
    brand_ids = [bid for (bid,) in db_session.query(Brand.id).filter(Brand.slug.like("fuzz-%"))]
    per_brand = sum(brand_query(db_session, Goods, bid).count() for bid in brand_ids)
    total = db_session.query(Goods).count()
    # Every item belongs to exactly one brand — no shared/orphaned items.
    assert per_brand == total
    assert db_session.query(Goods).filter(Goods.brand_id.is_(None)).count() == 0


def test_branch_inventory_isolated_to_its_brand(db_session):
    generate_fuzz_data(db_session, random.Random(9), num_brands=5)
    store_brand = {s.id: s.brand_id for s in db_session.query(Store).all()}
    item_brand = {g.name: g.brand_id for g in db_session.query(Goods).all()}
    for bi in db_session.query(BranchInventory).all():
        # A branch's inventory may only reference items of the branch's own brand.
        assert store_brand[bi.store_id] == item_brand[bi.item_name], (
            f"branch {bi.store_id} (brand {store_brand[bi.store_id]}) holds item "
            f"{bi.item_name!r} of brand {item_brand[bi.item_name]} — cross-contamination"
        )


def test_branches_of_same_brand_have_independent_stock(db_session):
    """Two branches of one brand must not share a stock counter for the same item."""
    brand = Brand(name="Multi", slug="multi-branch")
    db_session.add(brand)
    db_session.flush()
    s1 = Store(name="A", brand_id=brand.id, is_default=True)
    s2 = Store(name="B", brand_id=brand.id)
    db_session.add_all([s1, s2])
    db_session.flush()
    cat = Categories(name="multi:Drinks", brand_id=brand.id)
    db_session.add(cat)
    db_session.flush()
    item = Goods(
        name="multi:Water",
        brand_id=brand.id,
        category_name=cat.name,
        price=20,
        description="x",
        item_type="product",
        stock_quantity=0,
    )
    db_session.add(item)
    bi1 = BranchInventory(store_id=s1.id, item_name=item.name, stock_quantity=10)
    bi2 = BranchInventory(store_id=s2.id, item_name=item.name, stock_quantity=99)
    db_session.add_all([bi1, bi2])
    db_session.flush()
    # Mutating one branch's stock must not affect the other.
    bi1.stock_quantity = 3
    db_session.flush()
    assert db_session.query(BranchInventory).filter_by(store_id=s2.id, item_name=item.name).first().stock_quantity == 99
    assert db_session.query(BranchInventory).filter_by(store_id=s1.id, item_name=item.name).first().stock_quantity == 3


def test_global_name_pk_blocks_same_item_name_in_two_brands(db_session):
    """EDGE CASE (documented limitation): Goods.name is a GLOBAL primary key, so two
    brands cannot both have an item literally named e.g. 'Coke'. Multi-brand menus
    must namespace item/category names per brand (the seeders do; a human admin in
    multi-bot mode would hit this)."""
    from sqlalchemy.exc import IntegrityError

    a = Brand(name="BrandA", slug="brand-a")
    b = Brand(name="BrandB", slug="brand-b")
    db_session.add_all([a, b])
    db_session.flush()
    ca = Categories(name="a:Drinks", brand_id=a.id)
    cb = Categories(name="b:Drinks", brand_id=b.id)
    db_session.add_all([ca, cb])
    db_session.flush()
    db_session.add(
        Goods(
            name="Coke",
            brand_id=a.id,
            category_name=ca.name,
            price=20,
            description="x",
            item_type="product",
            stock_quantity=1,
        )
    )
    db_session.flush()
    db_session.add(
        Goods(
            name="Coke",
            brand_id=b.id,
            category_name=cb.name,
            price=20,
            description="x",
            item_type="product",
            stock_quantity=1,
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_brand_query_does_not_scope_columnless_models(db_session):
    """Documents the isolation contract: models with no brand_id are NOT filtered by
    brand_query — so callers must scope them via their parent (order/store)."""
    for model in NO_BRAND_COLUMN:
        assert not hasattr(model, "brand_id"), f"{model.__name__} unexpectedly has brand_id"
        # brand_query returns an unfiltered query for these (no crash, no silent partial filter).
        q = brand_query(db_session, model, 12345)
        assert q is not None


# --------------------------------------------------------------------------- #
# 2. Generated configs are always integrity-clean across many seeds.
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("brands", [1, 2, 8, 20])
def test_varied_brand_counts_stay_clean(db_session, brands):
    generate_fuzz_data(db_session, random.Random(brands * 7 + 1), num_brands=brands)
    errs = [v for v in check_integrity(db_session) if v.severity is Severity.ERROR]
    assert errs == [], [str(e) for e in errs]


# --------------------------------------------------------------------------- #
# 3. Edge-case value probes — availability properties, currency, reserve/release.
# --------------------------------------------------------------------------- #


def _edge_brand(db_session):
    brand = Brand(name="Edge", slug="edge")
    db_session.add(brand)
    db_session.flush()
    db_session.add(Store(name="Main", brand_id=brand.id, is_default=True))
    cat = Categories(name="edge:Cat", brand_id=brand.id)
    db_session.add(cat)
    db_session.flush()
    return brand, cat


def test_goods_properties_never_crash_on_extremes(db_session):
    brand, cat = _edge_brand(db_session)
    edge_items = [
        # name, price, type, stock, reserved, sold_out, daily_limit, daily_sold
        ("edge:p_min", Decimal("0.01"), "product", 0, 0, False, None, 0),
        ("edge:p_max", Decimal("99999.99"), "prepared", 0, 0, False, None, 0),
        ("edge:huge_stock", Decimal("50"), "product", 2_000_000_000, 0, False, None, 0),
        ("edge:reserved_eq_stock", Decimal("50"), "product", 10, 10, False, None, 0),
        ("edge:sold_out", Decimal("50"), "prepared", 0, 0, True, None, 0),
        ("edge:limit_hit", Decimal("50"), "prepared", 0, 0, False, 5, 5),
        ("edge:limit_over", Decimal("50"), "prepared", 0, 0, False, 5, 99),
        ("edge:unlimited_prepared", Decimal("50"), "prepared", 0, 0, False, None, 0),
        ("edge:ünïcodé 🌶", Decimal("50"), "prepared", 0, 0, False, None, 0),
    ]
    for name, price, itype, stock, reserved, sold_out, dlimit, dsold in edge_items:
        g = Goods(
            name=name,
            brand_id=brand.id,
            category_name=cat.name,
            price=price,
            description="x",
            item_type=itype,
            stock_quantity=stock,
            daily_limit=dlimit,
        )
        g.reserved_quantity = reserved
        g.sold_out_today = sold_out
        g.daily_sold_count = dsold
        db_session.add(g)
    db_session.flush()

    for g in db_session.query(Goods).filter(Goods.name.like("edge:%")).all():
        assert g.available_quantity >= 0, f"{g.name}: negative available_quantity"
        dr = g.daily_remaining
        assert dr is None or dr >= 0, f"{g.name}: negative daily_remaining {dr}"
        avail = g.is_currently_available
        assert isinstance(avail, bool)
        # Invariants that must hold:
        if g.sold_out_today:
            assert not avail, f"{g.name}: sold_out but reported available"
        if g.is_product and g.available_quantity == 0:
            assert not avail, f"{g.name}: product with 0 available but reported available"
        if g.daily_limit is not None and g.daily_sold_count >= g.daily_limit:
            assert not avail, f"{g.name}: daily limit hit but reported available"


def test_currency_formatting_survives_extremes(db_session):
    for amt in [Decimal("0"), Decimal("0.01"), Decimal("99999.99"), Decimal("1000000"), Decimal("123456789.55")]:
        out = format_currency(amt)
        assert isinstance(out, str) and out, f"format_currency({amt}) returned {out!r}"


def _seed_item_and_order(db_session, stock, qty):
    brand, cat = _edge_brand(db_session)
    item = Goods(
        name="edge:Cola",
        brand_id=brand.id,
        category_name=cat.name,
        price=30,
        description="x",
        item_type="product",
        stock_quantity=stock,
    )
    db_session.add(item)
    db_session.flush()
    o = Order(
        total_price=Decimal("30"),
        payment_method="cash",
        delivery_address="addr",
        phone_number="0800000000",
        buyer_id=None,
    )
    o.order_status = "pending"
    db_session.add(o)
    db_session.flush()
    db_session.add(OrderItem(order_id=o.id, item_name=item.name, price=Decimal("30"), quantity=qty))
    db_session.flush()
    return item, o


def test_reserve_then_release_roundtrip(db_session):
    item, o = _seed_item_and_order(db_session, stock=5, qty=3)
    ok, msg = reserve_inventory(o.id, [{"item_name": item.name, "quantity": 3}], session=db_session)
    assert ok is True, msg
    db_session.flush()
    assert db_session.query(Goods).filter_by(name=item.name).first().reserved_quantity == 3

    rok, rmsg = release_reservation(o.id, session=db_session)
    assert rok is True, rmsg
    db_session.flush()
    g = db_session.query(Goods).filter_by(name=item.name).first()
    assert g.reserved_quantity == 0, "release must restore reserved to 0"
    assert g.available_quantity == 5


def test_oversell_fails_gracefully_without_exception(db_session):
    # Fresh transaction (per-test fixture) — reserve_inventory rolls back its session
    # on failure, so we only assert the *return contract*, not surviving state.
    item, o = _seed_item_and_order(db_session, stock=5, qty=99)
    ok, msg = reserve_inventory(o.id, [{"item_name": item.name, "quantity": 99}], session=db_session)
    assert ok is False
    assert isinstance(msg, str) and msg


def test_failed_reservation_preserves_caller_uncommitted_work(db_session):
    """A failed reservation must undo ONLY its own partial work (via SAVEPOINT) and
    leave the caller's other uncommitted changes intact — no shared-session footgun."""
    brand, cat = _edge_brand(db_session)
    item = Goods(
        name="edge:Soda",
        brand_id=brand.id,
        category_name=cat.name,
        price=30,
        description="x",
        item_type="product",
        stock_quantity=1,
    )
    db_session.add(item)
    db_session.flush()
    marker = Categories(name="edge:UncommittedMarker", brand_id=brand.id)
    db_session.add(marker)  # caller's other pending work
    o = Order(total_price=Decimal("30"), payment_method="cash", delivery_address="a", phone_number="0", buyer_id=None)
    db_session.add(o)
    db_session.flush()
    db_session.add(OrderItem(order_id=o.id, item_name=item.name, price=Decimal("30"), quantity=50))
    db_session.flush()

    ok, _ = reserve_inventory(o.id, [{"item_name": item.name, "quantity": 50}], session=db_session)
    assert ok is False
    # The caller's pending marker SURVIVES — the failed reservation rolled back only itself.
    assert db_session.query(Categories).filter_by(name="edge:UncommittedMarker").first() is not None
    # And the reservation's own (partial) effect was undone.
    db_session.flush()
    assert db_session.query(Goods).filter_by(name=item.name).first().reserved_quantity == 0
