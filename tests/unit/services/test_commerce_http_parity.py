"""Web commerce HTTP adapter must mirror the Telegram service spine.

Telegram: cart_handler / order_handler → cart + checkout + order_query
Web HTTP: commerce_api routes → same services

These tests run the web HTTP path and compare domain outcomes to a parallel
Telegram-style service call for the same catalog / payment method.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from bot.database.main import Database
from bot.database.models.main import Brand, Order
from bot.services import cart as cart_svc
from bot.services import checkout as checkout_svc
from bot.services import order_query
from bot.utils.constants import PAYMENT_CASH, PAYMENT_PROMPTPAY
from bot.web import auth_api, commerce_api


async def _client_for(app: web.Application) -> TestClient:
    server = TestServer(app)
    client = TestClient(server)
    await client.start_server()
    return client


def _commerce_app() -> web.Application:
    app = web.Application()
    auth_api.register_auth_and_ticket_routes(app)
    commerce_api.register_commerce_routes(app)
    return app


async def _dev_login(client: TestClient, email: str, name: str = "Web Shopper") -> dict[str, Any]:
    res = await client.post(
        "/api/public/auth/dev-login",
        json={"email": email, "name": name},
    )
    assert res.status == 200, await res.text()
    return await res.json()


async def _tg_service_checkout(
    user_id: int,
    *,
    goods_name: str,
    goods_price: Decimal,
    brand_id: int,
    store_id: int,
    payment_method: str,
    quantity: int = 1,
) -> dict[str, Any]:
    """Telegram-equivalent path: service calls only (no HTTP)."""
    checkout_svc.ensure_delivery_profile(
        user_id,
        username="tg",
        phone_number="+66810001111",
        delivery_address="TG HTTP Parity St",
        delivery_note="tg",
    )
    await cart_svc.clear(user_id)
    add = await cart_svc.add_item(
        user_id, goods_name, quantity=quantity, brand_id=brand_id, store_id=store_id
    )
    assert add.ok
    listed = await cart_svc.list_items(user_id)
    items = listed.data["items"]
    plain = [
        {
            "item_name": it["item_name"],
            "quantity": it["quantity"],
            "price": it["price"],
            "total": it.get("total", it["price"] * it["quantity"]),
            "selected_modifiers": it.get("selected_modifiers"),
        }
        for it in items
    ]
    total = listed.data["total_decimal"]
    if payment_method == PAYMENT_CASH:
        res = checkout_svc.start_cash_order(
            user_id,
            plain,
            total_amount=total,
            brand_id=brand_id,
            store_id=store_id,
        )
    else:
        res = checkout_svc.start_promptpay_order(
            user_id,
            plain,
            total_amount=total,
            brand_id=brand_id,
            store_id=store_id,
        )
    assert res.ok, (res.error_key, res.error_detail)
    got = order_query.get_order(user_id, order_code=res.data["order_code"])
    assert got.ok
    return {
        "checkout": res.data,
        "order": got.data["order"],
    }


@pytest.fixture
def store_slug(test_store):
    """HTTP store_slug: explicit slug or slugify(name)."""
    from bot.services.catalog_public import slugify

    if test_store.slug:
        return test_store.slug
    # Persist slug so resolve_brand_store finds it cleanly
    with Database().session() as s:
        st = s.query(type(test_store)).filter_by(id=test_store.id).one()
        st.slug = slugify(st.name)
        s.commit()
        return st.slug


@pytest.mark.asyncio
async def test_commerce_requires_auth(db_engine):
    app = _commerce_app()
    client = await _client_for(app)
    try:
        for method, path in (
            ("GET", "/api/public/cart"),
            ("POST", "/api/public/cart/items"),
            ("POST", "/api/public/cart/clear"),
            ("POST", "/api/public/checkout"),
            ("GET", "/api/public/orders"),
            ("POST", "/api/public/customer/delivery"),
        ):
            if method == "GET":
                res = await client.get(path)
            else:
                res = await client.post(path, json={})
            assert res.status == 401, path
            body = await res.json()
            assert body.get("error_key") == "auth.required" or body.get("error") == "unauthorized"
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_http_cash_checkout_matches_tg_service(
    test_user,
    test_goods,
    test_brand,
    test_store,
    store_slug,
    db_engine,
    monkeypatch,
):
    """Full web HTTP cash order ≈ Telegram service cash order domain shape."""
    monkeypatch.setenv("OAUTH_DEV_LOGIN", "true")
    # TG side
    tg = await _tg_service_checkout(
        test_user.telegram_id,
        goods_name=test_goods.name,
        goods_price=test_goods.price,
        brand_id=test_brand.id,
        store_id=test_store.id,
        payment_method=PAYMENT_CASH,
        quantity=2,
    )

    app = _commerce_app()
    client = await _client_for(app)
    try:
        await _dev_login(client, "http-cash@example.com", "HTTP Cash")

        # Delivery (same CustomerInfo spine as TG)
        deliv = await client.post(
            "/api/public/customer/delivery",
            json={
                "phone": "+66812223333",
                "address": "Web HTTP Lane",
                "note": "ring",
            },
        )
        assert deliv.status == 200, await deliv.text()

        # Cart add by item_slug (web storefront path)
        add = await client.post(
            "/api/public/cart/items",
            json={
                "brand_slug": test_brand.slug,
                "store_slug": store_slug,
                "item_slug": "test-product",
                "quantity": 2,
            },
        )
        assert add.status == 201, await add.text()
        cart_body = await add.json()
        assert cart_body["cart"]["item_count"] == 1
        assert cart_body["cart"]["items"][0]["item_name"] == test_goods.name
        assert int(cart_body["cart"]["items"][0]["quantity"]) == 2

        cart_get = await client.get("/api/public/cart")
        assert cart_get.status == 200
        cart = await cart_get.json()
        assert cart["empty"] is False

        checkout = await client.post(
            "/api/public/checkout",
            json={
                "brand_slug": test_brand.slug,
                "store_slug": store_slug,
                "payment_method": "cash",
                "delivery_type": "door",
            },
        )
        assert checkout.status == 201, await checkout.text()
        web_order = await checkout.json()
        assert web_order["ok"] is True
        assert web_order["payment_method"] == PAYMENT_CASH
        assert web_order["order_code"]

        # Cart empty after checkout (same as TG)
        cart_after = await client.get("/api/public/cart")
        assert (await cart_after.json())["empty"] is True

        orders = await client.get("/api/public/orders")
        assert orders.status == 200
        orders_body = await orders.json()
        assert orders_body["count"] >= 1
        assert any(o["order_code"] == web_order["order_code"] for o in orders_body["orders"])

        detail = await client.get(f"/api/public/orders/{web_order['order_code']}")
        assert detail.status == 200
        detail_body = await detail.json()
        assert detail_body["payment_method"] == PAYMENT_CASH
        assert detail_body["brand_id"] == test_brand.id
        assert detail_body["store_id"] == test_store.id
        assert len(detail_body["items"]) == 1
        assert detail_body["items"][0]["item_name"] == test_goods.name
        assert detail_body["items"][0]["quantity"] == 2

        # Domain parity with TG service path
        assert web_order["payment_method"] == tg["checkout"]["payment_method"]
        assert str(web_order["total_amount"]) == str(tg["checkout"]["total_amount"])
        assert str(web_order["final_amount"]) == str(tg["checkout"]["final_amount"])
        assert detail_body["items"][0]["item_name"] == tg["order"]["items"][0]["item_name"]
        assert detail_body["items"][0]["quantity"] == tg["order"]["items"][0]["quantity"]
        assert detail_body["brand_id"] == tg["order"]["brand_id"]
        assert detail_body["store_id"] == tg["order"]["store_id"]
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_http_promptpay_checkout_and_qr(
    test_user,
    test_goods,
    test_brand,
    test_store,
    store_slug,
    db_engine,
    monkeypatch,
):
    monkeypatch.setenv("OAUTH_DEV_LOGIN", "true")
    # Ensure brand has promptpay for QR path (optional)
    with Database().session() as s:
        b = s.query(Brand).filter_by(id=test_brand.id).one()
        b.promptpay_id = "0812345678"
        b.promptpay_name = "Test Brand"
        s.commit()

    tg = await _tg_service_checkout(
        test_user.telegram_id,
        goods_name=test_goods.name,
        goods_price=test_goods.price,
        brand_id=test_brand.id,
        store_id=test_store.id,
        payment_method=PAYMENT_PROMPTPAY,
        quantity=1,
    )

    app = _commerce_app()
    client = await _client_for(app)
    try:
        await _dev_login(client, "http-pp@example.com", "HTTP PP")

        await client.post(
            "/api/public/customer/delivery",
            json={"phone": "+66815555555", "address": "PP Web St"},
        )
        add = await client.post(
            "/api/public/cart/items",
            json={
                "brand_slug": test_brand.slug,
                "store_slug": store_slug,
                "item_name": test_goods.name,
                "quantity": 1,
            },
        )
        assert add.status == 201, await add.text()

        checkout = await client.post(
            "/api/public/checkout",
            json={
                "brand_slug": test_brand.slug,
                "store_slug": store_slug,
                "payment_method": "promptpay",
            },
        )
        assert checkout.status == 201, await checkout.text()
        body = await checkout.json()
        assert body["payment_method"] == PAYMENT_PROMPTPAY
        assert body["payment_method"] == tg["checkout"]["payment_method"]
        assert str(body["total_amount"]) == str(tg["checkout"]["total_amount"])
        # QR payload attached on PromptPay (same builder as TG)
        assert "promptpay" in body
        assert body["promptpay"]["order_code"] == body["order_code"]

        qr = await client.get(f"/api/public/orders/{body['order_code']}/promptpay-qr")
        assert qr.status == 200, await qr.text()
        qr_body = await qr.json()
        assert qr_body["order_code"] == body["order_code"]
        assert "amount" in qr_body
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_http_empty_cart_checkout_fails(
    test_user, test_brand, test_store, store_slug, db_engine, monkeypatch
):
    monkeypatch.setenv("OAUTH_DEV_LOGIN", "true")
    app = _commerce_app()
    client = await _client_for(app)
    try:
        await _dev_login(client, "http-empty@example.com")
        await client.post(
            "/api/public/customer/delivery",
            json={"phone": "+66810000000", "address": "Empty Cart St"},
        )
        # clear ensures empty
        await client.post("/api/public/cart/clear")
        res = await client.post(
            "/api/public/checkout",
            json={
                "brand_slug": test_brand.slug,
                "store_slug": store_slug,
                "payment_method": "cash",
            },
        )
        assert res.status == 400
        body = await res.json()
        assert body.get("error_key") == "cart.empty"
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_http_checkout_disabled_portfolio(
    test_user, test_goods, test_brand, test_store, store_slug, db_engine, monkeypatch
):
    monkeypatch.setenv("OAUTH_DEV_LOGIN", "true")
    with Database().session() as s:
        b = s.query(Brand).filter_by(id=test_brand.id).one()
        b.commerce_mode = "portfolio"
        s.commit()

    app = _commerce_app()
    client = await _client_for(app)
    try:
        await _dev_login(client, "http-portfolio@example.com")
        # Cart may also be disabled
        add = await client.post(
            "/api/public/cart/items",
            json={
                "brand_slug": test_brand.slug,
                "store_slug": store_slug,
                "item_slug": "test-product",
                "quantity": 1,
            },
        )
        # portfolio: cart/checkout off → 403
        assert add.status == 403, await add.text()
        body = await add.json()
        assert "cap" in (body.get("error_key") or "")

        # Even if cart were seeded, checkout must 403
        checkout = await client.post(
            "/api/public/checkout",
            json={
                "brand_slug": test_brand.slug,
                "payment_method": "cash",
            },
        )
        assert checkout.status == 403
        cbody = await checkout.json()
        assert cbody.get("error_key") == "cap.checkout_disabled"
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_http_cannot_read_other_users_order(
    test_user,
    test_goods,
    test_brand,
    test_store,
    store_slug,
    db_engine,
    monkeypatch,
):
    monkeypatch.setenv("OAUTH_DEV_LOGIN", "true")
    # TG places an order via service
    tg = await _tg_service_checkout(
        test_user.telegram_id,
        goods_name=test_goods.name,
        goods_price=test_goods.price,
        brand_id=test_brand.id,
        store_id=test_store.id,
        payment_method=PAYMENT_CASH,
    )

    app = _commerce_app()
    client = await _client_for(app)
    try:
        await _dev_login(client, "http-isolation@example.com")
        res = await client.get(f"/api/public/orders/{tg['checkout']['order_code']}")
        assert res.status == 404
        body = await res.json()
        assert body.get("error_key") == "order.query.not_found"
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_http_cart_remove_and_clear(
    test_user, test_goods, test_brand, test_store, store_slug, db_engine, monkeypatch
):
    monkeypatch.setenv("OAUTH_DEV_LOGIN", "true")
    app = _commerce_app()
    client = await _client_for(app)
    try:
        await _dev_login(client, "http-cart-mut@example.com")
        add = await client.post(
            "/api/public/cart/items",
            json={
                "brand_slug": test_brand.slug,
                "store_slug": store_slug,
                "item_slug": "test-product",
                "quantity": 1,
            },
        )
        assert add.status == 201, await add.text()
        cart = (await add.json())["cart"]
        cart_id = cart["items"][0]["cart_id"]

        rem = await client.delete(f"/api/public/cart/items/{cart_id}")
        assert rem.status == 200, await rem.text()

        empty = await client.get("/api/public/cart")
        assert (await empty.json())["empty"] is True

        await client.post(
            "/api/public/cart/items",
            json={
                "brand_slug": test_brand.slug,
                "item_name": test_goods.name,
                "quantity": 1,
            },
        )
        cleared = await client.post("/api/public/cart/clear")
        assert cleared.status == 200
        empty2 = await client.get("/api/public/cart")
        assert (await empty2.json())["empty"] is True
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_http_invalid_payment_method(
    test_user, test_goods, test_brand, test_store, store_slug, db_engine, monkeypatch
):
    monkeypatch.setenv("OAUTH_DEV_LOGIN", "true")
    app = _commerce_app()
    client = await _client_for(app)
    try:
        await _dev_login(client, "http-badpay@example.com")
        await client.post(
            "/api/public/customer/delivery",
            json={"phone": "+66810000001", "address": "X"},
        )
        await client.post(
            "/api/public/cart/items",
            json={
                "brand_slug": test_brand.slug,
                "store_slug": store_slug,
                "item_slug": "test-product",
                "quantity": 1,
            },
        )
        res = await client.post(
            "/api/public/checkout",
            json={
                "brand_slug": test_brand.slug,
                "store_slug": store_slug,
                "payment_method": "visa",
            },
        )
        assert res.status == 400
        body = await res.json()
        assert body.get("error_key") == "order.payment.invalid_method"
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_http_item_not_found(
    test_user, test_brand, test_store, store_slug, db_engine, monkeypatch
):
    monkeypatch.setenv("OAUTH_DEV_LOGIN", "true")
    app = _commerce_app()
    client = await _client_for(app)
    try:
        await _dev_login(client, "http-nofound@example.com")
        res = await client.post(
            "/api/public/cart/items",
            json={
                "brand_slug": test_brand.slug,
                "store_slug": store_slug,
                "item_slug": "does-not-exist-xyz",
                "quantity": 1,
            },
        )
        assert res.status == 404
        body = await res.json()
        assert body.get("error_key") == "cart.item_not_found"
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_http_and_tg_kitchen_status_same_row_shape(
    test_user,
    test_goods,
    test_brand,
    test_store,
    store_slug,
    db_engine,
    monkeypatch,
):
    """After HTTP checkout, kitchen status walk is readable via order_query like TG."""
    monkeypatch.setenv("OAUTH_DEV_LOGIN", "true")
    from bot.utils.order_status import is_valid_transition

    app = _commerce_app()
    client = await _client_for(app)
    try:
        await _dev_login(client, "http-kitchen@example.com")
        await client.post(
            "/api/public/customer/delivery",
            json={"phone": "+66817777777", "address": "Kitchen St"},
        )
        await client.post(
            "/api/public/cart/items",
            json={
                "brand_slug": test_brand.slug,
                "store_slug": store_slug,
                "item_slug": "test-product",
                "quantity": 1,
            },
        )
        checkout = await client.post(
            "/api/public/checkout",
            json={
                "brand_slug": test_brand.slug,
                "store_slug": store_slug,
                "payment_method": "cash",
            },
        )
        assert checkout.status == 201, await checkout.text()
        code = (await checkout.json())["order_code"]

        # Kitchen ops update Order row; both HTTP GET and order_query must agree
        with Database().session() as s:
            order = s.query(Order).filter_by(order_code=code).one()
            uid = order.buyer_id
            if order.order_status == "pending":
                order.order_status = "reserved"
                s.commit()
            current = order.order_status
            for nxt in ("confirmed", "preparing", "ready", "out_for_delivery", "delivered"):
                if is_valid_transition(current, nxt):
                    order.order_status = nxt
                    current = nxt
                    s.commit()
                    s.refresh(order)

        # Web GET order + service get_order must agree
        http_detail = await client.get(f"/api/public/orders/{code}")
        assert http_detail.status == 200
        http_order = await http_detail.json()
        svc = order_query.get_order(uid, order_code=code)
        assert svc.ok
        assert http_order["order_status"] == svc.data["order"]["order_status"] == "delivered"
        assert http_order["order_code"] == svc.data["order"]["order_code"]
        assert http_order["items"] == svc.data["order"]["items"]
    finally:
        await client.close()
