# CARD-41: Physical Invite Cards + Brand A4 PDF Sheets

## Status: ✅ DONE (2026-07-17)

## Priority: P2 — Growth / offline acquisition  
## Effort: Medium (shipped in one pass)  
## Phase: Feature

---

## Why

Reference codes already controlled shop access, but the real-world use case is a **tear-off business card**:

1. Print a numbered sheet of cards (QR half + name stub).  
2. Write the guest’s name on the stub, tear the QR half, hand it out.  
3. Guest scans → Telegram opens the bot with a **unique pre-shared code**.  
4. Later, map the written stub name back into the DB by **card index #**.

Without index tracking + deep-link auto-redeem + printable brand sheets, codes stay “type this 8-letter string” and offline distribution is manual chaos.

---

## Product shape

```
┌────────────────────┬────────────────────┐
│  #0007             │  #0007             │
│  [ QR CODE ]       │  Name: ________    │  ← write on stub
│  Scan → Telegram   │  keep this half    │
│  code: NIIEETWA    │                    │
│  GIVE THIS HALF →  │  ← tear line       │
└────────────────────┴────────────────────┘
```

| Printed | Database column | Role |
|---------|-----------------|------|
| Index `#0007` | `reference_codes.card_number` (unique) | Match stub after hand-out |
| Code `NIIEETWA` | `reference_codes.code` (PK) | QR / `t.me/bot?start=CODE` |
| Batch id | `card_batch_id` | Print run |
| Brand | `brand_id` | Sheet theme + filter |
| Written name | `recipient_name` | Who received the card |
| Given at | `given_at` | When stub was logged |
| Redemptions | `current_uses` + `reference_code_usages` | Scan/join tracking |

---

## Scope (shipped)

### A — Deep-link auto-redeem
- Parse `/start CODE` (invite QR / `https://t.me/<bot>?start=CODE`).
- After language pick, **auto-validate and redeem** the reference code for new users.
- Fall back to typed entry if payload invalid/used.

### B — Invite card batch + registry
- Generate N admin codes with sequential `card_number`, optional `brand_id`, `card_batch_id`.
- CLI + logging for create / list / assign.
- Assign recipient by **index** (`7 Ali`) or **code** (`ABCDEFGH Mai`); bulk multi-line.
- Admin: **Card registry (#↔code)** + **Assign stub name**.

### C — Brand-templated A4 PDF (+ LaTeX)
- Select brand → theme from `Brand` + `web_profile` (name, tagline, primary colour, footer).
- Codes **created in DB first**, then sheet rendered.
- Outputs: `sheet.pdf` (reportlab; pdflatex if present), `sheet.tex` (template), `qr/*.png`.
- Template file: `templates/invite_cards/a4_business_card_sheet.tex`.
- Admin: **Brand PDF sheet (A4)** → pick brand → count 1–40 → PDF document in chat.

### D — Ops / deploy notes (related)
- Tailscale Funnel publishes bot HTTP (`:9090`) at `https://telegram-shop-1.<tailnet>.ts.net` (private mesh + optional public Funnel).
- `BOT_USERNAME` required for deep links.

---

## Files

| Path | Purpose |
|------|---------|
| `bot/database/models/main.py` | `ReferenceCode`: `card_number`, `card_batch_id`, `recipient_name`, `given_at`, `brand_id` |
| `migrations/versions/g7d1c6f9b4e2_invite_cards_reference_codes.py` | invite card columns |
| `migrations/versions/h8e2d7a0c5f3_invite_card_brand_id.py` | `brand_id` FK |
| `bot/referrals/codes.py` | create/validate/use reference codes |
| `bot/referrals/invite_cards.py` | batch, QR, assign, registry, deep-link helpers |
| `bot/referrals/invite_card_sheet.py` | brand theme, LaTeX fill, reportlab PDF |
| `templates/invite_cards/a4_business_card_sheet.tex` | A4 LaTeX template |
| `bot/handlers/user/main.py` | `/start` payload + auto-redeem path |
| `bot/handlers/user/reference_code_handler.py` | shared `try_register_with_reference_code` |
| `bot/handlers/admin/reference_code_management.py` | sheet / registry / assign FSM |
| `bot/keyboards/inline.py` | admin buttons |
| `bot/states/user_state.py` | `waiting_sheet_count`, `waiting_assign_names` |
| `bot_cli.py` | `invite-cards generate\|sheet\|assign\|list\|export` |
| `requirements.txt` | `reportlab` |
| `deploy/tailscale/*` | Funnel serve config (ops; related share path) |

---

## Acceptance criteria

- [x] Generating a batch stores unique `code` + sequential unique `card_number` (+ optional `brand_id` / `batch_id`).
- [x] Printed PDF shows the same index on QR half and name stub.
- [x] Guest QR opens `https://t.me/<bot>?start=<CODE>` and new users redeem without retyping (when code valid).
- [x] Admin/CLI can assign `recipient_name` + `given_at` by **card index** or code after distribution.
- [x] Registry lists `# ↔ code ↔ name ↔ uses/redeemed`.
- [x] Brand sheet uses selected brand name/colours/tagline; PDF is downloadable from admin or CLI.
- [x] LaTeX source is emitted alongside PDF for offline `pdflatex` workflows.
- [x] Codes used for the sheet exist in the database before/at print time (no orphan QR).

---

## CLI cheat sheet

```bash
# Generate N cards + brand PDF
python bot_cli.py invite-cards sheet --brand snus-demo --count 20 --bot-username YourBot

# Registry
python bot_cli.py invite-cards list
python bot_cli.py invite-cards list --unassigned-only

# After hand-out (stub name → DB)
python bot_cli.py invite-cards assign --card 7 --name "Ali"
python bot_cli.py invite-cards assign --file names.txt   # lines: 7 Ali
```

---

## Admin (Telegram)

Reference codes menu:

1. **Brand PDF sheet (A4)** — create codes + send PDF  
2. **Card registry (#↔code)** — inventory  
3. **Assign stub name** — multi-line `7 Ali` after distribution  
4. Help text for physical tear-off workflow  

---

## Test plan (manual / follow-up automation)

| Check | Assert |
|-------|--------|
| Generate sheet for brand | PDF opens; N rows in `reference_codes` with `card_number` + `brand_id` |
| Deep link | `/start CODE` as new user → access without typing code |
| Assign by index | `assign --card N --name X` → `recipient_name` set |
| Registry | list shows #, code, name, redeemed flag |
| Funnel health (ops) | `https://<node>.ts.net/health` → 200 when stack up |

Unit follow-ups (optional): `parse_assign_line`, `parse_start_payload`, theme hex cleaning.

---

## Links

- Builds on existing **reference codes** / referral access control (C-21).  
- Brand theming: [CARD-38](CARD-38-white-label-brand-branch-sites.md) `web_profile`.  
- Deploy share path: `deploy/tailscale/README.md` (Serve + Funnel).  
- Flow sketch: [C-21 Referrals / reference codes](../Specifications/flows/C-21.md).

---

## Completion note (2026-07-17)

Shipped end-to-end: deep-link redeem, numbered invite cards, brand A4 PDF/LaTeX sheet, and post-distribution name assignment by card index. Verified sample batch + assign (`#7` → name) and Funnel `/health` 200 with Docker Compose + Tailscale node `telegram-shop-1`.
