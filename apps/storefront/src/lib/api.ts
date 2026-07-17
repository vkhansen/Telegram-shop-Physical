/** Client for public catalog API — channel-agnostic brand/catalog DTOs. */

/**
 * Resolve API origin:
 * - Browser: PUBLIC_API_BASE (empty string = same-origin, for Funnel reverse-proxy)
 * - SSR (Node): API_INTERNAL_BASE (e.g. http://bot:9090) so Docker SSR can reach the API
 */
function resolveApiBase(): string {
  const isServer = import.meta.env.SSR || typeof window === "undefined";
  if (isServer) {
    const internal =
      (typeof process !== "undefined" && process.env.API_INTERNAL_BASE) ||
      import.meta.env.API_INTERNAL_BASE ||
      "";
    if (internal) return String(internal).replace(/\/$/, "");
  }
  // Explicit empty PUBLIC_API_BASE means same-origin (do not fall back to localhost)
  if (import.meta.env.PUBLIC_API_BASE === "" || import.meta.env.PUBLIC_API_BASE === "same-origin") {
    return "";
  }
  const pub = import.meta.env.PUBLIC_API_BASE;
  if (pub == null || pub === undefined) {
    return isServer ? "http://127.0.0.1:9090" : "http://127.0.0.1:9090";
  }
  return String(pub).replace(/\/$/, "");
}

const API_BASE = resolveApiBase();

/** Surface this storefront represents when requesting capability masks. */
export const CLIENT_CHANNEL = "web" as const;

export type Capabilities = Record<string, boolean>;

export type BrandPublic = {
  slug: string;
  name: string;
  description?: string | null;
  logo_url?: string | null;
  timezone?: string | null;
  commerce_mode: string;
  age_gate_enabled: boolean;
  min_age?: number | null;
  channel?: string;
  capabilities?: Capabilities;
  channels?: Record<string, boolean>;
  legal: { legal_name?: string | null; dbd_number?: string | null };
  contact: { support_email?: string | null; support_phone?: string | null };
  web: Record<string, unknown>;
  stores: StoreSummary[];
};

export type StoreSummary = {
  slug: string;
  name: string;
  address?: string | null;
  phone?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  maps_url?: string | null;
  is_default?: boolean;
  menu_image_url?: string | null;
};

export type CatalogItem = {
  slug: string;
  name: string;
  category?: string;
  price?: string | null;
  image_url?: string | null;
  media_urls?: string[];
  available: boolean;
  badges: string[];
  cta: string;
  description?: string;
  inquiry_only?: boolean;
  web_orderable?: boolean;
  prep_time_minutes?: number | null;
  allergens?: string | null;
  /** Geometry-driven product identity (optional — from goods.media web_visual) */
  accent_hex?: string | null;
  accent_hex_2?: string | null;
  strength?: number | null;
  tag?: string | null;
  visual_motif?: string | null;
  featured_xl?: boolean;
};

export type StoreMenu = {
  brand: {
    slug: string;
    name: string;
    commerce_mode: string;
    age_gate_enabled: boolean;
    min_age?: number | null;
    capabilities?: Capabilities;
    web: Record<string, unknown>;
    legal: { legal_name?: string | null; dbd_number?: string | null };
  };
  store: StoreSummary & { web?: Record<string, unknown> };
  categories: {
    slug: string;
    name: string;
    sort_order?: number;
    image_url?: string | null;
    items: CatalogItem[];
  }[];
};

async function getJson<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      headers: { Accept: "application/json" },
    });
    if (res.status === 404) return null;
    if (!res.ok) throw new Error(`API ${res.status}`);
    return (await res.json()) as T;
  } catch (e) {
    console.error("catalog fetch failed", path, e);
    return null;
  }
}

export function getApiBase() {
  return API_BASE;
}

export async function fetchBrand(slug: string, channel: string = CLIENT_CHANNEL) {
  const q = channel && channel !== "web" ? `?channel=${encodeURIComponent(channel)}` : "?channel=web";
  return getJson<BrandPublic>(`/api/public/brands/${encodeURIComponent(slug)}${q}`);
}

export async function fetchStoreMenu(brand: string, store: string) {
  return getJson<StoreMenu>(
    `/api/public/brands/${encodeURIComponent(brand)}/stores/${encodeURIComponent(store)}`,
  );
}

export async function fetchItem(brand: string, store: string, item: string) {
  return getJson<CatalogItem & { brand_slug?: string; store_slug?: string }>(
    `/api/public/brands/${encodeURIComponent(brand)}/stores/${encodeURIComponent(store)}/items/${encodeURIComponent(item)}`,
  );
}

export async function fetchBrands() {
  const data = await getJson<{ brands: { slug: string; name: string; description?: string }[] }>(
    `/api/public/brands`,
  );
  return data?.brands ?? [];
}

/** CTA labels — prefer brand.web.cta when passed; keep neutral defaults. */
export function ctaLabel(cta: string, labels?: { inquire?: string; order?: string; contact?: string }): string {
  switch (cta) {
    case "order":
      return labels?.order || "Order";
    case "inquire":
      return labels?.inquire || "Inquire";
    default:
      return labels?.contact || "Contact";
  }
}

export function cap(caps: Capabilities | undefined | null, key: string, fallback = true): boolean {
  if (!caps || !(key in caps)) return fallback;
  return Boolean(caps[key]);
}
