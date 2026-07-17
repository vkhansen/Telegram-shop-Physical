# A-01…A-12: Admin / ops inventory (Telegram only)

> Spec status: `accepted` (inventory + core anchors) · Platforms: **telegram only**

| ID | Flow | Primary code | Notes |
|----|------|--------------|-------|
| A-01 | Admin console entry | `handlers/admin/main.py` | permission gates |
| A-02 | Shop / goods / categories CRUD | `*_management_states.py`, `adding_position_states.py` | FSM heavy |
| A-03 | Stock / sold-out / modifiers admin | goods + modifier admin | |
| A-04 | Order management + status | `order_management.py` | drives kitchen path |
| A-05 | Kitchen group buttons | group handlers / order_management | preparing→ready |
| A-06 | Rider group / photo proof | rider group + delivery | CARD-04 |
| A-07 | Users ban/role/bonus | `user_management_states.py` | |
| A-08 | Broadcast | `broadcast.py`, segmented | |
| A-09 | Coupons / accounting / settings / stores | coupon, accounting, settings, store_management | |
| A-10 | Tickets admin | `ticket_management.py` | |
| A-11 | Admin Grok | `grok_assistant.py` | CARD-17 |
| A-12 | CLI ops | `bot_cli.py` | no chat UX |

**Mask:** Never expose on LINE/IG/web customer. Platform caps: `admin_console`, `kitchen_ops`, `broadcast`.
