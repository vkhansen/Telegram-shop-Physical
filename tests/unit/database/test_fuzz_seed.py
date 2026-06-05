"""The fuzz seeder must always produce integrity-clean data, and its chaos
mode must produce data the validator catches."""

import random

import pytest

from bot.database.integrity import Severity, check_integrity
from bot.database.models.main import Brand, Goods, Store
from scripts.fuzz_seed import clean_fuzz_data, generate_fuzz_data, inject_chaos

pytestmark = pytest.mark.database


@pytest.mark.parametrize("seed", [1, 7, 42, 1337, 99999])
def test_fuzz_output_is_integrity_clean(db_session, seed):
    counts = generate_fuzz_data(db_session, random.Random(seed), num_brands=4)
    assert counts["brands"] == 4
    assert counts["items"] > 0
    errs = [v for v in check_integrity(db_session) if v.severity is Severity.ERROR]
    assert errs == [], f"seed {seed} produced integrity errors: {[str(e) for e in errs]}"


def test_fuzz_is_deterministic(db_session):
    c1 = generate_fuzz_data(db_session, random.Random(2024), num_brands=3)
    names1 = sorted(n for (n,) in db_session.query(Goods.name).all())
    clean_fuzz_data(db_session)
    c2 = generate_fuzz_data(db_session, random.Random(2024), num_brands=3)
    names2 = sorted(n for (n,) in db_session.query(Goods.name).all())
    assert c1 == c2
    assert names1 == names2


def test_chaos_is_caught_by_validator(db_session):
    generate_fuzz_data(db_session, random.Random(5), num_brands=3)
    assert [v for v in check_integrity(db_session) if v.severity is Severity.ERROR] == []
    expected = inject_chaos(db_session, random.Random(5))
    caught = {v.check for v in check_integrity(db_session)}
    assert expected, "chaos should have injected at least one violation"
    assert expected <= caught, f"validator missed {expected - caught}"


def test_clean_removes_all_fuzz_data(db_session):
    generate_fuzz_data(db_session, random.Random(3), num_brands=2)
    assert db_session.query(Brand).filter(Brand.slug.like("fuzz-%")).count() == 2
    clean_fuzz_data(db_session)
    assert db_session.query(Brand).filter(Brand.slug.like("fuzz-%")).count() == 0
    assert db_session.query(Store).count() == 0
    assert db_session.query(Goods).count() == 0
