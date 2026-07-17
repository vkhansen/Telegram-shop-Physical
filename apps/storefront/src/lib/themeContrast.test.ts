/**
 * Contrast enforcement unit checks (run with: npx tsx or vitest if available).
 * Also mirrored for Python-side seed confidence via storefront theme exports.
 */
import { contrastRatio, enforceColorContrast, ensureContrast, parseThemeTokens } from "./theme";

function assert(cond: unknown, msg: string) {
  if (!cond) throw new Error(msg);
}

// Bad seed: white text on white paper → must be fixed
const broken = enforceColorContrast(
  {
    paper: "#ffffff",
    ink: "#ffffff",
    on_ink: "#ffffff",
    accent: "#eeeeee",
    sun: "#f5f5f5",
    on_accent: "#ffffff",
    muted: "#ffffff",
  },
  "light",
);
assert((contrastRatio(broken.ink, broken.paper) ?? 0) >= 4.5, "ink/paper fixed");
assert((contrastRatio(broken.on_ink, broken.ink) ?? 0) >= 4.5, "on_ink/ink fixed");
assert((contrastRatio(broken.on_accent, broken.sun) ?? 0) >= 4.5, "on_accent/sun fixed");

// Dark page with dark text → fixed to light text
const darkBroken = enforceColorContrast({ paper: "#0a0a0b", ink: "#111111" }, "dark");
assert((contrastRatio(darkBroken.ink, darkBroken.paper) ?? 0) >= 4.5, "dark ink/paper");

// Light theme must NOT become editorial just because mode=light
const lightWeb = {
  theme: "ig_default",
  theme_tokens: {
    mode: "light",
    colors: {
      paper: "#f6efe6",
      ink: "#1c120c",
      accent: "#8b4513",
      sun: "#c4782a",
      on_ink: "#f6efe6",
      on_accent: "#ffffff",
    },
    chrome: { catalog: "ig_grid", hero: "profile" },
  },
};
const lightTok = parseThemeTokens(lightWeb);
assert(lightTok.isEditorial === false, "light non-editorial");
assert(lightTok.mode === "light", "mode light");
assert((contrastRatio(lightTok.colors.ink, lightTok.colors.paper) ?? 0) >= 4.5, "coffee ink/paper");

// Editorial stays editorial
const snus = parseThemeTokens({
  theme: "landing_editorial",
  theme_tokens: {
    mode: "light",
    chrome: { catalog: "flavor_tiles" },
    colors: { paper: "#fbf8f3", ink: "#06122e", sun: "#ffd60a", on_accent: "#06122e" },
  },
});
assert(snus.isEditorial === true, "snus editorial");
assert((contrastRatio(snus.colors.ink, snus.colors.paper) ?? 0) >= 4.5, "snus ink/paper");

// ensureContrast helper
assert(ensureContrast("#fff", "#fff") !== "#fff", "ensure flips white/white");

console.log("themeContrast.test.ts: all passed");
