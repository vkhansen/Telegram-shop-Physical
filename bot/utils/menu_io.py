import json
import os
import shutil
from pathlib import Path
from datetime import datetime
from decimal import Decimal
from typing import Optional

from bot.database.main import Database
from bot.database.models.main import Categories, Goods
from bot.logger_mesh import logger


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal types."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def export_menu_to_json(output_dir: str = None) -> str:
    """
    Export entire menu (categories + items) to JSON + images folder.

    Args:
        output_dir: Output directory path. Defaults to menu_export_{timestamp}

    Returns:
        Path to the created export directory
    """
    if not output_dir:
        output_dir = f"menu_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    os.makedirs(output_dir, exist_ok=True)
    images_dir = os.path.join(output_dir, "images")
    os.makedirs(images_dir, exist_ok=True)

    menu_data = {
        "version": "2.0",
        "exported_at": datetime.now().isoformat(),
        "currency": None,  # Will be set from EnvKeys
        "categories": [],
        "items": []
    }

    # Set currency
    from bot.config.env import EnvKeys
    menu_data["currency"] = EnvKeys.PAY_CURRENCY

    with Database().session() as session:
        # Export categories
        categories = session.query(Categories).order_by(Categories.sort_order).all()
        for cat in categories:
            cat_data = {
                "name": cat.name,
                "sort_order": cat.sort_order,
                "description": cat.description,
                "image": None,  # filename reference
                "available_from": cat.available_from,
                "available_until": cat.available_until,
            }
            # Image reference (will be downloaded separately by async function)
            if cat.image_file_id:
                filename = f"cat_{_safe_filename(cat.name)}.jpg"
                cat_data["image"] = f"images/{filename}"
                cat_data["_image_file_id"] = cat.image_file_id  # For download
            menu_data["categories"].append(cat_data)

        # Export items
        items = session.query(Goods).order_by(Goods.category_name, Goods.name).all()
        for item in items:
            item_data = {
                "name": item.name,
                "price": str(item.price),
                "description": item.description,
                "category": item.category_name,
                "stock_quantity": item.stock_quantity,
                "modifiers": item.modifiers,
                "image": None,
                "gallery": [],
                "prep_time_minutes": item.prep_time_minutes,
                "allergens": item.allergens,
                "is_active": item.is_active,
                "daily_limit": item.daily_limit,
                "available_from": item.available_from,
                "available_until": item.available_until,
                "calories": item.calories,
            }

            # Primary image reference
            if item.image_file_id:
                filename = f"item_{_safe_filename(item.name)}_main.jpg"
                item_data["image"] = f"images/{filename}"
                item_data["_image_file_id"] = item.image_file_id

            # Gallery media references
            if item.media and isinstance(item.media, list):
                for idx, m in enumerate(item.media):
                    ext = "mp4" if m.get("type") == "video" else "jpg"
                    filename = f"item_{_safe_filename(item.name)}_{idx}.{ext}"
                    item_data["gallery"].append({
                        "file": f"images/{filename}",
                        "type": m.get("type", "photo"),
                        "_file_id": m.get("file_id"),
                    })

            menu_data["items"].append(item_data)

    # Write JSON
    json_path = os.path.join(output_dir, "menu.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(menu_data, f, cls=DecimalEncoder, indent=2, ensure_ascii=False)

    logger.info(f"Menu exported to {output_dir}: {len(menu_data['categories'])} categories, {len(menu_data['items'])} items")
    return output_dir


async def download_menu_images(bot, export_dir: str) -> int:
    """
    Download all images referenced in a menu export using the Telegram Bot API.
    Must be called with a running bot instance.

    Args:
        bot: aiogram Bot instance
        export_dir: Path to the export directory containing menu.json

    Returns:
        Number of images downloaded
    """
    json_path = os.path.join(export_dir, "menu.json")
    with open(json_path, 'r', encoding='utf-8') as f:
        menu_data = json.load(f)

    images_dir = os.path.join(export_dir, "images")
    os.makedirs(images_dir, exist_ok=True)
    downloaded = 0

    # Download category images
    for cat in menu_data.get("categories", []):
        file_id = cat.get("_image_file_id")
        image_path = cat.get("image")
        if file_id and image_path:
            full_path = os.path.join(export_dir, image_path)
            try:
                file = await bot.get_file(file_id)
                await bot.download_file(file.file_path, full_path)
                downloaded += 1
            except Exception as e:
                logger.warning(f"Failed to download category image {cat['name']}: {e}")

    # Download item images
    for item in menu_data.get("items", []):
        # Primary image
        file_id = item.get("_image_file_id")
        image_path = item.get("image")
        if file_id and image_path:
            full_path = os.path.join(export_dir, image_path)
            try:
                file = await bot.get_file(file_id)
                await bot.download_file(file.file_path, full_path)
                downloaded += 1
            except Exception as e:
                logger.warning(f"Failed to download item image {item['name']}: {e}")

        # Gallery
        for media_entry in item.get("gallery", []):
            file_id = media_entry.get("_file_id")
            media_path = media_entry.get("file")
            if file_id and media_path:
                full_path = os.path.join(export_dir, media_path)
                try:
                    file = await bot.get_file(file_id)
                    await bot.download_file(file.file_path, full_path)
                    downloaded += 1
                except Exception as e:
                    logger.warning(f"Failed to download gallery media {item['name']}: {e}")

    # Remove _file_id keys from JSON (they're bot-specific)
    _strip_file_ids(menu_data)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(menu_data, f, cls=DecimalEncoder, indent=2, ensure_ascii=False)

    logger.info(f"Downloaded {downloaded} images for menu export")
    return downloaded


def import_menu_from_json(json_path: str, mode: str = "merge",
                          default_stock: int = 0) -> dict:
    """
    Import menu from JSON file. Does NOT handle images (use upload_menu_images for that).

    Args:
        json_path: Path to menu.json file
        mode: "merge" (update existing, add new) or "replace" (delete all, import fresh)
        default_stock: Default stock quantity for new items

    Returns:
        dict with counts: {"categories_created", "categories_updated", "items_created", "items_updated", "errors"}
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        menu_data = json.load(f)

    stats = {
        "categories_created": 0,
        "categories_updated": 0,
        "items_created": 0,
        "items_updated": 0,
        "items_skipped": 0,
        "errors": [],
    }

    with Database().session() as session:
        if mode == "replace":
            # Delete all existing items and categories
            session.query(Goods).delete()
            session.query(Categories).delete()
            session.flush()

        # Import categories
        for cat_data in menu_data.get("categories", []):
            try:
                existing = session.query(Categories).filter_by(name=cat_data["name"]).first()
                if existing:
                    existing.sort_order = cat_data.get("sort_order", 0)
                    existing.description = cat_data.get("description")
                    existing.available_from = cat_data.get("available_from")
                    existing.available_until = cat_data.get("available_until")
                    # image_file_id left as-is (will be set by upload_menu_images)
                    stats["categories_updated"] += 1
                else:
                    new_cat = Categories(
                        name=cat_data["name"],
                        sort_order=cat_data.get("sort_order", 0),
                        description=cat_data.get("description"),
                        available_from=cat_data.get("available_from"),
                        available_until=cat_data.get("available_until"),
                    )
                    session.add(new_cat)
                    stats["categories_created"] += 1
            except Exception as e:
                stats["errors"].append(f"Category {cat_data.get('name')}: {e}")

        session.flush()

        # Import items
        for item_data in menu_data.get("items", []):
            try:
                # Verify category exists
                cat_name = item_data.get("category", "")
                cat = session.query(Categories).filter_by(name=cat_name).first()
                if not cat:
                    stats["errors"].append(f"Item {item_data['name']}: category '{cat_name}' not found")
                    stats["items_skipped"] += 1
                    continue

                existing = session.query(Goods).filter_by(name=item_data["name"]).first()
                if existing:
                    existing.price = item_data.get("price", existing.price)
                    existing.description = item_data.get("description", existing.description)
                    existing.category_name = cat_name
                    existing.modifiers = item_data.get("modifiers")
                    existing.prep_time_minutes = item_data.get("prep_time_minutes")
                    existing.allergens = item_data.get("allergens")
                    existing.is_active = item_data.get("is_active", True)
                    existing.daily_limit = item_data.get("daily_limit")
                    existing.available_from = item_data.get("available_from")
                    existing.available_until = item_data.get("available_until")
                    existing.calories = item_data.get("calories")
                    stats["items_updated"] += 1
                else:
                    new_item = Goods(
                        name=item_data["name"],
                        price=item_data.get("price", 0),
                        description=item_data.get("description", ""),
                        category_name=cat_name,
                        stock_quantity=item_data.get("stock_quantity", default_stock),
                        prep_time_minutes=item_data.get("prep_time_minutes"),
                        allergens=item_data.get("allergens"),
                        daily_limit=item_data.get("daily_limit"),
                        available_from=item_data.get("available_from"),
                        available_until=item_data.get("available_until"),
                        calories=item_data.get("calories"),
                    )
                    if item_data.get("modifiers"):
                        new_item.modifiers = item_data["modifiers"]
                    session.add(new_item)
                    stats["items_created"] += 1
            except Exception as e:
                stats["errors"].append(f"Item {item_data.get('name')}: {e}")

        session.commit()

    logger.info(f"Menu import: {stats}")
    return stats


async def upload_menu_images(bot, json_path: str, chat_id: int) -> int:
    """
    Upload images from a menu export directory and update file_ids in the database.
    Uploads each image to a private chat (with the bot owner) to get Telegram file_ids,
    then updates the DB.

    Args:
        bot: aiogram Bot instance
        json_path: Path to menu.json
        chat_id: Telegram chat ID to upload images to (usually OWNER_ID)

    Returns:
        Number of images uploaded
    """
    from aiogram.types import FSInputFile

    base_dir = os.path.dirname(json_path)
    with open(json_path, 'r', encoding='utf-8') as f:
        menu_data = json.load(f)

    uploaded = 0

    with Database().session() as session:
        # Upload category images
        for cat_data in menu_data.get("categories", []):
            image_path = cat_data.get("image")
            if not image_path:
                continue
            full_path = os.path.join(base_dir, image_path)
            if not os.path.exists(full_path):
                continue

            try:
                msg = await bot.send_photo(chat_id, FSInputFile(full_path))
                file_id = msg.photo[-1].file_id
                cat = session.query(Categories).filter_by(name=cat_data["name"]).first()
                if cat:
                    cat.image_file_id = file_id
                uploaded += 1
                # Delete the uploaded message to keep chat clean
                try:
                    await bot.delete_message(chat_id, msg.message_id)
                except Exception:
                    pass
            except Exception as e:
                logger.warning(f"Failed to upload category image {cat_data['name']}: {e}")

        # Upload item images
        for item_data in menu_data.get("items", []):
            item = session.query(Goods).filter_by(name=item_data["name"]).first()
            if not item:
                continue

            # Primary image
            image_path = item_data.get("image")
            if image_path:
                full_path = os.path.join(base_dir, image_path)
                if os.path.exists(full_path):
                    try:
                        msg = await bot.send_photo(chat_id, FSInputFile(full_path))
                        item.image_file_id = msg.photo[-1].file_id
                        uploaded += 1
                        try:
                            await bot.delete_message(chat_id, msg.message_id)
                        except Exception:
                            pass
                    except Exception as e:
                        logger.warning(f"Failed to upload item image {item_data['name']}: {e}")

            # Gallery
            new_media = []
            for media_entry in item_data.get("gallery", []):
                media_path = media_entry.get("file")
                media_type = media_entry.get("type", "photo")
                if not media_path:
                    continue
                full_path = os.path.join(base_dir, media_path)
                if not os.path.exists(full_path):
                    continue

                try:
                    if media_type == "video":
                        msg = await bot.send_video(chat_id, FSInputFile(full_path))
                        file_id = msg.video.file_id
                    else:
                        msg = await bot.send_photo(chat_id, FSInputFile(full_path))
                        file_id = msg.photo[-1].file_id

                    new_media.append({"file_id": file_id, "type": media_type})
                    uploaded += 1
                    try:
                        await bot.delete_message(chat_id, msg.message_id)
                    except Exception:
                        pass
                except Exception as e:
                    logger.warning(f"Failed to upload gallery media {item_data['name']}: {e}")

            if new_media:
                item.media = new_media

        session.commit()

    logger.info(f"Uploaded {uploaded} images for menu import")
    return uploaded


def validate_menu_json(json_path: str) -> tuple[bool, list[str]]:
    """
    Validate a menu.json file before import.

    Returns:
        (is_valid, list_of_errors)
    """
    errors = []

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON: {e}"]
    except FileNotFoundError:
        return False, [f"File not found: {json_path}"]

    if not isinstance(data, dict):
        return False, ["Root must be a JSON object"]

    # Check required fields
    if "categories" not in data or not isinstance(data["categories"], list):
        errors.append("Missing or invalid 'categories' array")
    if "items" not in data or not isinstance(data["items"], list):
        errors.append("Missing or invalid 'items' array")

    if errors:
        return False, errors

    # Validate categories
    cat_names = set()
    for i, cat in enumerate(data["categories"]):
        if not isinstance(cat, dict):
            errors.append(f"Category [{i}] must be an object")
            continue
        if "name" not in cat or not cat["name"]:
            errors.append(f"Category [{i}] missing 'name'")
        else:
            cat_names.add(cat["name"])

    # Validate items
    for i, item in enumerate(data["items"]):
        if not isinstance(item, dict):
            errors.append(f"Item [{i}] must be an object")
            continue
        if "name" not in item or not item["name"]:
            errors.append(f"Item [{i}] missing 'name'")
        if "category" not in item:
            errors.append(f"Item [{i}] ({item.get('name', '?')}) missing 'category'")
        elif item["category"] not in cat_names:
            errors.append(f"Item [{i}] ({item.get('name', '?')}) references unknown category '{item['category']}'")
        if "price" in item:
            try:
                float(item["price"])
            except (ValueError, TypeError):
                errors.append(f"Item [{i}] ({item.get('name', '?')}) invalid price: {item['price']}")

        # Validate modifiers structure
        mods = item.get("modifiers")
        if mods and isinstance(mods, dict):
            for gk, group in mods.items():
                if not isinstance(group, dict):
                    errors.append(f"Item [{i}] modifier group '{gk}' must be an object")
                elif "options" not in group or not isinstance(group["options"], list):
                    errors.append(f"Item [{i}] modifier group '{gk}' missing 'options' array")

    # Check for image files if directory exists
    base_dir = os.path.dirname(json_path)
    missing_images = []
    for item in data.get("items", []):
        if item.get("image"):
            path = os.path.join(base_dir, item["image"])
            if not os.path.exists(path):
                missing_images.append(item["image"])
        for m in item.get("gallery", []):
            if m.get("file"):
                path = os.path.join(base_dir, m["file"])
                if not os.path.exists(path):
                    missing_images.append(m["file"])

    if missing_images:
        errors.append(f"Missing {len(missing_images)} image file(s): {', '.join(missing_images[:5])}")

    return len(errors) == 0, errors


def _safe_filename(name: str) -> str:
    """Convert a name to a safe filename."""
    import re
    safe = re.sub(r'[^\w\s-]', '', name.lower())
    safe = re.sub(r'[-\s]+', '_', safe).strip('_')
    return safe[:50]  # Limit length


def _strip_file_ids(data: dict):
    """Remove internal _file_id and _image_file_id keys from exported JSON."""
    for cat in data.get("categories", []):
        cat.pop("_image_file_id", None)
    for item in data.get("items", []):
        item.pop("_image_file_id", None)
        for m in item.get("gallery", []):
            m.pop("_file_id", None)
