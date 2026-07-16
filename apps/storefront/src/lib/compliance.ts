/**
 * White-label compliance — all prose from brand.web.compliance (DB web_profile).
 * Template has no product-vertical defaults beyond neutral age-gate fallbacks.
 */

import { asRecord, asString, asStringList } from "./util";

export type AgeGateConfig = {
  title: string;
  body: string;
  confirmLabel: string;
  denyLabel: string;
  footerNote: string;
  denyRedirectUrl: string;
  disclaimerLines: string[];
};

export type DisclaimerBlock = {
  id?: string;
  title?: string;
  body: string;
  placement?: "footer" | "gate" | "page" | "inline";
};

export type ComplianceView = {
  ageGate: AgeGateConfig;
  footerWarnings: string[];
  disclaimerBlocks: DisclaimerBlock[];
  productDisclaimer: string | null;
  legalNote: string;
  showDbd: boolean;
  ticker: string | null;
};

const DEFAULT_LEGAL_NOTE =
  "Content and offers are provided by the brand operator. Availability, pricing, and legality vary by location. Operators are responsible for their own compliance.";

function parseDisclaimerBlocks(compliance: Record<string, unknown>): DisclaimerBlock[] {
  const raw = compliance.disclaimers;
  if (!Array.isArray(raw)) return [];
  const out: DisclaimerBlock[] = [];
  for (const item of raw) {
    const r = asRecord(item);
    const body = asString(r.body_md) || asString(r.body) || asString(r.text);
    if (!body) continue;
    out.push({
      id: asString(r.id) || undefined,
      title: asString(r.title) || undefined,
      body,
      placement: (asString(r.placement) as DisclaimerBlock["placement"]) || undefined,
    });
  }
  return out;
}

export function parseCompliance(
  web: Record<string, unknown> | null | undefined,
  opts: { minAge?: number | null } = {},
): ComplianceView {
  const w = web || {};
  const compliance = asRecord(w.compliance);
  const ageRaw = asRecord(compliance.age_gate);
  const minAge = opts.minAge ?? null;
  const agePhrase = minAge ? ` (${minAge}+)` : "";

  const footerWarnings = asStringList(compliance.footer_warnings);
  const gateDisclaimers = asStringList(ageRaw.disclaimer_lines);
  const disclaimerLines = gateDisclaimers.length > 0 ? gateDisclaimers : footerWarnings;

  const productDisclaimer =
    asString(compliance.product_disclaimer_md) ||
    asString(compliance.product_disclaimer) ||
    asString(compliance.restricted_categories_note_md);

  const disclaimerBlocks = parseDisclaimerBlocks(compliance);
  if (productDisclaimer && !disclaimerBlocks.some((b) => b.body === productDisclaimer)) {
    disclaimerBlocks.push({
      id: "product",
      title: asString(compliance.product_disclaimer_title) || "Product notice",
      body: productDisclaimer,
      placement: "footer",
    });
  }

  const ticker =
    asString(compliance.ticker) || asString(w.ticker) || asString(asRecord(w.hero).ticker) || null;

  return {
    ageGate: {
      title: asString(ageRaw.title) || "Are you of legal age?",
      body:
        asString(ageRaw.body_md) ||
        asString(ageRaw.body) ||
        `You must be of legal age${agePhrase} in your country to enter this site.`,
      confirmLabel:
        asString(ageRaw.confirm_label) || (minAge ? `I am ${minAge} or older` : "I am of legal age"),
      denyLabel: asString(ageRaw.deny_label) || "I am under age",
      footerNote: asString(ageRaw.footer_note) || "For adults of legal age only",
      denyRedirectUrl: asString(ageRaw.deny_redirect_url) || "https://www.google.com",
      disclaimerLines,
    },
    footerWarnings,
    disclaimerBlocks,
    productDisclaimer,
    legalNote: asString(compliance.legal_note) || DEFAULT_LEGAL_NOTE,
    showDbd: compliance.show_dbd_in_footer === undefined ? true : Boolean(compliance.show_dbd_in_footer),
    ticker,
  };
}
