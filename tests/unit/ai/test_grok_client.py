"""Tests for Grok API client session management (Card 17)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp

import bot.ai.grok_client as client_module
from bot.ai.grok_client import close_grok_session


class TestCloseGrokSession:
    """Tests for close_grok_session() — cleanup of the module-level aiohttp session."""

    @pytest.mark.asyncio
    async def test_closes_open_session(self):
        """An open session is closed when close_grok_session() is called."""
        mock_session = AsyncMock(spec=aiohttp.ClientSession)
        mock_session.closed = False

        saved = client_module._grok_session
        try:
            client_module._grok_session = mock_session
            await close_grok_session()
        finally:
            client_module._grok_session = saved

        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_is_none_after_close(self):
        """Module-level _grok_session is set to None after closing."""
        mock_session = AsyncMock(spec=aiohttp.ClientSession)
        mock_session.closed = False

        saved = client_module._grok_session
        try:
            client_module._grok_session = mock_session
            await close_grok_session()
            assert client_module._grok_session is None
        finally:
            client_module._grok_session = saved

    @pytest.mark.asyncio
    async def test_safe_when_no_session(self):
        """Does not raise when _grok_session is None."""
        saved = client_module._grok_session
        try:
            client_module._grok_session = None
            await close_grok_session()  # Must not raise
        finally:
            client_module._grok_session = saved

    @pytest.mark.asyncio
    async def test_safe_when_session_already_closed(self):
        """Does not call close() a second time when session.closed is True."""
        mock_session = AsyncMock(spec=aiohttp.ClientSession)
        mock_session.closed = True

        saved = client_module._grok_session
        try:
            client_module._grok_session = mock_session
            await close_grok_session()  # Must not raise
        finally:
            client_module._grok_session = saved

        mock_session.close.assert_not_called()
