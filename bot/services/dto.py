"""Shared application-service result types (CARD-32).

Channel-agnostic: no Telegram / HTTP / LINE types.
Adapters map ``error_key`` via i18n and ``data`` into UI.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ServiceResult:
    """Standard return for customer application services."""

    ok: bool
    error_key: str | None = None
    """Stable machine key for adapters (e.g. cart.empty, order.bonus.insufficient)."""
    error_detail: str | None = None
    """Optional human/debug detail (inventory message, exception text)."""
    data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def success(cls, **data: Any) -> ServiceResult:
        return cls(ok=True, data=dict(data))

    @classmethod
    def fail(cls, error_key: str, error_detail: str | None = None, **data: Any) -> ServiceResult:
        return cls(ok=False, error_key=error_key, error_detail=error_detail, data=dict(data))
