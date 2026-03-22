"""AI image generation for menu items via xAI Grok API (Card 17).

Uses the xAI images endpoint to generate food photos from item descriptions.
Generated images are uploaded to Telegram to obtain a file_id, then saved
to the Goods model.
"""

import asyncio
import base64
import logging
import uuid
from functools import partial

import aiohttp
from aiogram import Bot
from aiogram.types import BufferedInputFile

from bot.config.env import EnvKeys
from bot.database import Database
from bot.database.models.main import Goods

logger = logging.getLogger(__name__)

GROK_IMAGE_URL = "https://api.x.ai/v1/images/generations"
IMAGE_MODEL = "grok-2-image"

# Module-level reusable aiohttp session for image generation requests
_image_session: aiohttp.ClientSession | None = None


async def _get_image_session() -> aiohttp.ClientSession:
    """Get or create the module-level aiohttp session."""
    global _image_session
    if _image_session is None or _image_session.closed:
        timeout = aiohttp.ClientTimeout(total=60)
        _image_session = aiohttp.ClientSession(timeout=timeout)
    return _image_session


def _build_prompt(item_name: str, description: str, category: str) -> str:
    """Build an image generation prompt from item details."""
    return (
        f"Professional food photography of \"{item_name}\": {description}. "
        f"Category: {category}. "
        f"Shot from above on a clean plate, restaurant quality, "
        f"natural lighting, appetizing presentation, no text or watermarks."
    )


async def generate_image(prompt: str) -> bytes:
    """Call xAI image generation API and return image bytes.

    Returns PNG bytes of the generated image.
    """
    headers = {
        "Authorization": f"Bearer {EnvKeys.GROK_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": IMAGE_MODEL,
        "prompt": prompt,
        "n": 1,
        "size": "1024x1024",
        "response_format": "b64_json",
    }

    session = await _get_image_session()
    async with session.post(GROK_IMAGE_URL, json=payload, headers=headers) as resp:
        if resp.status != 200:
            body = await resp.text()
            logger.error("Image generation error %s: %s", resp.status, body[:500])
            raise RuntimeError(f"Image generation API returned {resp.status}")
        data = await resp.json()

    b64_data = data["data"][0]["b64_json"]
    return base64.b64decode(b64_data)


async def generate_and_save_item_image(
    bot: Bot,
    chat_id: int,
    item_name: str,
    description: str,
    category: str,
) -> dict:
    """Generate an AI image for a menu item, upload to Telegram, save file_id.

    Args:
        bot: Telegram Bot instance (needed to upload photo and get file_id)
        chat_id: Admin's chat ID (photo is sent here for preview)
        item_name: Name of the menu item
        description: Item description (used as generation prompt)
        category: Item category (adds context to the prompt)

    Returns:
        dict with success status and file_id
    """
    prompt = _build_prompt(item_name, description, category)

    try:
        image_bytes = await generate_image(prompt)
    except Exception as e:
        logger.error("Failed to generate image for '%s': %s", item_name, e)
        return {"error": f"Image generation failed for '{item_name}': {e}"}

    # Upload to Telegram by sending to admin chat — this gives us a file_id
    photo = BufferedInputFile(image_bytes, filename=f"{item_name}.png")
    msg = await bot.send_photo(
        chat_id=chat_id,
        photo=photo,
        caption=f"AI-generated image for: {item_name}",
    )

    file_id = msg.photo[-1].file_id
    media_id = str(uuid.uuid4())[:8]

    # Save to media array in database (run sync DB call in executor)
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None, partial(_add_media_entry, item_name, file_id, True, media_id)
    )

    logger.info("Generated and saved AI image for '%s' (media_id=%s)", item_name, media_id)
    return {"success": True, "item": item_name, "file_id": file_id, "media_id": media_id}


def get_items_missing_images() -> list[dict]:
    """Return all active menu items that have no images (neither image_file_id nor media)."""
    with Database().session() as s:
        items = s.query(Goods).filter(
            Goods.is_active.is_(True),
            Goods.image_file_id.is_(None),
        ).order_by(Goods.category_name, Goods.name).all()

        result = []
        for g in items:
            # Also skip items that already have media entries
            if g.media and isinstance(g.media, list) and len(g.media) > 0:
                continue
            result.append({
                "name": g.name,
                "description": g.description,
                "category_name": g.category_name,
            })
        return result


def _add_media_entry(
    item_name: str,
    file_id: str,
    is_ai_generated: bool = False,
    media_id: str | None = None,
    media_type: str = "photo",
    caption: str | None = None,
) -> str:
    """Add a media entry to an item's media array.

    Returns the media_id of the added entry.
    """
    media_id = media_id or str(uuid.uuid4())[:8]
    entry = {
        "id": media_id,
        "file_id": file_id,
        "type": media_type,
        "is_ai_generated": is_ai_generated,
    }
    if caption:
        entry["caption"] = caption

    with Database().session() as s:
        goods = s.query(Goods).filter(Goods.name == item_name).first()
        if not goods:
            raise ValueError(f"Item '{item_name}' not found")

        media_list = list(goods.media) if goods.media and isinstance(goods.media, list) else []
        media_list.append(entry)
        goods.media = media_list

        # Also set image_file_id if it's the first image (for backward compat)
        if not goods.image_file_id:
            goods.image_file_id = file_id

        s.commit()

    return media_id


def remove_media_entry(item_name: str, media_id: str) -> dict:
    """Remove a specific media entry from an item by its media_id.

    Returns the removed entry or error.
    """
    with Database().session() as s:
        goods = s.query(Goods).filter(Goods.name == item_name).first()
        if not goods:
            return {"error": f"Item '{item_name}' not found"}

        media_list = list(goods.media) if goods.media and isinstance(goods.media, list) else []

        # Find and remove the entry
        removed = None
        new_list = []
        for entry in media_list:
            if entry.get("id") == media_id:
                removed = entry
            else:
                new_list.append(entry)

        if not removed:
            return {"error": f"Media '{media_id}' not found on item '{item_name}'"}

        goods.media = new_list if new_list else None

        # Update image_file_id: set to first remaining image, or clear
        remaining_photos = [e for e in new_list if e.get("type") == "photo"]
        if remaining_photos:
            goods.image_file_id = remaining_photos[0]["file_id"]
        elif removed.get("file_id") == goods.image_file_id:
            goods.image_file_id = None

        s.commit()

    return {"success": True, "removed": removed}


def list_item_media(item_name: str) -> dict:
    """List all media entries for an item."""
    with Database().session() as s:
        goods = s.query(Goods).filter(Goods.name == item_name).first()
        if not goods:
            return {"error": f"Item '{item_name}' not found"}

        media_list = goods.media if goods.media and isinstance(goods.media, list) else []

        entries = []
        for entry in media_list:
            entries.append({
                "id": entry.get("id", "legacy"),
                "type": entry.get("type", "photo"),
                "is_ai_generated": entry.get("is_ai_generated", False),
                "caption": entry.get("caption"),
            })

        return {
            "item": item_name,
            "image_count": len(entries),
            "images": entries,
            "has_primary": goods.image_file_id is not None,
        }
