"""Per-user LINE conversation state (not aiogram FSM)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class LineSession:
    state: str = "idle"
    data: dict[str, Any] = field(default_factory=dict)

    def reset(self) -> None:
        self.state = "idle"
        self.data.clear()


class SessionStore:
    def __init__(self) -> None:
        self._by_uid: dict[str, LineSession] = {}

    def get(self, line_user_id: str) -> LineSession:
        key = str(line_user_id).strip()
        if key not in self._by_uid:
            self._by_uid[key] = LineSession()
        return self._by_uid[key]

    def clear(self, line_user_id: str) -> None:
        self._by_uid.pop(str(line_user_id).strip(), None)

    def clear_all(self) -> None:
        self._by_uid.clear()


default_session_store = SessionStore()
