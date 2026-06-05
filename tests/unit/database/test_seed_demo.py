"""The demo seeder must produce a coherent, integrity-clean menu and be idempotent."""

import pytest

from bot.database.integrity import Severity, check_integrity
from bot.database.models.main import Brand, Categories, Goods, Store
from scripts.seed_demo import seed_demo

pytestmark = pytest.mark.database


def _make_brand(session):
    brand = Brand(name="Demo Co", slug="demo-co")
    session.add(brand)
    session.flush()
    return brand


def test_seed_demo_is_integrity_clean(db_session):
    brand = _make_brand(db_session)
    counts = seed_demo(db_session, brand.id)
    assert counts["branches"] == 3
    assert counts["categories"] == 5
    assert counts["items"] > 10
    errs = [v for v in check_integrity(db_session) if v.severity is Severity.ERROR]
    assert errs == [], [str(e) for e in errs]
    # one default branch, real menu attached to the brand
    assert db_session.query(Store).filter_by(brand_id=brand.id, is_default=True).count() == 1
    assert db_session.query(Goods).filter_by(brand_id=brand.id).count() == counts["items"]


def test_seed_demo_is_idempotent(db_session):
    brand = _make_brand(db_session)
    seed_demo(db_session, brand.id)
    items_after_first = db_session.query(Goods).count()
    cats_after_first = db_session.query(Categories).count()
    second = seed_demo(db_session, brand.id)
    assert second["items"] == 0 and second["branches"] == 0 and second["categories"] == 0
    assert second["skipped"] > 0
    assert db_session.query(Goods).count() == items_after_first
    assert db_session.query(Categories).count() == cats_after_first
