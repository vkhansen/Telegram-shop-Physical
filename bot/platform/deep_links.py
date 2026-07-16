"""Deep-link policy: Telegram → web funnel without cloning forms (CARD-40 E2).

Telegram customer adapters **must not** implement lead/booking FSM forms
"for parity." When a brand wants funnel conversion from chat, send a **URL
button** (or plain link) to the storefront pages:

  /{brand}/inquire  — leads (capability ``leads``)
  /{brand}/book     — booking (capability ``booking``)
  /{brand}/contact  — contact chrome (capability ``contact``)

Base URL comes from ``PUBLIC_SITE_URL`` (same env as web CORS / OAuth redirects).
"""

from __future__ import annotations

import os
from typing import Literal
from urllib.parse import quote, urlencode

FunnelPage = Literal["inquire", "book", "contact", "home"]

# Storefront path segment for each funnel page (apps/storefront routes).
FUNNEL_PATHS: dict[str, str] = {
    "home": "",
    "inquire": "inquire",
    "book": "book",
    "contact": "contact",
}

# Capability that must be ON for the deep link to be product-honest.
FUNNEL_REQUIRED_CAP: dict[str, str | None] = {
    "home": None,
    "inquire": "leads",
    "book": "booking",
    "contact": "contact",
}


def public_site_base(base: str | None = None) -> str:
    """Resolve storefront origin (no trailing slash)."""
    raw = (base if base is not None else os.getenv("PUBLIC_SITE_URL", "http://127.0.0.1:4321")).strip()
    return raw.rstrip("/")


def storefront_path(
    brand_slug: str,
    page: FunnelPage | str = "home",
    *,
    store_slug: str | None = None,
    query: dict[str, str] | None = None,
) -> str:
    """Relative storefront path for a brand funnel page."""
    slug = (brand_slug or "").strip().strip("/")
    if not slug:
        raise ValueError("brand_slug_required")
    key = (page or "home").strip().lower()
    if key not in FUNNEL_PATHS:
        raise ValueError(f"unknown_funnel_page:{key}")
    parts = [quote(slug, safe="-_.~")]
    if store_slug:
        parts.append(quote(store_slug.strip().strip("/"), safe="-_.~"))
    segment = FUNNEL_PATHS[key]
    if segment:
        parts.append(segment)
    path = "/" + "/".join(parts)
    if query:
        path = f"{path}?{urlencode(query)}"
    return path


def storefront_url(
    brand_slug: str,
    page: FunnelPage | str = "home",
    *,
    store_slug: str | None = None,
    query: dict[str, str] | None = None,
    base: str | None = None,
) -> str:
    """Absolute storefront URL for TG URL buttons / copy-paste links."""
    return public_site_base(base) + storefront_path(
        brand_slug,
        page,
        store_slug=store_slug,
        query=query,
    )


def funnel_url_button(
    brand_slug: str,
    page: FunnelPage | str,
    *,
    text: str | None = None,
    store_slug: str | None = None,
    query: dict[str, str] | None = None,
    base: str | None = None,
) -> dict[str, str]:
    """Inline URL button payload for Messenger / Telegram keyboards.

    Returns ``{"text": ..., "url": ...}`` — adapters map to platform widgets.
    Never implements form fields; link-only policy (CARD-40 E2).
    """
    url = storefront_url(
        brand_slug,
        page,
        store_slug=store_slug,
        query=query,
        base=base,
    )
    defaults = {
        "inquire": "Inquire on web",
        "book": "Book on web",
        "contact": "Contact on web",
        "home": "Open storefront",
    }
    label = (text or defaults.get((page or "home").lower()) or "Open web").strip()
    return {"text": label, "url": url}


def required_cap_for_funnel(page: FunnelPage | str) -> str | None:
    """Capability key that should be ON before offering this deep link."""
    return FUNNEL_REQUIRED_CAP.get((page or "home").strip().lower())
