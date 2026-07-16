/// <reference path="../.astro/types.d.ts" />
/// <reference types="astro/client" />

interface ImportMetaEnv {
  readonly PUBLIC_SITE_URL: string;
  readonly PUBLIC_SITE_NAME: string;
  readonly PUBLIC_IG_URL: string;
  readonly PUBLIC_LINE_URL: string;
  readonly PUBLIC_WA_E164: string;
  readonly PUBLIC_FB_URL: string;
  readonly PUBLIC_TELEGRAM_URL: string;
  readonly PUBLIC_PLAUSIBLE_DOMAIN: string;
  readonly RESEND_API_KEY: string;
  readonly RESEND_FROM: string;
  readonly LEAD_NOTIFY_EMAIL: string;
  readonly LEAD_WEBHOOK_URL: string;
  readonly AGE_GATE_ENABLED: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
