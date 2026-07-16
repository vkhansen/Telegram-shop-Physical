"""Web commerce HTTP adapter (CARD-40 Tier B).

Thin routes over the same application services Telegram uses:
  cart · checkout · order_query · catalog_public (resolve) · capabilities

No second order writer. Storefront UI may lag; API is the parity surface.
"""

from __future__ import annotations

import base64
import logging
from decimal import Decimal
from typing import Any

from aiohttp import web

from bot.platform.capabilities import cap_enabled, resolve_capabilities
from bot.services import cart as cart_svc
from bot.services import catalog_public as catalog
from bot.services import checkout as checkout_svc
from bot.services import order_query
from bot.services import web_auth
from bot.utils.constants import PAYMENT_CASH, PAYMENT_PROMPTPAY

logger = logging.getLogger(__name__)

COOKIE = web_auth.SESSION_COOKIE


def register_commerce_routes(app: web.Application) -> None:
    app.router.add_get("/api/public/cart", cart_get)
    app.router.add_post("/api/public/cart/items", cart_add)
    app.router.add_delete("/api/public/cart/items/{cart_id}", cart_remove)
    app.router.add_post("/api/public/cart/clear", cart_clear)
    app.router.add_post("/api/public/checkout", checkout_create)
    app.router.add_get("/api/public/orders", orders_list)
    app.router.add_get("/api/public/orders/{order_code}", orders_get)
    app.router.add_get("/api/public/orders/{order_code}/promptpay-qr", orders_promptpay_qr)
    app.router.add_post("/api/public/customer/delivery", customer_delivery)
    logger.info("Commerce API routes registered (CARD-40-B)")


def _session(request: web.Request) -> dict | None:
    return web_auth.verify_session(request.cookies.get(COOKIE))


def _require_user(request: web.Request) -> tuple[int | None, web.Response | None]:
    sess = _session(request)
    if not sess:
        return None, web.json_response({"error": "unauthorized", "error_key": "auth.required"}, status=401)
    return int(sess["uid"]), None


def _fail(result, *, status: int = 400) -> web.Response:
    body: dict[str, Any] = {
        "error": result.error_key or "error",
        "error_key": result.error_key,
    }
    if result.error_detail:
        body["detail"] = result.error_detail
    if result.data:
        body["data"] = {k: v for k, v in result.data.items() if k != "qr_bytes"}
    return web.json_response(body, status=status)


async def _brand_caps(brand_slug: str) -> tuple[dict[str, Any] | None, dict[str, bool] | None, web.Response | None]:
    ctx = catalog.resolve_brand_store(brand_slug)
    if not ctx:
        return None, None, web.json_response({"error": "not_found", "error_key": "brand.not_found"}, status=404)
    caps = resolve_capabilities(
        commerce_mode=ctx["commerce_mode"],
        age_gate_enabled=ctx["age_gate_enabled"],
        web_profile=ctx["web_profile"],
        channel="web",
        role="customer",
    )
    return ctx, caps, None


async def cart_get(request: web.Request) -> web.Response:
    user_id, err = _require_user(request)
    if err:
        return err
    res = await cart_svc.list_items(user_id)
    if not res.ok:
        return _fail(res)
    return web.json_response(
        {
            "items": cart_svc.cart_items_as_plain(res.data.get("items") or []),
            "item_count": res.data.get("item_count", 0),
            "total": str(res.data.get("total", 0)),
            "empty": res.data.get("empty", True),
        }
    )


async def cart_add(request: web.Request) -> web.Response:
    user_id, err = _require_user(request)
    if err:
        return err
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "invalid_json"}, status=400)

    brand_slug = (body.get("brand_slug") or body.get("brand") or "").strip()
    store_slug = (body.get("store_slug") or body.get("store") or "").strip() or None
    item_slug = (body.get("item_slug") or body.get("item") or "").strip() or None
    item_name = (body.get("item_name") or "").strip() or None
    quantity = int(body.get("quantity") or 1)
    modifiers = body.get("selected_modifiers") or body.get("modifiers")

    if not brand_slug:
        return web.json_response({"error": "brand_required", "error_key": "cart.brand_required"}, status=400)

    ctx, caps, cerr = await _brand_caps(brand_slug)
    if cerr:
        return cerr
    assert ctx is not None and caps is not None
    if not cap_enabled(caps, "cart") and not cap_enabled(caps, "checkout"):
        return web.json_response(
            {"error": "cart_disabled", "error_key": "cap.cart_disabled"},
            status=403,
        )

    if store_slug:
        full = catalog.resolve_brand_store(brand_slug, store_slug)
        if not full:
            return web.json_response({"error": "store_not_found", "error_key": "store.not_found"}, status=404)
        ctx = full

    name = catalog.resolve_goods_name(brand_slug, item_slug=item_slug, item_name=item_name)
    if not name:
        return web.json_response({"error": "item_not_found", "error_key": "cart.item_not_found"}, status=404)

    res = await cart_svc.add_item(
        user_id,
        name,
        quantity=max(1, quantity),
        selected_modifiers=modifiers if isinstance(modifiers, dict) else None,
        brand_id=ctx["brand_id"],
        store_id=ctx.get("store_id"),
    )
    if not res.ok:
        return _fail(res, status=400)
    listed = await cart_svc.list_items(user_id)
    return web.json_response(
        {
            "ok": True,
            "message": res.data.get("message"),
            "cart": {
                "items": cart_svc.cart_items_as_plain(listed.data.get("items") or []) if listed.ok else [],
                "item_count": listed.data.get("item_count", 0) if listed.ok else 0,
                "total": str(listed.data.get("total", 0)) if listed.ok else "0",
            },
        },
        status=201,
    )


async def cart_remove(request: web.Request) -> web.Response:
    user_id, err = _require_user(request)
    if err:
        return err
    cart_id = int(request.match_info["cart_id"])
    res = await cart_svc.remove_item(cart_id, user_id)
    if not res.ok:
        return _fail(res, status=400)
    return web.json_response({"ok": True, "message": res.data.get("message")})


async def cart_clear(request: web.Request) -> web.Response:
    user_id, err = _require_user(request)
    if err:
        return err
    res = await cart_svc.clear(user_id)
    if not res.ok:
        return _fail(res)
    return web.json_response({"ok": True})


async def customer_delivery(request: web.Request) -> web.Response:
    """Upsert delivery profile (same CustomerInfo row TG checkout reads)."""
    user_id, err = _require_user(request)
    if err:
        return err
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "invalid_json"}, status=400)
    sess = _session(request) or {}
    res = checkout_svc.ensure_delivery_profile(
        user_id,
        username=sess.get("name") or sess.get("email") or "",
        phone_number=body.get("phone") or body.get("phone_number"),
        delivery_address=body.get("address") or body.get("delivery_address"),
        delivery_note=body.get("note") or body.get("delivery_note"),
        latitude=body.get("latitude"),
        longitude=body.get("longitude"),
    )
    if not res.ok:
        return _fail(res)
    return web.json_response({"ok": True})


async def checkout_create(request: web.Request) -> web.Response:
    """Create pending order via checkout service (cash or promptpay)."""
    user_id, err = _require_user(request)
    if err:
        return err
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "invalid_json"}, status=400)

    brand_slug = (body.get("brand_slug") or body.get("brand") or "").strip()
    store_slug = (body.get("store_slug") or body.get("store") or "").strip() or None
    method = (body.get("payment_method") or body.get("method") or PAYMENT_PROMPTPAY).strip().lower()
    if method in ("promptpay", "qr"):
        method = PAYMENT_PROMPTPAY
    elif method in ("cash", "cod"):
        method = PAYMENT_CASH
    else:
        return web.json_response(
            {"error": "invalid_payment_method", "error_key": "order.payment.invalid_method"},
            status=400,
        )

    if not brand_slug:
        return web.json_response({"error": "brand_required", "error_key": "checkout.brand_required"}, status=400)

    ctx = catalog.resolve_brand_store(brand_slug, store_slug)
    if not ctx:
        return web.json_response({"error": "not_found", "error_key": "brand.not_found"}, status=404)

    caps = resolve_capabilities(
        commerce_mode=ctx["commerce_mode"],
        age_gate_enabled=ctx["age_gate_enabled"],
        web_profile=ctx["web_profile"],
        channel="web",
        role="customer",
    )
    if not cap_enabled(caps, "checkout"):
        return web.json_response(
            {"error": "checkout_disabled", "error_key": "cap.checkout_disabled"},
            status=403,
        )

    # Delivery profile (required by create_pending_order)
    sess = _session(request) or {}
    phone = body.get("phone") or body.get("phone_number")
    address = body.get("address") or body.get("delivery_address")
    note = body.get("note") or body.get("delivery_note")
    if phone or address or note or body.get("latitude") is not None:
        prof = checkout_svc.ensure_delivery_profile(
            user_id,
            username=sess.get("name") or sess.get("email") or "",
            phone_number=phone,
            delivery_address=address,
            delivery_note=note,
            latitude=body.get("latitude"),
            longitude=body.get("longitude"),
        )
        if not prof.ok:
            return _fail(prof)

    cart_res = await cart_svc.list_items(user_id)
    if not cart_res.ok:
        return _fail(cart_res)
    items = cart_res.data.get("items") or []
    if not items:
        return web.json_response({"error": "cart_empty", "error_key": "cart.empty"}, status=400)

    total = cart_res.data.get("total_decimal") or Decimal(str(cart_res.data.get("total") or 0))
    bonus = Decimal(str(body.get("bonus_applied") or 0))
    username = sess.get("name") or sess.get("email") or None

    cart_plain = [
        {
            "item_name": it["item_name"],
            "quantity": it["quantity"],
            "price": it["price"],
            "total": it.get("total", it["price"] * it["quantity"]),
            "selected_modifiers": it.get("selected_modifiers"),
        }
        for it in items
    ]

    if method == PAYMENT_CASH:
        order_res = checkout_svc.start_cash_order(
            user_id,
            cart_plain,
            total_amount=total,
            bonus_applied=bonus,
            username=username,
            brand_id=ctx["brand_id"],
            store_id=ctx.get("store_id"),
            delivery_type=body.get("delivery_type") or "door",
        )
    else:
        order_res = checkout_svc.start_promptpay_order(
            user_id,
            cart_plain,
            total_amount=total,
            bonus_applied=bonus,
            username=username,
            brand_id=ctx["brand_id"],
            store_id=ctx.get("store_id"),
            delivery_type=body.get("delivery_type") or "door",
        )

    if not order_res.ok:
        status = 409 if order_res.error_key and "inventory" in order_res.error_key else 400
        return _fail(order_res, status=status)

    payload: dict[str, Any] = {
        "ok": True,
        "order_id": order_res.data.get("order_id"),
        "order_code": order_res.data.get("order_code"),
        "payment_method": order_res.data.get("payment_method"),
        "total_amount": order_res.data.get("total_amount"),
        "final_amount": order_res.data.get("final_amount"),
        "bonus_applied": order_res.data.get("bonus_applied"),
        "items_summary": order_res.data.get("items_summary"),
        "brand_id": order_res.data.get("brand_id"),
        "store_id": order_res.data.get("store_id"),
    }

    if method == PAYMENT_PROMPTPAY:
        qr = checkout_svc.build_promptpay_qr_payload(
            final_amount=order_res.data.get("final_amount") or total,
            order_code=order_res.data["order_code"],
            store_id=ctx.get("store_id"),
            brand_id=ctx["brand_id"],
        )
        if qr.ok:
            payload["promptpay"] = {
                "promptpay_id": qr.data.get("promptpay_id"),
                "amount": qr.data.get("amount"),
                "order_code": qr.data.get("order_code"),
                "has_dynamic_qr": qr.data.get("has_dynamic_qr"),
                "has_static_qr": qr.data.get("has_static_qr"),
                "static_qr_file_id": qr.data.get("static_qr_file_id"),
                "qr_png_base64": (
                    base64.b64encode(qr.data["qr_bytes"]).decode("ascii")
                    if qr.data.get("qr_bytes")
                    else None
                ),
            }

    return web.json_response(payload, status=201)


async def orders_list(request: web.Request) -> web.Response:
    user_id, err = _require_user(request)
    if err:
        return err
    status = request.query.get("status")
    try:
        limit = min(int(request.query.get("limit", "20")), 50)
    except ValueError:
        limit = 20
    res = order_query.list_orders(user_id, status=status, limit=limit)
    if not res.ok:
        return _fail(res)
    return web.json_response({"orders": res.data.get("orders") or [], "count": res.data.get("count", 0)})


async def orders_get(request: web.Request) -> web.Response:
    user_id, err = _require_user(request)
    if err:
        return err
    code = request.match_info["order_code"]
    res = order_query.get_order(user_id, order_code=code)
    if not res.ok:
        status = 404 if res.error_key == "order.query.not_found" else 400
        return _fail(res, status=status)
    return web.json_response(res.data.get("order"))


async def orders_promptpay_qr(request: web.Request) -> web.Response:
    """Re-fetch PromptPay QR for an existing pending order (web QR page)."""
    user_id, err = _require_user(request)
    if err:
        return err
    code = request.match_info["order_code"]
    res = order_query.get_order(user_id, order_code=code)
    if not res.ok:
        return _fail(res, status=404)
    order = res.data["order"]
    if order.get("payment_method") not in (PAYMENT_PROMPTPAY, "promptpay"):
        return web.json_response(
            {"error": "not_promptpay", "error_key": "order.payment.not_promptpay"},
            status=400,
        )
    final = Decimal(str(order.get("total_price") or 0)) - Decimal(str(order.get("bonus_applied") or 0))
    qr = checkout_svc.build_promptpay_qr_payload(
        final_amount=final,
        order_code=order["order_code"],
        store_id=order.get("store_id"),
        brand_id=order.get("brand_id"),
    )
    if not qr.ok:
        return _fail(qr)
    return web.json_response(
        {
            "order_code": order["order_code"],
            "promptpay_id": qr.data.get("promptpay_id"),
            "amount": qr.data.get("amount"),
            "has_dynamic_qr": qr.data.get("has_dynamic_qr"),
            "has_static_qr": qr.data.get("has_static_qr"),
            "qr_png_base64": (
                base64.b64encode(qr.data["qr_bytes"]).decode("ascii")
                if qr.data.get("qr_bytes")
                else None
            ),
        }
    )
