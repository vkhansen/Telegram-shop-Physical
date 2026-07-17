"""Generate simple clipart-style placeholder PNGs for demo catalogs.

Files land under ``tests/test-data/`` as ``ph-*.png`` and are served via
``local:<filename>`` (media proxy). Created once; re-run with force to refresh.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parents[2]
TEST_DATA = _ROOT / "tests" / "test-data"

# (filename, bg_hex, accent_hex, short_label)
PLACEHOLDERS: list[tuple[str, str, str, str]] = [
    # Food
    ("ph-food-padthai.png", "#c45c26", "#2a1508", "PAD THAI"),
    ("ph-food-curry.png", "#2d6a4f", "#081c15", "CURRY"),
    ("ph-food-rice.png", "#f4a261", "#3d2000", "RICE"),
    ("ph-food-salad.png", "#52b788", "#1b4332", "SALAD"),
    ("ph-food-drink.png", "#48cae4", "#023e8a", "DRINK"),
    ("ph-food-dessert.png", "#e5989b", "#6d2e46", "SWEET"),
    ("ph-food-logo.png", "#e8a838", "#1a1200", "KITCHEN"),
    # Coffee
    ("ph-coffee-latte.png", "#6f4e37", "#2b1608", "LATTE"),
    ("ph-coffee-espresso.png", "#3c2f2f", "#1a1210", "ESPRESSO"),
    ("ph-coffee-cold.png", "#87a96b", "#1e2f14", "COLD BREW"),
    ("ph-coffee-pastry.png", "#d4a373", "#4a2c0a", "PASTRY"),
    ("ph-coffee-tea.png", "#c9ada7", "#4a3728", "TEA"),
    ("ph-coffee-logo.png", "#4a3728", "#f5ebe0", "BEANS"),
    # Herb / adult (demo only)
    ("ph-herb-flower.png", "#40916c", "#081c15", "FLOWER"),
    ("ph-herb-preroll.png", "#74c69d", "#1b4332", "PRE-ROLL"),
    ("ph-herb-edible.png", "#95d5b2", "#2d6a4f", "EDIBLE"),
    ("ph-herb-vape.png", "#52b788", "#081c15", "VAPE"),
    ("ph-herb-access.png", "#2d6a4f", "#d8f3dc", "GEAR"),
    ("ph-herb-logo.png", "#1b4332", "#b7e4c7", "HERB"),
    # Bakery
    ("ph-bakery-bread.png", "#ddb892", "#5c3d1e", "BREAD"),
    ("ph-bakery-croissant.png", "#e6b980", "#6b3e1e", "CROISSANT"),
    ("ph-bakery-cake.png", "#f2c6de", "#6b2d5c", "CAKE"),
    ("ph-bakery-cookie.png", "#c9a66b", "#3e2723", "COOKIE"),
    ("ph-bakery-logo.png", "#a47148", "#fff8f0", "BAKE"),
    # Grocery / minimart
    ("ph-grocery-water.png", "#90e0ef", "#0077b6", "WATER"),
    ("ph-grocery-snack.png", "#ffb703", "#6a4c00", "SNACK"),
    ("ph-grocery-dairy.png", "#f8f9fa", "#495057", "DAIRY"),
    ("ph-grocery-produce.png", "#80ed99", "#1b4332", "PRODUCE"),
    ("ph-grocery-logo.png", "#023e8a", "#caf0f8", "MART"),
]


def _hex_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def ensure_placeholder_png(
    filename: str,
    *,
    bg: str,
    accent: str,
    label: str,
    size: int = 512,
    force: bool = False,
) -> Path:
    """Create a simple clipart-style square PNG if missing (or force)."""
    TEST_DATA.mkdir(parents=True, exist_ok=True)
    path = TEST_DATA / Path(filename).name
    if path.is_file() and not force:
        return path

    from PIL import Image, ImageDraw, ImageFont

    bg_rgb = _hex_rgb(bg)
    ac_rgb = _hex_rgb(accent)
    img = Image.new("RGB", (size, size), bg_rgb)
    draw = ImageDraw.Draw(img)

    # Soft circle “clipart” body
    margin = size // 8
    draw.ellipse(
        [margin, margin, size - margin, size - margin],
        fill=ac_rgb if sum(ac_rgb) > 200 else tuple(min(255, c + 40) for c in bg_rgb),
        outline=ac_rgb,
        width=max(4, size // 64),
    )
    # Inner disc
    m2 = size // 4
    draw.ellipse([m2, m2, size - m2, size - m2], fill=bg_rgb, outline=ac_rgb, width=2)

    # Label
    text = (label or "?").upper()[:14]
    try:
        font = ImageFont.truetype("arial.ttf", size // 10)
    except OSError:
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", size // 10)
        except OSError:
            font = ImageFont.load_default()

    # Pillow 10+ uses textbbox
    if hasattr(draw, "textbbox"):
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    else:
        tw, th = draw.textsize(text, font=font)  # type: ignore[attr-defined]
    draw.text(
        ((size - tw) / 2, (size - th) / 2),
        text,
        fill=ac_rgb if sum(bg_rgb) > 400 else (255, 255, 255),
        font=font,
    )

    # Corner badge
    draw.rectangle([0, 0, size // 5, size // 12], fill=ac_rgb)
    badge = "DEMO"
    if hasattr(draw, "textbbox"):
        bb = draw.textbbox((0, 0), badge, font=font)
        bw = bb[2] - bb[0]
    else:
        bw, _ = draw.textsize(badge, font=font)  # type: ignore[attr-defined]
    draw.text((8, 4), badge, fill=bg_rgb if sum(ac_rgb) > 400 else (255, 255, 255), font=font)

    img.save(path, format="PNG", optimize=True)
    logger.info("Wrote placeholder %s", path.name)
    return path


def ensure_all_placeholders(*, force: bool = False) -> list[str]:
    """Generate every known demo placeholder. Returns filenames created/ensured."""
    out: list[str] = []
    for name, bg, accent, label in PLACEHOLDERS:
        ensure_placeholder_png(name, bg=bg, accent=accent, label=label, force=force)
        out.append(name)
    return out


def local_ref(filename: str) -> str:
    return f"local:{Path(filename).name}"
