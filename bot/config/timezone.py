import logging
import time
from datetime import datetime
from typing import Optional
import pytz
from pytz.exceptions import UnknownTimeZoneError

logger = logging.getLogger(__name__)

# MISC-03 fix: Cache with TTL (3600 seconds = 1 hour)
_TIMEZONE_CACHE_TTL = 3600
_cached_timezone: Optional[str] = None
_cached_tz_object: Optional[pytz.tzinfo.BaseTzInfo] = None
_cache_timestamp: float = 0


def get_timezone() -> str:
    """
    Get the configured timezone from bot_settings.

    Returns:
        Timezone string (e.g., "UTC", "Europe/Moscow")
        Falls back to "UTC" if not found in database.
    """
    global _cached_timezone, _cache_timestamp

    # MISC-03 fix: Check TTL before using cache
    if _cached_timezone is not None and (time.time() - _cache_timestamp) < _TIMEZONE_CACHE_TTL:
        return _cached_timezone

    # Import here to avoid circular imports
    from bot.database.methods.read import get_bot_setting

    try:
        timezone_str = get_bot_setting('timezone', default='Asia/Bangkok', value_type=str)
        # Validate timezone
        try:
            pytz.timezone(timezone_str)
            _cached_timezone = timezone_str
            _cache_timestamp = time.time()
            logger.debug(f"Timezone loaded from database: {timezone_str}")
        except UnknownTimeZoneError:
            logger.warning(f"Invalid timezone '{timezone_str}' in database, falling back to UTC")
            _cached_timezone = "Asia/Bangkok"
    except Exception as e:
        # This can happen if database tables don't exist yet or database is unreachable
        # Use Asia/Bangkok as default (Thailand restaurant deployment)
        # Only log at debug level to avoid spamming logs during startup
        error_type = type(e).__name__
        if "does not exist" in str(e) or "relation" in str(e):
            # Table doesn't exist - completely normal during first-time initialization
            logger.debug("Timezone table not yet created, using Asia/Bangkok (normal on first startup)")
        else:
            # Other database error - worth noting but not critical
            logger.debug(f"Could not read timezone from database ({error_type}), using Asia/Bangkok: {e}")
        _cached_timezone = "Asia/Bangkok"
        _cache_timestamp = time.time()

    return _cached_timezone


def get_timezone_object() -> pytz.tzinfo.BaseTzInfo:
    """
    Get the pytz timezone object.

    Returns:
        pytz timezone object for the configured timezone
    """
    global _cached_tz_object

    if _cached_tz_object is not None:
        return _cached_tz_object

    timezone_str = get_timezone()
    _cached_tz_object = pytz.timezone(timezone_str)
    return _cached_tz_object


def get_localized_time() -> datetime:
    """
    Get current time in the configured timezone.

    Returns:
        Timezone-aware datetime object in the configured timezone
    """
    tz = get_timezone_object()
    return datetime.now(tz)


def reload_timezone() -> None:
    """
    Reload timezone from database, clearing the cache.

    This function should be called when timezone setting is updated
    to apply changes without restarting the bot (hot reload).
    """
    global _cached_timezone, _cached_tz_object

    _cached_timezone = None
    _cached_tz_object = None

    # Force reload
    new_timezone = get_timezone()
    logger.info(f"Timezone reloaded: {new_timezone}")


def validate_timezone(tz: str) -> bool:
    """
    Validate if a timezone string is valid.

    Args:
        tz: Timezone string to validate

    Returns:
        True if valid, False otherwise
    """
    try:
        pytz.timezone(tz)
        return True
    except UnknownTimeZoneError:
        return False
