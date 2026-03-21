from __future__ import annotations
from functools import lru_cache
from typing import Any

from bot.config import EnvKeys
from .strings import TRANSLATIONS, DEFAULT_LOCALE
from bot.logger_mesh import logger

# Thread-local-style per-request locale override
_request_locale: str | None = None


@lru_cache(maxsize=1)
def get_locale() -> str:
    loc = EnvKeys.BOT_LOCALE.lower().strip()
    return loc if loc in TRANSLATIONS else DEFAULT_LOCALE


def set_request_locale(locale: str | None) -> None:
    """Set the locale for the current request (called by middleware)."""
    global _request_locale
    _request_locale = locale


def get_request_locale() -> str | None:
    """Get the per-request locale override."""
    return _request_locale


def get_user_locale(telegram_id: int) -> str | None:
    """
    Get a user's saved locale from the database.
    Returns None if not set (user hasn't picked yet).
    """
    try:
        from bot.database import Database
        from bot.database.models.main import User
        with Database().session() as session:
            user = session.query(User.locale).filter_by(telegram_id=telegram_id).first()
            if user and user.locale:
                return user.locale
    except Exception:
        pass
    return None


def localize(key: str, /, locale: str | None = None, **kwargs: Any) -> str:
    """
    Get translation by key.
    Priority: explicit locale param > request locale > BOT_LOCALE > DEFAULT_LOCALE.
    """
    loc = locale or _request_locale or get_locale()

    text = TRANSLATIONS.get(loc, {}).get(key)
    if text is None:
        text = TRANSLATIONS.get(DEFAULT_LOCALE, {}).get(key)
    if text is None:
        text = key

    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Failed to format translation key '{key}' with kwargs {kwargs}: {e}")

    return str(text)


def validate_translations() -> list[str]:
    """Check all locales have the same translation keys. Returns list of warnings."""
    warnings = []
    all_keys = set()
    for d in TRANSLATIONS.values():
        all_keys |= set(d.keys())
    for locale, d in TRANSLATIONS.items():
        missing = all_keys - set(d.keys())
        if missing:
            warnings.append(f"Locale '{locale}' missing {len(missing)} keys: {', '.join(sorted(missing)[:5])}...")
    return warnings
