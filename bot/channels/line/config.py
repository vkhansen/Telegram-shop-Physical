"""LINE channel env config (CARD-16)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field


def _truthy(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "on")


def parse_oa_brand_map(raw: str | None) -> dict[str, int]:
    """
    Map LINE bot destination (OA user id) → brand_id.

    Formats:
      - JSON object: {"Uxxxx": 1, "Uyyyy": 2}
      - CSV pairs: Uxxxx:1,Uyyyy:2
    """
    text = (raw or "").strip()
    if not text:
        return {}
    out: dict[str, int] = {}
    if text.startswith("{"):
        try:
            data = json.loads(text)
            if isinstance(data, dict):
                for k, v in data.items():
                    try:
                        out[str(k).strip()] = int(v)
                    except (TypeError, ValueError):
                        continue
            return out
        except json.JSONDecodeError:
            pass
    for part in text.split(","):
        part = part.strip()
        if not part or ":" not in part:
            continue
        dest, _, brand = part.partition(":")
        dest = dest.strip()
        try:
            out[dest] = int(brand.strip())
        except ValueError:
            continue
    return out


@dataclass(frozen=True)
class LineConfig:
    enabled: bool
    channel_access_token: str
    channel_secret: str
    webhook_path: str
    default_brand_id: int | None
    api_base: str
    oa_brand_map: dict[str, int] = field(default_factory=dict)
    session_backend: str = "memory"
    use_flex: bool = True

    @property
    def reply_url(self) -> str:
        return f"{self.api_base.rstrip('/')}/v2/bot/message/reply"

    @property
    def push_url(self) -> str:
        return f"{self.api_base.rstrip('/')}/v2/bot/message/push"

    def brand_id_for_destination(self, destination: str | None) -> int | None:
        """Resolve brand from multi-OA map, else default brand."""
        dest = (destination or "").strip()
        if dest and dest in self.oa_brand_map:
            return self.oa_brand_map[dest]
        return self.default_brand_id


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
        oa_brand_map=parse_oa_brand_map(
            os.getenv("LINE_OA_BRAND_MAP") or os.getenv("LINE_BRAND_MAP")
        ),
        session_backend=(os.getenv("LINE_SESSION_BACKEND", "memory") or "memory").strip().lower(),
        use_flex=_truthy("LINE_USE_FLEX", "true"),
    )
