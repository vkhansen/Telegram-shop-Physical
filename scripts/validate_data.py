#!/usr/bin/env python3
"""Validate the live database's brand / store / menu data integrity.

Runs every check in bot.database.integrity and prints a report. Exits non-zero
when ERROR-level violations exist (so it can gate CI / deploys). Use
--strict to also fail on warnings.

    python scripts/validate_data.py
    python scripts/validate_data.py --strict
"""

import argparse
import logging
import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from bot.database.integrity import Severity, check_integrity, summarize  # noqa: E402
from bot.database.main import Database  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description="Validate database data integrity.")
    p.add_argument("--strict", action="store_true", help="Exit non-zero on warnings too.")
    args = p.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    with Database().session() as session:
        violations = check_integrity(session)

    for v in violations:
        log = logging.error if v.severity is Severity.ERROR else logging.warning
        log("%s", v)

    s = summarize(violations)
    logging.info("Integrity: %d error(s), %d warning(s)", s["errors"], s["warnings"])
    if s["errors"] or (args.strict and s["warnings"]):
        return 1
    logging.info("Data integrity OK ✅")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
