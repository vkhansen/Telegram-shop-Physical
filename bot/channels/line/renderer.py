"""LINE text + quick-reply helpers (CARD-16)."""

from __future__ import annotations

from typing import Any


def quick_reply_item(label: str, text: str | None = None) -> dict[str, Any]:
    """Message-action quick reply (user taps → sends text)."""
    t = (text or label or "OK")[:300]
    lab = (label or "OK")[:20]
    return {
        "type": "action",
        "action": {"type": "message", "label": lab, "text": t},
    }


def postback_item(label: str, data: str, display: str | None = None) -> dict[str, Any]:
    lab = (label or "OK")[:20]
    return {
        "type": "action",
        "action": {
            "type": "postback",
            "label": lab,
            "data": (data or "noop")[:300],
            "displayText": (display or lab)[:300],
        },
    }


def main_menu_items() -> list[dict[str, Any]]:
    return [
        postback_item("Menu", "LN_MENU", "Menu"),
        postback_item("Cart", "LN_CART", "Cart"),
        postback_item("Orders", "LN_ORDERS", "My orders"),
        postback_item("Support", "LN_SUPPORT", "Support"),
        postback_item("Help", "LN_HELP", "Help"),
    ]


def checkout_items() -> list[dict[str, Any]]:
    return [
        postback_item("Checkout", "LN_CHECKOUT", "Checkout"),
        postback_item("Menu", "LN_MENU", "Menu"),
        postback_item("Cancel", "LN_CANCEL", "Cancel"),
    ]


def payment_items() -> list[dict[str, Any]]:
    return [
        postback_item("Cash", "LN_PAY_CASH", "Cash"),
        postback_item("PromptPay", "LN_PAY_PROMPTPAY", "PromptPay"),
        postback_item("Cancel", "LN_CANCEL", "Cancel"),
    ]


def text_message(text: str, *, quick_items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    msg: dict[str, Any] = {"type": "text", "text": (text or "")[:5000]}
    if quick_items:
        msg["quickReply"] = {"items": quick_items[:13]}
    return msg


def welcome_text(brand_name: str | None = None) -> str:
    shop = brand_name or "our shop"
    return (
        f"Welcome to {shop} on LINE.\n\n"
        "Browse the menu, add items, checkout, check orders, or open support.\n"
        "Advanced features (live tracking, kitchen ops) are on Telegram."
    )


def ops_denied_text() -> str:
    return (
        "Admin, kitchen, and driver tools are only available on Telegram. "
        "This LINE chat is for customer shopping and support."
    )


def cap_denied_text(feature: str) -> str:
    return (
        f"Sorry — {feature} isn't available on LINE for this shop. "
        "Try another option from the menu, or open the full experience on Telegram."
    )
