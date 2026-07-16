"""Meta webhook signature verification (X-Hub-Signature-256)."""

from __future__ import annotations

import hashlib
import hmac


def verify_hub_signature_256(
    *,
    app_secret: str,
    body: bytes,
    header_value: str | None,
) -> bool:
    """
    Return True if ``header_value`` matches ``sha256=HMAC(app_secret, body)``.

    When *app_secret* is empty (dev), verification is skipped and returns True.
    """
    if not app_secret:
        return True
    if not header_value:
        return False
    raw = header_value.strip()
    if raw.lower().startswith("sha256="):
        raw = raw[7:]
    expect = hmac.new(app_secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expect, raw)
