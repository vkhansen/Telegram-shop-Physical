# Card 39: Web OAuth Login & Ticket Portal

## Implementation Status

> **~50% Complete** | `██████████░░░░░░░░░` | Auth + tickets + brand_id; storefront login/tickets; Google path; leads/bookings related (CARD-36).

**Priority:** **P1** — required for authenticated ticket access on white-label sites  
**Depends on:** CARD-38 storefront ✅ · existing SupportTicket  
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
- [ ] Production Google OAuth end-to-end (code path ready; needs live credentials)

### Phase 2

- [ ] Google OAuth production config + redirect hardening  
- [ ] Optional email-link to existing Telegram user  
- [ ] `brand_id` on tickets for multi-tenant queues  

---

## Exit criteria (Phase 1)

- [x] Documented flow + matching rules  
- [x] Logged-in user accesses only own tickets via API  
- [x] UI pages on multi-tenant Astro storefront  
- [ ] E2E with real Google client id in deploy env  

---

## Related

- [WHITE-LABEL-OAUTH-TICKETS.md](../Specifications/WHITE-LABEL-OAUTH-TICKETS.md)  
- [CARD-30](CARD-30-user-identities.md)  
- [CARD-38](CARD-38-white-label-brand-branch-sites.md)  
