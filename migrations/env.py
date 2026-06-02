"""Alembic migration environment for Telegram-shop-Physical.

URL precedence:
  1. ``ALEMBIC_DSN`` env var (used for offline autogenerate against a scratch DB)
  2. the application's own ``dsn()`` (Postgres in Docker / DATABASE_URL locally)

``target_metadata`` is the live application metadata, so ``--autogenerate``
diffs real models against the connected database.
"""
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Import the application's declarative Base and register every model on its
# metadata (the star-import in bot.database.models triggers table registration).
from bot.database.main import Database
import bot.database.models  # noqa: F401  -- registers all tables on Database.BASE.metadata
from bot.database.dsn import dsn

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Database.BASE.metadata


def _url() -> str:
    return os.getenv("ALEMBIC_DSN") or dsn()


def run_migrations_offline() -> None:
    context.configure(
        url=_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    section = config.get_section(config.config_ini_section, {})
    section["sqlalchemy.url"] = _url()
    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
