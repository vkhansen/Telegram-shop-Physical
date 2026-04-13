"""
Root conftest.py — adds the --run-e2e CLI gate.

E2E tests under tests/e2e are skipped by default so that routine
`pytest tests/` and `pytest tests/unit` runs stay fast and isolated.
Pass --run-e2e (via scripts/test/run.ps1 -Suite e2e/all) to opt in.

Unit/integration fixtures live in tests/conftest.py and are untouched.
"""
from __future__ import annotations

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-e2e",
        action="store_true",
        default=False,
        help="Run end-to-end tests under tests/e2e (skipped by default).",
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    if config.getoption("--run-e2e"):
        return

    skip_e2e = pytest.mark.skip(reason="e2e tests skipped; pass --run-e2e to enable")
    for item in items:
        # Skip by marker OR by path — tests/e2e files may lack an explicit marker.
        if "e2e" in item.keywords or "tests/e2e" in str(item.fspath).replace("\\", "/"):
            item.add_marker(skip_e2e)
