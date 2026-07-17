import asyncio
import logging
import os
import runpy
from pathlib import Path

if __name__ == "__main__":
    try:
        # Funnel / storefront testing without a valid Telegram bot token.
        # Set WEB_API_ONLY=1 to serve /health, /api/public/*, /media/* only.
        if os.getenv("WEB_API_ONLY", "").lower() in ("1", "true", "yes"):
            logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
            logging.getLogger(__name__).info(
                "WEB_API_ONLY=1 — starting public HTTP API (no Telegram polling)"
            )
            runpy.run_path(str(Path(__file__).resolve().parent / "scripts" / "run_public_api.py"), run_name="__main__")
        else:
            from bot import start_bot

            asyncio.run(start_bot())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped.")
