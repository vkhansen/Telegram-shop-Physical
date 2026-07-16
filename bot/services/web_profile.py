"""Pydantic validation for brand/store web_profile JSON (CARD-38)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ThemeTokensV1(BaseModel):
    """Per-brand visual system (CSS variables + chrome enums). Tokens only — no raw CSS."""

    model_config = ConfigDict(extra="allow")

    mode: Literal["light", "dark"] | None = None
    colors: dict[str, str] | None = None
    type: dict[str, Any] | None = None
    geometry: dict[str, Any] | None = None
    motion: dict[str, Any] | None = None
    # chrome enums: nav, ticker, age_gate, benefits, catalog, product_media, logo
    chrome: dict[str, str] | None = None


class WebProfileV1(BaseModel):
    """Loose schema — extra keys allowed for forward compatibility.

    Channel-agnostic white-label config (not Telegram-specific):
      modules / capabilities — feature toggles
      channels — per-surface enable + mask (web, telegram, line, …)
      compliance — age gate + disclaimers (tenant legal prose)
      nav / sections / cta — UI labels
      theme / theme_tokens — skin + CSS variable pack (per brand)
    """

    model_config = ConfigDict(extra="allow")

    schema_version: int = 1
    web_enabled: bool = True
    theme: str | None = None
    theme_tokens: ThemeTokensV1 | dict[str, Any] | None = None
    tagline: str | None = None
    tagline_i18n: dict[str, str] | None = None
    ticker: str | None = None
    about: dict[str, Any] | None = None
    hero: dict[str, Any] | None = None
    social: dict[str, Any] | None = None
    faq: list[dict[str, Any]] | None = None
    seo: dict[str, Any] | None = None
    modules: dict[str, Any] | None = None
    # Explicit capability overrides (see bot.platform.capabilities)
    capabilities: dict[str, Any] | None = None
    # Per-channel enable + mask: { "web": {"enabled": true, "mask": {...}}, ... }
    channels: dict[str, Any] | None = None
    compliance: dict[str, Any] | None = None
    booking: dict[str, Any] | None = None
    nav: dict[str, Any] | None = None
    sections: dict[str, Any] | None = None
    cta: dict[str, Any] | None = None
    benefits: list[dict[str, Any]] | None = None


class StoreWebProfileV1(BaseModel):
    model_config = ConfigDict(extra="allow")

    schema_version: int = 1
    about_md: str | None = None
    amenities: list[str] | None = None
    pickup_notes_md: str | None = None
    seo: dict[str, Any] | None = None
    # Prefer gallery_media_refs; gallery_file_ids kept as legacy alias
    gallery_media_refs: list[str] | None = None
    gallery_file_ids: list[str] | None = None


CommerceMode = Literal["full_store", "portfolio", "hybrid"]
VALID_COMMERCE_MODES = frozenset({"full_store", "portfolio", "hybrid"})


def validate_brand_web_profile(data: dict | None) -> dict:
    """Normalize/validate brand web_profile; returns plain dict for JSON storage."""
    if not data:
        return {"schema_version": 1}
    return WebProfileV1.model_validate(data).model_dump(exclude_none=False)


def validate_store_web_profile(data: dict | None) -> dict:
    if not data:
        return {"schema_version": 1}
    return StoreWebProfileV1.model_validate(data).model_dump(exclude_none=False)


def normalize_commerce_mode(mode: str | None) -> str:
    m = (mode or "full_store").strip().lower()
    if m not in VALID_COMMERCE_MODES:
        return "full_store"
    return m
