/**
 * Web commerce adapter client — same spine as Telegram cart/order handlers.
 *
 * Flow (CARD-34 C-08 → C-17 · CARD-40 shared caps):
 *   cart.add/list/remove/clear → delivery profile → checkout cash|promptpay → orders
 *
 * All calls go through bot/web/commerce_api → bot/services/{cart,checkout,order_query}.
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
  if (import.meta.env.PUBLIC_API_BASE === "" || import.meta.env.PUBLIC_API_BASE === "same-origin") {
    return "";
  }
  const pub = import.meta.env.PUBLIC_API_BASE;
  if (pub == null || pub === undefined) return "http://127.0.0.1:9090";
  return String(pub).replace(/\/$/, "");
}

const API_BASE = resolveApiBase();

export type CommerceResult<T> = {
  ok: boolean;
  status: number;
  data: T | null;
  error?: string;
  error_key?: string;
  detail?: string;
};

async function api<T>(path: string, init: RequestInit = {}): Promise<CommerceResult<T>> {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      ...init,
      credentials: "include",
      headers: {
        Accept: "application/json",
        ...(init.body ? { "Content-Type": "application/json" } : {}),
        ...(init.headers || {}),
      },
    });
    const data = res.status === 204 ? null : await res.json().catch(() => null);
    const obj = data && typeof data === "object" ? (data as Record<string, unknown>) : null;
    return {
      ok: res.ok,
      status: res.status,
      data: data as T,
      error: obj && "error" in obj ? String(obj.error ?? "") : undefined,
      error_key: obj && "error_key" in obj ? String(obj.error_key ?? "") : undefined,
      detail: obj && "detail" in obj ? String(obj.detail ?? "") : undefined,
    };
  } catch {
    return { ok: false, status: 0, data: null, error: "network_error", error_key: "network_error" };
  }
}

export type CartLine = {
  cart_id: number;
  item_name: string;
  quantity: number;
  price: string;
  total: string;
  selected_modifiers?: Record<string, string> | null;
  brand_id?: number | null;
  store_id?: number | null;
};

export type CartPayload = {
  items: CartLine[];
  item_count: number;
  total: string;
  empty: boolean;
};

export type CheckoutResult = {
  ok: boolean;
  order_id: number;
  order_code: string;
  payment_method: string;
  total_amount: string;
  final_amount: string;
  bonus_applied?: string;
  items_summary?: string[];
  brand_id?: number;
  store_id?: number;
  promptpay?: {
    promptpay_id?: string | null;
    amount?: string;
    order_code?: string;
    has_dynamic_qr?: boolean;
    has_static_qr?: boolean;
    qr_png_base64?: string | null;
  };
};

export type OrderDto = {
  id: number;
  order_code: string;
  order_status: string;
  payment_method: string;
  total_price: string;
  bonus_applied?: string;
  delivery_address?: string;
  phone_number?: string;
  created_at?: string | null;
  brand_id?: number | null;
  store_id?: number | null;
  items: {
    item_name: string;
    quantity: number;
    price: string;
    selected_modifiers?: Record<string, string> | null;
  }[];
};

export function getCommerceApiBase() {
  return API_BASE;
}

/** C-08 — list cart */
export async function getCart() {
  return api<CartPayload>("/api/public/cart");
}

/** C-08 — add item (by slug or name, brand/store context) */
export async function addCartItem(body: {
  brand_slug: string;
  store_slug?: string;
  item_slug?: string;
  item_name?: string;
  quantity?: number;
  selected_modifiers?: Record<string, string>;
}) {
  return api<{ ok: boolean; message?: string; cart?: CartPayload }>("/api/public/cart/items", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

/** C-08 — remove line */
export async function removeCartItem(cartId: number) {
  return api<{ ok: boolean; message?: string }>(`/api/public/cart/items/${cartId}`, {
    method: "DELETE",
  });
}

/** C-08 — clear */
export async function clearCart() {
  return api<{ ok: boolean }>("/api/public/cart/clear", { method: "POST" });
}

/** C-10/C-12 — delivery profile (same CustomerInfo as TG) */
export async function setDeliveryProfile(body: {
  phone?: string;
  phone_number?: string;
  address?: string;
  delivery_address?: string;
  note?: string;
  delivery_note?: string;
  latitude?: number;
  longitude?: number;
}) {
  return api<{ ok: boolean }>("/api/public/customer/delivery", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

/** C-11 + C-13/C-14 — place order */
export async function createCheckout(body: {
  brand_slug: string;
  store_slug?: string;
  payment_method: "cash" | "promptpay" | "cod" | "qr";
  delivery_type?: "door" | "dead_drop" | "pickup";
  phone?: string;
  address?: string;
  note?: string;
  bonus_applied?: number | string;
  latitude?: number;
  longitude?: number;
}) {
  return api<CheckoutResult>("/api/public/checkout", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

/** C-17 — list orders */
export async function listOrders(opts?: { status?: string; limit?: number }) {
  const q = new URLSearchParams();
  if (opts?.status) q.set("status", opts.status);
  if (opts?.limit) q.set("limit", String(opts.limit));
  const qs = q.toString();
  return api<{ orders: OrderDto[]; count: number }>(`/api/public/orders${qs ? `?${qs}` : ""}`);
}

/** C-17 — order detail */
export async function getOrder(orderCode: string) {
  return api<OrderDto>(`/api/public/orders/${encodeURIComponent(orderCode)}`);
}

/** C-14 — re-fetch PromptPay QR */
export async function getPromptpayQr(orderCode: string) {
  return api<{
    order_code: string;
    promptpay_id?: string | null;
    amount?: string;
    has_dynamic_qr?: boolean;
    qr_png_base64?: string | null;
  }>(`/api/public/orders/${encodeURIComponent(orderCode)}/promptpay-qr`);
}

export function humanError(r: CommerceResult<unknown>, fallback = "Something went wrong"): string {
  if (r.error_key === "auth.required" || r.status === 401) return "Please sign in to continue.";
  if (r.error_key === "cart.empty") return "Your cart is empty.";
  if (r.error_key === "cap.checkout_disabled" || r.error_key === "cap.cart_disabled") {
    return "Ordering is not available for this brand.";
  }
  if (r.error_key === "cart.item_not_found") return "Item not found.";
  if (r.error_key === "order.payment.customer_not_found") {
    return "Add a phone and delivery address first.";
  }
  if (r.error_key === "order.bonus.insufficient") return "Not enough bonus balance.";
  if (r.error_key === "order.inventory.unable_to_reserve") return "Not enough stock — try again.";
  if (r.error_key === "network_error") return "Network error — is the API running?";
  return r.detail || r.error || r.error_key || fallback;
}

export function statusLabel(status: string): string {
  const s = (status || "").toLowerCase();
  const map: Record<string, string> = {
    pending: "Pending",
    reserved: "Reserved",
    confirmed: "Confirmed",
    preparing: "Preparing",
    ready: "Ready",
    out_for_delivery: "Out for delivery",
    delivered: "Delivered",
    cancelled: "Cancelled",
    expired: "Expired",
  };
  return map[s] || status || "Unknown";
}

export function paymentLabel(method: string): string {
  const m = (method || "").toLowerCase();
  if (m === "cash" || m === "cod") return "Cash on delivery";
  if (m === "promptpay" || m === "qr") return "PromptPay";
  if (m === "bitcoin") return "Bitcoin";
  return method || "—";
}
