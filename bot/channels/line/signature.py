"""LINE webhook signature verification (X-Line-Signature)."""

from __future__ import annotations

import base64
import hashlib
import hmac


def verify_line_signature(
    *,
    channel_secret: str,
    body: bytes,
    header_value: str | None,
) -> bool:
    """
    Return True if header is Base64(HMAC-SHA256(channel_secret, body)).

    Empty *channel_secret* skips verification (dev only).
    """
    if not channel_secret:
        return True
    if not header_value:
        return False
    digest = hmac.new(channel_secret.encode("utf-8"), body, hashlib.sha256).digest()
    expect = base64.b64encode(digest).decode("ascii")
    return hmac.compare_digest(expect, header_value.strip())
