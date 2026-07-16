/** Shared small helpers for web_profile / DTO parsing. */

export function asRecord(v: unknown): Record<string, unknown> {
  return v && typeof v === "object" && !Array.isArray(v) ? (v as Record<string, unknown>) : {};
}

export function asString(v: unknown): string | null {
  if (typeof v !== "string") return null;
  const t = v.trim();
  return t || null;
}

export function asStringList(v: unknown): string[] {
  if (!Array.isArray(v)) return [];
  return v.map((x) => (typeof x === "string" ? x.trim() : "")).filter(Boolean);
}

export function asBool(v: unknown, defaultValue = false): boolean {
  if (v === undefined || v === null) return defaultValue;
  return Boolean(v);
}
