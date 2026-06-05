import asyncio
import contextlib
from collections.abc import Coroutine
from typing import Any

from bot.utils.background import track_task


def safe_create_task(coro: Coroutine[Any, Any, None]) -> None:
    """
    Safely create an async task for cache invalidation.
    Works both in async context (with event loop) and sync context (tests).
    """
    try:
        # Try to get the running event loop
        loop = asyncio.get_running_loop()
        # If we have a loop, create task as usual (tracked so it isn't GC'd)
        track_task(loop.create_task(coro))
    except RuntimeError:
        # No event loop running (probably in tests)
        # Run the coroutine in a new event loop
        with contextlib.suppress(RuntimeError):
            # If asyncio.run() also fails (nested event loop), just ignore
            # This is fire-and-forget for cache invalidation anyway
            asyncio.run(coro)
