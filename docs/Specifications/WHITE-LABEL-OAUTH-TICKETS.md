# White-Label Site: OAuth Login & Ticket Portal

> **Status:** design + Phase 1 foundation  
> **Card:** [CARD-39](../later/CARD-39-web-oauth-ticket-portal.md)  
> **Depends on:** CARD-38 storefront shell ✅ · CARD-30 identity pattern · existing `SupportTicket` / `TicketMessage`  
> **Related:** [CLEAR-START.md](../CLEAR-START.md)

---

## 1. Requirement

The white-label website **must**:

1. Allow customers to **log in with OAuth** (e.g. Google; extensible to others).  
2. Capture and match **profile fields**: provider subject id, email, display name, avatar URL, optional username.  
3. Link that identity to the platform **user** record (same spine as Telegram tickets).  
4. After login, grant access to the **support ticket system**: list tickets, open ticket, view thread, reply — scoped to that user.

Public catalog remains browsable without login. Tickets (and later order history) require auth.

---

## 2. Why this is not “just a form”

Telegram tickets use `SupportTicket.user_id → users.telegram_id`. Web users may never have opened Telegram. Strategy:

| Concern | Approach |
|---------|----------|
| Keep existing FKs | Do **not** change `users.telegram_id` PK |
| Web-only accounts | Create `User` with **synthetic** `telegram_id` in reserved high range |
| Link OAuth | `user_identities` + `oauth_profiles` tables |
| Match Telegram later | Optional: link code / same email when TG user appears (future) |

---

## 3. Data model

### 3.1 `user_identities` (CARD-30 shape)

```text
id, user_id (FK users.telegram_id), platform, external_id, created_at
UNIQUE (platform, external_id)
```

Platforms: `telegram` | `google` | `web` | …

### 3.2 `oauth_profiles`

```text
id
user_id              FK users
provider            e.g. google
provider_subject    OIDC `sub`
email               nullable
email_verified      bool
display_name        nullable
username            nullable (if provider gives)
avatar_url          nullable
raw_claims          JSON optional
updated_at
UNIQUE (provider, provider_subject)
```

### 3.3 Synthetic user ids

```text
synthetic_id = 1_000_000_000_000_000 + (sha256(provider:sub) % 8_000_000_000_000_000)
```

Collision check on insert; bump hash if needed. Real Telegram IDs stay well below this range in practice.

### 3.4 Tickets (existing)

| Table | Web use |
|-------|---------|
| `support_tickets` | List/create where `user_id` = session user |
| `ticket_messages` | Thread; `sender_role` user/admin |

**Optional later:** `brand_id` on tickets for multi-tenant isolation of support queues. v1: user-scoped as Telegram.

---

## 4. Auth flow

```text
Browser                  Storefront                 API (bot monitoring / auth)
   |                         |                              |
   |  GET /{brand}/login     |                              |
   |  Click "Google"         |                              |
   |------------------------>|  redirect OAuth authorize    |
   |                         |----------------------------->|
   |                         |     callback ?code=          |
   |                         |<-----------------------------|
   |                         |  exchange code, get profile  |
   |                         |  upsert User + identity       |
   |                         |  set session cookie          |
   |  redirect /{brand}/tickets                             |
   |<------------------------|                              |
```

**Session:** signed HTTP-only cookie `wl_session` (JWT or iron-session style) containing `user_id`, `email`, `exp`.  
**CSRF:** state param on OAuth; SameSite=Lax cookies.

**Providers (config):**

| Env | Purpose |
|-----|---------|
| `OAUTH_GOOGLE_CLIENT_ID` | Google OAuth |
| `OAUTH_GOOGLE_CLIENT_SECRET` | |
| `OAUTH_GOOGLE_REDIRECT_URI` | e.g. `https://shop.example.com/api/auth/google/callback` |
| `WEB_SESSION_SECRET` | Sign sessions |
| `OAUTH_DEV_LOGIN` | `true` enables email-only dev login (non-prod) |

---

## 5. Ticket portal (post-login)

| Route | Access | Behavior |
|-------|--------|----------|
| `/{brand}/login` | public | OAuth buttons + optional dev login |
| `/{brand}/logout` | auth | Clear session |
| `/{brand}/account` | auth | Profile: name, email, avatar, linked providers |
| `/{brand}/tickets` | auth | List my tickets |
| `/{brand}/tickets/new` | auth | Create ticket (subject + body) |
| `/{brand}/tickets/{code}` | auth | Thread + reply (must own ticket) |

**API (authenticated):**

```text
GET  /api/public/auth/me
POST /api/public/auth/logout
GET  /api/public/tickets
POST /api/public/tickets
GET  /api/public/tickets/{code}
POST /api/public/tickets/{code}/messages
```

Session cookie or `Authorization: Bearer` for API.

Staff replies remain via Telegram admin (`ticket_management`); messages appear in web thread when `sender_role=admin`.

---

## 6. Matching rules

On OAuth success:

1. Find `oauth_profiles` by `(provider, sub)` → load user.  
2. Else find `user_identities` by `(platform=provider, external_id=sub)`.  
3. Else if email matches an existing `oauth_profiles.email` (verified) → **link** new provider to that user (optional flag `OAUTH_LINK_BY_EMAIL`).  
4. Else create synthetic `User` + identity + oauth_profile.  
5. Update profile fields (name, avatar, email) on each login.

**Username:** store provider `preferred_username` or email local-part in `oauth_profiles.username`; show on account page.

---

## 7. Security

- Never trust client-supplied user_id for tickets — always from session.  
- Rate-limit auth and ticket create.  
- No session for ticket list if cookie invalid.  
- OAuth secrets only server-side.  
- Dev login disabled unless `OAUTH_DEV_LOGIN=true` and not production.

---

## 8. UX (desktop + mobile)

- Login page: primary “Continue with Google”, profile chip in header when authed.  
- Tickets: list cards → detail thread (chat-like, mobile-friendly).  
- Logged-out visit to `/tickets` → redirect to login with `?next=`.  

---

## 9. Phased delivery

| Phase | Scope |
|-------|--------|
| **1 — Foundation** | Tables, session helpers, ticket read/write API, storefront pages, **dev login** |
| **2 — Google OAuth** | Real Google authorize + callback when env set |
| **3 — Polish** | brand_id on tickets, link TG user, attachments, email notify |

---

## 10. Acceptance criteria

- [ ] User can authenticate (dev or Google) and see email/name on account  
- [ ] Session required for ticket routes  
- [ ] User lists only own tickets; create + reply works against `support_tickets` / `ticket_messages`  
- [ ] Same user row powers web tickets; Telegram tickets for TG-native users unchanged  
- [ ] Desktop + mobile usable ticket UI  
