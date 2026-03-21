"""
Menu modifier utilities for restaurant items (Card 8).

Handles modifier validation and price calculation for items
with customization options (spice level, extras, removals).
"""
from decimal import Decimal
from typing import Optional


def calculate_item_price(base_price: Decimal, modifiers_schema: Optional[dict],
                         selected_modifiers: Optional[dict]) -> Decimal:
    """
    Calculate total item price including modifier adjustments.

    Args:
        base_price: Base price of the item
        modifiers_schema: Modifier definition from Goods.modifiers
        selected_modifiers: User's selected choices

    Returns:
        Total price (base + modifier surcharges)
    """
    base_price = Decimal(str(base_price))

    if not modifiers_schema or not selected_modifiers:
        return base_price

    modifier_total = Decimal(0)

    for group_key, selection in selected_modifiers.items():
        group = modifiers_schema.get(group_key)
        if not group:
            continue

        options = group.get("options", [])

        if isinstance(selection, list):
            # Multi-choice: sum all selected option prices
            for opt_id in selection:
                opt = _find_option(options, opt_id)
                if opt:
                    modifier_total += Decimal(str(opt.get("price", 0)))
        else:
            # Single-choice
            opt = _find_option(options, selection)
            if opt:
                modifier_total += Decimal(str(opt.get("price", 0)))

    return base_price + modifier_total


def validate_modifier_selection(modifiers_schema: Optional[dict],
                                selected_modifiers: Optional[dict]) -> tuple[bool, str]:
    """
    Validate that selected modifiers match the schema.

    Returns:
        (is_valid, error_message)
    """
    if not modifiers_schema:
        return True, ""

    if not selected_modifiers:
        selected_modifiers = {}

    for group_key, group in modifiers_schema.items():
        required = group.get("required", False)
        selection = selected_modifiers.get(group_key)

        if required and not selection:
            label = group.get("label", group_key)
            return False, f"Required modifier '{label}' not selected"

        if selection:
            options = group.get("options", [])
            valid_ids = {opt["id"] for opt in options}

            if isinstance(selection, list):
                for opt_id in selection:
                    if opt_id not in valid_ids:
                        return False, f"Invalid option '{opt_id}' in '{group_key}'"
            else:
                if selection not in valid_ids:
                    return False, f"Invalid option '{selection}' in '{group_key}'"

    return True, ""


def _find_option(options: list, opt_id: str) -> Optional[dict]:
    """Find option by ID in options list."""
    for opt in options:
        if opt.get("id") == opt_id:
            return opt
    return None
