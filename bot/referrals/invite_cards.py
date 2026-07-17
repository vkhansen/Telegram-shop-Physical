"""Physical invite cards: numbered tear-off stubs + Telegram QR deep links.

Print flow
----------
1. Generate a batch of cards (unique 8-letter codes, sequential card numbers).
2. Export printable HTML (QR half + name stub with tear line) + CSV.
3. Print, cut, write guest name on stub, tear QR half and hand it out.
4. Guest scans QR → opens ``t.me/<bot>?start=<CODE>`` → bot auto-applies code.

CLI: ``python bot_cli.py invite-cards generate --count 20 --bot-username YourBot``
"""

from __future__ import annotations

import base64
import csv
import html
import io
import os
import re
import secrets
import string
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import qrcode
from qrcode.constants import ERROR_CORRECT_M

from bot.config.timezone import get_localized_time
from bot.database.main import Database
from bot.database.models.main import ReferenceCode
from bot.export.custom_logging import log_reference_code_creation
from bot.referrals.codes import generate_reference_code


@dataclass(frozen=True)
class InviteCard:
    card_number: int
    code: str
    deep_link: str
    batch_id: str
    recipient_name: str | None = None
    given_at: datetime | None = None
    current_uses: int = 0
    max_uses: int | None = 1
    is_active: bool = True


def normalize_bot_username(bot_username: str | None = None) -> str:
    raw = (bot_username or os.getenv("BOT_USERNAME") or "").strip().lstrip("@")
    if not raw:
        raise ValueError(
            "bot_username required — pass --bot-username or set BOT_USERNAME in .env "
            "(e.g. Afghanorder611bot)"
        )
    return raw


def telegram_start_link(code: str, bot_username: str | None = None) -> str:
    """https://t.me/<bot>?start=<CODE> — Telegram start payload (A-Za-z0-9_, max 64)."""
    username = normalize_bot_username(bot_username)
    payload = (code or "").strip().upper()
    if not payload or not all(c.isalnum() or c == "_" for c in payload):
        raise ValueError(f"invalid start payload for Telegram deep link: {code!r}")
    return f"https://t.me/{username}?start={payload}"


def qr_png_bytes(data: str, *, box_size: int = 8, border: int = 2) -> bytes:
    """Render a QR code PNG for a deep link or arbitrary string."""
    qr = qrcode.QRCode(version=None, error_correction=ERROR_CORRECT_M, box_size=box_size, border=border)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _next_card_number(session) -> int:
    current = session.query(ReferenceCode.card_number).filter(ReferenceCode.card_number.isnot(None)).all()
    if not current:
        return 1
    return max(n for (n,) in current if n is not None) + 1


def _new_batch_id() -> str:
    stamp = get_localized_time().strftime("%Y%m%d")
    suffix = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))
    return f"B{stamp}{suffix}"


def create_invite_card_batch(
    *,
    count: int,
    created_by: int,
    created_by_username: str = "admin",
    bot_username: str | None = None,
    max_uses: int = 1,
    expires_in_hours: int | None = None,
    batch_id: str | None = None,
    start_card_number: int | None = None,
    note_prefix: str = "invite card",
    brand_id: int | None = None,
) -> list[InviteCard]:
    """Create numbered invite cards (admin reference codes with card metadata)."""
    if count < 1 or count > 500:
        raise ValueError("count must be between 1 and 500")
    if max_uses is not None and max_uses < 1:
        raise ValueError("max_uses must be >= 1")

    normalize_bot_username(bot_username)  # validate early
    batch = batch_id or _new_batch_id()
    expires_at = None
    if expires_in_hours is not None and expires_in_hours > 0:
        from datetime import timedelta

        expires_at = get_localized_time() + timedelta(hours=expires_in_hours)

    # FK: created_by must exist in users (ensure stub row for CLI/system creators)
    from bot.database.models.main import User

    with Database().session() as session:
        if not session.query(User).filter_by(telegram_id=created_by).first():
            session.add(
                User(
                    telegram_id=created_by,
                    role_id=3,  # OWNER-ish for system creator
                    registration_date=get_localized_time(),
                    referral_id=None,
                )
            )
            session.commit()

    cards: list[InviteCard] = []
    used_codes: set[str] = set()
    with Database().session() as session:
        next_num = start_card_number if start_card_number is not None else _next_card_number(session)
        for i in range(count):
            # Generate unique within this batch + DB (same session sees pending inserts)
            code = None
            for _ in range(100):
                candidate = generate_reference_code()
                if candidate in used_codes:
                    continue
                if session.query(ReferenceCode).filter_by(code=candidate).first():
                    continue
                code = candidate
                used_codes.add(candidate)
                break
            if not code:
                raise RuntimeError("Failed to generate unique reference code for invite card")

            card_number = next_num + i
            note = f"{note_prefix} #{card_number} batch={batch}"
            ref = ReferenceCode(
                code=code,
                created_by=created_by,
                expires_at=expires_at,
                max_uses=max_uses,
                note=note,
                is_admin_code=True,
                card_number=card_number,
                card_batch_id=batch,
                brand_id=brand_id,
            )
            session.add(ref)
            session.flush()  # make code visible to next uniqueness checks
            cards.append(
                InviteCard(
                    card_number=card_number,
                    code=code,
                    deep_link=telegram_start_link(code, bot_username),
                    batch_id=batch,
                    max_uses=max_uses,
                )
            )
            log_reference_code_creation(
                code=code,
                created_by=created_by,
                created_by_username=created_by_username,
                expires_at=expires_at,
                max_uses=max_uses,
                note=note,
                is_admin=True,
            )
        session.commit()
    return cards


def assign_invite_card(
    card_number: int | None = None,
    recipient_name: str = "",
    *,
    code: str | None = None,
) -> InviteCard:
    """Record the name written on the physical stub after distributing a card.

    Lookup by **card index** (``card_number`` / printed #0007) or by **code**.
    Both sides of the card print the same number so the stub maps 1:1 to the DB row.
    """
    name = (recipient_name or "").strip()
    if not name:
        raise ValueError("recipient_name required")
    if len(name) > 200:
        raise ValueError("recipient_name too long (max 200)")
    if card_number is None and not code:
        raise ValueError("card_number or code required")

    with Database().session() as session:
        ref = None
        if card_number is not None:
            ref = session.query(ReferenceCode).filter_by(card_number=int(card_number)).first()
        if ref is None and code:
            ref = session.query(ReferenceCode).filter_by(code=str(code).strip().upper()).first()
        if not ref or ref.card_number is None:
            key = f"#{card_number}" if card_number is not None else f"code {code}"
            raise ValueError(f"no invite card for {key}")
        ref.recipient_name = name
        ref.given_at = get_localized_time()
        session.commit()
        return _to_card(ref)


def clear_invite_card_assignment(card_number: int) -> InviteCard:
    """Remove recipient name (if you mis-wrote a stub)."""
    with Database().session() as session:
        ref = session.query(ReferenceCode).filter_by(card_number=int(card_number)).first()
        if not ref or ref.card_number is None:
            raise ValueError(f"no invite card with number {card_number}")
        ref.recipient_name = None
        ref.given_at = None
        session.commit()
        return _to_card(ref)


def parse_assign_line(line: str) -> tuple[int | None, str | None, str]:
    """Parse ``7 Ali``, ``#7: Ali``, ``7=Ali``, or ``CODE Ali`` (8-letter code).

    Returns (card_number|None, code|None, name).
    """
    raw = (line or "").strip()
    if not raw:
        raise ValueError("empty line")
    # #0007: Name  |  7 Name  |  7=Name  |  7 - Name
    m = re.match(
        r"^#?\s*(\d{1,6})\s*[=:\-–—]?\s+(.+)$",
        raw,
    )
    if m:
        return int(m.group(1)), None, m.group(2).strip()
    m = re.match(r"^([A-Za-z]{8})\s+(.+)$", raw)
    if m:
        return None, m.group(1).upper(), m.group(2).strip()
    raise ValueError(f"could not parse assignment: {raw!r} (use: 7 Ali  or  ABCDEFGH Ali)")


def assign_invite_cards_bulk(lines: list[str] | str) -> list[tuple[bool, str, InviteCard | None]]:
    """Assign many stubs from text lines. Returns list of (ok, message, card|None)."""
    if isinstance(lines, str):
        text_lines = [ln.strip() for ln in lines.splitlines() if ln.strip()]
    else:
        text_lines = [ln.strip() for ln in lines if ln and ln.strip()]
    results: list[tuple[bool, str, InviteCard | None]] = []
    for ln in text_lines:
        try:
            num, code, name = parse_assign_line(ln)
            card = assign_invite_card(num, name, code=code)
            results.append(
                (
                    True,
                    f"#{card.card_number:04d} {card.code} → {card.recipient_name}",
                    card,
                )
            )
        except Exception as e:
            results.append((False, f"{ln!r}: {e}", None))
    return results


def get_invite_card(card_number: int | None = None, code: str | None = None) -> InviteCard | None:
    with Database().session() as session:
        q = session.query(ReferenceCode)
        if card_number is not None:
            ref = q.filter_by(card_number=card_number).first()
        elif code:
            ref = q.filter_by(code=code.strip().upper()).first()
        else:
            return None
        return _to_card(ref) if ref and ref.card_number is not None else None


def list_invite_cards(
    *,
    batch_id: str | None = None,
    brand_id: int | None = None,
    only_unused: bool = False,
    only_unassigned: bool = False,
    only_assigned: bool = False,
    limit: int = 200,
) -> list[InviteCard]:
    with Database().session() as session:
        q = session.query(ReferenceCode).filter(ReferenceCode.card_number.isnot(None))
        if batch_id:
            q = q.filter_by(card_batch_id=batch_id)
        if brand_id is not None:
            q = q.filter_by(brand_id=brand_id)
        if only_unused:
            q = q.filter(ReferenceCode.current_uses == 0, ReferenceCode.is_active.is_(True))
        if only_unassigned:
            q = q.filter(ReferenceCode.recipient_name.is_(None))
        if only_assigned:
            q = q.filter(ReferenceCode.recipient_name.isnot(None))
        rows = q.order_by(ReferenceCode.card_number.asc()).limit(limit).all()
        return [_to_card(r) for r in rows]


def format_invite_card_registry(cards: list[InviteCard], *, title: str = "Invite card registry") -> str:
    """Human-readable # ↔ code ↔ name table for admins."""
    if not cards:
        return f"{title}\n\n(no cards)"
    lines = [
        f"<b>{title}</b>",
        f"<code>{'#':>5}  {'CODE':8}  {'USES':5}  NAME / STATUS</code>",
        "<code>────────────────────────────────</code>",
    ]
    for c in cards:
        uses = f"{c.current_uses}/{c.max_uses if c.max_uses is not None else '∞'}"
        if c.recipient_name:
            status = c.recipient_name
            if c.given_at:
                status += f" · {c.given_at.strftime('%Y-%m-%d')}"
        else:
            status = "— unassigned"
        if c.current_uses and c.current_uses > 0:
            status += " · redeemed"
        lines.append(f"<code>{c.card_number:5d}  {c.code:8}  {uses:5}  </code>{status}")
    lines.append("")
    lines.append("Assign after hand-out: send <code>7 Ali</code> or use Assign name.")
    return "\n".join(lines)


def _to_card(ref: ReferenceCode) -> InviteCard:
    bot = os.getenv("BOT_USERNAME") or ""
    try:
        link = telegram_start_link(ref.code, bot) if bot else f"?start={ref.code}"
    except ValueError:
        link = f"?start={ref.code}"
    return InviteCard(
        card_number=int(ref.card_number),
        code=ref.code,
        deep_link=link,
        batch_id=ref.card_batch_id or "",
        recipient_name=ref.recipient_name,
        given_at=ref.given_at,
        current_uses=int(ref.current_uses or 0),
        max_uses=ref.max_uses,
        is_active=bool(ref.is_active),
    )


def export_invite_cards(
    cards: list[InviteCard],
    output_dir: str | Path,
    *,
    bot_username: str | None = None,
    shop_title: str = "Invite Card",
) -> dict[str, Any]:
    """Write CSV + per-card QR PNGs + printable HTML (tear-off layout)."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    qr_dir = out / "qr"
    qr_dir.mkdir(exist_ok=True)

    # Refresh deep links with explicit username when provided
    enriched: list[InviteCard] = []
    for c in cards:
        link = telegram_start_link(c.code, bot_username) if bot_username or os.getenv("BOT_USERNAME") else c.deep_link
        enriched.append(
            InviteCard(
                card_number=c.card_number,
                code=c.code,
                deep_link=link,
                batch_id=c.batch_id,
                recipient_name=c.recipient_name,
                given_at=c.given_at,
                current_uses=c.current_uses,
                max_uses=c.max_uses,
                is_active=c.is_active,
            )
        )

    csv_path = out / "invite_cards.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "card_number",
                "code",
                "deep_link",
                "batch_id",
                "recipient_name",
                "given_at",
                "current_uses",
                "max_uses",
                "is_active",
            ]
        )
        for c in enriched:
            w.writerow(
                [
                    c.card_number,
                    c.code,
                    c.deep_link,
                    c.batch_id,
                    c.recipient_name or "",
                    c.given_at.isoformat() if c.given_at else "",
                    c.current_uses,
                    c.max_uses if c.max_uses is not None else "",
                    c.is_active,
                ]
            )

    # Individual QR PNGs
    for c in enriched:
        png = qr_png_bytes(c.deep_link)
        (qr_dir / f"card_{c.card_number:04d}_{c.code}.png").write_bytes(png)

    html_path = out / "print_cards.html"
    html_path.write_text(_print_html(enriched, shop_title=shop_title), encoding="utf-8")

    return {
        "output_dir": str(out.resolve()),
        "csv": str(csv_path.resolve()),
        "html": str(html_path.resolve()),
        "qr_dir": str(qr_dir.resolve()),
        "count": len(enriched),
    }


def _print_html(cards: list[InviteCard], *, shop_title: str) -> str:
    """Printable double half: left = QR (give away), right = stub (keep / name)."""
    parts = [
        "<!DOCTYPE html><html><head><meta charset='utf-8'/>",
        f"<title>{html.escape(shop_title)} — Invite Cards</title>",
        "<style>",
        "@page { size: A4; margin: 10mm; }",
        "body { font-family: system-ui, sans-serif; color: #111; }",
        "h1 { font-size: 16px; margin: 0 0 12px; }",
        ".hint { font-size: 12px; color: #444; margin-bottom: 16px; }",
        ".sheet { display: grid; grid-template-columns: 1fr; gap: 10mm; }",
        ".card { display: grid; grid-template-columns: 1fr 1fr; border: 1.5px dashed #333;",
        "  border-radius: 6px; overflow: hidden; page-break-inside: avoid; min-height: 48mm; }",
        ".half { padding: 8mm 6mm; }",
        ".qr-half { border-right: 2px dashed #999; text-align: center; }",
        ".stub-half { background: #fafafa; }",
        ".num { font-size: 18px; font-weight: 700; letter-spacing: 0.04em; }",
        ".label { font-size: 11px; text-transform: uppercase; color: #666; margin-top: 4px; }",
        ".code { font-family: ui-monospace, monospace; font-size: 13px; margin: 6px 0; }",
        "img.qr { width: 32mm; height: 32mm; image-rendering: pixelated; margin: 4px auto; display: block; }",
        ".name-line { margin-top: 14px; border-bottom: 1px solid #333; min-height: 22px; font-size: 14px; }",
        ".tear { font-size: 10px; color: #888; margin-top: 10px; }",
        "@media print { .hint { display: none; } body { margin: 0; } }",
        "</style></head><body>",
        f"<h1>{html.escape(shop_title)} — physical invite cards</h1>",
        "<p class='hint'>Print → cut on outer edge → write name on stub → tear along dashed line → "
        "give <b>QR half</b> to guest. Guest scans → Telegram opens bot with unique code.</p>",
        "<div class='sheet'>",
    ]
    for c in cards:
        b64 = base64.b64encode(qr_png_bytes(c.deep_link)).decode("ascii")
        name_display = html.escape(c.recipient_name) if c.recipient_name else ""
        parts.append(
            f"""
<div class="card">
  <div class="half qr-half">
    <div class="num">#{c.card_number:04d}</div>
    <div class="label">Scan to open shop</div>
    <img class="qr" alt="QR {c.code}" src="data:image/png;base64,{b64}"/>
    <div class="code">{html.escape(c.code)}</div>
    <div class="tear">GIVE THIS HALF →</div>
  </div>
  <div class="half stub-half">
    <div class="num">#{c.card_number:04d}</div>
    <div class="label">Your stub — write name</div>
    <div class="name-line">{name_display}</div>
    <div class="code">code: {html.escape(c.code)}</div>
    <div class="tear">← keep this half</div>
  </div>
</div>
"""
        )
    parts.append("</div></body></html>")
    return "".join(parts)


def parse_start_payload(text: str | None) -> str:
    """Extract payload from ``/start CODE`` or ``/startCODE``."""
    if not text:
        return ""
    raw = text.strip()
    if not raw.startswith("/start"):
        return raw.strip().upper()
    rest = raw[len("/start") :].strip()
    # deep-link args may be space-separated; only first token is the payload
    if rest:
        rest = rest.split()[0]
    return rest.strip().upper()
