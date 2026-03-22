"""xAI Grok API client for admin assistant (Card 17)."""

import logging

import aiohttp

from bot.config.env import EnvKeys

logger = logging.getLogger(__name__)

GROK_API_URL = "https://api.x.ai/v1/chat/completions"


async def call_grok(
    messages: list[dict],
    tools: list[dict],
    model: str | None = None,
) -> dict:
    """Call the Grok API with conversation history and tool definitions."""
    model = model or EnvKeys.GROK_MODEL
    timeout = aiohttp.ClientTimeout(total=int(EnvKeys.GROK_TIMEOUT))

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

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(GROK_API_URL, json=payload, headers=headers) as resp:
            if resp.status != 200:
                body = await resp.text()
                logger.error("Grok API error %s: %s", resp.status, body[:500])
                raise RuntimeError(f"Grok API returned {resp.status}")
            return await resp.json()
