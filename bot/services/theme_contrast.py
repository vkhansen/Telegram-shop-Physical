"""Contrast rules for white-label theme_tokens (seed + validation).

Rule
----
Every text color must contrast with the surface it sits on. Seeds must never
ship white-on-white / dark-on-dark. The Astro storefront re-enforces the same
pairs; this module keeps **generation** honest so DB tokens are already safe.

Pairs enforced (min ratio ~4.5 for body, ~3.0 for muted/links)::

  ink        on paper
  muted      on paper
  sea        on paper
  on_ink     on ink        (inverted panels / nav active)
  on_accent  on sun        (primary CTA fill)
  on_footer  on footer
"""

from __future__ import annotations

from typing import Any

MIN_BODY = 4.5
MIN_SOFT = 3.0


def _hex_rgb(hex_color: str) -> tuple[int, int, int] | None:
    h = (hex_color or "").strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6:
        return None
    try:
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    except ValueError:
        return None


def _lin(c: int) -> float:
    v = c / 255.0
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4


def relative_luminance(hex_color: str) -> float | None:
    rgb = _hex_rgb(hex_color)
    if not rgb:
        return None
    r, g, b = rgb
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def contrast_ratio(a: str, b: str) -> float | None:
    L1, L2 = relative_luminance(a), relative_luminance(b)
    if L1 is None or L2 is None:
        return None
    hi, lo = max(L1, L2), min(L1, L2)
    return (hi + 0.05) / (lo + 0.05)


def contrasting_text(bg: str) -> str:
    """Pick near-black or near-white — whichever contrasts better with bg."""
    black, white = "#14110a", "#f7f5f2"
    rb = contrast_ratio(black, bg) or 0
    rw = contrast_ratio(white, bg) or 0
    return black if rb >= rw else white


def ensure_contrast(fg: str, bg: str, min_ratio: float = MIN_BODY) -> str:
    ratio = contrast_ratio(fg, bg)
    if ratio is not None and ratio >= min_ratio:
        return fg
    return contrasting_text(bg)


def enforce_theme_colors(colors: dict[str, Any], *, mode: str = "dark") -> dict[str, Any]:
    """Return a corrected color pack with readable text on every surface."""
    out = {k: v for k, v in (colors or {}).items() if isinstance(v, str)}
    paper = out.get("paper") or ("#f7f5f2" if mode == "light" else "#0c0c0e")
    out["paper"] = paper
    out["paper_warm"] = out.get("paper_warm") or paper

    out["ink"] = ensure_contrast(out.get("ink") or contrasting_text(paper), paper, MIN_BODY)
    out["on_ink"] = ensure_contrast(
        out.get("on_ink") or contrasting_text(out["ink"]), out["ink"], MIN_BODY
    )

    sun = out.get("sun") or out.get("accent") or ("#c4782a" if mode == "light" else "#e8b84a")
    accent = out.get("accent") or sun
    out["sun"] = sun
    out["accent"] = accent
    out["on_accent"] = ensure_contrast(
        out.get("on_accent") or contrasting_text(sun), sun, MIN_BODY
    )

    # Soft text / links on paper
    muted = out.get("muted") or contrasting_text(paper)
    if muted.startswith("rgba") or muted.startswith("rgb"):
        # keep rgba muted if present; storefront re-checks
        out["muted"] = muted
    else:
        out["muted"] = ensure_contrast(muted, paper, MIN_SOFT)

    sea = out.get("sea") or ("#0a4ea2" if mode == "light" else "#93c5fd")
    if not sea.startswith("rgb"):
        out["sea"] = ensure_contrast(sea, paper, MIN_SOFT)
    else:
        out["sea"] = sea
    out["sea_deep"] = out.get("sea_deep") or out["sea"]

    footer = out.get("footer") or ("#14110a" if mode == "light" else "#050506")
    out["footer"] = footer
    out["on_footer"] = ensure_contrast(
        out.get("on_footer") or contrasting_text(footer), footer, MIN_BODY
    )

    if "line" not in out:
        out["line"] = "rgba(255,255,255,.14)" if mode == "dark" else "rgba(20,17,10,.14)"
    return out


def enforce_theme_tokens(tokens: dict[str, Any] | None) -> dict[str, Any]:
    """Apply contrast law to a full theme_tokens dict (mutates colors only)."""
    if not tokens:
        return {"mode": "dark", "colors": enforce_theme_colors({}, mode="dark")}
    out = dict(tokens)
    mode = str(out.get("mode") or "dark").lower()
    if mode not in ("light", "dark"):
        mode = "dark"
    out["mode"] = mode
    colors = out.get("colors") if isinstance(out.get("colors"), dict) else {}
    out["colors"] = enforce_theme_colors(colors, mode=mode)
    return out


def assert_palette_readable(colors: dict[str, str], *, mode: str = "dark") -> None:
    """Raise AssertionError if any required pair fails contrast (tests)."""
    fixed = enforce_theme_colors(colors, mode=mode)
    paper = fixed["paper"]
    checks = [
        ("ink/paper", fixed["ink"], paper, MIN_BODY),
        ("on_ink/ink", fixed["on_ink"], fixed["ink"], MIN_BODY),
        ("on_accent/sun", fixed["on_accent"], fixed["sun"], MIN_BODY),
        ("on_footer/footer", fixed["on_footer"], fixed["footer"], MIN_BODY),
    ]
    for name, fg, bg, need in checks:
        if fg.startswith("rgb") or bg.startswith("rgb"):
            continue
        r = contrast_ratio(fg, bg)
        if r is None or r < need:
            raise AssertionError(f"{name}: ratio={r} need>={need} fg={fg} bg={bg}")
