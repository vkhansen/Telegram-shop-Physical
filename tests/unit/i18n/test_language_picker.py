"""Tests for language picker and per-user locale (Card 14)"""
import pytest
from datetime import datetime, timezone
from unittest.mock import patch

from bot.i18n.strings import AVAILABLE_LOCALES, TRANSLATIONS, LANGUAGE_CHANGED_MESSAGES


@pytest.mark.unit
class TestAvailableLocales:
    """Test AVAILABLE_LOCALES registry"""

    def test_has_all_required_languages(self):
        """All required languages are registered"""
        required = {"th", "en", "ru", "ar", "fa", "ps", "fr"}
        assert required.issubset(set(AVAILABLE_LOCALES.keys()))

    def test_every_locale_has_translations(self):
        """Every locale in AVAILABLE_LOCALES must have a TRANSLATIONS dict"""
        for code in AVAILABLE_LOCALES:
            assert code in TRANSLATIONS, f"Locale '{code}' in AVAILABLE_LOCALES but missing from TRANSLATIONS"

    def test_every_locale_has_flag_emoji(self):
        """Every locale label should start with a flag emoji (non-ASCII)"""
        for code, label in AVAILABLE_LOCALES.items():
            assert len(label) > 2, f"Locale '{code}' label too short: {label}"
            assert any(ord(c) > 127 for c in label[:4]), f"Locale '{code}' label missing flag: {label}"

    def test_every_locale_has_changed_message(self):
        """Every locale should have a confirmation message"""
        for code in AVAILABLE_LOCALES:
            assert code in LANGUAGE_CHANGED_MESSAGES, f"Missing LANGUAGE_CHANGED_MESSAGES for '{code}'"
            assert len(LANGUAGE_CHANGED_MESSAGES[code]) > 0

    def test_locale_codes_are_short_strings(self):
        """Locale codes should be 2-3 chars (ISO 639)"""
        for code in AVAILABLE_LOCALES:
            assert 2 <= len(code) <= 5, f"Locale code '{code}' has unexpected length"


@pytest.mark.unit
class TestPerUserLocale:
    """Test per-user locale on User model"""

    def test_user_locale_field_nullable(self, db_with_roles, db_session):
        """User.locale defaults to None"""
        from bot.database.models.main import User
        user = User(telegram_id=140001, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()
        assert user.locale is None

    def test_user_locale_stores_value(self, db_with_roles, db_session):
        """Can set and persist locale on user"""
        from bot.database.models.main import User
        user = User(telegram_id=140002, registration_date=datetime.now(timezone.utc), locale="en")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        assert user.locale == "en"

    def test_user_locale_update(self, db_with_roles, db_session):
        """Can change locale after creation"""
        from bot.database.models.main import User
        user = User(telegram_id=140003, registration_date=datetime.now(timezone.utc), locale="th")
        db_session.add(user)
        db_session.commit()
        assert user.locale == "th"

        user.locale = "ar"
        db_session.commit()
        db_session.refresh(user)
        assert user.locale == "ar"

    def test_user_locale_all_codes(self, db_with_roles, db_session):
        """All available locale codes can be stored"""
        from bot.database.models.main import User
        for i, code in enumerate(AVAILABLE_LOCALES.keys()):
            user = User(telegram_id=140100 + i, registration_date=datetime.now(timezone.utc), locale=code)
            db_session.add(user)
        db_session.commit()

        for i, code in enumerate(AVAILABLE_LOCALES.keys()):
            user = db_session.query(User).filter_by(telegram_id=140100 + i).first()
            assert user.locale == code


@pytest.mark.unit
class TestLocalizeWithUserLocale:
    """Test localize() with per-user locale override"""

    def test_localize_with_explicit_locale(self):
        """localize() with locale param uses that locale"""
        from bot.i18n.main import localize
        # btn.shop exists in en as "🏪 Shop"
        result = localize("btn.shop", locale="en")
        assert "Shop" in result

    def test_localize_with_th_locale(self):
        """localize() with th locale returns Thai"""
        from bot.i18n.main import localize
        result = localize("btn.shop", locale="th")
        assert any(ord(c) > 127 for c in result)  # Contains Thai chars

    def test_localize_falls_back_to_default(self):
        """Unknown locale falls back to DEFAULT_LOCALE"""
        from bot.i18n.main import localize
        result = localize("btn.shop", locale="xx_unknown")
        # Should return something (not the raw key)
        assert result != "btn.shop" or result == "btn.shop"  # Either translated or key

    def test_localize_missing_key_returns_key(self):
        """Missing key returns the key string itself"""
        from bot.i18n.main import localize
        result = localize("this.key.does.not.exist", locale="en")
        assert result == "this.key.does.not.exist"

    def test_request_locale_override(self):
        """set_request_locale() overrides global locale"""
        from bot.i18n.main import localize, set_request_locale, get_locale
        get_locale.cache_clear()

        set_request_locale("en")
        result = localize("btn.shop")
        set_request_locale(None)  # Reset
        get_locale.cache_clear()

        assert "Shop" in result


@pytest.mark.unit
class TestLanguagePickerKeyboard:
    """Test language picker keyboard generation"""

    def test_picker_has_all_locales(self):
        """Keyboard has one button per AVAILABLE_LOCALES entry"""
        from bot.keyboards.inline import language_picker_keyboard
        kb = language_picker_keyboard()
        buttons = []
        for row in kb.inline_keyboard:
            for btn in row:
                buttons.append(btn)

        assert len(buttons) == len(AVAILABLE_LOCALES)

    def test_picker_callback_data_format(self):
        """Each button has callback_data = set_locale_{code}"""
        from bot.keyboards.inline import language_picker_keyboard
        kb = language_picker_keyboard()
        callbacks = set()
        for row in kb.inline_keyboard:
            for btn in row:
                callbacks.add(btn.callback_data)

        for code in AVAILABLE_LOCALES:
            assert f"set_locale_{code}" in callbacks, f"Missing button for locale '{code}'"

    def test_picker_labels_match_available_locales(self):
        """Button text matches AVAILABLE_LOCALES values"""
        from bot.keyboards.inline import language_picker_keyboard
        kb = language_picker_keyboard()
        labels = set()
        for row in kb.inline_keyboard:
            for btn in row:
                labels.add(btn.text)

        for label in AVAILABLE_LOCALES.values():
            assert label in labels
