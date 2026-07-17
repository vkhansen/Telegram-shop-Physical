"""Shared order-flow spine: Telegram and web customers use the same services.

Both adapters must produce comparable domain outcomes for:
  delivery profile → cart → checkout (cash / PromptPay) → order list/get
  → kitchen status walk (channel-agnostic)

TG handlers call cart/checkout/order_query directly; web HTTP wraps the same
calls. These tests exercise the shared path for both user-id shapes.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest

from bot.database.main import Database
from bot.database.models.main import CustomerInfo, Order, ShoppingCart
from bot.services import cart as cart_svc
from bot.services import checkout as checkout_svc
from bot.services import order_query
from bot.services import web_auth
from bot.utils.constants import PAYMENT_CASH, PAYMENT_PROMPTPAY
from bot.utils.order_status import is_valid_transition

# Happy-path kitchen walk after reserve/confirm (shared ops, not web UI)
_STATUS_WALK = (
    "confirmed",
    "preparing",
    "ready",
    "out_for_delivery",
    "delivered",
)


def _ensure_customer(
    user_id: int,
    *,
    phone: str = "+66811112222",
    address: str = "99 Parity Lane, Bangkok",
    note: str = "parity",
) -> None:
    with Database().session() as s:
        row = s.query(CustomerInfo).filter_by(telegram_id=user_id).first()
        if row:
            row.phone_number = phone
            row.delivery_address = address
            row.delivery_note = note
        else:
            s.add(
                CustomerInfo(
                    telegram_id=user_id,
                    phone_number=phone,
                    delivery_address=address,
                    delivery_note=note,
                    total_spendings=Decimal("0"),
                    completed_orders_count=0,
                    bonus_balance=Decimal("0"),
                )
            )
        s.commit()


def _web_user(subject: str, email: str) -> int:
    web = web_auth.upsert_oauth_user(
        provider="dev",
        subject=subject,
        email=email,
        email_verified=True,
        display_name=f"Web {subject}",
        username=subject[:32],
    )
    return int(web["user_id"])


def _cart_plain(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize cart service lines the same way commerce_api does for checkout."""
    out = []
    for it in items:
        out.append(
            {
                "item_name": it["item_name"],
                "quantity": it["quantity"],
                "price": it["price"],
                "total": it.get("total", it["price"] * it["quantity"]),
                "selected_modifiers": it.get("selected_modifiers"),
            }
        )
    return out


def _domain_snapshot(order_data: dict[str, Any]) -> dict[str, Any]:
    """Comparable fields only (not order_code / buyer / timestamps)."""
    return {
        "payment_method": order_data["payment_method"],
        "order_status": order_data["order_status"],
        "total_price": str(order_data["total_price"]),
        "bonus_applied": str(order_data.get("bonus_applied") or "0"),
        "brand_id": order_data.get("brand_id"),
        "store_id": order_data.get("store_id"),
        "items": [
            {
                "item_name": i["item_name"],
                "quantity": i["quantity"],
                "price": str(i["price"]),
            }
            for i in (order_data.get("items") or [])
        ],
    }


async def run_customer_order_spine(
    user_id: int,
    *,
    goods_name: str,
    goods_price: Decimal,
    brand_id: int,
    store_id: int,
    payment_method: str = PAYMENT_CASH,
    quantity: int = 1,
    username: str = "parity",
    phone: str = "+66812345678",
    address: str = "1 Shared Spine Rd",
    note: str = "leave at door",
    walk_kitchen: bool = False,
) -> dict[str, Any]:
    """Channel-agnostic customer journey used by TG and web adapters.

    Mirrors: cart_handler + order_handler (TG) and commerce_api (web).
    """
    # 1. Delivery profile (web POST /customer/delivery · TG customer info FSM)
    prof = checkout_svc.ensure_delivery_profile(
        user_id,
        username=username,
        phone_number=phone,
        delivery_address=address,
        delivery_note=note,
    )
    assert prof.ok, (user_id, prof.error_key, prof.error_detail)

    # 2. Cart ops (cart service)
    cleared = await cart_svc.clear(user_id)
    assert cleared.ok
    add = await cart_svc.add_item(
        user_id,
        goods_name,
        quantity=quantity,
        brand_id=brand_id,
        store_id=store_id,
    )
    assert add.ok, (user_id, add.error_key, add.error_detail)

    listed = await cart_svc.list_items(user_id)
    assert listed.ok
    assert listed.data["empty"] is False
    assert listed.data["item_count"] == 1
    assert listed.data["items"][0]["item_name"] == goods_name
    assert listed.data["items"][0]["quantity"] == quantity

    total = listed.data.get("total_decimal") or Decimal(str(listed.data.get("total") or 0))
    cart_plain = _cart_plain(listed.data["items"])

    # 3. Checkout (checkout service — same for TG payment handlers and web)
    if payment_method == PAYMENT_CASH:
        order_res = checkout_svc.start_cash_order(
            user_id,
            cart_plain,
            total_amount=total,
            bonus_applied=0,
            username=username,
            brand_id=brand_id,
            store_id=store_id,
        )
    elif payment_method == PAYMENT_PROMPTPAY:
        order_res = checkout_svc.start_promptpay_order(
            user_id,
            cart_plain,
            total_amount=total,
            bonus_applied=0,
            username=username,
            brand_id=brand_id,
            store_id=store_id,
        )
    else:
        raise ValueError(f"unsupported payment_method for spine: {payment_method}")

    assert order_res.ok, (user_id, order_res.error_key, order_res.error_detail)
    assert order_res.data["payment_method"] == payment_method
    assert order_res.data["order_code"]
    assert order_res.data["order_id"]

    # Cart cleared after successful checkout
    after_cart = await cart_svc.list_items(user_id)
    assert after_cart.ok and after_cart.data["empty"] is True

    # 4. Order query (orders view TG · GET /orders web)
    listed_orders = order_query.list_orders(user_id)
    assert listed_orders.ok
    assert listed_orders.data["count"] >= 1
    code = order_res.data["order_code"]
    codes = {o["order_code"] for o in listed_orders.data["orders"]}
    assert code in codes

    got = order_query.get_order(user_id, order_code=code)
    assert got.ok
    order = got.data["order"]
    assert order["payment_method"] == payment_method
    assert order["brand_id"] == brand_id
    assert order["store_id"] == store_id
    assert len(order["items"]) == 1
    assert order["items"][0]["item_name"] == goods_name
    assert order["items"][0]["quantity"] == quantity

    # Initial status after reserve path
    assert order["order_status"] in ("pending", "reserved")

    if walk_kitchen:
        with Database().session() as s:
            row = s.query(Order).filter_by(id=order_res.data["order_id"]).one()
            # If still pending (e.g. no reserve), step into reserved first
            if row.order_status == "pending" and is_valid_transition("pending", "reserved"):
                row.order_status = "reserved"
                s.commit()
                s.refresh(row)
            current = row.order_status
            for nxt in _STATUS_WALK:
                if current == nxt:
                    continue
                if not is_valid_transition(current, nxt):
                    # skip illegal jump; walk only legal steps
                    continue
                row.order_status = nxt
                current = nxt
                s.commit()
                s.refresh(row)
            final_status = row.order_status

        got2 = order_query.get_order(user_id, order_code=code)
        assert got2.ok
        assert got2.data["order"]["order_status"] == final_status
        order = got2.data["order"]

    return {
        "user_id": user_id,
        "order_id": order_res.data["order_id"],
        "order_code": code,
        "checkout": {
            "payment_method": order_res.data["payment_method"],
            "total_amount": str(order_res.data["total_amount"]),
            "final_amount": str(order_res.data["final_amount"]),
            "bonus_applied": str(order_res.data.get("bonus_applied") or 0),
            "items_summary_len": len(order_res.data.get("items_summary") or []),
            "brand_id": order_res.data.get("brand_id"),
            "store_id": order_res.data.get("store_id"),
        },
        "order": _domain_snapshot(order),
        "expected_line_total": str(goods_price * quantity),
    }


@pytest.mark.asyncio
async def test_cash_order_spine_identical_tg_and_web(
    test_user, test_goods, test_brand, test_store, db_engine
):
    """TG telegram_id and web OAuth id get the same domain outcomes for cash."""
    web_uid = _web_user("spine-cash-web", "spine-cash@example.com")

    tg = await run_customer_order_spine(
        test_user.telegram_id,
        goods_name=test_goods.name,
        goods_price=test_goods.price,
        brand_id=test_brand.id,
        store_id=test_store.id,
        payment_method=PAYMENT_CASH,
        quantity=2,
        username="tg_user",
        walk_kitchen=True,
    )
    web = await run_customer_order_spine(
        web_uid,
        goods_name=test_goods.name,
        goods_price=test_goods.price,
        brand_id=test_brand.id,
        store_id=test_store.id,
        payment_method=PAYMENT_CASH,
        quantity=2,
        username="web_user",
        walk_kitchen=True,
    )

    assert tg["checkout"]["payment_method"] == web["checkout"]["payment_method"] == PAYMENT_CASH
    assert tg["checkout"]["total_amount"] == web["checkout"]["total_amount"]
    assert tg["checkout"]["final_amount"] == web["checkout"]["final_amount"]
    assert tg["checkout"]["items_summary_len"] == web["checkout"]["items_summary_len"] == 1
    assert tg["checkout"]["brand_id"] == web["checkout"]["brand_id"] == test_brand.id
    assert tg["checkout"]["store_id"] == web["checkout"]["store_id"] == test_store.id

    # Domain order shape matches (buyer/code differ by design)
    assert tg["order"]["payment_method"] == web["order"]["payment_method"]
    assert tg["order"]["items"] == web["order"]["items"]
    assert tg["order"]["brand_id"] == web["order"]["brand_id"]
    assert tg["order"]["store_id"] == web["order"]["store_id"]
    assert tg["order"]["order_status"] == web["order"]["order_status"] == "delivered"

    # Distinct buyers / codes
    assert tg["user_id"] != web["user_id"]
    assert tg["order_code"] != web["order_code"]


@pytest.mark.asyncio
async def test_promptpay_order_spine_identical_tg_and_web(
    test_user, test_goods, test_brand, test_store, db_engine
):
    web_uid = _web_user("spine-pp-web", "spine-pp@example.com")

    tg = await run_customer_order_spine(
        test_user.telegram_id,
        goods_name=test_goods.name,
        goods_price=test_goods.price,
        brand_id=test_brand.id,
        store_id=test_store.id,
        payment_method=PAYMENT_PROMPTPAY,
        quantity=1,
        username="tg_pp",
    )
    web = await run_customer_order_spine(
        web_uid,
        goods_name=test_goods.name,
        goods_price=test_goods.price,
        brand_id=test_brand.id,
        store_id=test_store.id,
        payment_method=PAYMENT_PROMPTPAY,
        quantity=1,
        username="web_pp",
    )

    assert tg["checkout"]["payment_method"] == web["checkout"]["payment_method"] == PAYMENT_PROMPTPAY
    assert tg["checkout"]["total_amount"] == web["checkout"]["total_amount"]
    assert tg["order"]["items"] == web["order"]["items"]
    assert tg["order"]["payment_method"] == PAYMENT_PROMPTPAY

    # QR builder is shared (web QR page + TG photo path both use this)
    for snap in (tg, web):
        qr = checkout_svc.build_promptpay_qr_payload(
            final_amount=Decimal(snap["checkout"]["final_amount"]),
            order_code=snap["order_code"],
            store_id=test_store.id,
            brand_id=test_brand.id,
        )
        assert qr.ok
        assert qr.data["order_code"] == snap["order_code"]
        assert "amount" in qr.data


@pytest.mark.asyncio
async def test_orders_isolated_between_channels(
    test_user, test_goods, test_brand, test_store, db_engine
):
    """A web customer must not see Telegram orders (and vice versa)."""
    web_uid = _web_user("spine-iso-web", "spine-iso@example.com")

    tg = await run_customer_order_spine(
        test_user.telegram_id,
        goods_name=test_goods.name,
        goods_price=test_goods.price,
        brand_id=test_brand.id,
        store_id=test_store.id,
        payment_method=PAYMENT_CASH,
    )
    web = await run_customer_order_spine(
        web_uid,
        goods_name=test_goods.name,
        goods_price=test_goods.price,
        brand_id=test_brand.id,
        store_id=test_store.id,
        payment_method=PAYMENT_CASH,
    )

    # Cross-get must fail
    leak_tg = order_query.get_order(web_uid, order_code=tg["order_code"])
    assert not leak_tg.ok
    assert leak_tg.error_key == "order.query.not_found"

    leak_web = order_query.get_order(test_user.telegram_id, order_code=web["order_code"])
    assert not leak_web.ok
    assert leak_web.error_key == "order.query.not_found"

    tg_list = order_query.list_orders(test_user.telegram_id)
    web_list = order_query.list_orders(web_uid)
    tg_codes = {o["order_code"] for o in tg_list.data["orders"]}
    web_codes = {o["order_code"] for o in web_list.data["orders"]}
    assert tg["order_code"] in tg_codes and tg["order_code"] not in web_codes
    assert web["order_code"] in web_codes and web["order_code"] not in tg_codes


@pytest.mark.asyncio
async def test_cart_mutations_same_for_tg_and_web(
    test_user, test_goods, test_brand, test_store, db_engine
):
    web_uid = _web_user("spine-cart-mut", "spine-cart-mut@example.com")

    for uid in (test_user.telegram_id, web_uid):
        await cart_svc.clear(uid)
        add = await cart_svc.add_item(
            uid, test_goods.name, quantity=3, brand_id=test_brand.id, store_id=test_store.id
        )
        assert add.ok
        listed = await cart_svc.list_items(uid)
        assert listed.data["item_count"] == 1
        assert listed.data["items"][0]["quantity"] == 3
        cart_id = listed.data["items"][0]["cart_id"]

        rem = await cart_svc.remove_item(cart_id, uid)
        assert rem.ok
        empty = await cart_svc.list_items(uid)
        assert empty.data["empty"] is True

        await cart_svc.add_item(
            uid, test_goods.name, quantity=1, brand_id=test_brand.id, store_id=test_store.id
        )
        await cart_svc.add_item(
            uid, test_goods.name, quantity=1, brand_id=test_brand.id, store_id=test_store.id
        )
        cleared = await cart_svc.clear(uid)
        assert cleared.ok
        assert (await cart_svc.list_items(uid)).data["empty"] is True


@pytest.mark.asyncio
async def test_empty_cart_checkout_fails_same_for_both(
    test_user, test_customer_info, db_engine
):
    web_uid = _web_user("spine-empty", "spine-empty@example.com")
    _ensure_customer(web_uid)

    for uid in (test_user.telegram_id, web_uid):
        await cart_svc.clear(uid)
        cash = checkout_svc.start_cash_order(uid, [], total_amount=0)
        pp = checkout_svc.start_promptpay_order(uid, [], total_amount=0)
        assert not cash.ok and cash.error_key == "cart.empty"
        assert not pp.ok and pp.error_key == "cart.empty"


@pytest.mark.asyncio
async def test_missing_customer_fails_same_for_both(
    test_user, test_goods, test_brand, test_store, db_engine
):
    """No CustomerInfo → same error key (TG and web)."""
    web_uid = _web_user("spine-nocust", "spine-nocust@example.com")
    # Ensure no CustomerInfo for web
    with Database().session() as s:
        s.query(CustomerInfo).filter_by(telegram_id=web_uid).delete()
        s.query(CustomerInfo).filter_by(telegram_id=test_user.telegram_id).delete()
        s.commit()

    cart_items = [
        {
            "item_name": test_goods.name,
            "quantity": 1,
            "price": test_goods.price,
            "total": test_goods.price,
        }
    ]
    for uid in (test_user.telegram_id, web_uid):
        res = checkout_svc.start_cash_order(
            uid,
            cart_items,
            total_amount=test_goods.price,
            brand_id=test_brand.id,
            store_id=test_store.id,
        )
        assert not res.ok
        assert res.error_key == "order.payment.customer_not_found"


@pytest.mark.asyncio
async def test_bonus_insufficient_same_for_both(
    test_user, test_goods, test_brand, test_store, db_engine
):
    web_uid = _web_user("spine-bonus", "spine-bonus@example.com")
    for uid in (test_user.telegram_id, web_uid):
        _ensure_customer(uid)
        with Database().session() as s:
            ci = s.query(CustomerInfo).filter_by(telegram_id=uid).one()
            ci.bonus_balance = Decimal("1.00")
            s.commit()

        cart_items = [
            {
                "item_name": test_goods.name,
                "quantity": 1,
                "price": test_goods.price,
                "total": test_goods.price,
            }
        ]
        res = checkout_svc.start_cash_order(
            uid,
            cart_items,
            total_amount=test_goods.price,
            bonus_applied=Decimal("50.00"),
            brand_id=test_brand.id,
            store_id=test_store.id,
        )
        assert not res.ok
        assert res.error_key == "order.bonus.insufficient"


@pytest.mark.asyncio
async def test_delivery_profile_shared_row(
    test_user, db_engine
):
    """ensure_delivery_profile writes CustomerInfo used by both channels."""
    _ = test_user  # roles for FK
    web_uid = _web_user("spine-deliv", "spine-deliv@example.com")

    for uid, phone, addr in (
        (test_user.telegram_id, "+66810000001", "TG Address"),
        (web_uid, "+66810000002", "Web Address"),
    ):
        res = checkout_svc.ensure_delivery_profile(
            uid,
            username="x",
            phone_number=phone,
            delivery_address=addr,
            delivery_note="n",
        )
        assert res.ok
        with Database().session() as s:
            row = s.query(CustomerInfo).filter_by(telegram_id=uid).one()
            assert row.phone_number == phone
            assert row.delivery_address == addr


@pytest.mark.asyncio
async def test_multi_item_checkout_parity(
    test_user, test_goods, test_goods_low_stock, test_brand, test_store, db_engine
):
    """Two different SKUs → same multi-line order shape for TG and web."""
    web_uid = _web_user("spine-multi", "spine-multi@example.com")

    async def multi(uid: int) -> dict[str, Any]:
        checkout_svc.ensure_delivery_profile(
            uid,
            username="multi",
            phone_number="+66819999999",
            delivery_address="Multi St",
        )
        await cart_svc.clear(uid)
        assert (
            await cart_svc.add_item(
                uid, test_goods.name, quantity=1, brand_id=test_brand.id, store_id=test_store.id
            )
        ).ok
        assert (
            await cart_svc.add_item(
                uid,
                test_goods_low_stock.name,
                quantity=2,
                brand_id=test_brand.id,
                store_id=test_store.id,
            )
        ).ok
        listed = await cart_svc.list_items(uid)
        assert listed.data["item_count"] == 2
        total = listed.data["total_decimal"]
        res = checkout_svc.start_cash_order(
            uid,
            _cart_plain(listed.data["items"]),
            total_amount=total,
            brand_id=test_brand.id,
            store_id=test_store.id,
        )
        assert res.ok, (res.error_key, res.error_detail)
        got = order_query.get_order(uid, order_code=res.data["order_code"])
        assert got.ok
        names = sorted(i["item_name"] for i in got.data["order"]["items"])
        qtys = {
            i["item_name"]: i["quantity"] for i in got.data["order"]["items"]
        }
        return {
            "names": names,
            "qtys": qtys,
            "total": str(res.data["total_amount"]),
            "n_items": len(got.data["order"]["items"]),
        }

    tg = await multi(test_user.telegram_id)
    web = await multi(web_uid)
    assert tg == web
    assert tg["n_items"] == 2
    assert test_goods.name in tg["names"]
    assert test_goods_low_stock.name in tg["names"]
    assert tg["qtys"][test_goods_low_stock.name] == 2


def test_cart_rows_cleared_after_checkout_for_both(
    test_user, test_goods, test_customer_info, test_brand, test_store, db_engine
):
    """ORM-level assert: no ShoppingCart rows remain (TG payment path expectation)."""
    web_uid = _web_user("spine-cart-clear", "spine-cart-clear@example.com")
    _ensure_customer(web_uid)

    for uid in (test_user.telegram_id, web_uid):
        with Database().session() as s:
            s.add(
                ShoppingCart(
                    user_id=uid,
                    item_name=test_goods.name,
                    quantity=1,
                    brand_id=test_brand.id,
                    store_id=test_store.id,
                )
            )
            s.commit()

        cart_items = [
            {
                "item_name": test_goods.name,
                "quantity": 1,
                "price": test_goods.price,
                "total": test_goods.price,
            }
        ]
        res = checkout_svc.start_promptpay_order(
            uid,
            cart_items,
            total_amount=test_goods.price,
            brand_id=test_brand.id,
            store_id=test_store.id,
        )
        assert res.ok, (uid, res.error_key)
        with Database().session() as s:
            assert s.query(ShoppingCart).filter_by(user_id=uid).count() == 0
