"""User identity resolve / link helpers (CARD-30).

Maps ``(platform, external_id)`` → ``users.telegram_id`` without changing FKs.
Telegram dual-write: every TG user has ``platform='telegram', external_id=str(id)``.
"""

from __future__ import annotations

import logging
from typing import Any

from bot.database.main import Database
from bot.database.models.main import User, UserIdentity

logger = logging.getLogger(__name__)

PLATFORM_TELEGRAM = "telegram"
PLATFORM_WEB = "web"
PLATFORM_GOOGLE = "google"
PLATFORM_LINE = "line"
PLATFORM_INSTAGRAM = "instagram"
PLATFORM_WHATSAPP = "whatsapp"


def resolve_user_id(platform: str, external_id: str, *, session: Any | None = None) -> int | None:
    """Return internal user id (users.telegram_id) for a platform external id."""
    platform = (platform or "").strip().lower()
    external_id = str(external_id).strip()
    if not platform or not external_id:
        return None

    def _resolve(s) -> int | None:
        row = (
            s.query(UserIdentity)
            .filter(UserIdentity.platform == platform, UserIdentity.external_id == external_id)
            .one_or_none()
        )
        return int(row.user_id) if row else None

    if session is not None:
        return _resolve(session)
    with Database().session() as s:
        return _resolve(s)


def link_identity(
    user_id: int,
    platform: str,
    external_id: str,
    *,
    session: Any | None = None,
) -> bool:
    """
    Ensure ``(platform, external_id)`` points at *user_id*.

    Returns True if a new row was inserted, False if already present (or conflict
    with a different user_id — logged and not overwritten).
    """
    platform = (platform or "").strip().lower()
    external_id = str(external_id).strip()
    if not platform or not external_id:
        return False

    def _link(s) -> bool:
        existing = (
            s.query(UserIdentity)
            .filter(UserIdentity.platform == platform, UserIdentity.external_id == external_id)
            .one_or_none()
        )
        if existing is not None:
            if int(existing.user_id) != int(user_id):
                logger.warning(
                    "identity conflict platform=%s external_id=%s existing_user=%s new_user=%s",
                    platform,
                    external_id,
                    existing.user_id,
                    user_id,
                )
            return False
        s.add(UserIdentity(user_id=int(user_id), platform=platform, external_id=external_id))
        return True

    if session is not None:
        return _link(session)
    with Database().session() as s:
        created = _link(s)
        return created


def ensure_telegram_identity(telegram_id: int, *, session: Any | None = None) -> bool:
    """Upsert telegram dual-write row. Returns True if inserted."""
    return link_identity(
        int(telegram_id),
        PLATFORM_TELEGRAM,
        str(int(telegram_id)),
        session=session,
    )


def backfill_telegram_identities(*, session: Any | None = None) -> int:
    """
    Create missing ``platform=telegram`` rows for all users.

    Returns number of identities inserted.
    """

    def _backfill(s) -> int:
        # Users that already have a telegram identity
        existing = {
            int(r.user_id)
            for r in s.query(UserIdentity.user_id)
            .filter(UserIdentity.platform == PLATFORM_TELEGRAM)
            .all()
        }
        created = 0
        for (tid,) in s.query(User.telegram_id).all():
            tid_i = int(tid)
            if tid_i in existing:
                continue
            s.add(
                UserIdentity(
                    user_id=tid_i,
                    platform=PLATFORM_TELEGRAM,
                    external_id=str(tid_i),
                )
            )
            created += 1
        return created

    if session is not None:
        return _backfill(session)
    with Database().session() as s:
        return _backfill(s)
