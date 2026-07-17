#!/usr/bin/env python3
"""Fetch live brand pages and print theme CSS vars (paper/ink contrast smoke)."""
from __future__ import annotations

import re
import sys
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "https://telegram-shop-1.tail31319c.ts.net"
SLUGS = ["coffee-demo", "food-demo", "herb-demo", "bakery-demo", "grocery-demo", "snus-demo"]


def grab(style: str, key: str) -> str:
    m = re.search(re.escape(key) + r":([^;]+)", style)
    return m.group(1).strip() if m else "?"


def main() -> int:
    for slug in SLUGS:
        url = f"{BASE.rstrip('/')}/{slug}"
        try:
            with urllib.request.urlopen(url, timeout=25) as resp:
                text = resp.read().decode("utf-8", "replace")
        except Exception as e:
            print(f"{slug}: FAIL {e}")
            continue
        m = re.search(r'<html[^>]*style="([^"]+)"', text)
        style = m.group(1) if m else ""
        mode = "light" if "theme-light" in text else "dark"
        print(
            f"{slug:14} mode={mode:5} "
            f"paper={grab(style, '--brand-paper'):10} "
            f"ink={grab(style, '--brand-ink'):10} "
            f"sun={grab(style, '--brand-sun'):10} "
            f"on_accent={grab(style, '--brand-on-accent')}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
