"""Tests for i18n string translations (Cards 5 & 11)"""
import pytest
import re

from bot.i18n.strings import TRANSLATIONS


@pytest.mark.unit
class TestThaiTranslations:
    """Test Thai locale completeness"""

    def test_th_locale_exists(self):
        """Thai locale should exist in TRANSLATIONS"""
        assert "th" in TRANSLATIONS, "Thai locale 'th' not found in TRANSLATIONS"

    def test_all_en_keys_have_th_translation(self):
        """Every English key should have a Thai translation"""
        en_keys = set(TRANSLATIONS.get("en", {}).keys())
        th_keys = set(TRANSLATIONS.get("th", {}).keys())

        missing = en_keys - th_keys
        assert not missing, f"Missing Thai translations for {len(missing)} keys: {sorted(missing)[:10]}..."

    def test_th_strings_not_empty(self):
        """No Thai translation should be empty"""
        th = TRANSLATIONS.get("th", {})
        empty_keys = [k for k, v in th.items() if not v or (isinstance(v, str) and not v.strip())]
        assert not empty_keys, f"Empty Thai translations: {empty_keys[:10]}"

    def test_th_format_placeholders_match(self):
        """Thai strings should have same {placeholders} as English"""
        en = TRANSLATIONS.get("en", {})
        th = TRANSLATIONS.get("th", {})

        placeholder_pattern = re.compile(r'\{(\w+)\}')
        mismatches = []

        for key in en:
            if key not in th:
                continue
            en_placeholders = set(placeholder_pattern.findall(str(en[key])))
            th_placeholders = set(placeholder_pattern.findall(str(th[key])))

            if en_placeholders != th_placeholders:
                mismatches.append(f"{key}: en={en_placeholders}, th={th_placeholders}")

        assert not mismatches, f"Placeholder mismatches:\n" + "\n".join(mismatches[:10])

    def test_cod_thai_label(self):
        """COD should have Thai label (Card 11)"""
        th = TRANSLATIONS.get("th", {})
        cod_key = "order.payment_method.cash"
        assert cod_key in th
        # Should contain Thai text (not just English)
        assert any(ord(c) > 127 for c in th[cod_key]), f"COD label should contain Thai characters: {th[cod_key]}"

    def test_locale_switch_to_th(self):
        """localize() should return Thai when BOT_LOCALE=th"""
        from unittest.mock import patch
        from bot.i18n.main import localize, get_locale

        # Clear LRU cache
        get_locale.cache_clear()

        with patch('bot.i18n.main.EnvKeys') as mock_env:
            mock_env.BOT_LOCALE = "th"
            get_locale.cache_clear()
            result = localize("btn.shop")
            # Should contain Thai characters
            assert any(ord(c) > 127 for c in result), f"Expected Thai text, got: {result}"

        get_locale.cache_clear()
