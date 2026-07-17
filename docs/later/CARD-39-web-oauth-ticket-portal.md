# Card 39: Web OAuth Login & Ticket Portal

## Implementation Status

> **~95% Complete** | `███████████████████░` | Code + preflight + env docs ready. **Live Google credentials** still operator-owned (ops checklist below).

**Priority:** **P1** — required for authenticated ticket access on white-label sites  
**Depends on:** CARD-38 storefront ✅ · existing SupportTicket · CARD-40 tickets service ✅  
**Spec:** [`WHITE-LABEL-OAUTH-TICKETS.md`](../Specifications/WHITE-LABEL-OAUTH-TICKETS.md)

---

## Why

Catalog can be public; **support tickets must be authenticated**. OAuth gives email/profile without forcing Telegram join first, while reusing the same ticket tables the bot uses. Same session also unlocks **web cart/checkout** (CARD-40 commerce).

---

## Scope

### Phase 1 (this delivery)

- [x] Spec  
- [x] `user_identities` + `oauth_profiles` models + migration  
- [x] Synthetic user id for web-only accounts  
- [x] Session cookie helpers  
- [x] Ticket list/create/reply API (session-scoped)  
- [x] Storefront: login, account, tickets list/new/detail  
- [x] Dev login when `OAUTH_DEV_LOGIN=true`  
- [x] Google OAuth code path (`google/start` + `callback`)  

### Phase 2 / portal polish (2026-07-17)

- [x] OAuth `next` open-redirect harden (`web_auth.safe_next_path`)  
- [x] `GET /api/public/auth/config` — google/dev discovery for login UI  
- [x] OAuth flow cookies honor `WEB_COOKIE_SECURE`  
- [x] Tickets API: brand capability gate + structured errors  
- [x] Storefront UX: loading/empty/error states, status badges, closed-ticket reply lock  
- [x] XSS-safe ticket subject/message rendering  
- [x] Tests: `tests/unit/services/test_auth_portal_card39.py`  

### Phase 3 / go-live ops (2026-07-17)

- [x] `.env.example` OAuth block + storefront notes  
- [x] `docker-compose.yml` explicit OAuth env passthrough  
- [x] Preflight: `OAUTH_GOOGLE`, `WEB_SESSION_SECRET`, `PUBLIC_SITE_URL`, `WEB_COOKIE_SECURE`  
- [x] Browser OAuth errors redirect to `/{brand}/login?error=…` (not raw JSON)  
- [x] Canonical redirect URI prefers `PUBLIC_SITE_URL` same-origin `/api/public/auth/google/callback`  
- [ ] **Operator:** create Google OAuth client + paste secrets into deploy `.env`  
- [ ] **Operator:** disable `OAUTH_DEV_LOGIN` on public Funnel  
- [ ] Optional email-link to existing Telegram user (nice-to-have)  
- [ ] Staff multi-tenant queue UI (ops — out of customer portal)

---

## Exit criteria

- [x] Documented flow + matching rules  
- [x] Logged-in user accesses only own tickets via API  
- [x] UI pages on multi-tenant Astro storefront  
- [x] Safe redirects + auth method discovery  
- [x] Preflight warns when Google/session secrets missing or weak  
- [ ] E2E with real Google client id in **your** deploy env (ops — cannot commit secrets)

---

## Ops checklist — live Google OAuth

Do this once per production / Funnel hostname.

### 1. Google Cloud Console

1. Create (or select) a project → **APIs & Services → Credentials**.  
2. **OAuth consent screen**: External (or Internal for Workspace), app name, support email, scopes `openid email profile`.  
3. **Create credentials → OAuth client ID → Web application**.  
4. **Authorized JavaScript origins** (examples):  
   - `https://telegram-shop.<tailnet>.ts.net`  
   - local: `http://127.0.0.1:4321` (dev only)  
5. **Authorized redirect URIs** — must match **exactly**:  
   - Funnel same-origin (recommended):  
     `https://telegram-shop.<tailnet>.ts.net/api/public/auth/google/callback`  
   - Or set `OAUTH_GOOGLE_REDIRECT_URI` to the same URL and register that.  

### 2. Deploy `.env` (bot / API process)

```bash
PUBLIC_SITE_URL=https://telegram-shop.<tailnet>.ts.net
WEB_SESSION_SECRET=<openssl rand -base64 48>
WEB_COOKIE_SECURE=true
OAUTH_DEV_LOGIN=false
OAUTH_GOOGLE_CLIENT_ID=....apps.googleusercontent.com
OAUTH_GOOGLE_CLIENT_SECRET=GOCSPX-...
# Optional if not using PUBLIC_SITE_URL-derived callback:
# OAUTH_GOOGLE_REDIRECT_URI=https://telegram-shop.<tailnet>.ts.net/api/public/auth/google/callback
```

Storefront on Funnel: leave `PUBLIC_API_BASE` **empty** (same-origin) so session cookies on `/api` work with the site origin.

### 3. Verify

```bash
# After bot restart
curl -sS https://YOUR_HOST/api/public/auth/config | jq .
# expect: "google_enabled": true, "dev_login_enabled": false

# Preflight logs should show:
#   ✅ OAUTH_GOOGLE: Google OAuth client configured
#   ✅ WEB_SESSION_SECRET: Set
#   ✅ WEB_COOKIE_SECURE: Session cookies marked Secure
```

Browser: open `https://YOUR_HOST/{brand}/login` → **Continue with Google** → land on tickets (or `next`).

### 4. Local without Google

```bash
OAUTH_DEV_LOGIN=true
# leave OAUTH_GOOGLE_* empty
python scripts/run_public_api.py
# storefront login → Dev sign in
```

---

## Related

- [WHITE-LABEL-OAUTH-TICKETS.md](../Specifications/WHITE-LABEL-OAUTH-TICKETS.md)  
- [CARD-30](../done/CARD-30-user-identities.md)  
- [CARD-38](../done/CARD-38-white-label-brand-branch-sites.md)  
- Storefront commerce session: cart/checkout also use `wl_session` cookie  
