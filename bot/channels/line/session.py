"""Per-user LINE conversation state (not aiogram FSM).

Default: in-process. Optional Redis for multi-worker:
  LINE_SESSION_BACKEND=redis
  (uses same Redis as bot FSM — REDIS_HOST/PORT/PASSWORD/DB)
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Protocol

logger = logging.getLogger(__name__)

_SESSION_PREFIX = "line:sess:"
_DEFAULT_TTL = int(os.getenv("LINE_SESSION_TTL_SECONDS", "86400") or "86400")


@dataclass
class LineSession:
    state: str = "idle"
    data: dict[str, Any] = field(default_factory=dict)

    def reset(self) -> None:
        self.state = "idle"
        self.data.clear()

    def to_dict(self) -> dict[str, Any]:
        return {"state": self.state, "data": dict(self.data)}

    @classmethod
    def from_dict(cls, raw: dict[str, Any] | None) -> LineSession:
        if not raw:
            return cls()
        data = raw.get("data") if isinstance(raw.get("data"), dict) else {}
        return cls(state=str(raw.get("state") or "idle"), data=dict(data))


class SessionStoreProtocol(Protocol):
    def get(self, line_user_id: str) -> LineSession: ...
    def save(self, line_user_id: str, session: LineSession) -> None: ...
    def clear(self, line_user_id: str) -> None: ...
    def clear_all(self) -> None: ...


class SessionStore:
    """In-memory session map (process-local)."""

    def __init__(self) -> None:
        self._by_uid: dict[str, LineSession] = {}

    def get(self, line_user_id: str) -> LineSession:
        key = str(line_user_id).strip()
        if key not in self._by_uid:
            self._by_uid[key] = LineSession()
        return self._by_uid[key]

    def save(self, line_user_id: str, session: LineSession) -> None:
        self._by_uid[str(line_user_id).strip()] = session

    def clear(self, line_user_id: str) -> None:
        self._by_uid.pop(str(line_user_id).strip(), None)

    def clear_all(self) -> None:
        self._by_uid.clear()


class RedisSessionStore:
    """Redis-backed sessions for multi-worker LINE webhooks."""

    def __init__(self, redis_client: Any, *, ttl_seconds: int = _DEFAULT_TTL) -> None:
        self._redis = redis_client
        self._ttl = max(60, int(ttl_seconds))
        self._local = SessionStore()  # write-through cache for same worker

    def _key(self, line_user_id: str) -> str:
        return f"{_SESSION_PREFIX}{str(line_user_id).strip()}"

    def get(self, line_user_id: str) -> LineSession:
        key = str(line_user_id).strip()
        try:
            raw = self._redis.get(self._key(key))
            if raw is None:
                sess = LineSession()
                self._local.save(key, sess)
                return sess
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8")
            data = json.loads(raw)
            sess = LineSession.from_dict(data if isinstance(data, dict) else {})
            self._local.save(key, sess)
            return sess
        except Exception:
            logger.exception("LINE Redis session get failed; using memory")
            return self._local.get(key)

    def save(self, line_user_id: str, session: LineSession) -> None:
        key = str(line_user_id).strip()
        self._local.save(key, session)
        try:
            self._redis.setex(self._key(key), self._ttl, json.dumps(session.to_dict()))
        except Exception:
            logger.exception("LINE Redis session save failed")

    def clear(self, line_user_id: str) -> None:
        key = str(line_user_id).strip()
        self._local.clear(key)
        try:
            self._redis.delete(self._key(key))
        except Exception:
            logger.exception("LINE Redis session clear failed")

    def clear_all(self) -> None:
        self._local.clear_all()
        try:
            for k in self._redis.scan_iter(match=f"{_SESSION_PREFIX}*"):
                self._redis.delete(k)
        except Exception:
            logger.exception("LINE Redis session clear_all failed")


def _sync_redis_from_env() -> Any | None:
    """Create a sync redis client if REDIS is configured."""
    host = os.getenv("REDIS_HOST", "").strip()
    if not host:
        return None
    try:
        import redis

        port = int(os.getenv("REDIS_PORT", "6379") or "6379")
        db = int(os.getenv("REDIS_DB", "0") or "0")
        password = os.getenv("REDIS_PASSWORD") or None
        client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password or None,
            decode_responses=False,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        client.ping()
        return client
    except Exception:
        logger.warning("LINE Redis session backend unavailable; falling back to memory")
        return None


def build_session_store() -> SessionStore | RedisSessionStore:
    backend = (os.getenv("LINE_SESSION_BACKEND", "memory") or "memory").strip().lower()
    if backend in ("redis", "redis_sync", "1", "true"):
        client = _sync_redis_from_env()
        if client is not None:
            logger.info("LINE sessions: Redis backend (ttl=%ss)", _DEFAULT_TTL)
            return RedisSessionStore(client, ttl_seconds=_DEFAULT_TTL)
    return SessionStore()


default_session_store: SessionStore | RedisSessionStore = build_session_store()
