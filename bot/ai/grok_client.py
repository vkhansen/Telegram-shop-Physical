"""xAI Grok API client for admin assistant (Card 17)."""

import logging

import aiohttp

from bot.config.env import EnvKeys

logger = logging.getLogger(__name__)

GROK_API_URL = "https://api.x.ai/v1/chat/completions"

# Module-level reusable aiohttp session for Grok API requests
_grok_session: aiohttp.ClientSession | None = None


async def _get_grok_session() -> aiohttp.ClientSession:
    """Get or create the module-level aiohttp session for Grok API."""
    global _grok_session
    if _grok_session is None or _grok_session.closed:
        timeout = aiohttp.ClientTimeout(total=int(EnvKeys.GROK_TIMEOUT))
        _grok_session = aiohttp.ClientSession(timeout=timeout)
    return _grok_session


async def call_grok(
    messages: list[dict],
    tools: list[dict],
    model: str | None = None,
) -> dict:
    """Call the Grok API with conversation history and tool definitions."""
    model = model or EnvKeys.GROK_MODEL

    payload = {
        "model": model,
        "messages": messages,
        "tools": tools,
        "tool_choice": "auto",
        "temperature": 0.1,
    }

    headers = {
        "Authorization": f"Bearer {EnvKeys.GROK_API_KEY}",
        "Content-Type": "application/json",
    }

    session = await _get_grok_session()
    async with session.post(GROK_API_URL, json=payload, headers=headers) as resp:
        if resp.status != 200:
            body = await resp.text()
            logger.error("Grok API error %s: %s", resp.status, body[:500])
            raise RuntimeError(f"Grok API returned {resp.status}")
        return await resp.json()


async def close_grok_session() -> None:
    """Close the shared aiohttp session. Call during bot shutdown."""
    global _grok_session
    if _grok_session and not _grok_session.closed:
        await _grok_session.close()
        _grok_session = None
        logger.info("Grok aiohttp session closed")
