#!/usr/bin/env python3
"""Deploy-safe database migration runner.

Decides between *stamping* and *upgrading* so that Alembic can be introduced
to a database that was originally built with ``Base.metadata.create_all()``:

  - No ``alembic_version`` table, but app tables already exist  → the DB predates
    Alembic (legacy create_all). Its schema already matches the baseline, so we
    ``stamp head`` to adopt it without re-creating tables.
  - No ``alembic_version`` table and no app tables             → fresh DB. Run
    ``upgrade head`` to build the schema from migrations.
  - ``alembic_version`` table present                          → normal case.
    Run ``upgrade head`` to apply any new migrations.

Idempotent: safe to run on every container start.
"""

import logging
import os
import sys

# Ensure the project root is importable regardless of how this script is invoked
# (`python scripts/migrate.py` otherwise only puts scripts/ on sys.path).
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from sqlalchemy import inspect  # noqa: E402

from bot.database.main import Database  # noqa: E402

# Sentinel tables that exist in any schema built from the app models.
_SENTINEL_TABLES = {"users", "roles", "goods"}


def run() -> None:
    inspector = inspect(Database().engine)
    tables = set(inspector.get_table_names())

    cfg = Config(os.path.join(_PROJECT_ROOT, "alembic.ini"))

    if "alembic_version" in tables:
        logging.info("alembic_version present — running 'upgrade head'")
        command.upgrade(cfg, "head")
    elif tables & _SENTINEL_TABLES:
        logging.info("Existing schema without alembic_version (legacy create_all) — stamping 'head' to adopt it")
        command.stamp(cfg, "head")
    else:
        logging.info("Fresh database — running 'upgrade head'")
        command.upgrade(cfg, "head")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    run()
