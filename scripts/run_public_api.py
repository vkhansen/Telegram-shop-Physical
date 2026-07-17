"""Local public catalog/auth API for storefront development (CARD-38/39).

Starts aiohttp on MONITORING_PORT with:
  /api/public/*  catalog + auth + tickets + leads
  /media/*       catalog media proxy
  /health

Does not start Telegram polling. Uses project Database config.
Seeds a demo brand if none exist.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

# project root on path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from aiohttp import web

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("public_api")


def seed_demo_if_empty() -> None:
    """Ensure NOVA-style snus demo (tests/test-data images) is present.

    Set SEED_SNUS_FORCE=1 to refresh web_profile, lineup, and local media paths.
    """
    from bot.services.seed_snus_demo import seed_snus_demo

    force = os.getenv("SEED_SNUS_FORCE", "").lower() in ("1", "true", "yes")
    summary = seed_snus_demo(force=force)
    logger.info("Snus demo seed: %s", summary)


async def main() -> None:
    # Ensure tables exist (create_all for local sqlite/dev; production uses alembic)
    from bot.config import EnvKeys
    from bot.database.main import Database
    from bot.database.models.main import register_models
    from bot.web.public_api import register_public_catalog_routes

    register_models()
    try:
        Database.BASE.metadata.create_all(Database().engine)
        logger.info("Database tables ensured via create_all")
    except Exception as e:
        logger.warning("create_all failed (%s); ensure migrations applied", e)

    seed_demo_if_empty()
    app = web.Application()
    register_public_catalog_routes(app)

    async def health(_request: web.Request) -> web.Response:
        return web.json_response({"status": "ok", "service": "public_api"})

    app.router.add_get("/health", health)

    host = os.getenv("MONITORING_HOST", "0.0.0.0")
    port = int(os.getenv("MONITORING_PORT", EnvKeys.MONITORING_PORT or 9090))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    logger.info("Public API listening on http://%s:%s", host if host != "0.0.0.0" else "127.0.0.1", port)
    logger.info("  Catalog: http://127.0.0.1:%s/api/public/brands", port)
    logger.info("  Health:  http://127.0.0.1:%s/health", port)
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    # Defaults for local demo
    os.environ.setdefault("OAUTH_DEV_LOGIN", "true")
    os.environ.setdefault("WEB_SESSION_SECRET", "local-dev-session-secret")
    os.environ.setdefault("PUBLIC_SITE_URL", "http://127.0.0.1:4321")
    os.environ.setdefault("MONITORING_HOST", "0.0.0.0")
    os.environ.setdefault("MONITORING_PORT", "9090")
    # Enable web cart/checkout on snus-demo (Telegram C-08–C-14 parity). Override with portfolio.
    os.environ.setdefault("SEED_SNUS_COMMERCE_MODE", "full_store")
    if not os.environ.get("DATABASE_URL") and not os.environ.get("POSTGRES_DB"):
        os.environ.setdefault("DATABASE_URL", f"sqlite:///{ROOT / 'data' / 'local_public.db'}")
        os.environ.setdefault("TOKEN", "000000000:LOCAL-DEV-TOKEN-NOT-FOR-PRODUCTION")
        os.environ.setdefault("OWNER_ID", "1")
        (ROOT / "data").mkdir(exist_ok=True)
        logger.info("Using local SQLite %s", os.environ["DATABASE_URL"])

    asyncio.run(main())
