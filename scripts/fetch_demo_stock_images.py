#!/usr/bin/env python3
"""Download free stock photos for coffee + food demo catalogs.

Sources: Unsplash (https://unsplash.com/license) — free to use for demos.
Images land in ``tests/test-data/`` as ``stock-*.jpg`` for ``local:`` media proxy.

  python scripts/fetch_demo_stock_images.py
  python scripts/fetch_demo_stock_images.py --force
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
TEST_DATA = _ROOT / "tests" / "test-data"

# (filename, unsplash photo path, description)
# Direct CDN URLs with fixed size for catalog tiles.
STOCK: list[tuple[str, str, str]] = [
    # Coffee
    (
        "stock-coffee-latte.jpg",
        "https://images.unsplash.com/photo-1561882468-9110e03e0f78?w=900&h=900&fit=crop&q=80",
        "latte art",
    ),
    (
        "stock-coffee-espresso.jpg",
        "https://images.unsplash.com/photo-1510591509098-f4fdc6d0ff04?w=900&h=900&fit=crop&q=80",
        "espresso shot",
    ),
    (
        "stock-coffee-cold.jpg",
        "https://images.unsplash.com/photo-1517701604599-bb29b565090c?w=900&h=900&fit=crop&q=80",
        "cold brew iced",
    ),
    (
        "stock-coffee-matcha.jpg",
        "https://images.unsplash.com/photo-1536256263959-770b48d82b0a?w=900&h=900&fit=crop&q=80",
        "matcha latte",
    ),
    (
        "stock-coffee-tea.jpg",
        "https://images.unsplash.com/photo-1571934811356-5cc061b6821f?w=900&h=900&fit=crop&q=80",
        "thai iced tea style",
    ),
    (
        "stock-coffee-croissant.jpg",
        "https://images.unsplash.com/photo-1555507036-ab1f4038808a?w=900&h=900&fit=crop&q=80",
        "croissant pastry",
    ),
    (
        "stock-coffee-banana.jpg",
        "https://images.unsplash.com/photo-1606313564200-e75d5e30476c?w=900&h=900&fit=crop&q=80",
        "banana bread",
    ),
    (
        "stock-coffee-beans.jpg",
        "https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=900&h=900&fit=crop&q=80",
        "coffee beans bag",
    ),
    (
        "stock-coffee-logo.jpg",
        "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=900&h=900&fit=crop&q=80",
        "cafe ambiance logo",
    ),
    # Food / Thai kitchen
    (
        "stock-food-padthai.jpg",
        "https://images.unsplash.com/photo-1559314809-0d155014e29e?w=900&h=900&fit=crop&q=80",
        "pad thai noodles",
    ),
    (
        "stock-food-curry.jpg",
        "https://images.unsplash.com/photo-1455619452474-d2be8b1e70cd?w=900&h=900&fit=crop&q=80",
        "thai curry bowl",
    ),
    (
        "stock-food-rice.jpg",
        "https://images.unsplash.com/photo-1603133872878-684f208fb84b?w=900&h=900&fit=crop&q=80",
        "fried rice basil",
    ),
    (
        "stock-food-salad.jpg",
        "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=900&h=900&fit=crop&q=80",
        "fresh salad / papaya style",
    ),
    (
        "stock-food-rolls.jpg",
        "https://images.unsplash.com/photo-1544025162-d76694265947?w=900&h=900&fit=crop&q=80",
        "spring rolls",
    ),
    (
        "stock-food-drink.jpg",
        "https://images.unsplash.com/photo-1556679343-c7306c1976bc?w=900&h=900&fit=crop&q=80",
        "iced drink",
    ),
    (
        "stock-food-coconut.jpg",
        "https://images.unsplash.com/photo-1587049352846-4a222e784d38?w=900&h=900&fit=crop&q=80",
        "coconut water",
    ),
    (
        "stock-food-dessert.jpg",
        "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=900&h=900&fit=crop&q=80",
        "mango sticky / dessert",
    ),
    (
        "stock-food-icecream.jpg",
        "https://images.unsplash.com/photo-1497034825429-c343d7c6a68f?w=900&h=900&fit=crop&q=80",
        "ice cream scoop",
    ),
    (
        "stock-food-logo.jpg",
        "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=900&h=900&fit=crop&q=80",
        "kitchen grill logo",
    ),
    (
        "stock-food-water.jpg",
        "https://images.unsplash.com/photo-1548839140-29a749e1cf4d?w=900&h=900&fit=crop&q=80",
        "bottled water",
    ),
]

UA = "TelegramShopPhysical-DemoSeed/1.0 (demo catalog; Unsplash free license)"


def download_one(filename: str, url: str, *, force: bool = False) -> Path | None:
    TEST_DATA.mkdir(parents=True, exist_ok=True)
    path = TEST_DATA / filename
    if path.is_file() and path.stat().st_size > 5000 and not force:
        logging.info("skip existing %s (%s bytes)", filename, path.stat().st_size)
        return path
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = resp.read()
            ctype = resp.headers.get("Content-Type", "")
    except (urllib.error.URLError, TimeoutError) as e:
        logging.error("download failed %s: %s", filename, e)
        return None
    if len(data) < 2000:
        logging.error("too small %s (%s bytes) ctype=%s", filename, len(data), ctype)
        return None
    # basic jpeg/png magic
    if not (data[:3] == b"\xff\xd8\xff" or data[:8] == b"\x89PNG\r\n\x1a\n" or data[:4] == b"RIFF"):
        logging.warning("unexpected magic for %s ctype=%s head=%r", filename, ctype, data[:12])
    path.write_bytes(data)
    logging.info("wrote %s (%s bytes)", path.name, len(data))
    return path


def main() -> int:
    p = argparse.ArgumentParser(description="Fetch free stock images for coffee/food demos.")
    p.add_argument("--force", action="store_true", help="Re-download even if present.")
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    ok, fail = 0, 0
    for name, url, desc in STOCK:
        logging.info("fetch %s (%s)", name, desc)
        if download_one(name, url, force=args.force):
            ok += 1
        else:
            fail += 1
    print({"ok": ok, "failed": fail, "dir": str(TEST_DATA)})
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
