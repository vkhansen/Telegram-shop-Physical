"""Host PromptPay QR PNGs for LINE image messages (public HTTPS URL required).

LINE cannot accept raw bytes; messages need ``originalContentUrl`` over HTTPS.
We cache PNG under ``data/line_qr_cache/`` and serve via ``GET /media/line-qr/{token}.png``.
"""

from __future__ import annotations

import hashlib
import logging
import os
import time
from pathlib import Path

logger = logging.getLogger(__name__)

_CACHE_DIR = Path(os.getenv("LINE_QR_CACHE_DIR", "data/line_qr_cache"))
_TTL_SEC = int(os.getenv("LINE_QR_TTL_SECONDS", "3600") or "3600")
_META: dict[str, float] = {}  # token -> expires_at


def _ensure_dir() -> Path:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return _CACHE_DIR


def media_public_base() -> str:
    """Absolute base for LINE-fetchable URLs (must be HTTPS in production)."""
    base = (
        os.getenv("PUBLIC_MEDIA_BASE_URL")
        or os.getenv("PUBLIC_API_BASE")
        or os.getenv("LINE_PUBLIC_BASE_URL")
        or ""
    ).strip().rstrip("/")
    if base:
        return base
    host = os.getenv("MONITORING_HOST", "localhost")
    if host in ("0.0.0.0", ""):
        host = "localhost"
    port = os.getenv("MONITORING_PORT", "9090")
    return f"http://{host}:{port}"


def store_qr_png(order_code: str, png_bytes: bytes) -> str | None:
    """Persist PNG and return public URL, or None if empty."""
    if not png_bytes:
        return None
    digest = hashlib.sha256(png_bytes + order_code.encode("utf-8")).hexdigest()[:32]
    token = f"{digest}"
    path = _ensure_dir() / f"{token}.png"
    try:
        path.write_bytes(png_bytes)
        _META[token] = time.time() + max(60, _TTL_SEC)
        return f"{media_public_base()}/media/line-qr/{token}.png"
    except OSError:
        logger.exception("LINE QR cache write failed")
        return None


def read_qr_png(token: str) -> bytes | None:
    """Load PNG if present and not expired."""
    token = (token or "").strip().replace("..", "")
    if not token or not all(c.isalnum() or c in "-_" for c in token):
        return None
    expires = _META.get(token)
    path = _CACHE_DIR / f"{token}.png"
    if not path.is_file():
        return None
    if expires is not None and time.time() > expires:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
        _META.pop(token, None)
        return None
    # File exists without meta (restart) — allow once, re-stamp TTL
    if expires is None:
        _META[token] = time.time() + max(60, _TTL_SEC)
    try:
        return path.read_bytes()
    except OSError:
        return None
