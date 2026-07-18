"""Channel-agnostic delivery location normalization.

Coordinates are the source of truth for dispatch (Thailand free-text addresses
are unreliable). Adapters (Telegram pin, Maps paste, browser geolocation, IG/LINE
text) all funnel through ``normalize_delivery_input`` / ``extract_coords``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import unquote

# Google Maps / Apple-style URL patterns (lat,lng)
_MAPS_COORD_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"@(-?\d+\.\d+),(-?\d+\.\d+)"),  # maps/@lat,lng
    re.compile(r"[?&]q=(-?\d+\.\d+),(-?\d+\.\d+)"),  # ?q=lat,lng
    re.compile(r"[?&]ll=(-?\d+\.\d+),(-?\d+\.\d+)"),  # ll=lat,lng
    re.compile(r"[?&]query=(-?\d+\.\d+),(-?\d+\.\d+)"),
    re.compile(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)"),  # data=!3dlat!4dlng
    re.compile(r"/(-?\d+\.\d+),(-?\d+\.\d+)"),  # path /lat,lng
)

# Bare "13.7563, 100.5018" or "13.7563 100.5018"
_BARE_COORD_RE = re.compile(
    r"^\s*(-?\d{1,2}(?:\.\d+)?)\s*[,;\s]\s*(-?\d{1,3}(?:\.\d+)?)\s*$"
)

_MAPS_HINTS = (
    "google.com/maps",
    "maps.google",
    "goo.gl/maps",
    "maps.app.goo.gl",
    "maps.apple.com",
)


@dataclass(frozen=True)
class DeliveryLocation:
    """Normalized delivery location for CustomerInfo / Order."""

    latitude: float | None
    longitude: float | None
    google_maps_link: str | None
    delivery_address: str
    source: str  # coords | maps_url | free_text | explicit
    has_gps: bool

    def as_profile_kwargs(self) -> dict[str, Any]:
        """Kwargs for ensure_delivery_profile / create_or_update_customer_info."""
        return {
            "delivery_address": self.delivery_address,
            "latitude": self.latitude,
            "longitude": self.longitude,
        }

    def as_state_dict(self) -> dict[str, Any]:
        """FSM / session dict (Telegram + messaging adapters)."""
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "google_maps_link": self.google_maps_link,
            "delivery_address": self.delivery_address,
            "location_source": self.source,
        }


def build_maps_link(latitude: float | None, longitude: float | None) -> str | None:
    """Canonical maps URL from coordinates."""
    if latitude is not None and longitude is not None:
        return f"https://www.google.com/maps?q={latitude},{longitude}"
    return None


def _valid_pair(lat: float, lng: float) -> bool:
    return -90.0 <= lat <= 90.0 and -180.0 <= lng <= 180.0


def extract_coords_from_url(url: str) -> tuple[float, float] | None:
    """Return (lat, lng) from a maps URL, or None."""
    if not url or not str(url).strip():
        return None
    text = unquote(str(url).strip())
    for pat in _MAPS_COORD_PATTERNS:
        m = pat.search(text)
        if m:
            lat, lng = float(m.group(1)), float(m.group(2))
            if _valid_pair(lat, lng):
                return lat, lng
    return None


def extract_coords_from_text(text: str) -> tuple[float, float] | None:
    """Return (lat, lng) from bare coordinates or a maps URL, or None."""
    if not text or not str(text).strip():
        return None
    raw = str(text).strip()
    m = _BARE_COORD_RE.match(raw)
    if m:
        lat, lng = float(m.group(1)), float(m.group(2))
        if _valid_pair(lat, lng):
            return lat, lng
    if looks_like_maps_url(raw):
        return extract_coords_from_url(raw)
    # Try URL patterns even without domain hint (query-only fragments)
    return extract_coords_from_url(raw)


def looks_like_maps_url(text: str) -> bool:
    t = (text or "").lower()
    return any(h in t for h in _MAPS_HINTS)


def normalize_delivery_input(
    *,
    text: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    maps_url: str | None = None,
    landmark: str | None = None,
    min_address_len: int = 5,
) -> DeliveryLocation | None:
    """
    Build a :class:`DeliveryLocation` from any channel input.

    Priority: explicit lat/lng → maps_url → text (coords / maps / free-text).

    Returns None only when there is no usable location payload at all.
    Free-text shorter than *min_address_len* with no GPS → None.
    """
    # 1) Explicit coordinates (browser geo, Telegram pin)
    if latitude is not None and longitude is not None:
        try:
            lat, lng = float(latitude), float(longitude)
        except (TypeError, ValueError):
            lat = lng = None  # type: ignore[assignment]
        else:
            if _valid_pair(lat, lng):
                link = build_maps_link(lat, lng)
                addr = (landmark or text or link or f"{lat},{lng}").strip()
                return DeliveryLocation(
                    latitude=lat,
                    longitude=lng,
                    google_maps_link=link,
                    delivery_address=addr or (link or f"{lat},{lng}"),
                    source="explicit",
                    has_gps=True,
                )

    # 2) Dedicated maps_url field
    if maps_url and str(maps_url).strip():
        url = str(maps_url).strip()
        coords = extract_coords_from_url(url)
        if coords:
            lat, lng = coords
            link = build_maps_link(lat, lng) or url
            addr = (landmark or text or link).strip()
            return DeliveryLocation(
                latitude=lat,
                longitude=lng,
                google_maps_link=link,
                delivery_address=addr,
                source="maps_url",
                has_gps=True,
            )
        # Short link without embeddable coords — keep URL as address/link
        addr = (landmark or text or url).strip()
        if len(addr) >= min_address_len or looks_like_maps_url(url):
            return DeliveryLocation(
                latitude=None,
                longitude=None,
                google_maps_link=url,
                delivery_address=addr,
                source="maps_url",
                has_gps=False,
            )

    # 3) Free text: bare coords, maps paste, or address
    raw = (text or "").strip()
    if not raw:
        return None

    coords = extract_coords_from_text(raw)
    if coords:
        lat, lng = coords
        link = build_maps_link(lat, lng)
        addr = (landmark or link or raw).strip()
        return DeliveryLocation(
            latitude=lat,
            longitude=lng,
            google_maps_link=link,
            delivery_address=addr,
            source="coords" if _BARE_COORD_RE.match(raw) else "maps_url",
            has_gps=True,
        )

    if looks_like_maps_url(raw):
        return DeliveryLocation(
            latitude=None,
            longitude=None,
            google_maps_link=raw,
            delivery_address=raw,
            source="maps_url",
            has_gps=False,
        )

    if len(raw) < min_address_len:
        return None

    return DeliveryLocation(
        latitude=None,
        longitude=None,
        google_maps_link=None,
        delivery_address=raw,
        source="free_text",
        has_gps=False,
    )
