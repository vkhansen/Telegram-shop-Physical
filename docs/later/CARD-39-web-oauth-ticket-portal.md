# Card 39: Web OAuth Login & Ticket Portal

## Implementation Status

> **~90% Complete** | `██████████████████░░` | Portal polish 2026-07-17: safe OAuth next, auth config, ticket UX, XSS-safe rendering, cap gates. Live Google credentials still env-dependent.

**Priority:** **P1** — required for authenticated ticket access on white-label sites  
**Depends on:** CARD-38 storefront ✅ · existing SupportTicket · CARD-40 tickets service ✅  
**Spec:** [`WHITE-LABEL-OAUTH-TICKETS.md`](../Specifications/WHITE-LABEL-OAUTH-TICKETS.md)

---

## Why

Catalog can be public; **support tickets must be authenticated**. OAuth gives email/profile without forcing Telegram join first, while reusing the same ticket tables the bot uses.

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
- [x] Google OAuth code path (needs live `OAUTH_GOOGLE_*` in deploy)

### Phase 2 / portal polish (2026-07-17)

- [x] OAuth `next` open-redirect harden (`web_auth.safe_next_path`)  
- [x] `GET /api/public/auth/config` — google/dev discovery for login UI  
- [x] OAuth flow cookies honor `WEB_COOKIE_SECURE`  
- [x] Tickets API: brand capability gate + structured errors  
- [x] Storefront UX: loading/empty/error states, status badges, closed-ticket reply lock  
- [x] XSS-safe ticket subject/message rendering  
- [x] Tests: `tests/unit/services/test_auth_portal_card39.py`  
- [ ] Optional email-link to existing Telegram user (nice-to-have)  
- [ ] Staff multi-tenant queue UI (ops — out of customer portal)

---

## Exit criteria (Phase 1 + polish)

- [x] Documented flow + matching rules  
- [x] Logged-in user accesses only own tickets via API  
- [x] UI pages on multi-tenant Astro storefront  
- [x] Safe redirects + auth method discovery  
- [ ] E2E with real Google client id in deploy env (ops checklist)

---

## Related

- [WHITE-LABEL-OAUTH-TICKETS.md](../Specifications/WHITE-LABEL-OAUTH-TICKETS.md)  
- [CARD-30](CARD-30-user-identities.md)  
- [CARD-38](CARD-38-white-label-brand-branch-sites.md)  
