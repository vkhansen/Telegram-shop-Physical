/**
 * Per-brand theme tokens from web_profile.theme_tokens.
 * Only tokens (colors, enums, numbers) — CSS lives in the app.
 *
 * Contrast law: primary text vs background must remain readable.
 * We enforce WCAG-ish relative-luminance ratios after parsing DB tokens
 * so a bad seed cannot ship white-on-white / dark-on-dark.
 */

import { asBool, asRecord, asString } from "./util";

export type ThemeMode = "light" | "dark";

export type ThemeChrome = {
  nav: "sticky_full" | "profile" | string;
  ticker: "marquee" | "static" | string;
  age_gate: "paper_card" | "dark_full" | string;
  benefits: "ink_strip_numbers" | "cards" | string;
  catalog: "flavor_tiles" | "ig_grid" | string;
  product_media: "vector_only" | "photo_or_vector" | "photo" | string;
  logo: "wordmark_svg" | "image" | string;
  hero: "editorial_display" | "profile" | string;
  featured: "spotlight" | "split" | string;
};

export type ThemeTokens = {
  mode: ThemeMode;
  themeName: string;
  colors: Record<string, string>;
  type: {
    display: string;
    body: string;
    mono: string;
    displayScale: string;
    letterSpacingDisplay: string;
    lineHeightDisplay: string;
    textTransformDisplay: string;
  };
  geometry: {
    radiusCard: string;
    radiusPill: string;
    radiusGate: string;
    containerMax: string;
    sectionPadY: string;
    gridCatalog: string;
    cardAspect: string;
    canTiltDeg: number;
    shadow: string;
    borderWidth: string;
  };
  motion: {
    tickerSeconds: number;
    hoverLiftPx: number;
    heroUnderline: boolean;
  };
  chrome: ThemeChrome;
  isEditorial: boolean;
};

const FONT_ALLOW = new Set(["Archivo Black", "Inter", "JetBrains Mono", "system-ui", "sans-serif"]);

/** Minimum contrast ratio for body text (approx WCAG AA). */
const MIN_TEXT_CONTRAST = 4.5;
/** Softer threshold for muted / secondary. */
const MIN_MUTED_CONTRAST = 3.0;

const DEFAULT_DARK: ThemeTokens = {
  mode: "dark",
  themeName: "ig_default",
  colors: {
    // Semantic: paper = page bg, ink = body text on paper, on_ink = text on solid ink surfaces
    ink: "#f4f2ef",
    sea: "#9ca3af",
    sea_deep: "#6b7280",
    sun: "#e8b84a",
    paper: "#0c0c0e",
    paper_warm: "#161618",
    line: "rgba(255,255,255,.12)",
    footer: "#050506",
    accent: "#e8b84a",
    on_ink: "#0c0c0e",
    on_accent: "#14110a",
    muted: "rgba(244,242,239,.72)",
  },
  type: {
    display: "system-ui",
    body: "system-ui",
    mono: "ui-monospace",
    displayScale: "normal",
    letterSpacingDisplay: "-0.02em",
    lineHeightDisplay: "1.05",
    textTransformDisplay: "none",
  },
  geometry: {
    radiusCard: "1rem",
    radiusPill: "999px",
    radiusGate: "0",
    containerMax: "72rem",
    sectionPadY: "2.5rem",
    gridCatalog: "3",
    cardAspect: "1/1",
    canTiltDeg: 0,
    shadow: "none",
    borderWidth: "1px",
  },
  motion: {
    tickerSeconds: 0,
    hoverLiftPx: 0,
    heroUnderline: false,
  },
  chrome: {
    nav: "profile",
    ticker: "static",
    age_gate: "dark_full",
    benefits: "cards",
    catalog: "ig_grid",
    product_media: "photo_or_vector",
    logo: "image",
    hero: "profile",
    featured: "split",
  },
  isEditorial: false,
};

const DEFAULT_EDITORIAL_COLORS: Record<string, string> = {
  ink: "#06122e",
  sea: "#0a4ea2",
  sea_deep: "#062f63",
  sun: "#ffd60a",
  paper: "#fbf8f3",
  paper_warm: "#f3ecdf",
  line: "rgba(6,18,46,.12)",
  footer: "#02091b",
  accent: "#ffd60a",
  on_ink: "#fbf8f3",
  on_accent: "#06122e",
  muted: "rgba(6,18,46,.62)",
};

// ── Color math (contrast enforcement) ──────────────────────────────────────

function parseHex(hex: string): [number, number, number] | null {
  const h = hex.trim().replace(/^#/, "");
  if (/^[0-9a-fA-F]{3}$/.test(h)) {
    return [parseInt(h[0] + h[0], 16), parseInt(h[1] + h[1], 16), parseInt(h[2] + h[2], 16)];
  }
  if (/^[0-9a-fA-F]{6}$/.test(h)) {
    return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
  }
  if (/^[0-9a-fA-F]{8}$/.test(h)) {
    return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
  }
  return null;
}

function parseCssColor(raw: string): [number, number, number, number] | null {
  const s = raw.trim();
  const hex = parseHex(s);
  if (hex) return [...hex, 1];

  const rgba = s.match(/^rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)(?:\s*,\s*([\d.]+))?\s*\)$/i);
  if (rgba) {
    return [
      Math.min(255, Number(rgba[1])),
      Math.min(255, Number(rgba[2])),
      Math.min(255, Number(rgba[3])),
      rgba[4] != null ? Math.min(1, Number(rgba[4])) : 1,
    ];
  }
  return null;
}

function srgbToLin(c: number): number {
  const v = c / 255;
  return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
}

/** Relative luminance 0–1 (WCAG). */
export function relativeLuminance(color: string): number | null {
  const p = parseCssColor(color);
  if (!p) return null;
  const [r, g, b, a] = p;
  if (a < 0.15) return null; // nearly transparent — skip
  // Composite translucent colors onto mid-gray for a conservative estimate
  const blend = (c: number) => c * a + 128 * (1 - a);
  return 0.2126 * srgbToLin(blend(r)) + 0.7152 * srgbToLin(blend(g)) + 0.0722 * srgbToLin(blend(b));
}

export function contrastRatio(a: string, b: string): number | null {
  const L1 = relativeLuminance(a);
  const L2 = relativeLuminance(b);
  if (L1 == null || L2 == null) return null;
  const hi = Math.max(L1, L2);
  const lo = Math.min(L1, L2);
  return (hi + 0.05) / (lo + 0.05);
}

function toHex(r: number, g: number, b: number): string {
  const h = (n: number) => Math.max(0, Math.min(255, Math.round(n))).toString(16).padStart(2, "0");
  return `#${h(r)}${h(g)}${h(b)}`;
}

/** Pick near-black or near-white — whichever contrasts better with bg. */
export function contrastingText(bg: string): string {
  const black = "#14110a";
  const white = "#f7f5f2";
  const rb = contrastRatio(black, bg) ?? 0;
  const rw = contrastRatio(white, bg) ?? 0;
  return rb >= rw ? black : white;
}

/**
 * Ensure `fg` contrasts with `bg`. If not, replace fg with black/white (or tinted).
 * Returns the (possibly corrected) foreground color.
 */
export function ensureContrast(fg: string, bg: string, minRatio = MIN_TEXT_CONTRAST): string {
  const ratio = contrastRatio(fg, bg);
  if (ratio != null && ratio >= minRatio) return fg;
  return contrastingText(bg);
}

/**
 * Normalize a full color pack so body text, inverted surfaces, and accents stay readable.
 */
export function enforceColorContrast(colors: Record<string, string>, mode: ThemeMode): Record<string, string> {
  const out = { ...colors };

  const paper = out.paper || (mode === "light" ? "#f7f5f2" : "#0c0c0e");
  const paperWarm = out.paper_warm || paper;
  out.paper = paper;
  out.paper_warm = paperWarm;

  // Body text on page
  out.ink = ensureContrast(out.ink || contrastingText(paper), paper, MIN_TEXT_CONTRAST);

  // Text on solid ink surfaces (nav active, benefits strip)
  out.on_ink = ensureContrast(out.on_ink || contrastingText(out.ink), out.ink, MIN_TEXT_CONTRAST);

  // Accent / sun — primary CTAs use sun as fill; on_accent must contrast sun
  // (do not re-check against a darker "accent" brand color — that caused
  // light text on mid-tone gold buttons).
  const accent = out.accent || out.sun || (mode === "light" ? "#0a4ea2" : "#e8b84a");
  const sun = out.sun || accent;
  out.accent = accent;
  out.sun = sun;
  out.on_accent = ensureContrast(out.on_accent || contrastingText(sun), sun, MIN_TEXT_CONTRAST);

  // Muted on paper (allow softer ratio)
  const mutedCandidate = out.muted || (mode === "light" ? "rgba(20,17,10,.62)" : "rgba(247,245,242,.72)");
  const mutedRatio = contrastRatio(mutedCandidate, paper);
  if (mutedRatio == null || mutedRatio < MIN_MUTED_CONTRAST) {
    // Derive muted from ink with opacity-like hex blend toward paper
    const inkRgb = parseCssColor(out.ink);
    const paperRgb = parseCssColor(paper);
    if (inkRgb && paperRgb) {
      const mix = 0.62;
      out.muted = toHex(
        inkRgb[0] * mix + paperRgb[0] * (1 - mix),
        inkRgb[1] * mix + paperRgb[1] * (1 - mix),
        inkRgb[2] * mix + paperRgb[2] * (1 - mix),
      );
      out.muted = ensureContrast(out.muted, paper, MIN_MUTED_CONTRAST);
    } else {
      out.muted = ensureContrast(contrastingText(paper), paper, MIN_MUTED_CONTRAST);
    }
  } else {
    out.muted = mutedCandidate;
  }

  // Sea (links / secondary brand) must not wash out on paper
  if (out.sea) {
    out.sea = ensureContrast(out.sea, paper, MIN_MUTED_CONTRAST);
  } else {
    out.sea = mode === "light" ? ensureContrast("#0a4ea2", paper, MIN_MUTED_CONTRAST) : ensureContrast("#93c5fd", paper, MIN_MUTED_CONTRAST);
  }
  out.sea_deep = out.sea_deep ? ensureContrast(out.sea_deep, paper, MIN_MUTED_CONTRAST) : out.sea;

  // Footer: solid dark-ish surface with readable text token via on_footer (optional)
  const footer = out.footer || (mode === "light" ? out.ink : "#050506");
  out.footer = footer;
  out.on_footer = ensureContrast(out.on_footer || contrastingText(footer), footer, MIN_TEXT_CONTRAST);

  // Line borders: keep as-is if provided; else derive
  if (!out.line) {
    out.line = mode === "light" ? "rgba(20,17,10,.12)" : "rgba(255,255,255,.12)";
  }

  return out;
}

function pickFont(v: unknown, fallback: string): string {
  const s = asString(v);
  if (!s) return fallback;
  if (FONT_ALLOW.has(s)) return s;
  const parts = s.split(",").map((p) => p.trim().replace(/^["']|["']$/g, ""));
  if (parts.every((p) => FONT_ALLOW.has(p) || p === "monospace" || p === "serif")) return s;
  return fallback;
}

function pickHexOrCss(v: unknown, fallback: string): string {
  const s = asString(v);
  if (!s) return fallback;
  if (/^#([0-9a-fA-F]{3,8})$/.test(s)) return s;
  if (/^(rgb|rgba|hsl|hsla)\(/.test(s)) return s;
  return fallback;
}

function pickCssLen(v: unknown, fallback: string): string {
  const s = asString(v);
  if (!s) return fallback;
  if (/^[\d.]+(px|rem|em|%|vh|vw)?$/.test(s) || s === "999px" || /^\d+\/\d+$/.test(s)) return s;
  if (/^[\d.]+px\s+[\d.]+px/.test(s)) return s;
  return fallback;
}

/** Parse web_profile.theme + theme_tokens into a resolved token pack. */
export function parseThemeTokens(web: Record<string, unknown>, themeName?: string | null): ThemeTokens {
  const name = asString(themeName) || asString(web.theme) || "ig_default";
  const raw = asRecord(web.theme_tokens);
  // Editorial ONLY for explicit editorial skins — not every light theme.
  const isEditorial =
    name === "landing_editorial" || asString(asRecord(raw.chrome).catalog) === "flavor_tiles";

  if (!Object.keys(raw).length && !isEditorial) {
    const colors = enforceColorContrast({ ...DEFAULT_DARK.colors }, "dark");
    return { ...DEFAULT_DARK, themeName: name, colors };
  }

  const colorsIn = asRecord(raw.colors);
  const typeIn = asRecord(raw.type);
  const geoIn = asRecord(raw.geometry);
  const motionIn = asRecord(raw.motion);
  const chromeIn = asRecord(raw.chrome);

  const modeRaw = asString(raw.mode);
  const mode: ThemeMode =
    modeRaw === "light" ? "light" : modeRaw === "dark" ? "dark" : isEditorial ? "light" : "dark";

  const baseColors = isEditorial
    ? { ...DEFAULT_EDITORIAL_COLORS }
    : mode === "light"
      ? {
          ink: "#14110a",
          sea: "#0a4ea2",
          sea_deep: "#062f63",
          sun: "#c4782a",
          paper: "#f7f5f2",
          paper_warm: "#efe8df",
          line: "rgba(20,17,10,.12)",
          footer: "#14110a",
          accent: "#c4782a",
          on_ink: "#f7f5f2",
          on_accent: "#14110a",
          muted: "rgba(20,17,10,.62)",
        }
      : { ...DEFAULT_DARK.colors };

  const colors: Record<string, string> = { ...baseColors };
  for (const [k, v] of Object.entries(colorsIn)) {
    colors[k] = pickHexOrCss(v, colors[k] || "#000000");
  }

  const fixed = enforceColorContrast(colors, mode);

  const baseChrome = isEditorial
    ? {
        nav: "sticky_full",
        ticker: "marquee",
        age_gate: "paper_card",
        benefits: "ink_strip_numbers",
        catalog: "flavor_tiles",
        product_media: "vector_only",
        logo: "wordmark_svg",
        hero: "editorial_display",
        featured: "spotlight",
      }
    : { ...DEFAULT_DARK.chrome };

  const baseType = isEditorial
    ? {
        display: "Archivo Black",
        body: "Inter",
        mono: "JetBrains Mono",
        displayScale: "hero_xl",
        letterSpacingDisplay: "-0.02em",
        lineHeightDisplay: "0.88",
        textTransformDisplay: "uppercase",
      }
    : { ...DEFAULT_DARK.type };

  const baseGeo = isEditorial
    ? {
        radiusCard: "20px",
        radiusPill: "999px",
        radiusGate: "24px",
        containerMax: "1280px",
        sectionPadY: "5rem",
        gridCatalog: "3",
        cardAspect: "4/5",
        canTiltDeg: 8,
        shadow: "0 30px 60px -30px rgba(6,18,46,.35)",
        borderWidth: "1.5px",
      }
    : { ...DEFAULT_DARK.geometry };

  return {
    mode,
    themeName: name,
    colors: fixed,
    type: {
      display: pickFont(typeIn.display, baseType.display),
      body: pickFont(typeIn.body, baseType.body),
      mono: pickFont(typeIn.mono, baseType.mono),
      displayScale: asString(typeIn.display_scale) || baseType.displayScale,
      letterSpacingDisplay: asString(typeIn.letter_spacing_display) || baseType.letterSpacingDisplay,
      lineHeightDisplay: asString(typeIn.line_height_display) || baseType.lineHeightDisplay,
      textTransformDisplay: asString(typeIn.text_transform_display) || baseType.textTransformDisplay,
    },
    geometry: {
      radiusCard: pickCssLen(geoIn.radius_card, baseGeo.radiusCard),
      radiusPill: pickCssLen(geoIn.radius_pill, baseGeo.radiusPill),
      radiusGate: pickCssLen(geoIn.radius_gate, baseGeo.radiusGate),
      containerMax: pickCssLen(geoIn.container_max, baseGeo.containerMax),
      sectionPadY: pickCssLen(geoIn.section_pad_y, baseGeo.sectionPadY),
      gridCatalog: asString(geoIn.grid_catalog) || baseGeo.gridCatalog,
      cardAspect: asString(geoIn.card_aspect) || baseGeo.cardAspect,
      canTiltDeg: Number(geoIn.can_tilt_deg ?? baseGeo.canTiltDeg) || 0,
      shadow: asString(geoIn.shadow) || baseGeo.shadow,
      borderWidth: pickCssLen(geoIn.border_width, baseGeo.borderWidth),
    },
    motion: {
      tickerSeconds: Number(motionIn.ticker_seconds ?? (isEditorial ? 28 : 0)) || 0,
      hoverLiftPx: Number(motionIn.hover_lift_px ?? (isEditorial ? 6 : 0)) || 0,
      heroUnderline: asBool(motionIn.hero_underline, isEditorial),
    },
    chrome: {
      nav: asString(chromeIn.nav) || baseChrome.nav,
      ticker: asString(chromeIn.ticker) || baseChrome.ticker,
      age_gate: asString(chromeIn.age_gate) || baseChrome.age_gate,
      benefits: asString(chromeIn.benefits) || baseChrome.benefits,
      catalog: asString(chromeIn.catalog) || baseChrome.catalog,
      product_media: asString(chromeIn.product_media) || baseChrome.product_media,
      logo: asString(chromeIn.logo) || baseChrome.logo,
      hero: asString(chromeIn.hero) || baseChrome.hero,
      featured: asString(chromeIn.featured) || baseChrome.featured,
    },
    isEditorial,
  };
}

/** CSS custom properties for injection on .brand-shell / :root. */
export function themeCssVars(t: ThemeTokens): Record<string, string> {
  const c = t.colors;
  return {
    "--brand-ink": c.ink || "#f4f2ef",
    "--brand-sea": c.sea || "#0a4ea2",
    "--brand-sea-deep": c.sea_deep || c.sea || "#062f63",
    "--brand-sun": c.sun || c.accent || "#e8b84a",
    "--brand-paper": c.paper || "#0c0c0e",
    "--brand-paper-warm": c.paper_warm || c.paper || "#161618",
    "--brand-line": c.line || "rgba(255,255,255,.12)",
    "--brand-footer": c.footer || "#050506",
    "--brand-accent": c.accent || c.sun || "#e8b84a",
    "--brand-on-ink": c.on_ink || "#0c0c0e",
    "--brand-on-accent": c.on_accent || contrastingText(c.sun || c.accent || "#e8b84a"),
    "--brand-on-footer": c.on_footer || contrastingText(c.footer || "#050506"),
    "--brand-muted": c.muted || "rgba(244,242,239,.72)",
    "--font-display": `"${t.type.display}", system-ui, sans-serif`,
    "--font-body": `"${t.type.body}", system-ui, sans-serif`,
    "--font-mono": `"${t.type.mono}", ui-monospace, monospace`,
    "--ls-display": t.type.letterSpacingDisplay,
    "--lh-display": t.type.lineHeightDisplay,
    "--radius-card": t.geometry.radiusCard,
    "--radius-pill": t.geometry.radiusPill,
    "--radius-gate": t.geometry.radiusGate,
    "--container-max": t.geometry.containerMax,
    "--section-pad-y": t.geometry.sectionPadY,
    "--card-aspect": t.geometry.cardAspect,
    "--can-tilt": `${t.geometry.canTiltDeg}deg`,
    "--brand-shadow": t.geometry.shadow,
    "--brand-border-w": t.geometry.borderWidth,
    "--ticker-seconds": `${t.motion.tickerSeconds || 28}s`,
    "--hover-lift": `${t.motion.hoverLiftPx}px`,
  };
}

/** Google Fonts URL for allowlisted families (editorial only). */
export function themeFontHref(t: ThemeTokens): string | null {
  if (!t.isEditorial) return null;
  const families = [t.type.display, t.type.body, t.type.mono]
    .filter((f) => FONT_ALLOW.has(f) && f !== "system-ui" && f !== "sans-serif")
    .map(
      (f) =>
        f.replace(/ /g, "+") +
        (f === "Archivo Black" ? ":wght@400" : f === "Inter" ? ":wght@400;500;600;700" : ":wght@400;500"),
    );
  if (!families.length) return null;
  const unique = [...new Set(families)];
  return `https://fonts.googleapis.com/css2?${unique.map((f) => `family=${f}`).join("&")}&display=swap`;
}
