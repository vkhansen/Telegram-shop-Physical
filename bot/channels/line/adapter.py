"""LINE conversation adapter — intents → application services (CARD-16).

Capability mask: ``can("line", feature)`` + brand ``resolve_capabilities``.
No admin/kitchen/driver. No live location.
"""

from __future__ import annotations

import logging
import re
from decimal import Decimal
from typing import Any

from bot.channels.line import renderer as R
from bot.channels.line.config import LineConfig, load_line_config
from bot.channels.line.messenger import LineMessenger
from bot.channels.line.qr_host import store_qr_png
from bot.channels.line.session import LineSession, SessionStore, default_session_store
from bot.platform.capabilities import can, cap_enabled, resolve_capabilities
from bot.platform.identity import ensure_line_user
from bot.platform.messaging import ButtonSpec
from bot.services import cart as cart_svc
from bot.services import catalog_public as catalog
from bot.services import checkout as checkout_svc
from bot.services import order_query
from bot.services import tickets as tickets_svc

logger = logging.getLogger(__name__)

_OPS_PAYLOADS = frozenset(
    {
        "LN_ADMIN",
        "ADMIN",
        "KITCHEN",
        "DRIVER",
        "BROADCAST",
        "LIVE_LOCATION",
        "DELIVERY_CHAT",
    }
)

_ADD_ITEM_RE = re.compile(r"^(?:add|buy)\s+(.+)$", re.I)
_CHANNEL = "line"


class LineAdapter:
    """Normalize LINE webhook events → service calls → replies."""

    def __init__(
        self,
        *,
        config: LineConfig | None = None,
        messenger: LineMessenger | None = None,
        sessions: SessionStore | None = None,
    ) -> None:
        self.config = config or load_line_config()
        self.sessions = sessions or default_session_store
        self.messenger = messenger or LineMessenger(
            channel_access_token=self.config.channel_access_token,
            reply_url=self.config.reply_url,
            push_url=self.config.push_url,
        )
        self._destination: str | None = None

    def set_destination(self, destination: str | None) -> None:
        """LINE webhook ``destination`` (OA bot user id) for multi-brand map."""
        self._destination = (destination or "").strip() or None

    def _persist(self, line_uid: str, sess: LineSession) -> None:
        save = getattr(self.sessions, "save", None)
        if callable(save):
            save(line_uid, sess)

    def _brand_ctx(self) -> dict[str, Any] | None:
        bid = self.config.brand_id_for_destination(self._destination)
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
            from bot.platform.capabilities import features_for

            allowed = features_for(_CHANNEL, "customer")
            return {
                k: (k in allowed)
                for k in (
                    "catalog",
                    "cart",
                    "checkout",
                    "order_status",
                    "tickets",
                    "payment_cash",
                    "payment_promptpay",
                    "location_live",
                    "admin_console",
                    "delivery_chat",
                )
            }
        return resolve_capabilities(
            commerce_mode=ctx.get("commerce_mode"),
            age_gate_enabled=bool(ctx.get("age_gate_enabled")),
            web_profile=ctx.get("web_profile"),
            channel=_CHANNEL,
            role="customer",
        )

    async def _reply(
        self,
        line_uid: str,
        text: str,
        *,
        quick_items: list[dict[str, Any]] | None = None,
    ) -> bool:
        buttons = ButtonSpec(native={"items": quick_items}) if quick_items else None
        return await self.messenger.send_text(line_uid, text, buttons=buttons)

    async def _reply_flex(
        self,
        line_uid: str,
        flex_msg: dict[str, Any],
        *,
        fallback_text: str | None = None,
        quick_items: list[dict[str, Any]] | None = None,
    ) -> bool:
        if self.config.use_flex:
            ok = await self.messenger.send_flex(line_uid, flex_msg)
            if ok:
                return True
        return await self._reply(
            line_uid,
            fallback_text or flex_msg.get("altText") or "…",
            quick_items=quick_items or R.main_menu_items(),
        )

    async def handle_event(
        self, event: dict[str, Any], *, destination: str | None = None
    ) -> None:
        if destination is not None:
            self.set_destination(destination)
        etype = (event.get("type") or "").strip()
        if etype in ("unfollow", "leave", "join", "memberJoined", "memberLeft"):
            return
        source = event.get("source") or {}
        line_uid = source.get("userId")
        if not line_uid:
            return
        line_uid = str(line_uid)
        reply_token = event.get("replyToken")
        if reply_token:
            self.messenger.set_reply_token(str(reply_token))

        user_id = ensure_line_user(line_uid)
        sess = self.sessions.get(line_uid)
        ctx = self._brand_ctx()
        caps = self._caps(ctx)

        payload, text = self._extract_intent(event)

        try:
            if etype == "follow":
                await self._reply_flex(
                    line_uid,
                    R.welcome_flex((ctx or {}).get("brand_name")),
                    fallback_text=R.welcome_text((ctx or {}).get("brand_name")),
                    quick_items=R.main_menu_items(),
                )
                return

            if payload and payload.upper() in _OPS_PAYLOADS:
                await self._reply(line_uid, R.ops_denied_text(), quick_items=R.main_menu_items())
                return

            if sess.state.startswith("checkout_"):
                await self._handle_checkout_step(
                    line_uid, user_id, sess, ctx, caps, payload, text
                )
                return

            if sess.state == "support_wait_body":
                await self._finish_support(line_uid, user_id, sess, ctx, caps, text)
                return

            intent = (payload or "").upper() or self._text_to_intent(text)
            await self._dispatch(line_uid, user_id, sess, ctx, caps, intent, text)
        finally:
            self._persist(line_uid, sess)

    def _extract_intent(self, event: dict[str, Any]) -> tuple[str | None, str]:
        etype = event.get("type")
        text = ""
        payload = None
        if etype == "message":
            msg = event.get("message") or {}
            if msg.get("type") == "text":
                text = (msg.get("text") or "").strip()
        elif etype == "postback":
            pb = event.get("postback") or {}
            payload = (pb.get("data") or "").strip()
            text = (pb.get("displayText") or "").strip()
        return payload, text

    def _text_to_intent(self, text: str) -> str:
        t = (text or "").strip().lower()
        if not t or t in ("hi", "hello", "hey", "start", "/start"):
            return "LN_HOME"
        if t in ("menu", "shop", "catalog"):
            return "LN_MENU"
        if t in ("cart", "basket"):
            return "LN_CART"
        if t in ("orders", "my orders", "status"):
            return "LN_ORDERS"
        if t == "support" or t == "ticket":
            return "LN_SUPPORT"
        if t == "help":
            return "LN_HELP"
        if t in ("checkout", "pay"):
            return "LN_CHECKOUT"
        if t in ("cancel", "stop"):
            return "LN_CANCEL"
        if t in ("admin", "kitchen", "driver"):
            return "LN_ADMIN"
        if _ADD_ITEM_RE.match(text or ""):
            return "LN_ADD"
        return "LN_FREE_TEXT"

    async def _dispatch(
        self,
        line_uid: str,
        user_id: int,
        sess: LineSession,
        ctx: dict[str, Any] | None,
        caps: dict[str, bool],
        intent: str,
        text: str,
    ) -> None:
        if intent in ("LN_ADMIN", "ADMIN", "KITCHEN", "DRIVER"):
            await self._reply(line_uid, R.ops_denied_text(), quick_items=R.main_menu_items())
            return
        if intent in ("LN_HOME", "LN_HELP", ""):
            name = (ctx or {}).get("brand_name")
            if intent == "LN_HELP":
                await self._reply(
                    line_uid,
                    R.welcome_text(name)
                    + "\n\nCommands: Menu · Cart · Checkout · Orders · Support\n"
                    "Add item: add <item name>\n"
                    "Live tracking & ops → Telegram only.",
                    quick_items=R.main_menu_items(),
                )
                return
            await self._reply_flex(
                line_uid,
                R.welcome_flex(name),
                fallback_text=R.welcome_text(name),
                quick_items=R.main_menu_items(),
            )
            return
        if intent == "LN_CANCEL":
            sess.reset()
            await self._reply(line_uid, "Cancelled. What next?", quick_items=R.main_menu_items())
            return
        if intent == "LN_MENU":
            await self._show_menu(line_uid, ctx, caps)
            return
        if intent == "LN_CART":
            await self._show_cart(line_uid, user_id, caps)
            return
        if intent == "LN_ORDERS":
            await self._show_orders(line_uid, user_id, caps)
            return
        if intent == "LN_SUPPORT":
            await self._start_support(line_uid, sess, caps)
            return
        if intent == "LN_CHECKOUT":
            await self._start_checkout(line_uid, user_id, sess, ctx, caps)
            return
        if intent == "LN_ADD" or _ADD_ITEM_RE.match(text or ""):
            await self._add_item(line_uid, user_id, ctx, caps, text)
            return
        if intent == "LN_FREE_TEXT":
            await self._reply(
                line_uid,
                "I didn't catch that. Use the buttons or try: Menu, Cart, Orders, Support.\n"
                "To add: add <item name>",
                quick_items=R.main_menu_items(),
            )
            return
        await self._reply(
            line_uid,
            R.welcome_text((ctx or {}).get("brand_name")),
            quick_items=R.main_menu_items(),
        )

    async def _show_menu(
        self, line_uid: str, ctx: dict[str, Any] | None, caps: dict[str, bool]
    ) -> None:
        if not can(_CHANNEL, "catalog") or not cap_enabled(caps, "catalog"):
            await self._reply(line_uid, R.cap_denied_text("menu"), quick_items=R.main_menu_items())
            return
        if not ctx or not ctx.get("brand_slug"):
            await self._reply(
                line_uid,
                "Menu is not configured (set LINE_DEFAULT_BRAND_ID).",
                quick_items=R.main_menu_items(),
            )
            return
        brand = catalog.get_brand_public(ctx["brand_slug"], channel=_CHANNEL)
        if not brand:
            await self._reply(
                line_uid, "Shop unavailable right now.", quick_items=R.main_menu_items()
            )
            return
        stores = brand.get("stores") or []
        store_slug = stores[0]["slug"] if stores else None
        brand_name = brand.get("name") or "Menu"
        item_lines: list[str] = []
        if store_slug:
            menu = catalog.get_store_menu(ctx["brand_slug"], store_slug)
            if menu:
                for cat in (menu.get("categories") or [])[:8]:
                    item_lines.append(f"[{cat.get('name') or 'Items'}]")
                    for it in (cat.get("items") or [])[:6]:
                        price = it.get("price")
                        name = it.get("name") or it.get("slug")
                        item_lines.append(f"• {name} — {price}")
                item_lines.append("Add: add <item name>")
            else:
                item_lines.append("No items listed yet.")
        else:
            item_lines.append("No store configured.")
        flex = R.menu_flex(brand_name, item_lines, quick_items=R.main_menu_items())
        await self._reply_flex(
            line_uid,
            flex,
            fallback_text="\n".join([brand_name, *item_lines])[:4500],
            quick_items=R.main_menu_items(),
        )

    async def _add_item(
        self,
        line_uid: str,
        user_id: int,
        ctx: dict[str, Any] | None,
        caps: dict[str, bool],
        text: str,
    ) -> None:
        if not can(_CHANNEL, "cart") and not cap_enabled(caps, "cart"):
            await self._reply(line_uid, R.cap_denied_text("cart"), quick_items=R.main_menu_items())
            return
        m = _ADD_ITEM_RE.match(text or "")
        name = (m.group(1) if m else text or "").strip()
        if not name:
            await self._reply(line_uid, "Usage: add <item name>", quick_items=R.main_menu_items())
            return
        res = await cart_svc.add_item(
            user_id,
            name,
            quantity=1,
            brand_id=(ctx or {}).get("brand_id"),
            store_id=(ctx or {}).get("store_id"),
        )
        if not res.ok:
            await self._reply(
                line_uid,
                res.error_detail or res.error_key or "Could not add item.",
                quick_items=R.main_menu_items(),
            )
            return
        await self._reply(
            line_uid,
            res.data.get("message") or f"Added {name}.",
            quick_items=R.checkout_items(),
        )

    async def _show_cart(self, line_uid: str, user_id: int, caps: dict[str, bool]) -> None:
        if not can(_CHANNEL, "cart"):
            await self._reply(line_uid, R.cap_denied_text("cart"), quick_items=R.main_menu_items())
            return
        res = await cart_svc.list_items(user_id)
        if not res.ok or res.data.get("empty"):
            await self._reply(line_uid, "Your cart is empty.", quick_items=R.main_menu_items())
            return
        lines = ["🛒 Cart"]
        for it in res.data.get("items") or []:
            lines.append(
                f"• {it.get('item_name')} x{it.get('quantity')} = {it.get('total', it.get('price'))}"
            )
        lines.append(f"Total: {res.data.get('total')}")
        await self._reply(line_uid, "\n".join(lines)[:4500], quick_items=R.checkout_items())

    async def _show_orders(self, line_uid: str, user_id: int, caps: dict[str, bool]) -> None:
        if not can(_CHANNEL, "order_status") or not cap_enabled(caps, "order_status"):
            await self._reply(
                line_uid, R.cap_denied_text("order status"), quick_items=R.main_menu_items()
            )
            return
        res = order_query.list_orders(user_id, limit=5)
        if not res.ok:
            await self._reply(line_uid, "Could not load orders.", quick_items=R.main_menu_items())
            return
        orders = res.data.get("orders") or []
        if not orders:
            await self._reply(line_uid, "No orders yet.", quick_items=R.main_menu_items())
            return
        lines = ["📦 Recent orders"]
        for o in orders:
            lines.append(
                f"• {o.get('order_code')} — {o.get('order_status')} — {o.get('total_price')}"
            )
        await self._reply(line_uid, "\n".join(lines)[:4500], quick_items=R.main_menu_items())

    async def _start_support(
        self, line_uid: str, sess: LineSession, caps: dict[str, bool]
    ) -> None:
        if not can(_CHANNEL, "tickets") or not cap_enabled(caps, "tickets"):
            await self._reply(
                line_uid, R.cap_denied_text("support tickets"), quick_items=R.main_menu_items()
            )
            return
        sess.state = "support_wait_body"
        await self._reply(
            line_uid,
            "Describe your issue in one message:",
            quick_items=[R.postback_item("Cancel", "LN_CANCEL", "Cancel")],
        )

    async def _finish_support(
        self,
        line_uid: str,
        user_id: int,
        sess: LineSession,
        ctx: dict[str, Any] | None,
        caps: dict[str, bool],
        text: str,
    ) -> None:
        if (text or "").strip().lower() in ("cancel", "stop"):
            sess.reset()
            await self._reply(line_uid, "Support cancelled.", quick_items=R.main_menu_items())
            return
        body = (text or "").strip()
        if not body:
            await self._reply(line_uid, "Please send a short description of the issue.")
            return
        res = tickets_svc.create_ticket(
            user_id,
            "LINE support",
            body,
            brand_id=(ctx or {}).get("brand_id"),
            priority="normal",
        )
        sess.reset()
        if not res.ok:
            await self._reply(
                line_uid,
                res.error_detail or "Could not open ticket.",
                quick_items=R.main_menu_items(),
            )
            return
        code = (res.data or {}).get("ticket_code") or (res.data or {}).get("code")
        await self._reply(
            line_uid,
            f"Ticket opened: {code}. We'll follow up here or on Telegram if linked.",
            quick_items=R.main_menu_items(),
        )

    async def _start_checkout(
        self,
        line_uid: str,
        user_id: int,
        sess: LineSession,
        ctx: dict[str, Any] | None,
        caps: dict[str, bool],
    ) -> None:
        if not can(_CHANNEL, "checkout") or not cap_enabled(caps, "checkout"):
            await self._reply(
                line_uid, R.cap_denied_text("checkout"), quick_items=R.main_menu_items()
            )
            return
        cart = await cart_svc.list_items(user_id)
        if not cart.ok or cart.data.get("empty"):
            await self._reply(
                line_uid, "Cart is empty — add items first.", quick_items=R.main_menu_items()
            )
            return
        sess.state = "checkout_phone"
        sess.data["cart_total"] = str(cart.data.get("total"))
        await self._reply(
            line_uid,
            f"Checkout (total {cart.data.get('total')}).\nSend your phone number:",
            quick_items=[R.postback_item("Cancel", "LN_CANCEL", "Cancel")],
        )

    async def _handle_checkout_step(
        self,
        line_uid: str,
        user_id: int,
        sess: LineSession,
        ctx: dict[str, Any] | None,
        caps: dict[str, bool],
        payload: str | None,
        text: str,
    ) -> None:
        intent = (payload or "").upper()
        if intent == "LN_CANCEL":
            sess.reset()
            await self._reply(line_uid, "Checkout cancelled.", quick_items=R.main_menu_items())
            return

        if sess.state == "checkout_phone":
            phone = (text or "").strip()
            if len(phone) < 8:
                await self._reply(line_uid, "Please send a valid phone number.")
                return
            sess.data["phone"] = phone
            sess.state = "checkout_address"
            await self._reply(line_uid, "Send your delivery address (text):")
            return

        if sess.state == "checkout_address":
            addr = (text or "").strip()
            if len(addr) < 5:
                await self._reply(line_uid, "Please send a fuller delivery address.")
                return
            sess.data["address"] = addr
            sess.state = "checkout_pay"
            pays = []
            if can(_CHANNEL, "payment_cash") and cap_enabled(caps, "payment_cash"):
                pays.append(R.postback_item("Cash", "LN_PAY_CASH", "Cash"))
            if can(_CHANNEL, "payment_promptpay") and cap_enabled(caps, "payment_promptpay"):
                pays.append(R.postback_item("PromptPay", "LN_PAY_PROMPTPAY", "PromptPay"))
            pays.append(R.postback_item("Cancel", "LN_CANCEL", "Cancel"))
            await self._reply(line_uid, "Choose payment method:", quick_items=pays or R.payment_items())
            return

        if sess.state == "checkout_pay":
            pay = intent
            if pay not in ("LN_PAY_CASH", "LN_PAY_PROMPTPAY"):
                t = (text or "").strip().lower()
                if t in ("cash", "cod"):
                    pay = "LN_PAY_CASH"
                elif t in ("promptpay", "qr", "transfer"):
                    pay = "LN_PAY_PROMPTPAY"
                else:
                    await self._reply(
                        line_uid, "Tap Cash or PromptPay.", quick_items=R.payment_items()
                    )
                    return
            await self._place_order(line_uid, user_id, sess, ctx, caps, pay)
            return

        sess.reset()
        await self._reply(line_uid, "Session reset.", quick_items=R.main_menu_items())

    async def _place_order(
        self,
        line_uid: str,
        user_id: int,
        sess: LineSession,
        ctx: dict[str, Any] | None,
        caps: dict[str, bool],
        pay_payload: str,
    ) -> None:
        cart = await cart_svc.list_items(user_id)
        if not cart.ok or cart.data.get("empty"):
            sess.reset()
            await self._reply(line_uid, "Cart is empty.", quick_items=R.main_menu_items())
            return
        items = cart.data.get("items") or []
        total = cart.data.get("total_decimal") or Decimal(str(cart.data.get("total") or 0))
        checkout_svc.ensure_delivery_profile(
            user_id,
            username=f"line:{line_uid[:24]}",
            phone_number=sess.data.get("phone"),
            delivery_address=sess.data.get("address"),
            delivery_note="line",
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
        if pay_payload == "LN_PAY_CASH":
            res = checkout_svc.start_cash_order(
                user_id,
                plain_items,
                total_amount=total,
                username=f"line:{line_uid[:24]}",
                brand_id=brand_id,
                store_id=store_id,
            )
        else:
            res = checkout_svc.start_promptpay_order(
                user_id,
                plain_items,
                total_amount=total,
                username=f"line:{line_uid[:24]}",
                brand_id=brand_id,
                store_id=store_id,
            )
        sess.reset()
        if not res.ok:
            await self._reply(
                line_uid,
                res.error_detail or res.error_key or "Order failed.",
                quick_items=R.main_menu_items(),
            )
            return
        code = res.data.get("order_code")
        pay_method = str(res.data.get("payment_method") or "")
        amount = str(res.data.get("final_amount") or total)
        await self._reply_flex(
            line_uid,
            R.order_confirm_flex(
                order_code=str(code),
                payment_method=pay_method,
                amount=amount,
            ),
            fallback_text=(
                f"✅ Order {code} placed ({pay_method}). Total {amount}."
            ),
            quick_items=R.main_menu_items(),
        )
        if pay_payload == "LN_PAY_PROMPTPAY":
            qr = checkout_svc.build_promptpay_qr_payload(
                final_amount=res.data.get("final_amount") or total,
                order_code=str(code),
                store_id=store_id,
                brand_id=brand_id,
            )
            if qr.ok and qr.data.get("promptpay_id"):
                qr_url = None
                raw = qr.data.get("qr_bytes")
                if raw:
                    qr_url = store_qr_png(str(code), raw)
                if qr_url:
                    # Image first (consumes reply token if any), then flex/text
                    await self.messenger.send_photo(
                        line_uid,
                        qr_url,
                        caption=(
                            f"PromptPay {qr.data.get('amount')} → {qr.data['promptpay_id']} "
                            f"(order {code})"
                        ),
                    )
                    if self.config.use_flex:
                        await self.messenger.send_flex(
                            line_uid,
                            R.payment_qr_flex(
                                order_code=str(code),
                                amount=str(qr.data.get("amount")),
                                promptpay_id=str(qr.data["promptpay_id"]),
                                qr_image_url=qr_url,
                            ),
                        )
                else:
                    await self._reply(
                        line_uid,
                        f"Transfer PromptPay to {qr.data['promptpay_id']} "
                        f"amount {qr.data.get('amount')}. "
                        "Upload slip via Telegram or web if needed."
                        + (
                            ""
                            if qr.data.get("has_dynamic_qr")
                            else " (Set PUBLIC_MEDIA_BASE_URL for QR images.)"
                        ),
                        quick_items=R.main_menu_items(),
                    )
