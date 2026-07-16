/**
 * Per-brand theme tokens from web_profile.theme_tokens.
 * Only tokens (colors, enums, numbers) — CSS lives in the app.
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

const DEFAULT_DARK: ThemeTokens = {
  mode: "dark",
  themeName: "ig_default",
  colors: {
    ink: "#0a0a0b",
    sea: "#2a2a2e",
    sea_deep: "#111113",
    sun: "#c8a96b",
    paper: "#0a0a0b",
    paper_warm: "#111113",
    line: "rgba(255,255,255,.08)",
    footer: "#0a0a0b",
    accent: "#c8a96b",
    on_ink: "#faf8f5",
    muted: "rgba(250,248,245,.55)",
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

function pickFont(v: unknown, fallback: string): string {
  const s = asString(v);
  if (!s) return fallback;
  if (FONT_ALLOW.has(s)) return s;
  // allow stack fragments only if every family is allowlisted or generic
  const parts = s.split(",").map((p) => p.trim().replace(/^["']|["']$/g, ""));
  if (parts.every((p) => FONT_ALLOW.has(p) || p === "monospace" || p === "serif")) return s;
  return fallback;
}

function pickHexOrCss(v: unknown, fallback: string): string {
  const s = asString(v);
  if (!s) return fallback;
  // allow #hex, rgb(), rgba(), hsl(), named basics
  if (/^#([0-9a-fA-F]{3,8})$/.test(s)) return s;
  if (/^(rgb|rgba|hsl|hsla)\(/.test(s)) return s;
  return fallback;
}

function pickCssLen(v: unknown, fallback: string): string {
  const s = asString(v);
  if (!s) return fallback;
  if (/^[\d.]+(px|rem|em|%|vh|vw)?$/.test(s) || s === "999px" || /^\d+\/\d+$/.test(s)) return s;
  if (/^[\d.]+px\s+[\d.]+px/.test(s)) return s; // shadow-ish
  return fallback;
}

/** Parse web_profile.theme + theme_tokens into a resolved token pack. */
export function parseThemeTokens(web: Record<string, unknown>, themeName?: string | null): ThemeTokens {
  const name = asString(themeName) || asString(web.theme) || "ig_default";
  const raw = asRecord(web.theme_tokens);
  const isEditorial =
    name === "landing_editorial" ||
    asString(asRecord(raw.chrome).catalog) === "flavor_tiles" ||
    asString(raw.mode) === "light";

  if (!Object.keys(raw).length && !isEditorial) {
    return { ...DEFAULT_DARK, themeName: name };
  }

  const colorsIn = asRecord(raw.colors);
  const typeIn = asRecord(raw.type);
  const geoIn = asRecord(raw.geometry);
  const motionIn = asRecord(raw.motion);
  const chromeIn = asRecord(raw.chrome);

  const base = isEditorial
    ? {
        ...DEFAULT_DARK,
        mode: "light" as ThemeMode,
        themeName: name,
        colors: {
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
          muted: "rgba(6,18,46,.55)",
        },
        type: {
          display: "Archivo Black",
          body: "Inter",
          mono: "JetBrains Mono",
          displayScale: "hero_xl",
          letterSpacingDisplay: "-0.02em",
          lineHeightDisplay: "0.88",
          textTransformDisplay: "uppercase",
        },
        geometry: {
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
        },
        motion: { tickerSeconds: 28, hoverLiftPx: 6, heroUnderline: true },
        chrome: {
          nav: "sticky_full",
          ticker: "marquee",
          age_gate: "paper_card",
          benefits: "ink_strip_numbers",
          catalog: "flavor_tiles",
          product_media: "vector_only",
          logo: "wordmark_svg",
          hero: "editorial_display",
          featured: "spotlight",
        },
        isEditorial: true,
      }
    : { ...DEFAULT_DARK, themeName: name };

  const colors: Record<string, string> = { ...base.colors };
  for (const [k, v] of Object.entries(colorsIn)) {
    colors[k] = pickHexOrCss(v, colors[k] || "#000000");
  }

  return {
    mode: asString(raw.mode) === "light" ? "light" : asString(raw.mode) === "dark" ? "dark" : base.mode,
    themeName: name,
    colors,
    type: {
      display: pickFont(typeIn.display, base.type.display),
      body: pickFont(typeIn.body, base.type.body),
      mono: pickFont(typeIn.mono, base.type.mono),
      displayScale: asString(typeIn.display_scale) || base.type.displayScale,
      letterSpacingDisplay: asString(typeIn.letter_spacing_display) || base.type.letterSpacingDisplay,
      lineHeightDisplay: asString(typeIn.line_height_display) || base.type.lineHeightDisplay,
      textTransformDisplay: asString(typeIn.text_transform_display) || base.type.textTransformDisplay,
    },
    geometry: {
      radiusCard: pickCssLen(geoIn.radius_card, base.geometry.radiusCard),
      radiusPill: pickCssLen(geoIn.radius_pill, base.geometry.radiusPill),
      radiusGate: pickCssLen(geoIn.radius_gate, base.geometry.radiusGate),
      containerMax: pickCssLen(geoIn.container_max, base.geometry.containerMax),
      sectionPadY: pickCssLen(geoIn.section_pad_y, base.geometry.sectionPadY),
      gridCatalog: asString(geoIn.grid_catalog) || base.geometry.gridCatalog,
      cardAspect: asString(geoIn.card_aspect) || base.geometry.cardAspect,
      canTiltDeg: Number(geoIn.can_tilt_deg ?? base.geometry.canTiltDeg) || 0,
      shadow: asString(geoIn.shadow) || base.geometry.shadow,
      borderWidth: pickCssLen(geoIn.border_width, base.geometry.borderWidth),
    },
    motion: {
      tickerSeconds: Number(motionIn.ticker_seconds ?? base.motion.tickerSeconds) || 0,
      hoverLiftPx: Number(motionIn.hover_lift_px ?? base.motion.hoverLiftPx) || 0,
      heroUnderline: asBool(motionIn.hero_underline, base.motion.heroUnderline),
    },
    chrome: {
      nav: asString(chromeIn.nav) || base.chrome.nav,
      ticker: asString(chromeIn.ticker) || base.chrome.ticker,
      age_gate: asString(chromeIn.age_gate) || base.chrome.age_gate,
      benefits: asString(chromeIn.benefits) || base.chrome.benefits,
      catalog: asString(chromeIn.catalog) || base.chrome.catalog,
      product_media: asString(chromeIn.product_media) || base.chrome.product_media,
      logo: asString(chromeIn.logo) || base.chrome.logo,
      hero: asString(chromeIn.hero) || base.chrome.hero,
      featured: asString(chromeIn.featured) || base.chrome.featured,
    },
    isEditorial: isEditorial || asString(chromeIn.catalog) === "flavor_tiles",
  };
}

/** CSS custom properties for injection on .brand-shell / :root. */
export function themeCssVars(t: ThemeTokens): Record<string, string> {
  const c = t.colors;
  return {
    "--brand-ink": c.ink || "#06122e",
    "--brand-sea": c.sea || "#0a4ea2",
    "--brand-sea-deep": c.sea_deep || c.sea || "#062f63",
    "--brand-sun": c.sun || c.accent || "#ffd60a",
    "--brand-paper": c.paper || "#fbf8f3",
    "--brand-paper-warm": c.paper_warm || c.paper || "#f3ecdf",
    "--brand-line": c.line || "rgba(6,18,46,.12)",
    "--brand-footer": c.footer || "#02091b",
    "--brand-accent": c.accent || c.sun || "#ffd60a",
    "--brand-on-ink": c.on_ink || "#fbf8f3",
    "--brand-muted": c.muted || "rgba(6,18,46,.55)",
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
    .map((f) => f.replace(/ /g, "+") + (f === "Archivo Black" ? ":wght@400" : f === "Inter" ? ":wght@400;500;600;700" : ":wght@400;500"));
  if (!families.length) return null;
  const unique = [...new Set(families)];
  return `https://fonts.googleapis.com/css2?${unique.map((f) => `family=${f}`).join("&")}&display=swap`;
}
