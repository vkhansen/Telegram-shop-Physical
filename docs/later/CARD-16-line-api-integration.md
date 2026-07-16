# Card 16: LINE Messaging API Integration (Tier 3)

## Implementation Status

> **0% Complete** | `░░░░░░░░░░░░░░░░░░░` | Re-scoped 2026-07-16 — blocked on multi-channel foundation + Instagram Phase 2.

**Tier:** T3 — Additional channels (after Instagram)  
**Phase:** M3 — Multi-Platform Growth  
**Priority:** Medium (deferred)  
**Effort:** High (5–8 days) after foundation  
**Dependencies:**  
- [CARD-34](CARD-34-conversation-workflow-specifications.md) LINE mask rows in platform-masks + flow docs  
- [CARD-29](CARD-29-messenger-port.md) Messenger port  
- [CARD-30](CARD-30-user-identities.md) User identities  
- [CARD-31](CARD-31-platform-capabilities.md) Capabilities  
- [CARD-32](CARD-32-customer-application-services.md) Customer services  
- Prefer [CARD-33](CARD-33-instagram-messaging-channel.md) completed first (proves channel pattern)  
- Multi-brand context ([CARD-19](../done/CARD-19-multi-brand-bot-coordination.md))

**Plan:** [`MULTI-CHANNEL-TIERED-PLAN.md`](MULTI-CHANNEL-TIERED-PLAN.md)

---

## Sequencing change (2026-07-16)

| Previous plan | Current plan |
|---------------|--------------|
| LINE as first/only multi-platform card | LINE is **Tier 3** |
| Full handler PlatformContext rewrite | **Telegram-first ports + services** (no full handler rewrite) |
| Phase 2 channel | **Instagram** is Phase 2 ([CARD-33](CARD-33-instagram-messaging-channel.md)) |

LINE remains strategically important for Thailand (~53M users) but lands **after** the abstraction foundation and Instagram adapter prove the pattern.

---

## Why

LINE is the dominant messaging platform in Thailand. After Telegram (primary) and Instagram (Phase 2 masked commerce), LINE reuses the same:

- `Messenger` port  
- `user_identities`  
- `features_for("line", "customer")`  
- `bot/services/*` checkout/cart/orders  

Admin, kitchen, riders, and drivers stay on **Telegram**.

---

## Scope (re-scoped)

### In

- LINE Messaging API webhook (HTTPS)  
- `LineMessenger` implementing `Messenger`  
- Adapter: events → services → Flex/QuickReply render  
- Masked **customer** subset (see CARD-31 `line` caps)  
- Live location: **off** (or later LIFF — separate card)  
- Flag: `LINE_CHANNEL_ENABLED` default false  

### Out

- Rewriting all Telegram handlers to PlatformContext  
- Changing `telegram_id` PK type (identities table only)  
- Admin/kitchen/driver on LINE  
- Full live-location parity (LIFF) in v1  

---

## Historical audit notes

The original 2026 audit correctly identified Telegram coupling in handlers, keyboards, FSM, and `telegram_id`. That analysis still holds. The **implementation approach** changed:

1. Do **not** force every handler through a neutral context first.  
2. Extract **outbound** + **customer services** + **identity**.  
3. Attach LINE as another channel adapter (same as Instagram).  

For platform differences (FlexMessage vs inline keyboards, webhook-only, no live location), see the original comparison tables retained below for engineering reference.

### Telegram vs LINE (reference)

| Feature | Telegram | LINE |
|---------|----------|------|
| Transport | Polling/webhook + aiogram | Webhook + line-bot-sdk |
| User id | Numeric int | String `userId` |
| Rich UI | Inline keyboards | Flex / QuickReply / Rich Menu |
| Live location | Native | Not native (LIFF later) |
| Groups (kitchen/rider) | Native | Possible but **not used** — ops stay Telegram |

---

## Exit criteria

- [ ] Foundation cards 29–32 done  
- [ ] Instagram pattern (CARD-33) stable or consciously parallelized only if staffed  
- [ ] Flag-off: no Telegram impact  
- [ ] Flag-on: LINE customer can complete masked order on shared backend  
- [ ] Suite green  

---

## Effort

**5–8 days** after T0–T1 (and preferably T2). Not 5–8 days from a greenfield full-stack rewrite.

---

## Related

- Tier plan: [MULTI-CHANNEL-TIERED-PLAN.md](MULTI-CHANNEL-TIERED-PLAN.md)  
- Phase 2: [CARD-33](CARD-33-instagram-messaging-channel.md)  
