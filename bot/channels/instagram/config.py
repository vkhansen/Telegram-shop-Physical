"""Instagram channel env config (CARD-33)."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _truthy(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class InstagramConfig:
    enabled: bool
    page_access_token: str
    app_secret: str
    verify_token: str
    webhook_path: str
    default_brand_id: int | None
    graph_api_version: str
    # When set, PromptPay QR PNG can be exposed temporarily (optional v1)
    public_media_base_url: str

    @property
    def graph_messages_url(self) -> str:
        ver = self.graph_api_version.strip("/") or "v21.0"
        return f"https://graph.facebook.com/{ver}/me/messages"


def load_instagram_config() -> InstagramConfig:
    brand_raw = os.getenv("INSTAGRAM_DEFAULT_BRAND_ID", "").strip()
    brand_id: int | None
    try:
        brand_id = int(brand_raw) if brand_raw else None
    except ValueError:
        brand_id = None
    return InstagramConfig(
        enabled=_truthy("INSTAGRAM_CHANNEL_ENABLED", "false"),
        page_access_token=os.getenv("INSTAGRAM_PAGE_ACCESS_TOKEN", "").strip(),
        app_secret=os.getenv("INSTAGRAM_APP_SECRET", "").strip(),
        verify_token=os.getenv("INSTAGRAM_VERIFY_TOKEN", "").strip(),
        webhook_path=os.getenv("INSTAGRAM_WEBHOOK_PATH", "/webhooks/instagram").strip()
        or "/webhooks/instagram",
        default_brand_id=brand_id,
        graph_api_version=os.getenv("INSTAGRAM_GRAPH_API_VERSION", "v21.0").strip() or "v21.0",
        public_media_base_url=(
            os.getenv("PUBLIC_MEDIA_BASE_URL") or os.getenv("PUBLIC_API_BASE") or ""
        ).rstrip("/"),
    )
