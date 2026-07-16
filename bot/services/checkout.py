"""Checkout application service (CARD-32) — channel-agnostic order creation.

Creates pending orders + inventory reserve + cart clear. Adapters handle
payment UI (Telegram photo, web QR page, etc.).

CARD-23: sessions never span network I/O; this module is sync DB-only.
Price feeds stay in adapters; address claim + CryptoPayment are sync here.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from bot.config.env import EnvKeys
from bot.database.main import Database
from bot.database.methods import reserve_inventory
from bot.database.models.main import CryptoPayment, CustomerInfo, Order, OrderItem, ShoppingCart
from bot.export.custom_logging import log_order_creation
from bot.services.dto import ServiceResult
from bot.utils import generate_unique_order_code
from bot.utils.constants import (
    CRYPTO_PAYMENT_METHODS,
    DELIVERY_DOOR,
    PAYMENT_BITCOIN,
    PAYMENT_CASH,
    PAYMENT_METHOD_TO_COIN,
    PAYMENT_PROMPTPAY,
)
from bot.utils.order_helpers import build_google_maps_link

logger = logging.getLogger(__name__)

_CRYPTO_TIMEOUT_BY_COIN = {
    "btc": "CRYPTO_PAYMENT_TIMEOUT_BTC",
    "ltc": "CRYPTO_PAYMENT_TIMEOUT_LTC",
    "sol": "CRYPTO_PAYMENT_TIMEOUT_SOL",
    "usdt_sol": "CRYPTO_PAYMENT_TIMEOUT_USDT",
}


def _as_decimal(v: Any) -> Decimal:
    if isinstance(v, Decimal):
        return v
    return Decimal(str(v or 0))


def _default_crypto_timeout_minutes(coin: str) -> int:
    attr = _CRYPTO_TIMEOUT_BY_COIN.get(coin)
    if attr and hasattr(EnvKeys, attr):
        return int(getattr(EnvKeys, attr))
    return 60


def create_pending_order(
    user_id: int,
    cart_items: list[dict[str, Any]],
    *,
    payment_method: str,
    total_amount: Decimal | int | float | str,
    bonus_applied: Decimal | int | float | str = 0,
    username: str | None = None,
    delivery_type: str = DELIVERY_DOOR,
    drop_instructions: str | None = None,
    drop_latitude: float | None = None,
    drop_longitude: float | None = None,
    drop_media: list | None = None,
    brand_id: int | None = None,
    store_id: int | None = None,
    bitcoin_address: str | None = None,
    crypto_address: str | None = None,
    payment_coin: str | None = None,
    clear_cart: bool = True,
    mark_bitcoin_address: bool = False,
    mark_crypto_address: bool = False,
    crypto_expected_amount: Decimal | int | float | str | None = None,
    crypto_required_confirmations: int | None = None,
    crypto_timeout_minutes: int | None = None,
) -> ServiceResult:
    """
    Create order + order items + reserve inventory (+ optional cart clear).

    *cart_items* shape matches ``get_cart_items`` / cart service:
    ``item_name``, ``quantity``, ``price``, ``total``, optional ``selected_modifiers``.

    Optional crypto extras (same transaction after successful reserve):
    mark address used, create ``CryptoPayment`` for on-chain verification.

    Returns on success::

        order_id, order_code, items_summary (list[str]), total_amount, final_amount,
        bonus_applied, payment_method, delivery_address, phone_number, delivery_note,
        bitcoin_address, crypto_address, payment_coin (when set)
    """
    if not cart_items:
        return ServiceResult.fail("cart.empty")

    total = _as_decimal(total_amount)
    bonus = _as_decimal(bonus_applied)
    if bonus < 0:
        return ServiceResult.fail("order.bonus.invalid")
    if bonus > total:
        # allow equal; over-total is invalid
        return ServiceResult.fail("order.bonus.invalid")

    final_amount = total - bonus
    items_summary: list[str] = []
    receive_address = crypto_address or bitcoin_address

    with Database().session() as session:
        try:
            customer_info = session.query(CustomerInfo).filter_by(telegram_id=user_id).first()
            if not customer_info:
                return ServiceResult.fail("order.payment.customer_not_found")

            if bonus > 0 and (customer_info.bonus_balance or Decimal("0")) < bonus:
                return ServiceResult.fail("order.bonus.insufficient")

            if bonus > 0:
                customer_info.bonus_balance = (customer_info.bonus_balance or Decimal("0")) - bonus

            order = Order(
                buyer_id=user_id,
                total_price=total,
                bonus_applied=bonus,
                payment_method=payment_method,
                delivery_address=customer_info.delivery_address or "",
                phone_number=customer_info.phone_number or "",
                delivery_note=customer_info.delivery_note or "",
                order_status="pending",
                latitude=customer_info.latitude,
                longitude=customer_info.longitude,
                google_maps_link=build_google_maps_link(
                    customer_info.latitude, customer_info.longitude
                ),
                delivery_type=delivery_type or DELIVERY_DOOR,
                drop_instructions=drop_instructions,
                drop_latitude=drop_latitude,
                drop_longitude=drop_longitude,
                drop_media=drop_media,
                brand_id=brand_id,
                store_id=store_id,
                bitcoin_address=bitcoin_address,
                crypto_address=crypto_address,
                payment_coin=payment_coin,
            )
            session.add(order)
            session.flush()
            order.order_code = generate_unique_order_code(session)

            items_to_reserve: list[dict[str, Any]] = []
            for cart_item in cart_items:
                item_name = cart_item["item_name"]
                quantity = int(cart_item["quantity"])
                price = _as_decimal(cart_item["price"])
                line_total = cart_item.get("total", price * quantity)

                session.add(
                    OrderItem(
                        order_id=order.id,
                        item_name=item_name,
                        price=price,
                        quantity=quantity,
                        selected_modifiers=cart_item.get("selected_modifiers"),
                    )
                )
                items_summary.append(
                    f"{item_name} x{quantity} = {line_total} {EnvKeys.PAY_CURRENCY}"
                )
                items_to_reserve.append({"item_name": item_name, "quantity": quantity})

            # reserve_inventory payment_method expects domain strings
            reserve_pm = payment_method
            if payment_method == PAYMENT_PROMPTPAY:
                reserve_pm = "promptpay"

            success, reserve_message = reserve_inventory(
                order.id, items_to_reserve, payment_method=reserve_pm, session=session
            )
            if not success:
                session.rollback()
                return ServiceResult.fail(
                    "order.inventory.unable_to_reserve",
                    error_detail=str(reserve_message) if reserve_message else None,
                    unavailable_items=reserve_message,
                )

            if mark_bitcoin_address and bitcoin_address:
                from bot.payments.bitcoin import mark_bitcoin_address_used

                mark_bitcoin_address_used(
                    bitcoin_address,
                    user_id,
                    username or "",
                    order.id,
                    session=session,
                    order_code=order.order_code,
                )

            if mark_crypto_address and crypto_address and payment_coin:
                from bot.payments.crypto_addresses import mark_address_used

                mark_address_used(
                    payment_coin, crypto_address, user_id, order.id, session=session
                )

            if crypto_expected_amount is not None and receive_address and payment_coin:
                timeout = (
                    int(crypto_timeout_minutes)
                    if crypto_timeout_minutes is not None
                    else _default_crypto_timeout_minutes(payment_coin)
                )
                confs = (
                    int(crypto_required_confirmations)
                    if crypto_required_confirmations is not None
                    else 1
                )
                session.add(
                    CryptoPayment(
                        order_id=order.id,
                        coin=payment_coin,
                        receive_address=receive_address,
                        expected_amount=_as_decimal(crypto_expected_amount),
                        required_confirmations=confs,
                        expires_at=datetime.now(UTC) + timedelta(minutes=timeout),
                    )
                )

            log_order_creation(
                order_id=order.id,
                buyer_id=user_id,
                buyer_username=username,
                items_summary="\n".join(items_summary),
                total_price=float(total),
                payment_method=payment_method,
                delivery_address=customer_info.delivery_address,
                phone_number=customer_info.phone_number,
                bitcoin_address=bitcoin_address or crypto_address,
                order_code=order.order_code,
            )

            if clear_cart:
                session.query(ShoppingCart).filter_by(user_id=user_id).delete()

            session.commit()

            return ServiceResult.success(
                order_id=order.id,
                order_code=order.order_code,
                items_summary=items_summary,
                total_amount=str(total),
                final_amount=str(final_amount),
                bonus_applied=str(bonus),
                payment_method=payment_method,
                delivery_address=customer_info.delivery_address,
                phone_number=customer_info.phone_number,
                delivery_note=customer_info.delivery_note or "",
                brand_id=brand_id,
                store_id=store_id,
                bitcoin_address=bitcoin_address,
                crypto_address=crypto_address,
                payment_coin=payment_coin,
                receive_address=receive_address,
                crypto_expected_amount=(
                    str(_as_decimal(crypto_expected_amount))
                    if crypto_expected_amount is not None
                    else None
                ),
                crypto_timeout_minutes=(
                    int(crypto_timeout_minutes)
                    if crypto_timeout_minutes is not None
                    else (
                        _default_crypto_timeout_minutes(payment_coin)
                        if crypto_expected_amount is not None and payment_coin
                        else None
                    )
                ),
            )
        except Exception as e:
            session.rollback()
            logger.exception("create_pending_order failed user_id=%s", user_id)
            return ServiceResult.fail("order.payment.error_general", error_detail=str(e))


def start_cash_order(
    user_id: int,
    cart_items: list[dict[str, Any]],
    *,
    total_amount: Decimal | int | float | str,
    bonus_applied: Decimal | int | float | str = 0,
    username: str | None = None,
    delivery_type: str = DELIVERY_DOOR,
    drop_instructions: str | None = None,
    drop_latitude: float | None = None,
    drop_longitude: float | None = None,
    drop_media: list | None = None,
    brand_id: int | None = None,
    store_id: int | None = None,
) -> ServiceResult:
    """Create a pending cash-on-delivery order (adapter sends confirm UI + admin notify)."""
    return create_pending_order(
        user_id,
        cart_items,
        payment_method=PAYMENT_CASH,
        total_amount=total_amount,
        bonus_applied=bonus_applied,
        username=username,
        delivery_type=delivery_type,
        drop_instructions=drop_instructions,
        drop_latitude=drop_latitude,
        drop_longitude=drop_longitude,
        drop_media=drop_media,
        brand_id=brand_id,
        store_id=store_id,
        clear_cart=True,
    )


def start_promptpay_order(
    user_id: int,
    cart_items: list[dict[str, Any]],
    *,
    total_amount: Decimal | int | float | str,
    bonus_applied: Decimal | int | float | str = 0,
    username: str | None = None,
    delivery_type: str = DELIVERY_DOOR,
    drop_instructions: str | None = None,
    drop_latitude: float | None = None,
    drop_longitude: float | None = None,
    drop_media: list | None = None,
    brand_id: int | None = None,
    store_id: int | None = None,
) -> ServiceResult:
    """Create a pending PromptPay order (QR generation stays with adapter or ``build_promptpay_qr_payload``)."""
    return create_pending_order(
        user_id,
        cart_items,
        payment_method=PAYMENT_PROMPTPAY,
        total_amount=total_amount,
        bonus_applied=bonus_applied,
        username=username,
        delivery_type=delivery_type,
        drop_instructions=drop_instructions,
        drop_latitude=drop_latitude,
        drop_longitude=drop_longitude,
        drop_media=drop_media,
        brand_id=brand_id,
        store_id=store_id,
        clear_cart=True,
    )


def start_crypto_order(
    user_id: int,
    cart_items: list[dict[str, Any]],
    *,
    payment_method: str,
    total_amount: Decimal | int | float | str,
    bonus_applied: Decimal | int | float | str = 0,
    username: str | None = None,
    delivery_type: str = DELIVERY_DOOR,
    drop_instructions: str | None = None,
    drop_latitude: float | None = None,
    drop_longitude: float | None = None,
    drop_media: list | None = None,
    brand_id: int | None = None,
    store_id: int | None = None,
    crypto_amount: Decimal | int | float | str | None = None,
    required_confirmations: int | None = None,
    timeout_minutes: int | None = None,
    legacy_bitcoin: bool | None = None,
) -> ServiceResult:
    """
    Create a pending crypto order: claim address, reserve stock, optional CryptoPayment.

    *legacy_bitcoin* (default True when ``payment_method == bitcoin`` and no
    ``crypto_amount``): uses ``BitcoinAddress`` pool + ``orders.bitcoin_address``,
    no on-chain ``CryptoPayment`` row (admin-confirm BTC path).

    Multi-coin path (LTC/SOL/USDT, or BTC with ``crypto_amount``): claims from
    ``CryptoAddress`` pool, sets ``crypto_address`` / ``payment_coin``, creates
    ``CryptoPayment`` when ``crypto_amount`` is provided.

    Network price conversion stays in the adapter (async). This function is sync DB-only.
    """
    if payment_method not in CRYPTO_PAYMENT_METHODS:
        return ServiceResult.fail("order.payment.invalid_method")

    coin = PAYMENT_METHOD_TO_COIN[payment_method]
    use_legacy_btc = (
        legacy_bitcoin
        if legacy_bitcoin is not None
        else (payment_method == PAYMENT_BITCOIN and crypto_amount is None)
    )

    if use_legacy_btc:
        from bot.payments.bitcoin import get_available_bitcoin_address

        address = get_available_bitcoin_address(user_id=user_id)
        if not address:
            return ServiceResult.fail("order.payment.system_unavailable", payment_coin=coin)

        return create_pending_order(
            user_id,
            cart_items,
            payment_method=PAYMENT_BITCOIN,
            total_amount=total_amount,
            bonus_applied=bonus_applied,
            username=username,
            delivery_type=delivery_type,
            drop_instructions=drop_instructions,
            drop_latitude=drop_latitude,
            drop_longitude=drop_longitude,
            drop_media=drop_media,
            brand_id=brand_id,
            store_id=store_id,
            bitcoin_address=address,
            payment_coin=coin,
            clear_cart=True,
            mark_bitcoin_address=True,
        )

    from bot.payments.crypto_addresses import get_available_address

    address = get_available_address(coin, user_id=user_id)
    if not address:
        return ServiceResult.fail(
            "crypto.payment.no_address",
            payment_coin=coin,
            coin=coin,
        )

    return create_pending_order(
        user_id,
        cart_items,
        payment_method=payment_method,
        total_amount=total_amount,
        bonus_applied=bonus_applied,
        username=username,
        delivery_type=delivery_type,
        drop_instructions=drop_instructions,
        drop_latitude=drop_latitude,
        drop_longitude=drop_longitude,
        drop_media=drop_media,
        brand_id=brand_id,
        store_id=store_id,
        crypto_address=address,
        payment_coin=coin,
        clear_cart=True,
        mark_crypto_address=True,
        crypto_expected_amount=crypto_amount,
        crypto_required_confirmations=required_confirmations,
        crypto_timeout_minutes=timeout_minutes,
    )


def ensure_delivery_profile(
    user_id: int,
    *,
    username: str | None = None,
    phone_number: str | None = None,
    delivery_address: str | None = None,
    delivery_note: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> ServiceResult:
    """
    Create/update CustomerInfo used by ``create_pending_order``.

    Web and TG adapters both call this so checkout reads the same profile row.
    """
    from bot.export.customer_csv import create_or_update_customer_info

    try:
        create_or_update_customer_info(
            telegram_id=user_id,
            username=username or "",
            phone_number=phone_number,
            delivery_address=delivery_address,
            delivery_note=delivery_note,
        )
        if latitude is not None or longitude is not None:
            with Database().session() as session:
                row = session.query(CustomerInfo).filter_by(telegram_id=user_id).first()
                if row:
                    if latitude is not None:
                        row.latitude = latitude
                    if longitude is not None:
                        row.longitude = longitude
                    session.commit()
        return ServiceResult.success(user_id=user_id)
    except Exception as e:
        logger.exception("ensure_delivery_profile failed user_id=%s", user_id)
        return ServiceResult.fail("order.customer.profile_error", error_detail=str(e))


def build_promptpay_qr_payload(
    *,
    final_amount: Decimal | int | float | str,
    order_code: str,
    store_id: int | None = None,
    brand_id: int | None = None,
) -> ServiceResult:
    """
    Resolve PromptPay account and optionally generate dynamic QR bytes.

    Returns data: promptpay_id, static_qr_file_id, qr_bytes (optional), amount, order_code
    """
    from bot.payments.promptpay import generate_promptpay_qr
    from bot.payments.store_payment import resolve_payment_target

    amount = _as_decimal(final_amount)
    target = resolve_payment_target(store_id=store_id, brand_id=brand_id)
    qr_bytes: bytes | None = None
    if target.promptpay_id:
        try:
            qr_bytes = generate_promptpay_qr(target.promptpay_id, amount)
        except Exception as e:
            logger.error("QR generation failed: %s", e)
            qr_bytes = None

    return ServiceResult.success(
        order_code=order_code,
        amount=str(amount),
        promptpay_id=target.promptpay_id,
        static_qr_file_id=getattr(target, "static_qr_file_id", None),
        qr_bytes=qr_bytes,
        has_dynamic_qr=qr_bytes is not None,
        has_static_qr=bool(getattr(target, "static_qr_file_id", None)),
    )
