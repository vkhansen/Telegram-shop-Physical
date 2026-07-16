"""CARD-32 checkout + cart application services (channel-agnostic)."""

from decimal import Decimal

import pytest

from bot.database.main import Database
from bot.database.models.main import (
    BitcoinAddress,
    CryptoAddress,
    CryptoPayment,
    Order,
    ShoppingCart,
)
from bot.services import cart as cart_svc
from bot.services import checkout as checkout_svc
from bot.services import order_query
from bot.utils.constants import (
    PAYMENT_BITCOIN,
    PAYMENT_CASH,
    PAYMENT_LITECOIN,
    PAYMENT_PROMPTPAY,
)


@pytest.mark.asyncio
async def test_cart_service_list_and_add(test_user, test_goods, db_engine):
    res = await cart_svc.list_items(test_user.telegram_id)
    assert res.ok
    assert res.data["empty"] is True

    add = await cart_svc.add_item(test_user.telegram_id, test_goods.name, quantity=2)
    assert add.ok

    res2 = await cart_svc.list_items(test_user.telegram_id)
    assert res2.ok
    assert res2.data["empty"] is False
    assert res2.data["item_count"] == 1
    assert Decimal(str(res2.data["total"])) > 0


@pytest.mark.asyncio
async def test_cart_service_remove_and_clear(test_user, test_goods, db_engine):
    add = await cart_svc.add_item(test_user.telegram_id, test_goods.name, quantity=1)
    assert add.ok

    listed = await cart_svc.list_items(test_user.telegram_id)
    assert listed.ok and listed.data["item_count"] == 1
    cart_id = listed.data["items"][0]["cart_id"]

    rem = await cart_svc.remove_item(cart_id, test_user.telegram_id)
    assert rem.ok
    empty = await cart_svc.list_items(test_user.telegram_id)
    assert empty.data["empty"] is True

    await cart_svc.add_item(test_user.telegram_id, test_goods.name, quantity=1)
    await cart_svc.add_item(test_user.telegram_id, test_goods.name, quantity=1)
    cleared = await cart_svc.clear(test_user.telegram_id)
    assert cleared.ok
    after = await cart_svc.list_items(test_user.telegram_id)
    assert after.data["empty"] is True


def test_start_promptpay_order_creates_order_and_clears_cart(
    test_user, test_goods, test_customer_info, test_brand, test_store, db_engine
):
    # Seed cart row
    with Database().session() as s:
        s.add(
            ShoppingCart(
                user_id=test_user.telegram_id,
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
    total = test_goods.price * 2

    result = checkout_svc.start_promptpay_order(
        test_user.telegram_id,
        cart_items,
        total_amount=total,
        bonus_applied=0,
        username="tester",
        brand_id=test_brand.id,
        store_id=test_store.id,
    )
    assert result.ok, (result.error_key, result.error_detail)
    assert result.data["order_code"]
    assert result.data["order_id"]
    assert result.data["payment_method"] == PAYMENT_PROMPTPAY
    assert len(result.data["items_summary"]) == 1

    with Database().session() as s:
        order = s.query(Order).filter_by(id=result.data["order_id"]).one()
        assert order.buyer_id == test_user.telegram_id
        assert order.payment_method == PAYMENT_PROMPTPAY
        assert order.order_status in ("pending", "reserved")
        cart_left = s.query(ShoppingCart).filter_by(user_id=test_user.telegram_id).count()
        assert cart_left == 0

    listed = order_query.list_orders(test_user.telegram_id)
    assert listed.ok
    assert listed.data["count"] >= 1


def test_start_cash_order_creates_order_and_clears_cart(
    test_user, test_goods, test_customer_info, test_brand, test_store, db_engine
):
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

    result = checkout_svc.start_cash_order(
        test_user.telegram_id,
        cart_items,
        total_amount=test_goods.price,
        bonus_applied=0,
        username="tester",
        brand_id=test_brand.id,
        store_id=test_store.id,
    )
    assert result.ok, (result.error_key, result.error_detail)
    assert result.data["order_code"]
    assert result.data["order_id"]
    assert result.data["payment_method"] == PAYMENT_CASH
    assert len(result.data["items_summary"]) == 1

    with Database().session() as s:
        order = s.query(Order).filter_by(id=result.data["order_id"]).one()
        assert order.buyer_id == test_user.telegram_id
        assert order.payment_method == PAYMENT_CASH
        assert order.order_status in ("pending", "reserved")
        cart_left = s.query(ShoppingCart).filter_by(user_id=test_user.telegram_id).count()
        assert cart_left == 0


def test_start_crypto_order_legacy_bitcoin(
    test_user, test_goods, test_customer_info, test_brand, test_store, db_engine
):
    with Database().session() as s:
        s.add(BitcoinAddress(address="bc1qcheckoutlegacybtc000000000000000"))
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

    result = checkout_svc.start_crypto_order(
        test_user.telegram_id,
        cart_items,
        payment_method=PAYMENT_BITCOIN,
        total_amount=test_goods.price,
        bonus_applied=0,
        username="tester",
        brand_id=test_brand.id,
        store_id=test_store.id,
        legacy_bitcoin=True,
    )
    assert result.ok, (result.error_key, result.error_detail)
    assert result.data["payment_method"] == PAYMENT_BITCOIN
    assert result.data["bitcoin_address"]
    assert result.data["receive_address"] == result.data["bitcoin_address"]

    with Database().session() as s:
        order = s.query(Order).filter_by(id=result.data["order_id"]).one()
        assert order.payment_method == PAYMENT_BITCOIN
        assert order.bitcoin_address == result.data["bitcoin_address"]
        # Legacy BTC path: no CryptoPayment row
        assert s.query(CryptoPayment).filter_by(order_id=order.id).count() == 0
        btc = s.query(BitcoinAddress).filter_by(address=order.bitcoin_address).one()
        assert btc.is_used is True
        assert btc.order_id == order.id
        cart_left = s.query(ShoppingCart).filter_by(user_id=test_user.telegram_id).count()
        assert cart_left == 0


def test_start_crypto_order_litecoin_creates_crypto_payment(
    test_user, test_goods, test_customer_info, test_brand, test_store, db_engine
):
    ltc_addr = "ltc1qcheckoutservicetest000000000000"
    with Database().session() as s:
        s.add(CryptoAddress(coin="ltc", address=ltc_addr))
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
    crypto_amount = Decimal("0.01234567")

    result = checkout_svc.start_crypto_order(
        test_user.telegram_id,
        cart_items,
        payment_method=PAYMENT_LITECOIN,
        total_amount=test_goods.price,
        bonus_applied=0,
        username="tester",
        brand_id=test_brand.id,
        store_id=test_store.id,
        crypto_amount=crypto_amount,
        required_confirmations=3,
        timeout_minutes=45,
        legacy_bitcoin=False,
    )
    assert result.ok, (result.error_key, result.error_detail)
    assert result.data["payment_method"] == PAYMENT_LITECOIN
    assert result.data["crypto_address"] == ltc_addr
    assert result.data["payment_coin"] == "ltc"
    assert result.data["crypto_expected_amount"] == str(crypto_amount)

    with Database().session() as s:
        order = s.query(Order).filter_by(id=result.data["order_id"]).one()
        assert order.crypto_address == ltc_addr
        assert order.payment_coin == "ltc"
        pay = s.query(CryptoPayment).filter_by(order_id=order.id).one()
        assert pay.coin == "ltc"
        assert pay.receive_address == ltc_addr
        assert Decimal(str(pay.expected_amount)) == crypto_amount
        assert pay.required_confirmations == 3
        addr = s.query(CryptoAddress).filter_by(coin="ltc", address=ltc_addr).one()
        assert addr.is_used is True
        assert addr.order_id == order.id
        cart_left = s.query(ShoppingCart).filter_by(user_id=test_user.telegram_id).count()
        assert cart_left == 0


def test_start_crypto_order_no_address_fails(
    test_user, test_goods, test_customer_info, test_brand, test_store, db_engine
):
    cart_items = [
        {
            "item_name": test_goods.name,
            "quantity": 1,
            "price": test_goods.price,
            "total": test_goods.price,
        }
    ]
    result = checkout_svc.start_crypto_order(
        test_user.telegram_id,
        cart_items,
        payment_method=PAYMENT_BITCOIN,
        total_amount=test_goods.price,
        legacy_bitcoin=True,
    )
    assert not result.ok
    assert result.error_key == "order.payment.system_unavailable"


def test_checkout_empty_cart_fails(test_user, test_customer_info, db_engine):
    result = checkout_svc.start_promptpay_order(
        test_user.telegram_id,
        [],
        total_amount=0,
    )
    assert not result.ok
    assert result.error_key == "cart.empty"


def test_checkout_missing_customer_fails(test_user, test_goods, db_engine):
    cart_items = [
        {
            "item_name": test_goods.name,
            "quantity": 1,
            "price": test_goods.price,
            "total": test_goods.price,
        }
    ]
    result = checkout_svc.start_promptpay_order(
        test_user.telegram_id,
        cart_items,
        total_amount=test_goods.price,
    )
    assert not result.ok
    assert result.error_key == "order.payment.customer_not_found"
