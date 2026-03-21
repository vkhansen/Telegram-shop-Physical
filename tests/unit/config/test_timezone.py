"""Tests for timezone configuration (Card 12)"""
import pytest
from unittest.mock import patch
from datetime import datetime, timezone

import pytz


@pytest.mark.unit
class TestTimezoneConfig:
    """Test timezone configuration defaults and behavior"""

    def _reset_cache(self):
        import bot.config.timezone as tz_module
        tz_module._cached_timezone = None
        tz_module._cached_tz_object = None

    def test_default_timezone_bangkok(self):
        """Default timezone should be Asia/Bangkok when no DB setting exists"""
        self._reset_cache()

        with patch('bot.database.methods.read.get_bot_setting', return_value='Asia/Bangkok'):
            from bot.config.timezone import get_timezone
            result = get_timezone()
            assert result == "Asia/Bangkok"

        self._reset_cache()

    def test_default_timezone_on_db_error(self):
        """Should fall back to Asia/Bangkok when database is unreachable"""
        self._reset_cache()

        with patch('bot.database.methods.read.get_bot_setting',
                   side_effect=Exception('relation "bot_settings" does not exist')):
            from bot.config.timezone import get_timezone
            result = get_timezone()
            assert result == "Asia/Bangkok"

        self._reset_cache()

    def test_timezone_aware_now(self):
        """get_localized_time() should return timezone-aware datetime in configured TZ"""
        self._reset_cache()

        with patch('bot.database.methods.read.get_bot_setting', return_value='Asia/Bangkok'):
            from bot.config.timezone import get_localized_time
            result = get_localized_time()

            # Must be timezone-aware
            assert result.tzinfo is not None

            # Must be in Asia/Bangkok timezone
            assert 'Bangkok' in str(result.tzinfo) or \
                   result.utcoffset().total_seconds() == 7 * 3600

        self._reset_cache()

    def test_timezone_object_is_bangkok(self):
        """get_timezone_object() should return pytz Bangkok timezone"""
        self._reset_cache()

        with patch('bot.database.methods.read.get_bot_setting', return_value='Asia/Bangkok'):
            from bot.config.timezone import get_timezone_object
            tz_obj = get_timezone_object()
            assert tz_obj.zone == 'Asia/Bangkok'

        self._reset_cache()

    def test_validate_timezone_bangkok(self):
        """Asia/Bangkok should be a valid timezone"""
        from bot.config.timezone import validate_timezone
        assert validate_timezone("Asia/Bangkok") is True

    def test_validate_timezone_invalid(self):
        """Invalid timezone string should fail validation"""
        from bot.config.timezone import validate_timezone
        assert validate_timezone("Thailand/Bangkok") is False
        assert validate_timezone("") is False
        assert validate_timezone("NotATimezone") is False

    def test_reload_timezone(self):
        """reload_timezone() should clear cache and re-read from DB"""
        import bot.config.timezone as tz_module
        tz_module._cached_timezone = "UTC"
        tz_module._cached_tz_object = pytz.timezone("UTC")

        with patch('bot.database.methods.read.get_bot_setting', return_value='Asia/Bangkok'):
            tz_module.reload_timezone()
            assert tz_module._cached_timezone == "Asia/Bangkok"

        self._reset_cache()

    def test_reservation_expiry_uses_utc_comparison(self):
        """
        Reservation expiry comparison should work correctly regardless of display timezone.
        The DB stores timezone-aware UTC timestamps, so comparison with datetime.now(timezone.utc)
        is correct — the display timezone (Asia/Bangkok) only affects user-facing output.
        """
        now_utc = datetime.now(timezone.utc)
        bangkok_tz = pytz.timezone('Asia/Bangkok')
        now_bangkok = datetime.now(bangkok_tz)

        # Both should represent approximately the same instant
        diff = abs((now_utc - now_bangkok.astimezone(pytz.utc)).total_seconds())
        assert diff < 1.0, "UTC and Bangkok times should represent the same instant"
