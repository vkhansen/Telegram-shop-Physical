# Identity and locale

> Spec status: `accepted` · CARD-34 / CARD-30

## Identity

- Internal key: `users.telegram_id` (synthetic for web/LINE/IG).
- `user_identities` dual-write `(platform, external_id) → user_id`.
- `ensure_line_user` / `ensure_instagram_user` / `resolve_user_id` / `link_identity`.

## Locale priority

explicit param > request contextvar > `BOT_LOCALE` > `DEFAULT_LOCALE` (`th`).

LINE/IG v1 adapters use fixed English strings; full i18n later.
