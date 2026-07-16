"""Web OAuth + session helpers for white-label ticket portal (CARD-39)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
import time
from typing import Any
from urllib.parse import urlencode

import httpx

from bot.database.main import Database
from bot.database.models.main import OAuthProfile, Role, User, UserIdentity

logger = logging.getLogger(__name__)

SESSION_COOKIE = "wl_session"
SESSION_MAX_AGE = int(os.getenv("WEB_SESSION_MAX_AGE", str(60 * 60 * 24 * 14)))  # 14 days


def _session_secret() -> bytes:
    secret = os.getenv("WEB_SESSION_SECRET") or os.getenv("TOKEN") or "dev-insecure-session-secret"
    return secret.encode("utf-8")


def synthetic_user_id(provider: str, subject: str) -> int:
    """Reserved high-range id so web users don't collide with real Telegram ids."""
    digest = hashlib.sha256(f"{provider}:{subject}".encode()).hexdigest()
    n = int(digest[:15], 16)
    return 1_000_000_000_000_000 + (n % 8_000_000_000_000_000)


def sign_session(payload: dict[str, Any]) -> str:
    body = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode().rstrip("=")
    sig = hmac.new(_session_secret(), body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"


def verify_session(token: str | None) -> dict[str, Any] | None:
    if not token or "." not in token:
        return None
    body, sig = token.rsplit(".", 1)
    expect = hmac.new(_session_secret(), body.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expect, sig):
        return None
    try:
        pad = "=" * (-len(body) % 4)
        data = json.loads(base64.urlsafe_b64decode(body + pad))
    except Exception:
        return None
    if int(data.get("exp", 0)) < int(time.time()):
        return None
    return data


def create_session_token(*, user_id: int, email: str | None, name: str | None, avatar: str | None = None) -> str:
    now = int(time.time())
    return sign_session(
        {
            "uid": user_id,
            "email": email,
            "name": name,
            "avatar": avatar,
            "iat": now,
            "exp": now + SESSION_MAX_AGE,
        }
    )


def ensure_role_user() -> int:
    with Database().session() as s:
        role = s.query(Role).filter_by(name="USER").first()
        if role:
            return role.id
        # Fallback id 1 used by insert_roles
        return 1


def upsert_oauth_user(
    *,
    provider: str,
    subject: str,
    email: str | None = None,
    email_verified: bool = False,
    display_name: str | None = None,
    username: str | None = None,
    avatar_url: str | None = None,
    raw_claims: dict | None = None,
    link_by_email: bool | None = None,
) -> dict[str, Any]:
    """Find or create User + identity + oauth profile. Returns session payload fields."""
    if link_by_email is None:
        link_by_email = os.getenv("OAUTH_LINK_BY_EMAIL", "true").lower() in ("1", "true", "yes")

    with Database().session() as s:
        profile = (
            s.query(OAuthProfile)
            .filter(OAuthProfile.provider == provider, OAuthProfile.provider_subject == subject)
            .one_or_none()
        )
        user: User | None = None
        if profile:
            user = s.query(User).filter_by(telegram_id=profile.user_id).one_or_none()

        if user is None:
            ident = (
                s.query(UserIdentity)
                .filter(UserIdentity.platform == provider, UserIdentity.external_id == subject)
                .one_or_none()
            )
            if ident:
                user = s.query(User).filter_by(telegram_id=ident.user_id).one_or_none()

        if user is None and link_by_email and email and email_verified:
            other = (
                s.query(OAuthProfile)
                .filter(OAuthProfile.email == email, OAuthProfile.email_verified.is_(True))
                .first()
            )
            if other:
                user = s.query(User).filter_by(telegram_id=other.user_id).one_or_none()

        if user is None:
            uid = synthetic_user_id(provider, subject)
            # collision retry
            for _ in range(5):
                if s.query(User).filter_by(telegram_id=uid).first() is None:
                    break
                uid = synthetic_user_id(provider, subject + secrets.token_hex(4))
            from datetime import UTC, datetime

            user = User(
                telegram_id=uid,
                registration_date=datetime.now(UTC),
                role_id=ensure_role_user(),
            )
            s.add(user)
            s.flush()

        uid = user.telegram_id
        if profile is None:
            profile = OAuthProfile(
                user_id=uid,
                provider=provider,
                provider_subject=subject,
                email=email,
                email_verified=email_verified,
                display_name=display_name,
                username=username or (email.split("@")[0] if email else None),
                avatar_url=avatar_url,
                raw_claims=raw_claims,
            )
            s.add(profile)
        else:
            profile.email = email or profile.email
            profile.email_verified = email_verified or profile.email_verified
            profile.display_name = display_name or profile.display_name
            profile.username = username or profile.username
            profile.avatar_url = avatar_url or profile.avatar_url
            if raw_claims:
                profile.raw_claims = raw_claims

        # ensure identity rows (flush first so pending inserts are queryable)
        s.flush()
        if (
            s.query(UserIdentity)
            .filter(UserIdentity.platform == provider, UserIdentity.external_id == subject)
            .one_or_none()
            is None
        ):
            s.add(UserIdentity(user_id=uid, platform=provider, external_id=subject))
        if (
            s.query(UserIdentity)
            .filter(UserIdentity.platform == "web", UserIdentity.external_id == str(uid))
            .one_or_none()
            is None
        ):
            s.add(UserIdentity(user_id=uid, platform="web", external_id=str(uid)))

        s.commit()
        return {
            "user_id": uid,
            "email": profile.email,
            "name": profile.display_name,
            "username": profile.username,
            "avatar": profile.avatar_url,
            "provider": provider,
        }


def get_profile(user_id: int) -> dict[str, Any] | None:
    with Database().session() as s:
        profiles = s.query(OAuthProfile).filter(OAuthProfile.user_id == user_id).all()
        if not profiles:
            user = s.query(User).filter_by(telegram_id=user_id).one_or_none()
            if not user:
                return None
            return {"user_id": user_id, "email": None, "name": None, "providers": []}
        primary = profiles[0]
        return {
            "user_id": user_id,
            "email": primary.email,
            "name": primary.display_name,
            "username": primary.username,
            "avatar": primary.avatar_url,
            "providers": [
                {
                    "provider": p.provider,
                    "email": p.email,
                    "name": p.display_name,
                    "username": p.username,
                    "avatar": p.avatar_url,
                }
                for p in profiles
            ],
        }


def google_enabled() -> bool:
    return bool(os.getenv("OAUTH_GOOGLE_CLIENT_ID") and os.getenv("OAUTH_GOOGLE_CLIENT_SECRET"))


def google_authorize_url(*, redirect_uri: str, state: str) -> str:
    params = {
        "client_id": os.getenv("OAUTH_GOOGLE_CLIENT_ID", ""),
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
    }
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)


async def google_exchange_code(*, code: str, redirect_uri: str) -> dict[str, Any] | None:
    client_id = os.getenv("OAUTH_GOOGLE_CLIENT_ID", "")
    client_secret = os.getenv("OAUTH_GOOGLE_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        return None
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            token_res = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            token_res.raise_for_status()
            tokens = token_res.json()
            access = tokens.get("access_token")
            if not access:
                return None
            ui = await client.get(
                "https://openidconnect.googleapis.com/v1/userinfo",
                headers={"Authorization": f"Bearer {access}"},
            )
            ui.raise_for_status()
            return ui.json()
    except Exception:
        logger.exception("Google OAuth exchange failed")
        return None


def dev_login_enabled() -> bool:
    return os.getenv("OAUTH_DEV_LOGIN", "false").lower() in ("1", "true", "yes")
