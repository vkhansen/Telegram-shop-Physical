"""Brand-templated A4 invite-card sheets (LaTeX + PDF).

Produces a business-card grid on A4 for codes **already in** ``reference_codes``.
Visual theme is driven by the selected ``Brand`` (+ ``web_profile``).

Outputs (per export):
  - ``sheet.pdf``  — print-ready (reportlab; optional pdflatex if installed)
  - ``sheet.tex``  — LaTeX source from ``templates/invite_cards/a4_business_card_sheet.tex``
  - ``qr/*.png``   — per-card QR images used by both backends
"""

from __future__ import annotations

import logging
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from bot.database.main import Database
from bot.database.models.main import Brand, ReferenceCode
from bot.referrals.invite_cards import (
    InviteCard,
    list_invite_cards,
    normalize_bot_username,
    qr_png_bytes,
    telegram_start_link,
)

logger = logging.getLogger(__name__)

# Standard-ish business card on A4: 2 columns × 5 rows = 10 / page
CARDS_PER_PAGE = 10
COLS = 2
# mm
CARD_W_MM = 90.0
CARD_H_MM = 52.0
PAGE_W_MM = 210.0
PAGE_H_MM = 297.0

_TEMPLATE_PATH = Path(__file__).resolve().parents[2] / "templates" / "invite_cards" / "a4_business_card_sheet.tex"


@dataclass(frozen=True)
class BrandSheetTheme:
    brand_id: int
    name: str
    slug: str
    tagline: str
    primary_hex: str  # RRGGBB no #
    footer: str
    support_line: str


def _hex_clean(value: str | None, default: str = "1a1a2e") -> str:
    raw = (value or default).strip().lstrip("#")
    if re.fullmatch(r"[0-9A-Fa-f]{6}", raw):
        return raw.upper()
    if re.fullmatch(r"[0-9A-Fa-f]{3}", raw):
        return "".join(c * 2 for c in raw).upper()
    return default.upper()


def load_brand_theme(brand: Brand | int | str) -> BrandSheetTheme:
    """Resolve brand by id/slug/object and build print theme from columns + web_profile."""
    with Database().session() as session:
        b: Brand | None
        if isinstance(brand, Brand):
            b = session.query(Brand).filter_by(id=brand.id).first()
        elif isinstance(brand, int):
            b = session.query(Brand).filter_by(id=brand).first()
        else:
            slug = str(brand).strip().lower()
            b = session.query(Brand).filter(Brand.slug == slug).first()
            if not b:
                b = session.query(Brand).filter(Brand.name.ilike(str(brand).strip())).first()
        if not b:
            raise ValueError(f"brand not found: {brand!r}")

        web = b.web_profile if isinstance(b.web_profile, dict) else {}
        theme = web.get("theme") if isinstance(web.get("theme"), dict) else {}
        hero = web.get("hero") if isinstance(web.get("hero"), dict) else {}

        primary = (
            theme.get("primary")
            or theme.get("primaryColor")
            or theme.get("accent")
            or web.get("primary_color")
            or "1a1a2e"
        )
        tagline = (
            hero.get("subtitle")
            or hero.get("tagline")
            or web.get("tagline")
            or (b.description or "")[:120]
            or "Scan to open shop"
        )
        footer_parts = [p for p in (b.support_phone, b.support_email, b.legal_name) if p]
        footer = " · ".join(footer_parts) if footer_parts else b.slug
        support = b.support_phone or b.support_email or ""

        return BrandSheetTheme(
            brand_id=int(b.id),
            name=b.name,
            slug=b.slug,
            tagline=str(tagline)[:160],
            primary_hex=_hex_clean(str(primary)),
            footer=str(footer)[:120],
            support_line=str(support)[:80],
        )


def cards_for_sheet(
    *,
    batch_id: str | None = None,
    brand_id: int | None = None,
    only_unused: bool = True,
    limit: int = 100,
    bot_username: str | None = None,
) -> list[InviteCard]:
    """Load invite cards already in DB for the sheet (optional brand/batch filters)."""
    with Database().session() as session:
        q = session.query(ReferenceCode).filter(ReferenceCode.card_number.isnot(None))
        if batch_id:
            q = q.filter_by(card_batch_id=batch_id)
        if brand_id is not None:
            q = q.filter_by(brand_id=brand_id)
        if only_unused:
            q = q.filter(ReferenceCode.current_uses == 0, ReferenceCode.is_active.is_(True))
        rows = q.order_by(ReferenceCode.card_number.asc()).limit(limit).all()

        bot = bot_username or ""
        out: list[InviteCard] = []
        for ref in rows:
            try:
                link = telegram_start_link(ref.code, bot) if bot else telegram_start_link(ref.code)
            except ValueError:
                link = f"https://t.me/?start={ref.code}"
            out.append(
                InviteCard(
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
            )
        return out


def _latex_escape(text: str) -> str:
    repl = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(repl.get(c, c) for c in text)


def _card_latex_cell(card: InviteCard, qr_rel: str, theme: BrandSheetTheme) -> str:
    """One business-card cell (minipage + fbox) for the LaTeX grid."""
    name_line = _latex_escape(card.recipient_name) if card.recipient_name else r"\underline{\hspace{3.2cm}}"
    code = _latex_escape(card.code)
    num = f"{card.card_number:04d}"
    qr = qr_rel.replace("\\", "/")
    # Avoid nested f-string brace hell — plain concatenation
    return (
        r"\begin{minipage}[t]{0.47\textwidth}"
        r"\fbox{\begin{minipage}{0.96\linewidth}\centering "
        + r"\textcolor{brandprimary}{\textbf{\#"
        + num
        + r"}}\\[2pt]"
        + r"\includegraphics[width=2.0cm]{"
        + qr
        + r"}\\[2pt]"
        + r"{\ttfamily\scriptsize "
        + code
        + r"}\\[2pt]"
        + r"{\tiny GIVE QR HALF $\rightarrow$}"
        + r"\end{minipage}\hfill\begin{minipage}{0.96\linewidth}\raggedright "
        + r"\textcolor{brandprimary}{\textbf{\#"
        + num
        + r"}}\\[2pt]"
        + r"{\scriptsize Name}\\"
        + name_line
        + r"\\[4pt]{\ttfamily\tiny "
        + code
        + r"}\\{\tiny keep stub}"
        + r"\end{minipage}}"
        + r"\end{minipage}"
    )


def render_latex_source(
    cards: list[InviteCard],
    theme: BrandSheetTheme,
    *,
    qr_dir_name: str = "qr",
) -> str:
    """Fill the A4 LaTeX template with brand theme + card grid."""
    if not _TEMPLATE_PATH.is_file():
        raise FileNotFoundError(f"LaTeX template missing: {_TEMPLATE_PATH}")

    tpl = _TEMPLATE_PATH.read_text(encoding="utf-8")
    cells: list[str] = []
    for i, card in enumerate(cards):
        qr_rel = f"{qr_dir_name}/card_{card.card_number:04d}_{card.code}.png"
        cell = _card_latex_cell(card, qr_rel, theme)
        if i % COLS == COLS - 1 or i == len(cards) - 1:
            cells.append(cell + r" \\[3mm]" + "\n")
        else:
            cells.append(cell + " &\n")

    batch = cards[0].batch_id if cards else "—"
    filled = (
        tpl.replace("<<BRAND_PRIMARY>>", theme.primary_hex)
        .replace("<<BRAND_NAME>>", _latex_escape(theme.name))
        .replace("<<BRAND_TAGLINE>>", _latex_escape(theme.tagline))
        .replace("<<BATCH_ID>>", _latex_escape(batch))
        .replace("<<CARD_COUNT>>", str(len(cards)))
        .replace("<<BRAND_FOOTER>>", _latex_escape(theme.footer))
        .replace("<<CARD_CELLS>>", "".join(cells))
    )
    return filled


def _try_pdflatex(tex_path: Path, work_dir: Path) -> Path | None:
    engine = shutil.which("pdflatex") or shutil.which("xelatex") or shutil.which("lualatex")
    if not engine:
        return None
    try:
        subprocess.run(
            [engine, "-interaction=nonstopmode", "-halt-on-error", tex_path.name],
            cwd=str(work_dir),
            check=True,
            capture_output=True,
            timeout=120,
        )
        pdf = work_dir / (tex_path.stem + ".pdf")
        return pdf if pdf.is_file() else None
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as e:
        logger.warning("LaTeX compile failed (%s): %s", engine, e)
        return None


def render_pdf_reportlab(
    cards: list[InviteCard],
    theme: BrandSheetTheme,
    output_pdf: Path,
    *,
    qr_files: dict[str, Path] | None = None,
) -> Path:
    """A4 multi-page business-card sheet via reportlab (Docker-friendly)."""
    from reportlab.lib.colors import HexColor, black, white
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas

    output_pdf = Path(output_pdf)
    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    primary = HexColor(f"#{theme.primary_hex}")
    muted = HexColor("#666666")
    light = HexColor("#f7f7f9")

    c = canvas.Canvas(str(output_pdf), pagesize=(PAGE_W_MM * mm, PAGE_H_MM * mm))
    page_w, page_h = PAGE_W_MM * mm, PAGE_H_MM * mm

    margin_x = 12 * mm
    margin_top = 22 * mm
    gap_x = 6 * mm
    gap_y = 5 * mm
    card_w = CARD_W_MM * mm
    card_h = CARD_H_MM * mm

    def draw_header():
        c.setFillColor(primary)
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(page_w / 2, page_h - 12 * mm, theme.name)
        c.setFillColor(muted)
        c.setFont("Helvetica", 9)
        c.drawCentredString(page_w / 2, page_h - 16.5 * mm, theme.tagline)
        batch = cards[0].batch_id if cards else ""
        c.setFont("Helvetica", 8)
        c.drawCentredString(
            page_w / 2,
            page_h - 20 * mm,
            f"Invite cards · batch {batch} · {len(cards)} codes · scan QR → Telegram",
        )

    def draw_card(card: InviteCard, x: float, y: float):
        # outer
        c.setStrokeColor(primary)
        c.setLineWidth(1.1)
        c.setFillColor(white)
        c.roundRect(x, y, card_w, card_h, 3 * mm, stroke=1, fill=1)

        mid_x = x + card_w / 2
        # tear line
        c.setStrokeColor(HexColor("#999999"))
        c.setDash(2, 2)
        c.setLineWidth(0.7)
        c.line(mid_x, y + 2 * mm, mid_x, y + card_h - 2 * mm)
        c.setDash()

        # left QR half
        c.setFillColor(primary)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(x + card_w * 0.25, y + card_h - 7 * mm, f"#{card.card_number:04d}")

        qr_path = None
        if qr_files and card.code in qr_files:
            qr_path = qr_files[card.code]
        if qr_path and Path(qr_path).is_file():
            qr_size = 22 * mm
            c.drawImage(
                str(qr_path),
                x + card_w * 0.25 - qr_size / 2,
                y + 12 * mm,
                qr_size,
                qr_size,
                preserveAspectRatio=True,
                mask="auto",
            )

        c.setFillColor(black)
        c.setFont("Courier-Bold", 8)
        c.drawCentredString(x + card_w * 0.25, y + 8 * mm, card.code)
        c.setFillColor(muted)
        c.setFont("Helvetica", 6)
        c.drawCentredString(x + card_w * 0.25, y + 4 * mm, "GIVE THIS HALF →")

        # right stub
        c.setFillColor(light)
        c.rect(mid_x + 0.3 * mm, y + 0.5 * mm, card_w / 2 - 1 * mm, card_h - 1 * mm, stroke=0, fill=1)
        c.setFillColor(primary)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(mid_x + 3 * mm, y + card_h - 7 * mm, f"#{card.card_number:04d}")
        c.setFillColor(muted)
        c.setFont("Helvetica", 7)
        c.drawString(mid_x + 3 * mm, y + card_h - 12 * mm, "NAME (write here)")
        c.setStrokeColor(black)
        c.setLineWidth(0.6)
        c.line(mid_x + 3 * mm, y + card_h - 18 * mm, x + card_w - 4 * mm, y + card_h - 18 * mm)
        if card.recipient_name:
            c.setFillColor(black)
            c.setFont("Helvetica", 9)
            c.drawString(mid_x + 3 * mm, y + card_h - 17 * mm, card.recipient_name[:28])

        c.setFillColor(black)
        c.setFont("Courier", 7)
        c.drawString(mid_x + 3 * mm, y + 14 * mm, card.code)
        c.setFillColor(muted)
        c.setFont("Helvetica", 6)
        c.drawString(mid_x + 3 * mm, y + 9 * mm, "← keep stub")
        c.setFont("Helvetica-Oblique", 6)
        c.drawString(mid_x + 3 * mm, y + 5 * mm, theme.name[:22])

    # paginate
    for page_start in range(0, len(cards), CARDS_PER_PAGE):
        page_cards = cards[page_start : page_start + CARDS_PER_PAGE]
        draw_header()
        for i, card in enumerate(page_cards):
            col = i % COLS
            row = i // COLS
            x = margin_x + col * (card_w + gap_x)
            y = page_h - margin_top - (row + 1) * card_h - row * gap_y
            draw_card(card, x, y)

        c.setFillColor(muted)
        c.setFont("Helvetica", 7)
        c.drawCentredString(
            page_w / 2,
            8 * mm,
            f"Tear on dashed line · give QR half · keep name stub · {theme.footer}",
        )
        c.showPage()

    c.save()
    return output_pdf


def export_branded_sheet(
    *,
    brand: Brand | int | str,
    cards: list[InviteCard] | None = None,
    batch_id: str | None = None,
    only_unused: bool = True,
    limit: int = 100,
    bot_username: str | None = None,
    output_dir: str | Path | None = None,
    prefer_latex: bool = True,
) -> dict[str, Any]:
    """Build branded A4 PDF (+ .tex) for invite codes already in the database.

    If ``cards`` is omitted, loads from DB via batch_id / brand filter.
    """
    theme = load_brand_theme(brand)
    bot = None
    try:
        bot = normalize_bot_username(bot_username)
    except ValueError:
        bot = bot_username

    if cards is None:
        cards = cards_for_sheet(
            batch_id=batch_id,
            brand_id=theme.brand_id,
            only_unused=only_unused,
            limit=limit,
            bot_username=bot,
        )
        # Fallback: batch without brand_id filter if none tagged yet
        if not cards and batch_id:
            cards = cards_for_sheet(
                batch_id=batch_id,
                brand_id=None,
                only_unused=only_unused,
                limit=limit,
                bot_username=bot,
            )
        if not cards:
            # last resort: any unused invite cards (not yet brand-tagged)
            cards = list_invite_cards(only_unused=only_unused, limit=limit)
            if bot:
                cards = [
                    InviteCard(
                        card_number=c.card_number,
                        code=c.code,
                        deep_link=telegram_start_link(c.code, bot),
                        batch_id=c.batch_id,
                        recipient_name=c.recipient_name,
                        given_at=c.given_at,
                        current_uses=c.current_uses,
                        max_uses=c.max_uses,
                        is_active=c.is_active,
                    )
                    for c in cards
                ]

    if not cards:
        raise ValueError("no invite cards to print — generate a batch first")

    batch = batch_id or cards[0].batch_id or "sheet"
    out = Path(output_dir or f"data/invite_cards/{batch}_{theme.slug}_sheet")
    out.mkdir(parents=True, exist_ok=True)
    qr_dir = out / "qr"
    qr_dir.mkdir(exist_ok=True)

    qr_files: dict[str, Path] = {}
    for card in cards:
        png_path = qr_dir / f"card_{card.card_number:04d}_{card.code}.png"
        png_path.write_bytes(qr_png_bytes(card.deep_link))
        qr_files[card.code] = png_path

    tex_path = out / "sheet.tex"
    tex_source = render_latex_source(cards, theme, qr_dir_name="qr")
    tex_path.write_text(tex_source, encoding="utf-8")

    pdf_path = out / "sheet.pdf"
    latex_pdf: Path | None = None
    if prefer_latex:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            # copy tex + qr into temp for relative includes
            (tmp_path / "qr").mkdir()
            for p in qr_dir.glob("*.png"):
                (tmp_path / "qr" / p.name).write_bytes(p.read_bytes())
            tmp_tex = tmp_path / "sheet.tex"
            tmp_tex.write_text(tex_source, encoding="utf-8")
            latex_pdf = _try_pdflatex(tmp_tex, tmp_path)
            if latex_pdf:
                pdf_path.write_bytes(latex_pdf.read_bytes())

    if not pdf_path.is_file() or pdf_path.stat().st_size == 0:
        render_pdf_reportlab(cards, theme, pdf_path, qr_files=qr_files)
        engine = "reportlab"
    else:
        engine = "pdflatex"

    return {
        "output_dir": str(out.resolve()),
        "pdf": str(pdf_path.resolve()),
        "tex": str(tex_path.resolve()),
        "qr_dir": str(qr_dir.resolve()),
        "count": len(cards),
        "brand": theme.slug,
        "brand_name": theme.name,
        "batch_id": batch,
        "engine": engine,
    }


def list_brands_for_admin(limit: int = 30) -> list[dict[str, Any]]:
    with Database().session() as session:
        rows = (
            session.query(Brand)
            .filter(Brand.is_active.is_(True))
            .order_by(Brand.name.asc())
            .limit(limit)
            .all()
        )
        return [{"id": b.id, "name": b.name, "slug": b.slug} for b in rows]
