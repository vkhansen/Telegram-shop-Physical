/** Auth + tickets client (CARD-39). Uses credentials cookies against PUBLIC_API_BASE. */

const API_BASE = (import.meta.env.PUBLIC_API_BASE || "http://127.0.0.1:9090").replace(/\/$/, "");

async function api<T>(path: string, init: RequestInit = {}): Promise<{ ok: boolean; status: number; data: T | null }> {
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
    return { ok: res.ok, status: res.status, data: data as T };
  } catch {
    return { ok: false, status: 0, data: null };
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
    providers?: unknown[];
  };
};

export async function fetchMe() {
  return api<MeResponse>("/api/public/auth/me");
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

export async function listTickets() {
  return api<{ tickets: TicketSummary[] }>("/api/public/tickets");
}

export async function createTicket(subject: string, message: string) {
  return api<{ ticket_code: string }>("/api/public/tickets", {
    method: "POST",
    body: JSON.stringify({ subject, message }),
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
