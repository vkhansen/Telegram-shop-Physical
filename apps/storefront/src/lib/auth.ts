/** Auth + tickets client (CARD-39 portal). Cookie session against PUBLIC_API_BASE. */

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

async function api<T>(
  path: string,
  init: RequestInit = {},
): Promise<{ ok: boolean; status: number; data: T | null; error?: string }> {
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
    const err =
      data && typeof data === "object" && "error" in data
        ? String((data as { error?: string }).error || "")
        : undefined;
    return { ok: res.ok, status: res.status, data: data as T, error: err };
  } catch {
    return { ok: false, status: 0, data: null, error: "network_error" };
  }
}

export type MeResponse = {
  authenticated: boolean;
  session?: { uid: number; email?: string; name?: string; avatar?: string };
  profile?: {
    user_id: number;
    email?: string;
    name?: string;
    username?: string;
    avatar?: string;
    providers?: { provider: string; email?: string; name?: string; avatar?: string }[];
  };
};

export type AuthConfig = {
  google_enabled: boolean;
  dev_login_enabled: boolean;
  session_cookie?: string;
  brand?: string;
  auth_enabled?: boolean;
  tickets_enabled?: boolean;
};

export async function fetchMe() {
  return api<MeResponse>("/api/public/auth/me");
}

export async function fetchAuthConfig(brand?: string) {
  const q = brand ? `?brand=${encodeURIComponent(brand)}` : "";
  return api<AuthConfig>(`/api/public/auth/config${q}`);
}

export async function devLogin(email: string, name: string) {
  return api<{ ok: boolean; user: unknown }>("/api/public/auth/dev-login", {
    method: "POST",
    body: JSON.stringify({ email, name }),
  });
}

export async function logout() {
  return api<{ ok: boolean }>("/api/public/auth/logout", { method: "POST" });
}

export function googleStartUrl(brand: string, next?: string) {
  const q = new URLSearchParams({ brand, next: next || `/${brand}/tickets` });
  return `${API_BASE}/api/public/auth/google/start?${q}`;
}

export async function listTickets(brand?: string) {
  const q = brand ? `?brand=${encodeURIComponent(brand)}` : "";
  return api<{ tickets: TicketSummary[]; count?: number }>(`/api/public/tickets${q}`);
}

export async function createTicket(subject: string, message: string, brand?: string) {
  return api<{ ticket_code: string; subject?: string; status?: string }>("/api/public/tickets", {
    method: "POST",
    body: JSON.stringify({
      subject,
      message,
      brand_slug: brand,
      brand,
    }),
  });
}

export async function getTicket(code: string) {
  return api<TicketDetail>(`/api/public/tickets/${encodeURIComponent(code)}`);
}

export async function replyTicket(code: string, message: string) {
  return api<TicketDetail>(`/api/public/tickets/${encodeURIComponent(code)}/messages`, {
    method: "POST",
    body: JSON.stringify({ message }),
  });
}

export type TicketSummary = {
  ticket_code: string;
  subject: string;
  status: string;
  priority: string;
  created_at?: string;
  updated_at?: string;
};

export type TicketDetail = TicketSummary & {
  messages: { sender_role: string; message_text: string; created_at?: string }[];
};

/** Escape text for safe innerHTML (ticket subjects / messages). */
export function escapeHtml(s: string | null | undefined): string {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

export function statusBadgeClass(status: string): string {
  const s = (status || "").toLowerCase();
  if (s === "open") return "bg-emerald-500/15 text-emerald-300 ring-emerald-500/30";
  if (s === "in_progress") return "bg-sky-500/15 text-sky-300 ring-sky-500/30";
  if (s === "resolved") return "bg-violet-500/15 text-violet-300 ring-violet-500/30";
  if (s === "closed") return "bg-ink-700/80 text-ink-400 ring-ink-600";
  return "bg-ink-800 text-sand-200 ring-ink-600";
}

export function formatWhen(iso?: string | null): string {
  if (!iso) return "";
  try {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    return d.toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export function isTicketClosed(status: string): boolean {
  const s = (status || "").toLowerCase();
  return s === "closed" || s === "resolved";
}

export function loginRedirect(brandSlug: string, nextPath: string): string {
  return `/${brandSlug}/login?next=${encodeURIComponent(nextPath)}`;
}
