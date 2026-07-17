# CARD-42: Google OAuth Credentials Runbook

## Status: ✅ DONE (docs / ops runbook) — 2026-07-17

## Priority: P1 — Required to finish CARD-39 live login  
## Effort: Operator only (no code after CARD-39 wiring)  
## Phase: Ops / deploy  
## Parent: [CARD-39 Web OAuth + Ticket Portal](../later/CARD-39-web-oauth-ticket-portal.md)

---

## Why

Storefront login and web cart/checkout use a **session cookie** (`wl_session`) created after OAuth (or dev login).  
**Google Client ID + Client Secret are not in the repo** — they come from Google Cloud Console and go into deploy `.env` only.

This card is the **single place** that answers: *where do I get the Google secrets, and how do I plug them in?*

---

## What you get from Google

| Google Console name | Env var in this project |
|---------------------|-------------------------|
| **Client ID** | `OAUTH_GOOGLE_CLIENT_ID` |
| **Client secret** | `OAUTH_GOOGLE_CLIENT_SECRET` |

Optional override:

| Env var | When |
|---------|------|
| `OAUTH_GOOGLE_REDIRECT_URI` | Callback is not `PUBLIC_SITE_URL` + `/api/public/auth/google/callback` |

Related (not from Google, but required for prod auth):

| Env var | Purpose |
|---------|---------|
| `PUBLIC_SITE_URL` | Where browser returns after OAuth |
| `WEB_SESSION_SECRET` | Signs session cookies (long random; not the Google secret) |
| `WEB_COOKIE_SECURE` | `true` on HTTPS Funnel |
| `OAUTH_DEV_LOGIN` | Local only — `false` in production |

---

## Where to get the secrets (Google Cloud)

### 1. Console + project

1. Open [Google Cloud Console](https://console.cloud.google.com/).  
2. Create or select a **project**.  

### 2. OAuth consent screen

1. **APIs & Services → OAuth consent screen**  
   · [Direct link](https://console.cloud.google.com/apis/credentials/consent)  
2. User type: **External** (or **Internal** for Google Workspace-only).  
3. App name, support email, developer contact.  
4. Scopes: **openid**, **email**, **profile**.  
5. While status is **Testing**, add your account under **Test users**.  

### 3. Create OAuth client (Web)

1. **APIs & Services → Credentials**  
   · [Direct link](https://console.cloud.google.com/apis/credentials)  
2. **+ Create credentials → OAuth client ID**.  
3. Type: **Web application**.  
4. Name: e.g. `Telegram Shop Storefront`.  

**Authorized JavaScript origins** (no path):

| Env | Value |
|-----|--------|
| Local storefront | `http://127.0.0.1:4321` |
| Funnel / prod | `https://telegram-shop.<tailnet>.ts.net` |

**Authorized redirect URIs** (must match **exactly**):

| Env | Value |
|-----|--------|
| Funnel same-origin (recommended) | `https://telegram-shop.<tailnet>.ts.net/api/public/auth/google/callback` |
| Local API on :9090 | `http://127.0.0.1:9090/api/public/auth/google/callback` |

5. **Create** → copy:

- **Client ID** → `OAUTH_GOOGLE_CLIENT_ID`  
- **Client secret** → `OAUTH_GOOGLE_CLIENT_SECRET`  

If you lose the secret later: Credentials → that client → **Reset secret**.

---

## Plug into this project

### Deploy / Funnel `.env` (bot / API process)

```bash
PUBLIC_SITE_URL=https://telegram-shop.<tailnet>.ts.net
WEB_SESSION_SECRET=   # openssl rand -base64 48
WEB_COOKIE_SECURE=true
OAUTH_DEV_LOGIN=false
OAUTH_GOOGLE_CLIENT_ID=xxxxx.apps.googleusercontent.com
OAUTH_GOOGLE_CLIENT_SECRET=GOCSPX-xxxxx
# Only if callback host differs from PUBLIC_SITE_URL:
# OAUTH_GOOGLE_REDIRECT_URI=https://telegram-shop.<tailnet>.ts.net/api/public/auth/google/callback
```

Also listed in root [`.env.example`](../../.env.example) under **WEB OAUTH + TICKETS (CARD-39)**.

### Storefront

On Funnel, leave `PUBLIC_API_BASE` **empty** (same-origin) so `/api/*` cookies work with the site.  
See [`apps/storefront/.env.example`](../../apps/storefront/.env.example).

### Restart

```bash
docker compose up -d --build bot
# or local: restart scripts/run_public_api.py / bot process
```

### Verify

```bash
curl -sS https://YOUR_HOST/api/public/auth/config
# expect: "google_enabled": true, "dev_login_enabled": false
```

Browser: `https://YOUR_HOST/{brand}/login` → **Continue with Google** → tickets (or `next` path).

Preflight at bot start should log:

- `OAUTH_GOOGLE` pass  
- `WEB_SESSION_SECRET` pass  
- `WEB_COOKIE_SECURE` pass when HTTPS  

---

## Local without Google

```bash
OAUTH_DEV_LOGIN=true
# leave OAUTH_GOOGLE_* empty
python scripts/run_public_api.py
```

Use **Dev sign in** on the storefront login page. Never leave `OAUTH_DEV_LOGIN=true` on a public Funnel.

---

## Code map (already shipped under CARD-39)

| Path | Role |
|------|------|
| `bot/services/web_auth.py` | `google_enabled`, authorize URL, token exchange |
| `bot/web/auth_api.py` | `/api/public/auth/google/start` · `callback` · config |
| `bot/preflight.py` | `_check_web_oauth` |
| `apps/storefront/.../login.astro` | Google button + auth/config discovery |
| `docker-compose.yml` | OAuth env passthrough to bot |

---

## Acceptance (this card)

- [x] Runbook written: where secrets come from, what env vars, Funnel vs local  
- [x] Linked from FEATURE_CARDS + CLEAR-START + CARD-39  
- [x] No secrets committed to git  
- [ ] **Operator residual:** create real Google client for production host and paste into deploy `.env` (cannot be done in-repo)

---

## Related

- [CARD-39](../later/CARD-39-web-oauth-ticket-portal.md) — portal product + full ops checklist  
- [WHITE-LABEL-OAUTH-TICKETS.md](../Specifications/WHITE-LABEL-OAUTH-TICKETS.md) — design  
- [CARD-30](CARD-30-user-identities.md) — identity spine  
- [CARD-38](CARD-38-white-label-brand-branch-sites.md) — storefront  

---

## Log

| Date | Note |
|------|------|
| 2026-07-17 | Card created; documents Google Cloud → Client ID/secret → `.env` path. Code wiring already in CARD-39. |
