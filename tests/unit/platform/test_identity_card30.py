"""CARD-30 — user_identities dual-write + resolve helpers."""

from datetime import UTC, datetime

import pytest
from sqlalchemy.exc import IntegrityError

from bot.database.main import Database
from bot.database.methods.create import create_user
from bot.database.models.main import User, UserIdentity
from bot.platform.identity import (
    PLATFORM_TELEGRAM,
    backfill_telegram_identities,
    ensure_telegram_identity,
    link_identity,
    resolve_user_id,
)


def test_create_user_dual_writes_telegram_identity(db_with_roles, db_engine):
    tid = 900_001_001
    create_user(tid, datetime.now(UTC), None, role=1)

    with Database().session() as s:
        user = s.query(User).filter_by(telegram_id=tid).one()
        assert user is not None
        ident = (
            s.query(UserIdentity)
            .filter_by(platform=PLATFORM_TELEGRAM, external_id=str(tid))
            .one()
        )
        assert ident.user_id == tid

    assert resolve_user_id(PLATFORM_TELEGRAM, str(tid)) == tid


def test_create_user_existing_ensures_identity(db_with_roles, test_user, db_engine):
    # Simulate legacy user without identity row
    with Database().session() as s:
        s.query(UserIdentity).filter_by(user_id=test_user.telegram_id).delete()
        s.commit()

    create_user(test_user.telegram_id, datetime.now(UTC), None, role=1)

    assert resolve_user_id(PLATFORM_TELEGRAM, str(test_user.telegram_id)) == test_user.telegram_id


def test_ensure_telegram_identity_idempotent(db_with_roles, test_user, db_engine):
    assert ensure_telegram_identity(test_user.telegram_id) is True
    assert ensure_telegram_identity(test_user.telegram_id) is False
    with Database().session() as s:
        n = (
            s.query(UserIdentity)
            .filter_by(platform=PLATFORM_TELEGRAM, external_id=str(test_user.telegram_id))
            .count()
        )
        assert n == 1


def test_link_and_resolve_other_platform(db_with_roles, test_user, db_engine):
    created = link_identity(test_user.telegram_id, "instagram", "ig_abc_123")
    assert created is True
    assert resolve_user_id("instagram", "ig_abc_123") == test_user.telegram_id
    # second link same mapping is no-op
    assert link_identity(test_user.telegram_id, "instagram", "ig_abc_123") is False


def test_unique_platform_external_id(db_with_roles, test_user, db_engine):
    link_identity(test_user.telegram_id, "line", "line-u-1")
    with pytest.raises(IntegrityError):
        with Database().session() as s:
            s.add(UserIdentity(user_id=test_user.telegram_id, platform="line", external_id="line-u-1"))
            s.flush()


def test_backfill_telegram_identities(db_with_roles, test_user, db_engine):
    # Create second user without identity by direct insert
    tid2 = 900_001_002
    with Database().session() as s:
        s.add(User(telegram_id=tid2, role_id=1, registration_date=datetime.now(UTC)))
        s.query(UserIdentity).filter_by(user_id=test_user.telegram_id).delete()
        s.commit()

    n = backfill_telegram_identities()
    assert n >= 2
    assert resolve_user_id(PLATFORM_TELEGRAM, str(test_user.telegram_id)) == test_user.telegram_id
    assert resolve_user_id(PLATFORM_TELEGRAM, str(tid2)) == tid2
    # second backfill inserts nothing new
    assert backfill_telegram_identities() == 0
