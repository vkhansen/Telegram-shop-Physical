"""
JSON Menu Loader for E2E tests.

Loads a restaurant menu from a JSON file and populates the database
with Categories and Goods (including modifiers).
"""
import json
import logging
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from bot.database.models.main import Categories, Goods

logger = logging.getLogger(__name__)

# Required top-level keys
_REQUIRED_TOP_KEYS = {"restaurant_name", "categories"}

# Required keys per category entry
_REQUIRED_CATEGORY_KEYS = {"name", "sort_order", "items"}

# Required keys per item entry
_REQUIRED_ITEM_KEYS = {"name", "description", "price", "stock_quantity"}

# Required keys for a modifier group
_REQUIRED_MODIFIER_GROUP_KEYS = {"label", "type", "required", "options"}

# Required keys per modifier option
_REQUIRED_OPTION_KEYS = {"id", "label", "price"}


class MenuValidationError(Exception):
    """Raised when the menu JSON fails schema validation."""


def validate_menu_schema(data: dict) -> list[str]:
    """
    Validate the menu JSON structure.

    Returns a list of error messages. An empty list means the schema is valid.
    """
    errors: list[str] = []

    # Top-level keys
    for key in _REQUIRED_TOP_KEYS:
        if key not in data:
            errors.append(f"Missing required top-level key: '{key}'")

    if "categories" not in data:
        return errors

    if not isinstance(data["categories"], list):
        errors.append("'categories' must be a list")
        return errors

    seen_category_names: set[str] = set()

    for ci, cat in enumerate(data["categories"]):
        cat_label = f"categories[{ci}]"

        if not isinstance(cat, dict):
            errors.append(f"{cat_label}: must be a dict")
            continue

        for key in _REQUIRED_CATEGORY_KEYS:
            if key not in cat:
                errors.append(f"{cat_label}: missing required key '{key}'")

        cat_name = cat.get("name", f"<unnamed-{ci}>")
        if cat_name in seen_category_names:
            errors.append(f"{cat_label}: duplicate category name '{cat_name}'")
        seen_category_names.add(cat_name)

        if not isinstance(cat.get("sort_order", 0), int):
            errors.append(f"{cat_label}: 'sort_order' must be an integer")

        items = cat.get("items", [])
        if not isinstance(items, list):
            errors.append(f"{cat_label}: 'items' must be a list")
            continue

        seen_item_names: set[str] = set()

        for ii, item in enumerate(items):
            item_label = f"{cat_label}.items[{ii}]"

            if not isinstance(item, dict):
                errors.append(f"{item_label}: must be a dict")
                continue

            for key in _REQUIRED_ITEM_KEYS:
                if key not in item:
                    errors.append(f"{item_label}: missing required key '{key}'")

            item_name = item.get("name", f"<unnamed-{ii}>")
            if item_name in seen_item_names:
                errors.append(f"{item_label}: duplicate item name '{item_name}' within category")
            seen_item_names.add(item_name)

            # Price must be a number
            price = item.get("price")
            if price is not None and not isinstance(price, (int, float)):
                errors.append(f"{item_label}: 'price' must be a number")

            # Stock must be a non-negative integer
            stock = item.get("stock_quantity")
            if stock is not None:
                if not isinstance(stock, int) or stock < 0:
                    errors.append(f"{item_label}: 'stock_quantity' must be a non-negative integer")

            # Validate modifiers if present
            modifiers = item.get("modifiers")
            if modifiers is not None and modifiers is not False:
                if not isinstance(modifiers, dict):
                    errors.append(f"{item_label}: 'modifiers' must be a dict or null")
                    continue

                for group_key, group in modifiers.items():
                    group_label = f"{item_label}.modifiers.{group_key}"

                    if not isinstance(group, dict):
                        errors.append(f"{group_label}: must be a dict")
                        continue

                    for key in _REQUIRED_MODIFIER_GROUP_KEYS:
                        if key not in group:
                            errors.append(f"{group_label}: missing required key '{key}'")

                    if group.get("type") not in ("single", "multi"):
                        errors.append(f"{group_label}: 'type' must be 'single' or 'multi'")

                    if not isinstance(group.get("required", False), bool):
                        errors.append(f"{group_label}: 'required' must be a boolean")

                    options = group.get("options", [])
                    if not isinstance(options, list):
                        errors.append(f"{group_label}: 'options' must be a list")
                        continue

                    if len(options) == 0:
                        errors.append(f"{group_label}: 'options' must not be empty")

                    seen_option_ids: set[str] = set()
                    for oi, opt in enumerate(options):
                        opt_label = f"{group_label}.options[{oi}]"
                        if not isinstance(opt, dict):
                            errors.append(f"{opt_label}: must be a dict")
                            continue

                        for key in _REQUIRED_OPTION_KEYS:
                            if key not in opt:
                                errors.append(f"{opt_label}: missing required key '{key}'")

                        opt_id = opt.get("id")
                        if opt_id in seen_option_ids:
                            errors.append(f"{opt_label}: duplicate option id '{opt_id}'")
                        if opt_id is not None:
                            seen_option_ids.add(opt_id)

                        opt_price = opt.get("price")
                        if opt_price is not None and not isinstance(opt_price, (int, float)):
                            errors.append(f"{opt_label}: 'price' must be a number")

    return errors


def load_menu_from_dict(data: dict, session: Session, *, clear_existing: bool = False) -> dict[str, Any]:
    """
    Load a menu dict into the database.

    Args:
        data: Parsed menu JSON dict.
        session: SQLAlchemy session.
        clear_existing: If True, delete all existing Categories and Goods first.

    Returns:
        Summary dict with counts: {"categories": int, "items": int, "restaurant_name": str}

    Raises:
        MenuValidationError: If the JSON schema is invalid.
    """
    errors = validate_menu_schema(data)
    if errors:
        raise MenuValidationError(
            f"Menu JSON validation failed with {len(errors)} error(s):\n" +
            "\n".join(f"  - {e}" for e in errors)
        )

    if clear_existing:
        # Delete goods first (FK dependency), then categories
        session.query(Goods).delete()
        session.query(Categories).delete()
        session.flush()

    category_count = 0
    item_count = 0

    for cat_data in data["categories"]:
        cat_name = cat_data["name"]
        sort_order = cat_data.get("sort_order", 0)

        # Create category
        category = Categories(name=cat_name, sort_order=sort_order)
        session.add(category)
        session.flush()  # Ensure PK is available for FK references
        category_count += 1

        for item_data in cat_data.get("items", []):
            modifiers = item_data.get("modifiers")
            # Normalise null/None modifiers
            if modifiers is None:
                modifiers_value = None
            else:
                modifiers_value = modifiers

            goods = Goods(
                name=item_data["name"],
                price=Decimal(str(item_data["price"])),
                description=item_data["description"],
                category_name=cat_name,
                stock_quantity=item_data.get("stock_quantity", 0),
            )
            # Set modifiers via attribute (not in __init__ since it uses **kw)
            goods.modifiers = modifiers_value
            goods.reserved_quantity = 0

            session.add(goods)
            item_count += 1

    session.flush()

    return {
        "restaurant_name": data.get("restaurant_name", "Unknown"),
        "categories": category_count,
        "items": item_count,
    }


def load_menu_from_file(file_path: str | Path, session: Session,
                        *, clear_existing: bool = False) -> dict[str, Any]:
    """
    Load a menu from a JSON file path.

    Args:
        file_path: Path to the JSON file.
        session: SQLAlchemy session.
        clear_existing: If True, delete existing data first.

    Returns:
        Summary dict from load_menu_from_dict.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Menu file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return load_menu_from_dict(data, session, clear_existing=clear_existing)
