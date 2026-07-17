"""LINE text, quick-reply, and Flex helpers (CARD-16)."""

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


def image_message(url: str, *, preview_url: str | None = None) -> dict[str, Any]:
    u = (url or "").strip()
    return {
        "type": "image",
        "originalContentUrl": u,
        "previewImageUrl": (preview_url or u).strip(),
    }


def flex_bubble(
    *,
    title: str,
    body_lines: list[str],
    footer_actions: list[dict[str, Any]] | None = None,
    alt_text: str | None = None,
    hero_url: str | None = None,
) -> dict[str, Any]:
    """Simple vertical bubble (header + body + optional buttons)."""
    contents: list[dict[str, Any]] = []
    for line in body_lines[:20]:
        contents.append(
            {
                "type": "text",
                "text": str(line)[:500],
                "wrap": True,
                "size": "sm",
                "color": "#333333",
            }
        )
    body: dict[str, Any] = {
        "type": "box",
        "layout": "vertical",
        "spacing": "sm",
        "contents": contents
        or [{"type": "text", "text": " ", "size": "sm"}],
    }
    bubble: dict[str, Any] = {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": (title or "Shop")[:40],
                    "weight": "bold",
                    "size": "md",
                    "color": "#FFFFFF",
                }
            ],
            "backgroundColor": "#1DB446",
            "paddingAll": "12px",
        },
        "body": body,
    }
    if hero_url:
        bubble["hero"] = {
            "type": "image",
            "url": hero_url,
            "size": "full",
            "aspectRatio": "1:1",
            "aspectMode": "cover",
        }
    if footer_actions:
        buttons = []
        for act in footer_actions[:4]:
            # act is postback/message action dict or quick-reply item
            action = act.get("action") if isinstance(act, dict) and "action" in act else act
            if not isinstance(action, dict):
                continue
            buttons.append(
                {
                    "type": "button",
                    "style": "primary" if len(buttons) == 0 else "secondary",
                    "height": "sm",
                    "action": action,
                }
            )
        if buttons:
            bubble["footer"] = {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": buttons,
                "flex": 0,
            }
    return {
        "type": "flex",
        "altText": (alt_text or title or "Message")[:400],
        "contents": bubble,
    }


def menu_flex(
    brand_name: str,
    item_lines: list[str],
    *,
    quick_items: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    lines = item_lines[:18] if item_lines else ["No items listed yet."]
    msg = flex_bubble(
        title=brand_name or "Menu",
        body_lines=lines,
        footer_actions=[
            postback_item("Cart", "LN_CART", "Cart"),
            postback_item("Checkout", "LN_CHECKOUT", "Checkout"),
        ],
        alt_text=f"Menu — {brand_name or 'shop'}",
    )
    if quick_items:
        msg["quickReply"] = {"items": quick_items[:13]}
    return msg


def payment_qr_flex(
    *,
    order_code: str,
    amount: str,
    promptpay_id: str,
    qr_image_url: str | None,
) -> dict[str, Any]:
    body = [
        f"Order: {order_code}",
        f"Amount: {amount}",
        f"PromptPay: {promptpay_id}",
        "Scan QR or transfer, then upload slip via Telegram/web if needed.",
    ]
    return flex_bubble(
        title="PromptPay",
        body_lines=body,
        hero_url=qr_image_url,
        footer_actions=[postback_item("Orders", "LN_ORDERS", "Orders")],
        alt_text=f"PromptPay {amount} for {order_code}",
    )


def order_confirm_flex(
    *,
    order_code: str,
    payment_method: str,
    amount: str,
) -> dict[str, Any]:
    return flex_bubble(
        title="Order placed",
        body_lines=[
            f"Code: {order_code}",
            f"Payment: {payment_method}",
            f"Total: {amount}",
            "Kitchen will prepare after payment is confirmed.",
        ],
        footer_actions=[
            postback_item("Orders", "LN_ORDERS", "Orders"),
            postback_item("Menu", "LN_MENU", "Menu"),
        ],
        alt_text=f"Order {order_code} placed",
    )


def welcome_text(brand_name: str | None = None) -> str:
    shop = brand_name or "our shop"
    return (
        f"Welcome to {shop} on LINE.\n\n"
        "Browse the menu, add items, checkout, check orders, or open support.\n"
        "Advanced features (live tracking, kitchen ops) are on Telegram."
    )


def welcome_flex(brand_name: str | None = None) -> dict[str, Any]:
    shop = brand_name or "our shop"
    return flex_bubble(
        title=shop,
        body_lines=[
            "Browse the menu, cart, and checkout here.",
            "Live tracking and ops stay on Telegram.",
        ],
        footer_actions=main_menu_items()[:4],
        alt_text=f"Welcome to {shop}",
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
