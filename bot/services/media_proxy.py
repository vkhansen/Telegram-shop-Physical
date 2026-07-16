"""Catalog media proxy (CARD-38 Phase B).

Resolves Telegram ``file_id`` values that appear on public catalog entities
(brand logo, store menu image, category cover, goods images) to cached bytes
served under ``/media/...``.

Private media (payment slips, delivery proof, chat photos) is never allowlisted.
"""

from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path

import httpx

from bot.config import EnvKeys
from bot.database.main import Database
from bot.database.models.main import BotConfig, Brand, Categories, Goods, Store

logger = logging.getLogger(__name__)

# Default cache under project data/
_DEFAULT_CACHE = Path(os.getenv("WEB_MEDIA_CACHE_DIR", "data/media_cache"))


def media_public_base() -> str:
    """Base URL for absolute media links in catalog JSON (no trailing slash)."""
    base = os.getenv("PUBLIC_MEDIA_BASE_URL") or os.getenv("PUBLIC_API_BASE") or ""
    if base:
        return base.rstrip("/")
    host = EnvKeys.MONITORING_HOST or "localhost"
    if host in ("0.0.0.0", ""):
        host = "localhost"
    return f"http://{host}:{EnvKeys.MONITORING_PORT}"


def media_url_for(file_id: str | None, *, brand_id: int | None = None) -> str | None:
    """Public relative/absolute URL for a catalog file_id, or None."""
    if not file_id:
        return None
    # Opaque token: brand-scoped when known (helps multi-bot token pick)
    token = _encode_token(file_id, brand_id)
    return f"{media_public_base()}/media/{token}"


def _encode_token(file_id: str, brand_id: int | None) -> str:
    """URL-safe token: hex(sha256(file_id)) + optional brand suffix (not secret, just routing)."""
    digest = hashlib.sha256(file_id.encode("utf-8")).hexdigest()[:40]
    if brand_id is not None:
        return f"{digest}-b{brand_id}"
    return digest


def _decode_brand_id(token: str) -> int | None:
    if "-b" in token:
        try:
            return int(token.rsplit("-b", 1)[-1])
        except ValueError:
            return None
    return None


def _cache_dir() -> Path:
    d = Path(os.getenv("WEB_MEDIA_CACHE_DIR", str(_DEFAULT_CACHE)))
    d.mkdir(parents=True, exist_ok=True)
    return d


def is_catalog_file_id(file_id: str, brand_id: int | None = None) -> bool:
    """True if file_id is referenced by public catalog fields for an active brand."""
    with Database().session() as s:
        # Brand logos
        q = s.query(Brand).filter(Brand.is_active.is_(True), Brand.logo_file_id == file_id)
        if brand_id is not None:
            q = q.filter(Brand.id == brand_id)
        if q.first() is not None:
            return True

        # Store menu images
        q = (
            s.query(Store)
            .join(Brand, Store.brand_id == Brand.id)
            .filter(Store.is_active.is_(True), Brand.is_active.is_(True), Store.menu_image_file_id == file_id)
        )
        if brand_id is not None:
            q = q.filter(Store.brand_id == brand_id)
        if q.first() is not None:
            return True

        # Category covers
        q = s.query(Categories).filter(Categories.image_file_id == file_id)
        if brand_id is not None:
            q = q.filter((Categories.brand_id == brand_id) | (Categories.brand_id.is_(None)))
        if q.first() is not None:
            return True

        # Goods primary image
        q = s.query(Goods).filter(Goods.image_file_id == file_id)
        if brand_id is not None:
            q = q.filter((Goods.brand_id == brand_id) | (Goods.brand_id.is_(None)))
        g0 = q.first()
        if g0 is not None and getattr(g0, "web_listable", True):
            return True

        # Goods gallery JSON — scan goods with media
        goods = s.query(Goods).filter(Goods.media.isnot(None))
        if brand_id is not None:
            goods = goods.filter((Goods.brand_id == brand_id) | (Goods.brand_id.is_(None)))
        for g in goods.limit(500):
            if not getattr(g, "web_listable", True):
                continue
            if not g.media or not isinstance(g.media, list):
                continue
            for m in g.media:
                if isinstance(m, dict) and m.get("file_id") == file_id:
                    return True
    return False


def resolve_file_id_from_token(token: str) -> tuple[str | None, int | None]:
    """
    Map URL token back to file_id by scanning allowlisted catalog media.
    Returns (file_id, brand_id_hint).
    """
    brand_hint = _decode_brand_id(token)
    digest = token.split("-b")[0]

    candidates: list[tuple[str, int | None]] = []
    with Database().session() as s:
        brands = s.query(Brand).filter(Brand.is_active.is_(True), Brand.logo_file_id.isnot(None))
        if brand_hint is not None:
            brands = brands.filter(Brand.id == brand_hint)
        for b in brands:
            if b.logo_file_id:
                candidates.append((b.logo_file_id, b.id))

        stores = (
            s.query(Store, Brand)
            .join(Brand, Store.brand_id == Brand.id)
            .filter(Store.is_active.is_(True), Brand.is_active.is_(True), Store.menu_image_file_id.isnot(None))
        )
        if brand_hint is not None:
            stores = stores.filter(Store.brand_id == brand_hint)
        for st, br in stores:
            if st.menu_image_file_id:
                candidates.append((st.menu_image_file_id, br.id))

        cats = s.query(Categories).filter(Categories.image_file_id.isnot(None))
        if brand_hint is not None:
            cats = cats.filter((Categories.brand_id == brand_hint) | (Categories.brand_id.is_(None)))
        for c in cats:
            if c.image_file_id:
                candidates.append((c.image_file_id, c.brand_id))

        goods = s.query(Goods).filter(Goods.web_listable.is_(True))
        if brand_hint is not None:
            goods = goods.filter((Goods.brand_id == brand_hint) | (Goods.brand_id.is_(None)))
        for g in goods:
            if g.image_file_id:
                candidates.append((g.image_file_id, g.brand_id))
            if g.media and isinstance(g.media, list):
                for m in g.media:
                    if isinstance(m, dict) and m.get("file_id"):
                        candidates.append((m["file_id"], g.brand_id))

    for fid, bid in candidates:
        if hashlib.sha256(fid.encode("utf-8")).hexdigest()[:40] == digest:
            return fid, bid if bid is not None else brand_hint
    return None, brand_hint


def bot_token_for_brand(brand_id: int | None) -> str | None:
    if brand_id is not None:
        with Database().session() as s:
            cfg = (
                s.query(BotConfig)
                .filter(BotConfig.brand_id == brand_id, BotConfig.is_active.is_(True))
                .one_or_none()
            )
            if cfg and cfg.bot_token and not cfg.bot_token.startswith("placeholder"):
                return cfg.bot_token
    return EnvKeys.TOKEN


async def fetch_telegram_file(file_id: str, brand_id: int | None) -> tuple[bytes, str] | None:
    """Download file bytes from Telegram. Returns (bytes, content_type) or None."""
    token = bot_token_for_brand(brand_id)
    if not token:
        logger.warning("No bot token for media brand_id=%s", brand_id)
        return None

    cache = _cache_dir()
    cache_key = hashlib.sha256(f"{brand_id}:{file_id}".encode()).hexdigest()
    meta_path = cache / f"{cache_key}.meta"
    bin_path = cache / f"{cache_key}.bin"

    if bin_path.exists() and meta_path.exists():
        ctype = meta_path.read_text(encoding="utf-8").strip() or "application/octet-stream"
        return bin_path.read_bytes(), ctype

    api = f"https://api.telegram.org/bot{token}"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(f"{api}/getFile", params={"file_id": file_id})
            r.raise_for_status()
            body = r.json()
            if not body.get("ok"):
                logger.warning("getFile failed: %s", body)
                return None
            file_path = body["result"]["file_path"]
            url = f"https://api.telegram.org/file/bot{token}/{file_path}"
            fr = await client.get(url)
            fr.raise_for_status()
            data = fr.content
            # Guess content type from path
            lower = file_path.lower()
            if lower.endswith(".png"):
                ctype = "image/png"
            elif lower.endswith(".webp"):
                ctype = "image/webp"
            elif lower.endswith((".jpg", ".jpeg")):
                ctype = "image/jpeg"
            elif lower.endswith(".gif"):
                ctype = "image/gif"
            else:
                ctype = fr.headers.get("content-type", "application/octet-stream")
            bin_path.write_bytes(data)
            meta_path.write_text(ctype, encoding="utf-8")
            return data, ctype
    except Exception:
        logger.exception("Telegram media download failed file_id=%s", file_id[:20])
        return None


async def get_media_bytes(token: str) -> tuple[bytes, str] | None:
    """Resolve URL token → cached catalog media bytes."""
    file_id, brand_id = resolve_file_id_from_token(token)
    if not file_id:
        return None
    if not is_catalog_file_id(file_id, brand_id):
        logger.warning("Rejected non-catalog media token=%s", token[:16])
        return None
    return await fetch_telegram_file(file_id, brand_id)
