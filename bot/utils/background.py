"""Helpers for fire-and-forget background tasks.

The event loop only keeps weak references to tasks, so a task created with
``asyncio.create_task`` can be garbage-collected before it finishes if nothing
holds a strong reference (see ruff RUF006). ``track_task`` keeps that reference
alive until the task completes.
"""

import asyncio
from typing import Any

_background_tasks: set[asyncio.Task[Any]] = set()


def track_task(task: asyncio.Task[Any]) -> asyncio.Task[Any]:
    """Keep a strong reference to ``task`` until it completes, then drop it."""
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    return task
