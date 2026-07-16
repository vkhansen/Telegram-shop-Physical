"""Instagram Messaging render helpers (text + quick replies).

No business rules — pure presentation for Graph API payloads.
"""

from __future__ import annotations

from typing import Any


def quick_reply(title: str, payload: str) -> dict[str, str]:
    return {
        "content_type": "text",
        "title": (title or "OK")[:20],
        "payload": (payload or "noop")[:1000],
    }


def text_message(text: str, *, quick_replies: list[dict[str, str]] | None = None) -> dict[str, Any]:
    msg: dict[str, Any] = {"text": (text or "")[:1000]}
    if quick_replies:
        msg["quick_replies"] = quick_replies[:13]
    return msg


def main_menu_replies() -> list[dict[str, str]]:
    return [
        quick_reply("Menu", "IG_MENU"),
        quick_reply("Cart", "IG_CART"),
        quick_reply("My orders", "IG_ORDERS"),
        quick_reply("Support", "IG_SUPPORT"),
        quick_reply("Help", "IG_HELP"),
    ]


def payment_replies() -> list[dict[str, str]]:
    return [
        quick_reply("Cash", "IG_PAY_CASH"),
        quick_reply("PromptPay", "IG_PAY_PROMPTPAY"),
        quick_reply("Cancel", "IG_CANCEL"),
    ]


def checkout_replies() -> list[dict[str, str]]:
    return [
        quick_reply("Checkout", "IG_CHECKOUT"),
        quick_reply("Menu", "IG_MENU"),
        quick_reply("Cancel", "IG_CANCEL"),
    ]


def welcome_text(brand_name: str | None = None) -> str:
    shop = brand_name or "our shop"
    return (
        f"Welcome to {shop} on Instagram.\n\n"
        "Browse the menu, add items, checkout, check orders, or open support.\n"
        "Advanced features (live tracking, full modifiers) are on Telegram."
    )


def ops_denied_text() -> str:
    return (
        "Admin, kitchen, and driver tools are only available on Telegram. "
        "This Instagram chat is for customer shopping and support."
    )


def cap_denied_text(feature: str) -> str:
    return (
        f"Sorry — {feature} isn't available on Instagram for this shop. "
        "Try another option from the menu, or open the full experience on Telegram."
    )
