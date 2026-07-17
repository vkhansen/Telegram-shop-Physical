# Order status machine

> Spec status: `accepted` · Mode: `as-built` · CARD-34
> Code: `bot/utils/order_status.py`

## Graph

```text
pending → reserved → confirmed → preparing → ready → out_for_delivery → delivered
                 ↘ cancelled
                 ↘ expired   (from reserved only, auto cleaner)
```

| Status | Meaning | Typical actor |
|--------|---------|---------------|
| pending | Just created | system / checkout |
| reserved | Inventory held, awaiting payment confirm | system |
| confirmed | Payment accepted | admin / auto slip |
| preparing | Kitchen cooking | kitchen / admin |
| ready | Ready for pickup/rider | kitchen |
| out_for_delivery | Rider en route | rider / dispatch |
| delivered | Complete | rider |
| cancelled | Aborted; inventory release + refund path | admin / system |
| expired | Unpaid timeout | reservation cleaner |

## Transitions

Only transitions in `VALID_TRANSITIONS` are allowed (`is_valid_transition`).

## Notifications (summary)

| Transition | Customer | Kitchen | Rider |
|------------|----------|---------|-------|
| → confirmed | yes | often | — |
| → preparing | optional | yes | — |
| → ready | yes | — | yes |
| → out_for_delivery | yes (+ TG tracking) | — | — |
| → delivered | yes | — | — |
| → cancelled / expired | yes | ops | — |

Ops always Telegram. Customer may be LINE/IG via `messenger_router`.

## Platform mask

| Platform | Status visibility | Who transitions |
|----------|-------------------|-----------------|
| telegram | full + live tracking | ops transition |
| line / instagram | list/detail text | no ops |
| web | commerce orders API | no kitchen |
