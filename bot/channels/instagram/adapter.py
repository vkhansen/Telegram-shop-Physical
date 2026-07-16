"""Instagram conversation adapter — intents → application services (CARD-33).

Capability mask: ``can("instagram", feature)`` + brand ``resolve_capabilities``.
No admin/kitchen/driver. No live location / delivery chat.
"""

from __future__ import annotations

import logging
import re
from decimal import Decimal
from typing import Any

from bot.channels.instagram.config import InstagramConfig, load_instagram_config
from bot.channels.instagram import renderer as R
from bot.channels.instagram.messenger import InstagramMessenger
from bot.channels.instagram.session import IgSession, SessionStore, default_session_store
from bot.platform.capabilities import can, cap_enabled, resolve_capabilities
from bot.platform.identity import ensure_instagram_user
from bot.platform.messaging import ButtonSpec
from bot.services import cart as cart_svc
from bot.services import catalog_public as catalog
from bot.services import checkout as checkout_svc
from bot.services import order_query
from bot.services import tickets as tickets_svc

logger = logging.getLogger(__name__)

# Payloads that map to ops — always deny on IG
_OPS_PAYLOADS = frozenset(
    {
        "IG_ADMIN",
        "ADMIN",
        "KITCHEN",
        "DRIVER",
        "BROADCAST",
        "LIVE_LOCATION",
        "DELIVERY_CHAT",
    }
)

_ADD_ITEM_RE = re.compile(r"^(?:add|buy)\s+(.+)$", re.I)


class InstagramAdapter:
    """Normalize Meta messaging events → service calls → IG replies."""

    def __init__(
        self,
        *,
        config: InstagramConfig | None = None,
        messenger: InstagramMessenger | None = None,
        sessions: SessionStore | None = None,
    ) -> None:
        self.config = config or load_instagram_config()
        self.sessions = sessions or default_session_store
        self.messenger = messenger or InstagramMessenger(
            page_access_token=self.config.page_access_token,
            graph_messages_url=self.config.graph_messages_url,
        )

    # ------------------------------------------------------------------
    # Brand / caps
    # ------------------------------------------------------------------

    def _brand_ctx(self) -> dict[str, Any] | None:
        bid = self.config.default_brand_id
        if bid is None:
            return None
        from bot.database.main import Database
        from bot.database.models.main import Brand

        with Database().session() as s:
            b = s.query(Brand).filter(Brand.id == int(bid), Brand.is_active.is_(True)).one_or_none()
            if not b:
                return None
            web = b.web_profile if isinstance(b.web_profile, dict) else {}
            return {
                "brand_id": b.id,
                "brand_slug": b.slug,
                "brand_name": b.name,
                "commerce_mode": b.commerce_mode,
                "age_gate_enabled": bool(b.age_gate_enabled),
                "web_profile": web,
                "store_id": None,
                "store_slug": None,
            }

    def _caps(self, ctx: dict[str, Any] | None) -> dict[str, bool]:
        if not ctx:
            # Platform ceiling only — no brand
            from bot.platform.capabilities import features_for

            allowed = features_for("instagram", "customer")
            return {k: (k in allowed) for k in (
                "catalog", "cart", "checkout", "order_status", "tickets",
                "payment_cash", "payment_promptpay", "location_live",
                "admin_console", "delivery_chat",
            )}
        return resolve_capabilities(
            commerce_mode=ctx.get("commerce_mode"),
            age_gate_enabled=bool(ctx.get("age_gate_enabled")),
            web_profile=ctx.get("web_profile"),
            channel="instagram",
            role="customer",
        )

    async def _reply(
        self,
        psid: str,
        text: str,
        *,
        quick_replies: list[dict[str, str]] | None = None,
    ) -> bool:
        buttons = ButtonSpec(native={"quick_replies": quick_replies}) if quick_replies else None
        return await self.messenger.send_text(psid, text, buttons=buttons)

    # ------------------------------------------------------------------
    # Inbound entry
    # ------------------------------------------------------------------

    async def handle_messaging_event(self, event: dict[str, Any]) -> None:
        sender = (event.get("sender") or {}).get("id")
        if not sender:
            return
        psid = str(sender)

        # Echo / delivery receipts
        if event.get("message", {}).get("is_echo"):
            return
        if "delivery" in event or "read" in event:
            return

        user_id = ensure_instagram_user(psid)
        sess = self.sessions.get(psid)
        ctx = self._brand_ctx()
        caps = self._caps(ctx)

        payload, text = self._extract_intent(event)

        if payload and payload.upper() in _OPS_PAYLOADS:
            await self._reply(psid, R.ops_denied_text(), quick_replies=R.main_menu_replies())
            return

        # In-progress checkout FSM takes free text
        if sess.state.startswith("checkout_"):
            await self._handle_checkout_step(psid, user_id, sess, ctx, caps, payload, text)
            return

        if sess.state == "support_wait_body":
            await self._finish_support(psid, user_id, sess, ctx, caps, text)
            return

        intent = (payload or "").upper() or self._text_to_intent(text)
        await self._dispatch(psid, user_id, sess, ctx, caps, intent, text)

    def _extract_intent(self, event: dict[str, Any]) -> tuple[str | None, str]:
        msg = event.get("message") or {}
        postback = event.get("postback") or {}
        text = (msg.get("text") or postback.get("title") or "").strip()
        payload = None
        if msg.get("quick_reply"):
            payload = (msg["quick_reply"].get("payload") or "").strip()
        if postback.get("payload"):
            payload = str(postback.get("payload")).strip()
        return payload, text

    def _text_to_intent(self, text: str) -> str:
        t = (text or "").strip().lower()
        if not t or t in ("hi", "hello", "hey", "start", "/start", "menu"):
            return "IG_HOME" if t not in ("menu",) else "IG_MENU"
        if t in ("menu", "shop", "catalog"):
            return "IG_MENU"
        if t in ("cart", "basket"):
            return "IG_CART"
        if t in ("orders", "my orders", "status"):
            return "IG_ORDERS"
        if t in ("support", "help", "ticket"):
            return "IG_SUPPORT" if t != "help" else "IG_HELP"
        if t in ("checkout", "pay"):
            return "IG_CHECKOUT"
        if t in ("cancel", "stop"):
            return "IG_CANCEL"
        if t in ("admin", "kitchen", "driver"):
            return "IG_ADMIN"
        if _ADD_ITEM_RE.match(text or ""):
            return "IG_ADD"
        return "IG_FREE_TEXT"

    async def _dispatch(
        self,
        psid: str,
        user_id: int,
        sess: IgSession,
        ctx: dict[str, Any] | None,
        caps: dict[str, bool],
        intent: str,
        text: str,
    ) -> None:
        if intent in ("IG_ADMIN", "ADMIN", "KITCHEN", "DRIVER"):
            await self._reply(psid, R.ops_denied_text(), quick_replies=R.main_menu_replies())
            return
        if intent in ("IG_HOME", "IG_HELP", ""):
            name = (ctx or {}).get("brand_name")
            extra = ""
            if intent == "IG_HELP":
                extra = (
                    "\n\nCommands: Menu · Cart · Checkout · Orders · Support\n"
                    "Add item: add <item name>\n"
                    "Live tracking & ops → Telegram only."
                )
            await self._reply(
                psid,
                R.welcome_text(name) + extra,
                quick_replies=R.main_menu_replies(),
            )
            return
        if intent == "IG_CANCEL":
            sess.reset()
            await self._reply(psid, "Cancelled. What next?", quick_replies=R.main_menu_replies())
            return
        if intent == "IG_MENU":
            await self._show_menu(psid, ctx, caps)
            return
        if intent == "IG_CART":
            await self._show_cart(psid, user_id, caps)
            return
        if intent == "IG_ORDERS":
            await self._show_orders(psid, user_id, caps)
            return
        if intent == "IG_SUPPORT":
            await self._start_support(psid, sess, caps)
            return
        if intent == "IG_CHECKOUT":
            await self._start_checkout(psid, user_id, sess, ctx, caps)
            return
        if intent == "IG_ADD" or _ADD_ITEM_RE.match(text or ""):
            await self._add_item(psid, user_id, ctx, caps, text)
            return
        if intent == "IG_FREE_TEXT":
            await self._reply(
                psid,
                "I didn't catch that. Use the buttons or try: Menu, Cart, Orders, Support.\n"
                "To add: add <item name>",
                quick_replies=R.main_menu_replies(),
            )
            return
        await self._reply(psid, R.welcome_text((ctx or {}).get("brand_name")), quick_replies=R.main_menu_replies())

    # ------------------------------------------------------------------
    # Features
    # ------------------------------------------------------------------

    async def _show_menu(self, psid: str, ctx: dict[str, Any] | None, caps: dict[str, bool]) -> None:
        if not can("instagram", "catalog") or not cap_enabled(caps, "catalog"):
            await self._reply(psid, R.cap_denied_text("menu"), quick_replies=R.main_menu_replies())
            return
        if not ctx or not ctx.get("brand_slug"):
            await self._reply(
                psid,
                "Menu is not configured (set INSTAGRAM_DEFAULT_BRAND_ID).",
                quick_replies=R.main_menu_replies(),
            )
            return
        brand = catalog.get_brand_public(ctx["brand_slug"], channel="instagram")
        if not brand:
            await self._reply(psid, "Shop unavailable right now.", quick_replies=R.main_menu_replies())
            return
        stores = brand.get("stores") or []
        store_slug = stores[0]["slug"] if stores else None
        lines = [f"📋 {brand.get('name') or 'Menu'}"]
        if store_slug:
            menu = catalog.get_store_menu(ctx["brand_slug"], store_slug)
            if menu:
                for cat in (menu.get("categories") or [])[:8]:
                    lines.append(f"\n*{cat.get('name') or 'Items'}*")
                    for it in (cat.get("items") or [])[:6]:
                        price = it.get("price")
                        name = it.get("name") or it.get("slug")
                        lines.append(f"• {name} — {price}")
                lines.append("\nAdd: add <item name>")
            else:
                lines.append("No items listed yet.")
        else:
            lines.append("No store configured.")
        await self._reply(psid, "\n".join(lines)[:1000], quick_replies=R.main_menu_replies())

    async def _add_item(
        self,
        psid: str,
        user_id: int,
        ctx: dict[str, Any] | None,
        caps: dict[str, bool],
        text: str,
    ) -> None:
        if not cap_enabled(caps, "cart") and not can("instagram", "cart"):
            await self._reply(psid, R.cap_denied_text("cart"), quick_replies=R.main_menu_replies())
            return
        m = _ADD_ITEM_RE.match(text or "")
        name = (m.group(1) if m else text or "").strip()
        if not name:
            await self._reply(psid, "Usage: add <item name>", quick_replies=R.main_menu_replies())
            return
        brand_id = (ctx or {}).get("brand_id")
        store_id = (ctx or {}).get("store_id")
        res = await cart_svc.add_item(
            user_id,
            name,
            quantity=1,
            brand_id=brand_id,
            store_id=store_id,
        )
        if not res.ok:
            await self._reply(
                psid,
                res.error_detail or res.error_key or "Could not add item.",
                quick_replies=R.main_menu_replies(),
            )
            return
        await self._reply(
            psid,
            res.data.get("message") or f"Added {name}.",
            quick_replies=R.checkout_replies(),
        )

    async def _show_cart(self, psid: str, user_id: int, caps: dict[str, bool]) -> None:
        if not can("instagram", "cart"):
            await self._reply(psid, R.cap_denied_text("cart"), quick_replies=R.main_menu_replies())
            return
        res = await cart_svc.list_items(user_id)
        if not res.ok or res.data.get("empty"):
            await self._reply(psid, "Your cart is empty.", quick_replies=R.main_menu_replies())
            return
        lines = ["🛒 Cart"]
        for it in res.data.get("items") or []:
            lines.append(f"• {it.get('item_name')} x{it.get('quantity')} = {it.get('total', it.get('price'))}")
        lines.append(f"Total: {res.data.get('total')}")
        await self._reply(psid, "\n".join(lines)[:1000], quick_replies=R.checkout_replies())

    async def _show_orders(self, psid: str, user_id: int, caps: dict[str, bool]) -> None:
        if not can("instagram", "order_status") or not cap_enabled(caps, "order_status"):
            await self._reply(psid, R.cap_denied_text("order status"), quick_replies=R.main_menu_replies())
            return
        res = order_query.list_orders(user_id, limit=5)
        if not res.ok:
            await self._reply(psid, "Could not load orders.", quick_replies=R.main_menu_replies())
            return
        orders = res.data.get("orders") or []
        if not orders:
            await self._reply(psid, "No orders yet.", quick_replies=R.main_menu_replies())
            return
        lines = ["📦 Recent orders"]
        for o in orders:
            lines.append(f"• {o.get('order_code')} — {o.get('order_status')} — {o.get('total_price')}")
        await self._reply(psid, "\n".join(lines)[:1000], quick_replies=R.main_menu_replies())

    async def _start_support(self, psid: str, sess: IgSession, caps: dict[str, bool]) -> None:
        if not can("instagram", "tickets") or not cap_enabled(caps, "tickets"):
            await self._reply(psid, R.cap_denied_text("support tickets"), quick_replies=R.main_menu_replies())
            return
        sess.state = "support_wait_body"
        await self._reply(psid, "Describe your issue in one message:", quick_replies=[R.quick_reply("Cancel", "IG_CANCEL")])

    async def _finish_support(
        self,
        psid: str,
        user_id: int,
        sess: IgSession,
        ctx: dict[str, Any] | None,
        caps: dict[str, bool],
        text: str,
    ) -> None:
        if (text or "").strip().lower() in ("cancel", "stop"):
            sess.reset()
            await self._reply(psid, "Support cancelled.", quick_replies=R.main_menu_replies())
            return
        body = (text or "").strip()
        if not body:
            await self._reply(psid, "Please send a short description of the issue.")
            return
        res = tickets_svc.create_ticket(
            user_id,
            "Instagram support",
            body,
            brand_id=(ctx or {}).get("brand_id"),
            priority="normal",
        )
        sess.reset()
        if not res.ok:
            await self._reply(
                psid,
                res.error_detail or "Could not open ticket.",
                quick_replies=R.main_menu_replies(),
            )
            return
        code = (res.data or {}).get("ticket_code") or (res.data or {}).get("code")
        await self._reply(
            psid,
            f"Ticket opened: {code}. We'll follow up here or on Telegram if linked.",
            quick_replies=R.main_menu_replies(),
        )

    async def _start_checkout(
        self,
        psid: str,
        user_id: int,
        sess: IgSession,
        ctx: dict[str, Any] | None,
        caps: dict[str, bool],
    ) -> None:
        if not can("instagram", "checkout") or not cap_enabled(caps, "checkout"):
            await self._reply(psid, R.cap_denied_text("checkout"), quick_replies=R.main_menu_replies())
            return
        cart = await cart_svc.list_items(user_id)
        if not cart.ok or cart.data.get("empty"):
            await self._reply(psid, "Cart is empty — add items first.", quick_replies=R.main_menu_replies())
            return
        sess.state = "checkout_phone"
        sess.data["cart_total"] = str(cart.data.get("total"))
        await self._reply(
            psid,
            f"Checkout (total {cart.data.get('total')}).\nSend your phone number:",
            quick_replies=[R.quick_reply("Cancel", "IG_CANCEL")],
        )

    async def _handle_checkout_step(
        self,
        psid: str,
        user_id: int,
        sess: IgSession,
        ctx: dict[str, Any] | None,
        caps: dict[str, bool],
        payload: str | None,
        text: str,
    ) -> None:
        intent = (payload or "").upper()
        if intent == "IG_CANCEL":
            sess.reset()
            await self._reply(psid, "Checkout cancelled.", quick_replies=R.main_menu_replies())
            return

        if sess.state == "checkout_phone":
            phone = (text or "").strip()
            if len(phone) < 8:
                await self._reply(psid, "Please send a valid phone number.")
                return
            sess.data["phone"] = phone
            sess.state = "checkout_address"
            await self._reply(psid, "Send your delivery address (text):")
            return

        if sess.state == "checkout_address":
            addr = (text or "").strip()
            if len(addr) < 5:
                await self._reply(psid, "Please send a fuller delivery address.")
                return
            sess.data["address"] = addr
            sess.state = "checkout_pay"
            pays = []
            if can("instagram", "payment_cash") and cap_enabled(caps, "payment_cash"):
                pays.append(R.quick_reply("Cash", "IG_PAY_CASH"))
            if can("instagram", "payment_promptpay") and cap_enabled(caps, "payment_promptpay"):
                pays.append(R.quick_reply("PromptPay", "IG_PAY_PROMPTPAY"))
            pays.append(R.quick_reply("Cancel", "IG_CANCEL"))
            await self._reply(psid, "Choose payment method:", quick_replies=pays)
            return

        if sess.state == "checkout_pay":
            pay = intent
            if pay not in ("IG_PAY_CASH", "IG_PAY_PROMPTPAY"):
                t = (text or "").strip().lower()
                if t in ("cash", "cod"):
                    pay = "IG_PAY_CASH"
                elif t in ("promptpay", "qr", "transfer"):
                    pay = "IG_PAY_PROMPTPAY"
                else:
                    await self._reply(psid, "Tap Cash or PromptPay.", quick_replies=R.payment_replies())
                    return
            await self._place_order(psid, user_id, sess, ctx, caps, pay)
            return

        sess.reset()
        await self._reply(psid, "Session reset.", quick_replies=R.main_menu_replies())

    async def _place_order(
        self,
        psid: str,
        user_id: int,
        sess: IgSession,
        ctx: dict[str, Any] | None,
        caps: dict[str, bool],
        pay_payload: str,
    ) -> None:
        cart = await cart_svc.list_items(user_id)
        if not cart.ok or cart.data.get("empty"):
            sess.reset()
            await self._reply(psid, "Cart is empty.", quick_replies=R.main_menu_replies())
            return
        items = cart.data.get("items") or []
        total = cart.data.get("total_decimal") or Decimal(str(cart.data.get("total") or 0))
        checkout_svc.ensure_delivery_profile(
            user_id,
            username=f"ig:{psid}",
            phone_number=sess.data.get("phone"),
            delivery_address=sess.data.get("address"),
            delivery_note="instagram",
        )
        brand_id = (ctx or {}).get("brand_id")
        store_id = (ctx or {}).get("store_id")
        plain_items = [
            {
                "item_name": it.get("item_name"),
                "quantity": it.get("quantity"),
                "price": it.get("price"),
                "total": it.get("total"),
                "selected_modifiers": it.get("selected_modifiers"),
            }
            for it in items
        ]

        if pay_payload == "IG_PAY_CASH":
            res = checkout_svc.start_cash_order(
                user_id,
                plain_items,
                total_amount=total,
                username=f"ig:{psid}",
                brand_id=brand_id,
                store_id=store_id,
            )
        else:
            res = checkout_svc.start_promptpay_order(
                user_id,
                plain_items,
                total_amount=total,
                username=f"ig:{psid}",
                brand_id=brand_id,
                store_id=store_id,
            )
        sess.reset()
        if not res.ok:
            await self._reply(
                psid,
                res.error_detail or res.error_key or "Order failed.",
                quick_replies=R.main_menu_replies(),
            )
            return
        code = res.data.get("order_code")
        msg = f"✅ Order {code} placed ({res.data.get('payment_method')}). Total {res.data.get('final_amount')}."
        await self._reply(psid, msg, quick_replies=R.main_menu_replies())
        if pay_payload == "IG_PAY_PROMPTPAY":
            qr = checkout_svc.build_promptpay_qr_payload(
                final_amount=res.data.get("final_amount") or total,
                order_code=str(code),
                store_id=store_id,
                brand_id=brand_id,
            )
            if qr.ok and qr.data.get("qr_bytes"):
                uri = InstagramMessenger.qr_data_uri(qr.data["qr_bytes"])
                await self.messenger.send_photo(
                    psid,
                    uri,
                    caption=f"PromptPay QR for order {code}. Upload slip in chat when paid (review on Telegram ops).",
                )
            elif qr.ok and qr.data.get("promptpay_id"):
                await self._reply(
                    psid,
                    f"Transfer PromptPay to {qr.data['promptpay_id']} amount {qr.data.get('amount')}.",
                )
