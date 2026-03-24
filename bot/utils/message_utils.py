"""Utility helpers for Telegram message sending / editing.

Centralises the repeated ``if from_callback: edit_text else: answer`` pattern
and the TelegramBadRequest "message is not modified" guard.
"""

from __future__ import annotations

import logging
from typing import Union

from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest

logger = logging.getLogger(__name__)


async def send_or_edit(
    target: Message,
    text: str,
    reply_markup=None,
    *,
    edit: bool = False,
    **kwargs,
) -> Message:
    """Send a new message **or** edit an existing one.

    Parameters
    ----------
    target:
        The ``Message`` object to operate on (typically ``call.message``).
    text:
        Message text (HTML).
    reply_markup:
        Optional keyboard markup.
    edit:
        When *True* and *target* supports ``edit_text``, the existing message
        is edited in-place.  Otherwise a new message is sent via ``answer``.
    **kwargs:
        Passed through to the underlying aiogram method (e.g. ``parse_mode``).
    """
    if edit and hasattr(target, "edit_text"):
        return await target.edit_text(text, reply_markup=reply_markup, **kwargs)
    return await target.answer(text, reply_markup=reply_markup, **kwargs)


async def safe_edit_text(
    message: Message,
    text: str,
    reply_markup=None,
    **kwargs,
) -> bool:
    """Edit message text, silently ignoring "message is not modified" errors.

    Returns *True* if the edit succeeded, *False* if the message was already
    identical.  Re-raises any other ``TelegramBadRequest``.
    """
    try:
        await message.edit_text(text, reply_markup=reply_markup, **kwargs)
        return True
    except TelegramBadRequest as exc:
        if "message is not modified" in str(exc):
            return False
        raise
