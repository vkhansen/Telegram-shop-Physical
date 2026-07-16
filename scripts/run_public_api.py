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
from decimal import Decimal
from pathlib import Path

# project root on path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from aiohttp import web

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("public_api")


def seed_demo_if_empty() -> None:
    from bot.database.main import Database
    from bot.database.models.main import Brand, Categories, Goods, Role, Store

    with Database().session() as s:
        if s.query(Brand).first() is not None:
            return
        if s.query(Role).filter_by(name="USER").first() is None:
            s.add(Role(name="USER", permissions=1))
        brand = Brand(
            name="Demo Brand",
            slug="demo",
            description="White-label demo storefront — Instagram-like grid.",
            legal_name="Demo Brand Co., Ltd.",
            dbd_number="0105550000000",
            support_email="hello@demo.local",
            support_phone="+66812345678",
            commerce_mode="hybrid",
            age_gate_enabled=False,
            web_profile={
                "schema_version": 1,
                "tagline": "Clean kicks · Desktop & mobile",
                "about": {"title": "About Demo", "body_md": "Demo brand for local white-label testing."},
                "compliance": {"footer_warnings": ["Demo environment only."]},
                "modules": {"show_lead_form": True, "show_booking": True},
            },
        )
        s.add(brand)
        s.flush()
        store = Store(
            name="Main Branch",
            slug="main",
            brand_id=brand.id,
            address="123 Demo Road, Bangkok",
            phone="+66812345678",
            latitude=13.7563,
            longitude=100.5018,
            is_default=True,
            is_active=True,
        )
        s.add(store)
        s.add(Categories(name="Featured", brand_id=brand.id, sort_order=1))
        s.flush()
        for i, (name, price) in enumerate(
            [("Aurora Mint", "120"), ("Citrus Wave", "130"), ("Berry Night", "140"), ("Coffee Ember", "125")],
            start=1,
        ):
            s.add(
                Goods(
                    name=name,
                    price=Decimal(price),
                    description=f"Demo product {name}.",
                    category_name="Featured",
                    brand_id=brand.id,
                    item_type="prepared",
                    is_active=True,
                )
            )
        s.commit()
        logger.info("Seeded demo brand slug=demo store=main")


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
    if not os.environ.get("DATABASE_URL") and not os.environ.get("POSTGRES_DB"):
        os.environ.setdefault("DATABASE_URL", f"sqlite:///{ROOT / 'data' / 'local_public.db'}")
        os.environ.setdefault("TOKEN", "000000000:LOCAL-DEV-TOKEN-NOT-FOR-PRODUCTION")
        os.environ.setdefault("OWNER_ID", "1")
        (ROOT / "data").mkdir(exist_ok=True)
        logger.info("Using local SQLite %s", os.environ["DATABASE_URL"])

    asyncio.run(main())
