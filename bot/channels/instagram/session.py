"""Lightweight conversation state for Instagram (not aiogram FSM).

Keyed by PSID. In-process default; swap for Redis in multi-worker deploys.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class IgSession:
    """Per-PSID conversation state."""

    state: str = "idle"
    data: dict[str, Any] = field(default_factory=dict)

    def reset(self) -> None:
        self.state = "idle"
        self.data.clear()


class SessionStore:
    """In-memory session map (process-local)."""

    def __init__(self) -> None:
        self._by_psid: dict[str, IgSession] = {}

    def get(self, psid: str) -> IgSession:
        key = str(psid).strip()
        if key not in self._by_psid:
            self._by_psid[key] = IgSession()
        return self._by_psid[key]

    def clear(self, psid: str) -> None:
        self._by_psid.pop(str(psid).strip(), None)

    def clear_all(self) -> None:
        self._by_psid.clear()


# Process default for the adapter
default_session_store = SessionStore()
