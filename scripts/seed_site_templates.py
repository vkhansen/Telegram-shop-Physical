#!/usr/bin/env python3
"""Seed white-label demo brands for local / Docker multi-user testing.

Templates
---------
  snus     — NOVA-style nicotine editorial (landing_editorial)
  food     — Thai multi-branch kitchen
  coffee   — specialty café (modifiers + retail beans)
  herb     — adult herb demo (age gate 21, hybrid CTAs)
  bakery   — bakery with daily limits
  grocery  — mini-mart branch inventory
  verticals — all non-snus verticals
  all      — snus + every vertical (default)

Examples
--------
  python scripts/seed_site_templates.py
  python scripts/seed_site_templates.py --template coffee --force
  python scripts/seed_site_templates.py --template all --force --snus-mode full_store
  python scripts/seed_site_templates.py --placeholders-only
"""

from __future__ import annotations

import argparse
import logging
import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

VERTICAL_KEYS = ("food", "coffee", "herb", "bakery", "grocery")
CHOICES = ("all", "snus", "verticals", *VERTICAL_KEYS)


def main() -> int:
    p = argparse.ArgumentParser(description="Seed multi-vertical white-label demo brands.")
    p.add_argument(
        "--template",
        choices=CHOICES,
        default="all",
        help="Which pack to seed (default: all).",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Refresh web_profile, goods flags, store fields, inventory overrides.",
    )
    p.add_argument(
        "--snus-mode",
        choices=("portfolio", "hybrid", "full_store"),
        default=None,
        help="Override SEED_SNUS_COMMERCE_MODE for snus.",
    )
    p.add_argument(
        "--placeholders-only",
        action="store_true",
        help="Only generate ph-*.png clipart under tests/test-data/.",
    )
    p.add_argument(
        "--force-placeholders",
        action="store_true",
        help="Regenerate placeholder PNGs even if they exist.",
    )
    args = p.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    from bot.services.demo_placeholders import ensure_all_placeholders

    names = ensure_all_placeholders(force=args.force_placeholders)
    logging.info("Placeholders ready: %s files", len(names))

    # Free stock photos for coffee/food (Unsplash license) — best-effort
    try:
        sys.path.insert(0, _PROJECT_ROOT)
        from scripts.fetch_demo_stock_images import STOCK, download_one

        stock_ok = 0
        for fname, url, _desc in STOCK:
            if download_one(fname, url, force=args.force_placeholders):
                stock_ok += 1
        logging.info("Stock photos ready: %s / %s", stock_ok, len(STOCK))
    except Exception as e:
        logging.warning("Stock photo fetch skipped: %s", e)

    if args.placeholders_only:
        print({"ok": True, "placeholders": names})
        return 0

    if args.snus_mode:
        os.environ["SEED_SNUS_COMMERCE_MODE"] = args.snus_mode
    else:
        os.environ.setdefault("SEED_SNUS_COMMERCE_MODE", "full_store")

    results: list = []

    if args.template in ("all", "snus"):
        from bot.services.seed_snus_demo import seed_snus_demo

        summary = seed_snus_demo(force=args.force)
        logging.info("snus: %s", summary)
        results.append(summary)

    if args.template == "all" or args.template == "verticals":
        from bot.services.seed_demo_verticals import seed_all_verticals

        for summary in seed_all_verticals(force=args.force):
            logging.info("%s: %s", summary.get("slug"), summary)
            results.append(summary)
    elif args.template in VERTICAL_KEYS:
        from bot.services.seed_demo_verticals import seed_named_vertical

        summary = seed_named_vertical(args.template, force=args.force)
        logging.info("%s: %s", summary.get("slug"), summary)
        results.append(summary)

    print(
        {
            "ok": True,
            "count": len(results),
            "slugs": [r.get("slug") for r in results],
            "templates": results,
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
