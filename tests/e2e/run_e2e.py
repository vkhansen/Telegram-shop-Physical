#!/usr/bin/env python3
"""
E2E test runner for the Telegram Shop Bot.

Sets up an in-memory SQLite database, loads the sample menu,
creates test users, and runs the full E2E test suite via pytest.

Usage:
    python -m tests.e2e.run_e2e          # from project root
    python tests/e2e/run_e2e.py          # direct invocation
"""
import os
import sys
import time

# ---------------------------------------------------------------------------
# 1. Set environment variables BEFORE any bot imports
# ---------------------------------------------------------------------------
os.environ.setdefault("TOKEN", "test_token_123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ")
os.environ.setdefault("OWNER_ID", "123456789")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("LOG_TO_STDOUT", "0")
os.environ.setdefault("LOG_TO_FILE", "0")
os.environ.setdefault("TESTING", "1")

# ---------------------------------------------------------------------------
# 2. Ensure project root is on sys.path
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def _pre_flight_check():
    """Quick sanity check that core imports work."""
    print("[run_e2e] Pre-flight: importing core modules ...")
    from bot.database.main import Database          # noqa: F401
    from bot.database.models.main import Role       # noqa: F401
    from tests.e2e.menu_loader import load_menu_from_file  # noqa: F401
    print("[run_e2e] Pre-flight: OK")


def _setup_database():
    """
    Create tables in an in-memory SQLite database and seed with
    the sample menu + default roles so the test suite has a baseline.
    """
    from sqlalchemy import create_engine, event
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    from bot.database.main import Database
    from bot.database.models.main import Role, Categories, Goods

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    @event.listens_for(engine, "connect")
    def _set_pragma(dbapi_conn, _):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Database.BASE.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    session = SessionLocal()

    # Insert default roles
    session.add(Role(name="USER", permissions=1))
    session.add(Role(name="ADMIN", permissions=31))
    session.add(Role(name="OWNER", permissions=127))
    session.commit()

    # Load sample menu
    from tests.e2e.menu_loader import load_menu_from_file
    from pathlib import Path

    menu_path = Path(__file__).parent / "sample_menu.json"
    summary = load_menu_from_file(menu_path, session)
    session.commit()
    session.close()

    print(f"[run_e2e] Database seeded: {summary}")
    return engine


def main():
    """Entry point: validate environment, then delegate to pytest."""
    start = time.time()
    print("=" * 60)
    print("  Telegram Shop Bot - E2E Test Runner")
    print("=" * 60)

    _pre_flight_check()

    # We do NOT need to set up the DB here because conftest.py
    # already creates a fresh in-memory DB per test function.
    # This runner simply invokes pytest with the right arguments.

    import pytest

    # Build pytest arguments
    test_dir = os.path.dirname(os.path.abspath(__file__))
    args = [
        test_dir,           # test directory
        "-v",               # verbose
        "--tb=short",       # short tracebacks
        "-x",               # stop on first failure
        "--no-header",      # cleaner output
        "-q",               # quieter (combined with -v gives balanced output)
    ]

    # Allow extra args from CLI (e.g., -k "TestMenuLoading")
    if len(sys.argv) > 1:
        args.extend(sys.argv[1:])

    print(f"\n[run_e2e] Running: pytest {' '.join(args)}\n")
    exit_code = pytest.main(args)

    elapsed = time.time() - start
    print(f"\n{'=' * 60}")
    print(f"  Completed in {elapsed:.1f}s  |  Exit code: {exit_code}")
    print(f"{'=' * 60}")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
