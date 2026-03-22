"""Multi-format data ingestion for Grok AI admin assistant (Card 17).

Handles CSV, Excel, JSON, and plain text uploads.
"""

import csv
import io
import json
import logging

from aiogram.types import Message

logger = logging.getLogger(__name__)


async def extract_content(message: Message) -> str:
    """Extract text content from any Telegram message format.

    Supports: plain text, CSV, Excel (.xlsx), JSON, and generic text files.
    Photos return a placeholder (Grok vision not implemented yet).
    """
    # Plain text
    if message.text:
        return message.text

    # Document upload
    if message.document:
        # Reject files larger than 10 MB to prevent resource exhaustion
        max_size = 10 * 1024 * 1024  # 10 MB
        if message.document.file_size and message.document.file_size > max_size:
            return "[File rejected: exceeds 10 MB size limit]"

        file = await message.bot.download(message.document)
        raw = file.read()
        filename = message.document.file_name or ""

        if filename.lower().endswith(".csv"):
            return _parse_csv_to_text(raw)
        elif filename.lower().endswith((".xlsx", ".xls")):
            return _parse_excel_to_text(raw)
        elif filename.lower().endswith(".json"):
            return _parse_json_to_text(raw)
        else:
            # Generic text file
            try:
                text = raw.decode("utf-8", errors="replace")
                return f"File content ({filename}):\n{text[:5000]}"
            except Exception:
                return f"[Could not read file: {filename}]"

    # Photo
    if message.photo:
        caption = message.caption or ""
        return f"[Admin sent a photo]{' — ' + caption if caption else ''}. Please ask what to do with it."

    return "[Empty message]"


def _parse_csv_to_text(raw: bytes) -> str:
    """Parse CSV and present as structured text for Grok."""
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")

    reader = csv.DictReader(io.StringIO(text))
    headers = reader.fieldnames
    if not headers:
        return "CSV file appears to be empty or has no headers."

    rows = list(reader)

    # LOGIC-35 fix: Don't duplicate first 5 rows in full data section
    preview = f"CSV with {len(rows)} rows, columns: {headers}\n\n"
    if len(rows) <= 5:
        preview += "All rows:\n"
        for row in rows:
            preview += str(dict(row)) + "\n"
    else:
        preview += "First 5 rows:\n"
        for row in rows[:5]:
            preview += str(dict(row)) + "\n"
        preview += f"\n... and {len(rows) - 5} more rows.\n"
        preview += f"\nRemaining rows ({len(rows) - 5}):\n"
        for row in rows[5:]:
            preview += str(dict(row)) + "\n"

    return f"Admin uploaded a CSV file. Please map these columns to menu items.\n\n{preview}"


def _parse_excel_to_text(raw: bytes) -> str:
    """Parse Excel file to text. Requires openpyxl."""
    try:
        import openpyxl
    except ImportError:
        return "[Excel support requires openpyxl. Please upload a CSV instead.]"

    try:
        wb = openpyxl.load_workbook(io.BytesIO(raw), read_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return "Excel file appears to be empty."

        headers = [str(h) if h else f"col_{i}" for i, h in enumerate(rows[0])]
        data_rows = rows[1:]

        preview = f"Excel with {len(data_rows)} data rows, columns: {headers}\n\n"
        preview += "First 5 rows:\n"
        for row in data_rows[:5]:
            row_dict = dict(zip(headers, row))
            preview += str(row_dict) + "\n"

        if len(data_rows) > 5:
            preview += f"\n... and {len(data_rows) - 5} more rows.\n"

        preview += f"\nFull data (all {len(data_rows)} rows):\n"
        for row in data_rows:
            row_dict = dict(zip(headers, row))
            preview += str(row_dict) + "\n"

        return f"Admin uploaded an Excel file. Please map these columns to menu items.\n\n{preview}"
    except Exception as e:
        return f"[Error reading Excel file: {e}]"


def _parse_json_to_text(raw: bytes) -> str:
    """Parse JSON data to text."""
    try:
        data = json.loads(raw.decode("utf-8"))
        formatted = json.dumps(data, indent=2, ensure_ascii=False)
        return f"Admin uploaded a JSON file:\n\n{formatted[:5000]}"
    except Exception as e:
        return f"[Error reading JSON file: {e}]"
