# {ID}: {Name}

> Spec status: `draft` | `reviewed` | `accepted`  
> Mode: `as-built` (default) | `desired` deltas optional below  
> Card: [CARD-34](../later/CARD-34-conversation-workflow-specifications.md)

| Field | Value |
|-------|-------|
| **ID** | e.g. C-14 |
| **Actors** | customer / admin / kitchen / rider / driver |
| **Platforms** | telegram: full · instagram: simplified \| off · line: simplified \| off |
| **Feature flags** | e.g. none / `CRYPTO_PAYMENTS_ENABLED` |
| **Capability keys** | e.g. `checkout`, `payment_promptpay` (see CARD-31) |
| **FSM / states** | e.g. `OrderStates.waiting_location` |
| **Related cards** | e.g. CARD-01, CARD-23 |

---

## Goal

One paragraph: what success looks like for the user and the system.

---

## Preconditions

- Authenticated? Banned blocked?
- Cart / brand / store requirements
- Permissions / role
- External config (PromptPay, groups, etc.)

---

## Entry points

| Kind | Value | Notes |
|------|-------|-------|
| callback | `…` | |
| command | `/…` | |
| message | text / photo / location | |
| push | notify from backend | |

---

## Conversation (Telegram)

| Step | Actor | Message / i18n key | User action | System effects |
|------|-------|--------------------|-------------|----------------|
| 1 | bot | `key` — gloss | — | |
| 2 | user | — | button `callback` / text / photo | |
| 3 | bot | … | … | DB / payment / notify |

### Buttons / keyboards

| Label key | callback_data / url | Visible when |
|-----------|---------------------|--------------|
| | | |

---

## State machine

```text
[state_a] --event--> [state_b]
[state_b] --back--> [state_a]
[state_b] --cancel--> [cleared / main menu]
```

List FSM group names and state attributes stored in context (keys).

---

## Branches / errors

| Condition | User-visible result (i18n) | System result |
|-----------|----------------------------|---------------|
| Empty cart | | |
| Validation fail | | |
| Insufficient stock | | |
| Payment fail | | |
| Unauthorized | | |

---

## Notifications & side effects

| When | Who | Channel | Content key / summary |
|------|-----|---------|------------------------|
| | customer / kitchen / rider / admin | telegram / … | |

---

## Platform masks

| Platform | Support | Script differences |
|----------|---------|-------------------|
| telegram | full | this document |
| instagram | simplified / off | describe quick-reply / text variant or “N/A” |
| line | simplified / off | |
| web | … | |

### Instagram variant (if not off)

| Step | Actor | Content | Action |
|------|-------|---------|--------|
| 1 | | | |

---

## Acceptance criteria

- [ ] …
- [ ] …
- [ ] Error path: …

---

## Code map

| Layer | Path |
|-------|------|
| Handler | `bot/handlers/…` |
| States | `bot/states/…` |
| Keyboards | `bot/keyboards/…` |
| Domain / payments | `bot/…` |
| Service (if any) | `bot/services/…` |

---

## Desired deltas (optional)

Only if as-built should change; otherwise leave empty.

- …
