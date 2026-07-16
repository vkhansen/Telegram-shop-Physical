/**
 * Single brand page context — everything the white-label template needs
 * is derived from public catalog API (DB columns + web_profile + media URLs).
 *
 * Capability masks come from the API (bot.platform.capabilities) so frontend
 * and future messaging surfaces share one switchboard.
 */

import {
  type BrandPublic,
  type Capabilities,
  type CatalogItem,
  type StoreMenu,
  type StoreSummary,
  CLIENT_CHANNEL,
  cap,
  fetchBrand,
  fetchStoreMenu,
  getApiBase,
} from "./api";
import { type ComplianceView, parseCompliance } from "./compliance";
import { asRecord, asString } from "./util";

export type NavChip = { href: string; label: string; active?: boolean };

export type Benefit = { n?: string; title: string; body: string };

export type SectionLabels = {
  home: string;
  catalog: string;
  about: string;
  contact: string;
  inquire: string;
  book: string;
  support: string;
  login: string;
  openBranch: string;
  featuredEyebrow: string;
  featuredBadge: string;
  featuredCta: string;
  catalogEyebrow: string;
  catalogHeadline: string;
  catalogSubline: string | null;
  benefitsEyebrow: string;
  benefitsHeadline: string;
  backToMenu: string;
};

export type BrandContext = {
  brand: BrandPublic;
  slug: string;
  web: Record<string, unknown>;
  compliance: ComplianceView;
  labels: SectionLabels;
  /** Resolved capability mask for this storefront channel. */
  capabilities: Capabilities;
  tagline: string | null;
  hero: Record<string, string>;
  about: { title: string; body: string };
  faq: { q: string; a: string }[];
  benefits: Benefit[];
  social: Record<string, string>;
  stores: StoreSummary[];
  defaultStore: StoreSummary | null;
  apiBase: string;
  channel: string;
};

export type HomeCatalog = {
  menu: StoreMenu | null;
  items: CatalogItem[];
  categories: StoreMenu["categories"];
  storeSlug: string;
  categoryName: string;
  featured: CatalogItem | null;
};

function parseLabels(web: Record<string, unknown>): SectionLabels {
  const nav = asRecord(web.nav);
  const sections = asRecord(web.sections);
  const hero = asRecord(web.hero);
  const about = asRecord(web.about);
  const cta = asRecord(web.cta);

  return {
    home: asString(nav.home) || "Home",
    catalog: asString(nav.catalog) || asString(sections.catalog_chip) || "Menu",
    about: asString(nav.about) || asString(about.title) || "About",
    contact: asString(nav.contact) || "Contact",
    inquire: asString(nav.inquire) || asString(cta.inquire) || "Inquire",
    book: asString(nav.book) || asString(cta.book) || "Book meeting",
    support: asString(nav.support) || asString(cta.support) || "Support",
    login: asString(nav.login) || asString(cta.login) || "Log in",
    openBranch: asString(sections.open_branch) || asString(cta.open_branch) || "Open branch →",
    featuredEyebrow:
      asString(hero.featured_eyebrow) || asString(sections.featured_eyebrow) || "Featured",
    featuredBadge: asString(hero.featured_badge) || asString(sections.featured_badge) || "Featured",
    featuredCta: asString(hero.featured_cta) || asString(sections.featured_cta) || "See all",
    catalogEyebrow: asString(sections.catalog_eyebrow) || "Catalog",
    catalogHeadline: asString(sections.catalog_headline) || "Explore the menu.",
    catalogSubline: asString(sections.catalog_subline),
    benefitsEyebrow: asString(sections.benefits_eyebrow) || "Highlights",
    benefitsHeadline: asString(sections.benefits_headline) || "What makes us different.",
    backToMenu: asString(cta.back_to_menu) || "← Back to menu",
  };
}

function parseBenefits(web: Record<string, unknown>): Benefit[] {
  const raw = web.benefits;
  if (!Array.isArray(raw)) return [];
  const out: Benefit[] = [];
  for (const item of raw) {
    const r = asRecord(item);
    const title = asString(r.title);
    const body = asString(r.body) || asString(r.body_md) || "";
    if (!title) continue;
    out.push({ n: asString(r.n) || undefined, title, body });
  }
  return out;
}

function parseFaq(web: Record<string, unknown>): { q: string; a: string }[] {
  const raw = web.faq;
  if (!Array.isArray(raw)) return [];
  const out: { q: string; a: string }[] = [];
  for (const item of raw) {
    const r = asRecord(item);
    const q = asString(r.q) || asString(r.question);
    const a = asString(r.a_md) || asString(r.a) || asString(r.answer);
    if (q && a) out.push({ q, a });
  }
  return out;
}

function parseSocial(web: Record<string, unknown>): Record<string, string> {
  const s = asRecord(web.social);
  const out: Record<string, string> = {};
  for (const [k, v] of Object.entries(s)) {
    const sv = asString(v);
    if (sv) out[k] = sv;
  }
  return out;
}

export async function loadBrandContext(slug: string): Promise<BrandContext | null> {
  const brand = await fetchBrand(slug, CLIENT_CHANNEL);
  if (!brand) return null;

  const web = (brand.web || {}) as Record<string, unknown>;
  const heroRec = asRecord(web.hero);
  const hero: Record<string, string> = {};
  for (const [k, v] of Object.entries(heroRec)) {
    const s = asString(v);
    if (s) hero[k] = s;
  }

  const aboutRec = asRecord(web.about);
  const about = {
    title: asString(aboutRec.title) || "About us",
    body:
      asString(aboutRec.body_md) ||
      asString(aboutRec.body) ||
      brand.description ||
      "More information coming soon.",
  };

  const stores = brand.stores || [];
  const defaultStore = stores.find((s) => s.is_default) || stores[0] || null;
  const capabilities: Capabilities = brand.capabilities || {};

  return {
    brand,
    slug: brand.slug,
    web,
    compliance: parseCompliance(web, { minAge: brand.min_age }),
    labels: parseLabels(web),
    capabilities,
    tagline: asString(web.tagline) || hero.headline || null,
    hero,
    about,
    faq: parseFaq(web),
    benefits: parseBenefits(web),
    social: cap(capabilities, "social_links", true) ? parseSocial(web) : {},
    stores,
    defaultStore,
    apiBase: getApiBase(),
    channel: brand.channel || CLIENT_CHANNEL,
  };
}

export async function loadHomeCatalog(ctx: BrandContext): Promise<HomeCatalog> {
  const empty: HomeCatalog = {
    menu: null,
    items: [],
    categories: [],
    storeSlug: "",
    categoryName: ctx.labels.catalog,
    featured: null,
  };
  if (!ctx.defaultStore || !cap(ctx.capabilities, "catalog", true)) return empty;

  const menu = await fetchStoreMenu(ctx.slug, ctx.defaultStore.slug);
  if (!menu) return { ...empty, storeSlug: ctx.defaultStore.slug };

  const categories = menu.categories || [];
  const items = categories.flatMap((c) => c.items);
  const categoryName = categories[0]?.name || ctx.labels.catalog;
  const featuredName = (ctx.hero.featured_item || "").toLowerCase();

  let featured: CatalogItem | null = null;
  if (featuredName) {
    featured = items.find((i) => i.name.toLowerCase() === featuredName) || null;
  }
  if (!featured) {
    featured =
      items.find((i) => /limited|new release|featured/i.test(i.description || "")) ||
      items[0] ||
      null;
  }

  return {
    menu,
    items,
    categories,
    storeSlug: menu.store.slug,
    categoryName,
    featured,
  };
}

export function buildNavChips(
  ctx: BrandContext,
  opts: {
    active?: "home" | "about" | "contact" | "store" | string;
    storeSlug?: string;
    includeCatalogAnchor?: boolean;
  } = {},
): NavChip[] {
  const { active = "home", storeSlug, includeCatalogAnchor = false } = opts;
  const s = ctx.slug;
  const L = ctx.labels;
  const C = ctx.capabilities;

  const chips: NavChip[] = [{ href: `/${s}`, label: L.home, active: active === "home" }];

  if (includeCatalogAnchor && cap(C, "catalog", true)) {
    chips.push({ href: `#catalog`, label: L.catalog, active: false });
  }

  if (cap(C, "catalog", true)) {
    for (const st of ctx.stores) {
      chips.push({
        href: `/${s}/${st.slug}`,
        label: st.name,
        active: active === "store" && storeSlug === st.slug,
      });
    }
  }

  if (cap(C, "about", true)) {
    chips.push({ href: `/${s}/about`, label: L.about, active: active === "about" });
  }
  if (cap(C, "contact", true)) {
    chips.push({ href: `/${s}/contact`, label: L.contact, active: active === "contact" });
  }

  return chips;
}

export function buildHeaderActions(
  ctx: BrandContext,
): { href: string; label: string; primary?: boolean }[] {
  const s = ctx.slug;
  const L = ctx.labels;
  const C = ctx.capabilities;
  const actions: { href: string; label: string; primary?: boolean }[] = [];

  if (cap(C, "contact", true)) {
    actions.push({ href: `/${s}/contact`, label: L.contact, primary: true });
  }
  if (cap(C, "leads", true) || cap(C, "portfolio", false)) {
    actions.push({ href: `/${s}/inquire`, label: L.inquire });
  }
  if (cap(C, "booking", true)) {
    actions.push({ href: `/${s}/book`, label: L.book });
  }
  if (cap(C, "tickets", true)) {
    actions.push({ href: `/${s}/tickets`, label: L.support });
  }
  if (cap(C, "auth", true)) {
    actions.push({ href: `/${s}/login`, label: L.login });
  }
  if (cap(C, "about", true)) {
    actions.push({ href: `/${s}/about`, label: L.about });
  }
  return actions;
}

/** Footer nav filtered by capabilities. */
export function buildFooterLinks(ctx: BrandContext): { href: string; label: string }[] {
  const s = ctx.slug;
  const L = ctx.labels;
  const C = ctx.capabilities;
  const links: { href: string; label: string }[] = [{ href: `/${s}`, label: L.home }];
  if (cap(C, "about", true)) links.push({ href: `/${s}/about`, label: L.about });
  if (cap(C, "contact", true)) links.push({ href: `/${s}/contact`, label: L.contact });
  if (cap(C, "leads", true)) links.push({ href: `/${s}/inquire`, label: L.inquire });
  if (cap(C, "booking", true)) links.push({ href: `/${s}/book`, label: L.book });
  if (cap(C, "tickets", true)) links.push({ href: `/${s}/tickets`, label: L.support });
  if (cap(C, "auth", true)) links.push({ href: `/${s}/login`, label: L.login });
  return links;
}

export function catalogSubline(ctx: BrandContext, home: HomeCatalog): string {
  if (ctx.labels.catalogSubline) return ctx.labels.catalogSubline;
  const storeName = home.menu?.store.name || ctx.defaultStore?.name || "";
  const parts = [home.categoryName, `${home.items.length} items`, storeName].filter(Boolean);
  return parts.join(" · ");
}

/** Convenience: capability check on context. */
export function can(ctx: BrandContext, key: string, fallback = true): boolean {
  return cap(ctx.capabilities, key, fallback);
}
