"""Theme contrast law — seed generation always produces readable text/surfaces."""

from bot.services.seed_demo_verticals import (
    PALETTE_BAKERY,
    PALETTE_COFFEE,
    PALETTE_FOOD,
    PALETTE_GROCERY,
    PALETTE_HERB,
)
from bot.services.seed_snus_demo import SNUS_THEME_TOKENS
from bot.services.theme_contrast import (
    assert_palette_readable,
    contrast_ratio,
    enforce_theme_colors,
    enforce_theme_tokens,
)


def test_broken_white_on_white_is_fixed():
    fixed = enforce_theme_colors(
        {"paper": "#ffffff", "ink": "#ffffff", "sun": "#eeeeee", "on_accent": "#ffffff"},
        mode="light",
    )
    assert (contrast_ratio(fixed["ink"], fixed["paper"]) or 0) >= 4.5
    assert (contrast_ratio(fixed["on_accent"], fixed["sun"]) or 0) >= 4.5


def test_all_vertical_palettes_readable():
    for name, pack in [
        ("food", PALETTE_FOOD),
        ("coffee", PALETTE_COFFEE),
        ("herb", PALETTE_HERB),
        ("bakery", PALETTE_BAKERY),
        ("grocery", PALETTE_GROCERY),
    ]:
        colors = pack["colors"]
        mode = pack["mode"]
        assert_palette_readable(colors, mode=mode)
        assert (contrast_ratio(colors["ink"], colors["paper"]) or 0) >= 4.5, name


def test_snus_tokens_readable_after_enforce():
    fixed = enforce_theme_tokens(SNUS_THEME_TOKENS)
    assert_palette_readable(fixed["colors"], mode=fixed["mode"])
