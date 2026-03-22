"""AI image generation for menu items via xAI Grok API (Card 17).

Uses the xAI images endpoint to generate food photos from item descriptions.
Generated images are uploaded to Telegram to obtain a file_id, then saved
to the Goods model.
"""

import base64
import io
import logging

import aiohttp
from aiogram import Bot
from aiogram.types import BufferedInputFile

from bot.config.env import EnvKeys
from bot.database import Database
from bot.database.models.main import Goods

logger = logging.getLogger(__name__)

GROK_IMAGE_URL = "https://api.x.ai/v1/images/generations"
IMAGE_MODEL = "grok-2-image"


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
    timeout = aiohttp.ClientTimeout(total=60)
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

    async with aiohttp.ClientSession(timeout=timeout) as session:
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

    # Save to database
    with Database().session() as s:
        goods = s.query(Goods).filter(Goods.name == item_name).first()
        if goods:
            goods.image_file_id = file_id
            s.commit()
        else:
            return {"error": f"Item '{item_name}' not found in database"}

    logger.info("Generated and saved AI image for '%s'", item_name)
    return {"success": True, "item": item_name, "file_id": file_id}


def get_items_missing_images() -> list[dict]:
    """Return all active menu items that have no image_file_id."""
    with Database().session() as s:
        items = s.query(Goods).filter(
            Goods.is_active.is_(True),
            Goods.image_file_id.is_(None),
        ).order_by(Goods.category_name, Goods.name).all()
        return [
            {
                "name": g.name,
                "description": g.description,
                "category_name": g.category_name,
            }
            for g in items
        ]
