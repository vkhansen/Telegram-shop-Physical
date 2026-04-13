"""
E2E smoke tests — fast sanity checks for the real stack.

These verify the bot package imports cleanly and core models/metadata
are reachable. They do NOT boot Telegram polling or external services.

Run with:
    pytest tests/e2e/test_smoke.py --run-e2e
or:
    scripts/test/run.ps1 -Suite e2e
"""
from __future__ import annotations

import importlib

import pytest

pytestmark = [pytest.mark.e2e, pytest.mark.smoke]


def test_bot_package_imports() -> None:
    """Core bot package must import without side-effect failures."""
    mod = importlib.import_module("bot")
    assert mod is not None


def test_database_models_load() -> None:
    """Models registered on the shared metadata must include core tables."""
    from bot.database.main import Database
    from bot.database.models.main import Goods, Order, ShoppingCart, User  # noqa: F401

    table_names = set(Database.BASE.metadata.tables.keys())
    # Core tables that must exist in the real stack
    assert "users" in table_names or any("user" in t for t in table_names)
    assert any("goods" in t or "product" in t for t in table_names)
    assert any("order" in t for t in table_names)
    assert any("cart" in t for t in table_names)


def test_inmemory_schema_creates(db_engine) -> None:
    """The in-memory SQLite schema from tests/conftest.py builds cleanly."""
    from bot.database.main import Database

    # db_engine fixture (from tests/conftest.py) already ran create_all.
    inspector_tables = Database.BASE.metadata.tables
    assert len(inspector_tables) > 0


def test_sample_menu_fixture_exists() -> None:
    """The e2e sample menu shipped alongside the suite must be present."""
    from pathlib import Path

    sample = Path(__file__).parent / "sample_menu.json"
    assert sample.exists(), f"Missing e2e fixture: {sample}"
    assert sample.stat().st_size > 0
