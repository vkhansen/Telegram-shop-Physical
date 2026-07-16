"""Channel-agnostic media references.

Storage schemes (stored in logo_file_id / image_file_id columns historically
named for Telegram — treat as opaque media refs):

  local:<filename>     demo / fixture files under tests/test-data
  tg:<file_id>         Telegram Bot API file_id (adapter only)
  https://... / http://...  absolute URL pass-through
  s3:<key>             reserved
  bare string          legacy Telegram file_id (normalized to tg:)

Public APIs never return raw refs — only resolved public URLs via media_proxy.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlparse

MediaScheme = Literal["local", "tg", "http", "https", "s3", "unknown"]


@dataclass(frozen=True)
class MediaRef:
    scheme: MediaScheme
    value: str  # path/key/file_id (for http(s) full URL is in value)

    @property
    def storage_key(self) -> str:
        """Canonical string for DB storage / allowlist matching."""
        if self.scheme in ("http", "https"):
            return self.value
        if self.scheme == "unknown":
            return self.value
        return f"{self.scheme}:{self.value}"


def parse_media_ref(raw: str | None) -> MediaRef | None:
    if not raw or not str(raw).strip():
        return None
    s = str(raw).strip()

    if s.startswith("https://"):
        return MediaRef("https", s)
    if s.startswith("http://"):
        return MediaRef("http", s)

    if ":" in s:
        scheme, rest = s.split(":", 1)
        scheme_l = scheme.lower()
        if scheme_l == "local":
            return MediaRef("local", rest.lstrip("/").replace("..", ""))
        if scheme_l in ("tg", "telegram"):
            return MediaRef("tg", rest)
        if scheme_l == "s3":
            return MediaRef("s3", rest)
        if scheme_l in ("http", "https"):
            return MediaRef(scheme_l, s)  # type: ignore[arg-type]

    # Legacy bare Telegram file_id
    return MediaRef("tg", s)


def normalize_media_ref(raw: str | None) -> str | None:
    """Canonical storage form (local:x, tg:x, or absolute URL)."""
    ref = parse_media_ref(raw)
    if not ref:
        return None
    return ref.storage_key


def media_url_for_ref(raw: str | None, *, brand_id: int | None = None) -> str | None:
    """Public URL for a media ref — delegates to media_proxy (no Telegram leakage)."""
    # Lazy import avoids circular deps at module load
    from bot.services.media_proxy import media_url_for

    ref = parse_media_ref(raw)
    if not ref:
        return None
    if ref.scheme in ("http", "https"):
        # Validate absolute URL lightly
        parsed = urlparse(ref.value)
        if parsed.scheme in ("http", "https") and parsed.netloc:
            return ref.value
        return None
    if ref.scheme == "local":
        return media_url_for(f"local:{ref.value}", brand_id=brand_id)
    if ref.scheme == "tg":
        # Pass bare file_id to existing proxy token path (legacy column values)
        return media_url_for(ref.value, brand_id=brand_id)
    # s3 / unknown not public yet
    return None
