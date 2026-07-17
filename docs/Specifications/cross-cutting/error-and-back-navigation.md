# Error and back navigation

> Spec status: `accepted` · CARD-34

## Telegram

- FSM Back/Cancel → prior state or main menu.
- Validation re-prompts same state with i18n error.
- Intentional swallow of "message is not modified".

## LINE / Instagram

- Cancel postback → session reset → main menu.
- Unknown text → help + quick replies.
- Cap denied → honest message; suggest Telegram for full UX.
- Ops payloads (ADMIN/KITCHEN/DRIVER) → denied.
