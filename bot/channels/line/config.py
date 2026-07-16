"""LINE channel env config (CARD-16)."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _truthy(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class LineConfig:
    enabled: bool
    channel_access_token: str
    channel_secret: str
    webhook_path: str
    default_brand_id: int | None
    api_base: str

    @property
    def reply_url(self) -> str:
        return f"{self.api_base.rstrip('/')}/v2/bot/message/reply"

    @property
    def push_url(self) -> str:
        return f"{self.api_base.rstrip('/')}/v2/bot/message/push"


def load_line_config() -> LineConfig:
    brand_raw = os.getenv("LINE_DEFAULT_BRAND_ID", "").strip()
    try:
        brand_id = int(brand_raw) if brand_raw else None
    except ValueError:
        brand_id = None
    return LineConfig(
        enabled=_truthy("LINE_CHANNEL_ENABLED", "false"),
        channel_access_token=os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "").strip(),
        channel_secret=os.getenv("LINE_CHANNEL_SECRET", "").strip(),
        webhook_path=os.getenv("LINE_WEBHOOK_PATH", "/webhooks/line").strip() or "/webhooks/line",
        default_brand_id=brand_id,
        api_base=os.getenv("LINE_API_BASE", "https://api.line.me").strip() or "https://api.line.me",
    )
