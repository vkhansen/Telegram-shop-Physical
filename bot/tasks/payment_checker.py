"""Background payment checker — polls blockchain APIs for pending crypto payments (Card 18).

Runs on a configurable interval (default 30 s). For each ``CryptoPayment`` with
status *awaiting* or *detected* whose expiry has not yet passed, it calls the
appropriate chain verifier.  State transitions:

    awaiting → detected  (tx found, < required confirmations)
    detected → confirmed (confirmations threshold met → auto-confirm order)
    awaiting → expired   (past ``expires_at`` with no tx)
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from bot.config.env import EnvKeys
from bot.database import Database
from bot.database.models.main import CryptoPayment, Order
from bot.utils.constants import STATUS_PENDING, STATUS_RESERVED, STATUS_CONFIRMED, STATUS_EXPIRED

logger = logging.getLogger(__name__)

POLL_INTERVAL: int = EnvKeys.CRYPTO_POLL_INTERVAL  # seconds


# ---------------------------------------------------------------------------
# Public entry-point — started from bot.main on startup
# ---------------------------------------------------------------------------

async def payment_checker_loop(bot):
    """Infinite loop: check pending crypto payments every *POLL_INTERVAL* seconds."""
    logger.info("Payment checker started (interval=%ds)", POLL_INTERVAL)
    while True:
        try:
            await check_pending_payments(bot)
        except Exception:
            logger.exception("Payment checker iteration failed")
        await asyncio.sleep(POLL_INTERVAL)


# ---------------------------------------------------------------------------
# Core checking logic
# ---------------------------------------------------------------------------

async def check_pending_payments(bot):
    """Check all ``CryptoPayment`` rows with status *awaiting* or *detected*."""
    # Late import to avoid circular deps at module load time
    from bot.payments.chain_verify import get_verifier

    now = datetime.now(timezone.utc)

    with Database().session() as session:
        pending = (
            session.query(CryptoPayment)
            .filter(
                CryptoPayment.status.in_(["awaiting", "detected"]),
                CryptoPayment.expires_at > now,
            )
            .all()
        )

        for payment in pending:
            try:
                verifier = get_verifier(payment.coin)
                result = await verifier.check_payment(
                    payment.receive_address, payment.expected_amount,
                )

                payment.last_checked_at = now

                if result.found:
                    payment.tx_hash = result.tx_hash
                    payment.received_amount = result.amount
                    payment.confirmations = result.confirmations or 0

                    if payment.status == "awaiting":
                        payment.status = "detected"
                        payment.detected_at = now
                        logger.info(
                            "Payment detected: order=%s coin=%s tx=%s amount=%s",
                            payment.order_id, payment.coin,
                            result.tx_hash, result.amount,
                        )
                        await _notify_payment_detected(bot, payment)

                    if (result.confirmations or 0) >= payment.required_confirmations:
                        payment.status = "confirmed"
                        payment.confirmed_at = now
                        _auto_confirm_order(session, payment.order_id)
                        logger.info(
                            "Payment confirmed: order=%s coin=%s confirmations=%s",
                            payment.order_id, payment.coin, result.confirmations,
                        )
                        await _notify_payment_confirmed(bot, payment)

            except Exception:
                logger.exception(
                    "Error checking payment id=%s order=%s",
                    payment.id, payment.order_id,
                )

        # --- Expire stale payments ---
        expired = (
            session.query(CryptoPayment)
            .filter(
                CryptoPayment.status == "awaiting",
                CryptoPayment.expires_at <= now,
            )
            .all()
        )
        for payment in expired:
            payment.status = "expired"
            _expire_order(session, payment.order_id)
            logger.info("Payment expired: order=%s coin=%s", payment.order_id, payment.coin)
            await _notify_payment_expired(bot, payment)

        session.commit()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _auto_confirm_order(session, order_id: int):
    """Transition order from pending/reserved → confirmed once payment is verified."""
    order = session.query(Order).get(order_id)
    if order and order.order_status in (STATUS_PENDING, STATUS_RESERVED):
        order.order_status = STATUS_CONFIRMED


def _expire_order(session, order_id: int):
    """Mark order as expired when crypto payment times out."""
    order = session.query(Order).get(order_id)
    if order and order.order_status in (STATUS_PENDING, STATUS_RESERVED):
        order.order_status = STATUS_EXPIRED


async def _notify_payment_detected(bot, payment: CryptoPayment):
    """Notify customer that a transaction was found on-chain."""
    try:
        order = payment.order
        if order and order.buyer_id:
            from bot.i18n import localize
            text = localize(
                "crypto.payment_detected",
                tx_hash=payment.tx_hash or "",
                amount=str(payment.received_amount or ""),
                coin=payment.coin.upper(),
                confirmations=payment.confirmations,
                required=payment.required_confirmations,
            )
            await bot.send_message(order.buyer_id, text)
    except Exception:
        logger.exception("Failed to notify payment detected for order %s", payment.order_id)


async def _notify_payment_confirmed(bot, payment: CryptoPayment):
    """Notify customer + admin that payment is fully confirmed."""
    try:
        order = payment.order
        if order and order.buyer_id:
            from bot.i18n import localize
            text = localize(
                "crypto.payment_confirmed",
                tx_hash=payment.tx_hash or "",
                amount=str(payment.received_amount or ""),
                coin=payment.coin.upper(),
                confirmations=payment.confirmations,
                required=payment.required_confirmations,
            )
            await bot.send_message(order.buyer_id, text)
    except Exception:
        logger.exception("Failed to notify payment confirmed for order %s", payment.order_id)


async def _notify_payment_expired(bot, payment: CryptoPayment):
    """Notify customer that the payment window has expired."""
    try:
        order = payment.order
        if order and order.buyer_id:
            from bot.i18n import localize
            text = localize(
                "crypto.payment_expired",
                coin=payment.coin.upper(),
                order_code=order.order_code or str(order.id),
            )
            await bot.send_message(order.buyer_id, text)
    except Exception:
        logger.exception("Failed to notify payment expired for order %s", payment.order_id)
