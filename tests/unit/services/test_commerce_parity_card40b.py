"""CARD-40 Tier B — commerce spine parity (same services, web vs TG user_ids)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from bot.database.main import Database
from bot.database.models.main import CustomerInfo, Order, ShoppingCart
from bot.services import cart as cart_svc
from bot.services import catalog_public as catalog
from bot.services import checkout as checkout_svc
from bot.services import order_query
from bot.services import web_auth
from bot.utils.constants import PAYMENT_CASH, PAYMENT_PROMPTPAY


def _ensure_customer(user_id: int) -> None:
    with Database().session() as s:
        if not s.query(CustomerInfo).filter_by(telegram_id=user_id).first():
            s.add(
                CustomerInfo(
                    telegram_id=user_id,
                    phone_number="+66811112222",
                    delivery_address="99 Web Lane",
                    delivery_note="web",
                    total_spendings=Decimal("0"),
                    completed_orders_count=0,
                    bonus_balance=Decimal("0"),
                )
            )
            s.commit()


@pytest.mark.asyncio
async def test_cart_service_same_for_web_and_tg_users(test_user, test_goods, test_brand, test_store, db_engine):
    """B5: cart ops via service work for TG id and web OAuth synthetic id."""
    web = web_auth.upsert_oauth_user(
        provider="dev",
        subject="parity-web-cart",
        email="parity-web@example.com",
        email_verified=True,
        display_name="Web Parity",
        username="webparity",
    )
    web_uid = int(web["user_id"])

    for uid in (test_user.telegram_id, web_uid):
        add = await cart_svc.add_item(
            uid,
            test_goods.name,
            quantity=1,
            brand_id=test_brand.id,
            store_id=test_store.id,
        )
        assert add.ok, (uid, add.error_key, add.error_detail)
        listed = await cart_svc.list_items(uid)
        assert listed.ok
        assert listed.data["item_count"] == 1
        assert listed.data["items"][0]["item_name"] == test_goods.name
        cleared = await cart_svc.clear(uid)
        assert cleared.ok


def test_promptpay_order_parity_web_vs_tg(
    test_user, test_goods, test_customer_info, test_brand, test_store, db_engine
):
    """B5: same cart fixture → start_promptpay_order for TG and web user → comparable rows."""
    web = web_auth.upsert_oauth_user(
        provider="dev",
        subject="parity-web-pp",
        email="parity-pp@example.com",
        email_verified=True,
        display_name="Web PP",
        username="webpp",
    )
    web_uid = int(web["user_id"])
    _ensure_customer(web_uid)

    results = []
    for uid, username in ((test_user.telegram_id, "tg_user"), (web_uid, "web_user")):
        with Database().session() as s:
            s.add(
                ShoppingCart(
                    user_id=uid,
                    item_name=test_goods.name,
                    quantity=2,
                    brand_id=test_brand.id,
                    store_id=test_store.id,
                )
            )
            s.commit()

        cart_items = [
            {
                "item_name": test_goods.name,
                "quantity": 2,
                "price": test_goods.price,
                "total": test_goods.price * 2,
                "selected_modifiers": None,
            }
        ]
        res = checkout_svc.start_promptpay_order(
            uid,
            cart_items,
            total_amount=test_goods.price * 2,
            bonus_applied=0,
            username=username,
            brand_id=test_brand.id,
            store_id=test_store.id,
        )
        assert res.ok, (uid, res.error_key, res.error_detail)
        results.append(res)

        with Database().session() as s:
            order = s.query(Order).filter_by(id=res.data["order_id"]).one()
            assert order.buyer_id == uid
            assert order.payment_method == PAYMENT_PROMPTPAY
            assert order.order_status in ("pending", "reserved")
            assert order.brand_id == test_brand.id
            assert order.store_id == test_store.id
            assert len(order.items) == 1
            assert order.items[0].item_name == test_goods.name
            assert order.items[0].quantity == 2
            assert s.query(ShoppingCart).filter_by(user_id=uid).count() == 0

    tg_data, web_data = results[0].data, results[1].data
    # Comparable domain outcomes (not same order_code / buyer)
    assert tg_data["payment_method"] == web_data["payment_method"] == PAYMENT_PROMPTPAY
    assert tg_data["total_amount"] == web_data["total_amount"]
    assert tg_data["final_amount"] == web_data["final_amount"]
    assert len(tg_data["items_summary"]) == len(web_data["items_summary"]) == 1

    # order_query works for both
    for uid in (test_user.telegram_id, web_uid):
        listed = order_query.list_orders(uid)
        assert listed.ok and listed.data["count"] >= 1
        code = listed.data["orders"][0]["order_code"]
        got = order_query.get_order(uid, order_code=code)
        assert got.ok
        assert got.data["order"]["payment_method"] == PAYMENT_PROMPTPAY


def test_cash_order_parity_and_qr_payload(
    test_user, test_goods, test_customer_info, test_brand, test_store, db_engine
):
    """Cash path + PromptPay QR builder (B4) for web adapter."""
    with Database().session() as s:
        s.add(
            ShoppingCart(
                user_id=test_user.telegram_id,
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
            "selected_modifiers": None,
        }
    ]
    cash = checkout_svc.start_cash_order(
        test_user.telegram_id,
        cart_items,
        total_amount=test_goods.price,
        brand_id=test_brand.id,
        store_id=test_store.id,
    )
    assert cash.ok, (cash.error_key, cash.error_detail)
    assert cash.data["payment_method"] == PAYMENT_CASH

    # QR helper is pure service (web QR page uses this; may lack promptpay_id in tests)
    qr = checkout_svc.build_promptpay_qr_payload(
        final_amount=test_goods.price,
        order_code=cash.data["order_code"],
        store_id=test_store.id,
        brand_id=test_brand.id,
    )
    assert qr.ok
    assert qr.data["order_code"] == cash.data["order_code"]
    assert "amount" in qr.data


def test_ensure_delivery_profile_and_resolve_helpers(
    test_user, test_brand, test_store, test_goods, db_engine
):
    """Web delivery upsert + catalog resolve for cart add by slug."""
    # test_user pulls db_with_roles so OAuth user FK (role_id) succeeds
    _ = test_user
    web = web_auth.upsert_oauth_user(
        provider="dev",
        subject="parity-delivery",
        email="delivery@example.com",
        email_verified=True,
        display_name="Delivery User",
        username="delivery",
    )
    uid = int(web["user_id"])

    res = checkout_svc.ensure_delivery_profile(
        uid,
        username="web",
        phone_number="+66999999999",
        delivery_address="1 Storefront Ave",
        delivery_note="leave at door",
    )
    assert res.ok

    with Database().session() as s:
        row = s.query(CustomerInfo).filter_by(telegram_id=uid).one()
        assert row.phone_number == "+66999999999"
        assert row.delivery_address == "1 Storefront Ave"

    ctx = catalog.resolve_brand_store(test_brand.slug, test_store.slug or "test-branch")
    assert ctx is not None
    assert ctx["brand_id"] == test_brand.id
    assert ctx["store_id"] == test_store.id

    # slugify of "Test Product"
    name = catalog.resolve_goods_name(test_brand.slug, item_slug="test-product")
    assert name == test_goods.name

    name2 = catalog.resolve_goods_name(test_brand.slug, item_name=test_goods.name)
    assert name2 == test_goods.name


def test_checkout_disabled_when_portfolio_mode(test_brand, db_engine):
    """Capability mask: portfolio brand has checkout off on web."""
    from bot.platform.capabilities import cap_enabled, resolve_capabilities

    with Database().session() as s:
        brand = s.query(type(test_brand)).filter_by(id=test_brand.id).one()
        brand.commerce_mode = "portfolio"
        s.commit()

    caps = resolve_capabilities(
        commerce_mode="portfolio",
        age_gate_enabled=False,
        web_profile={},
        channel="web",
    )
    assert cap_enabled(caps, "checkout") is False
    assert cap_enabled(caps, "portfolio") is True
