"""Payment reversal / refund path (Card 24).

A single ``reverse_payment(order, session)`` entry-point used by every
cancellation/expiry path so the money-safety logic lives in one place:

  (a) restore any ``bonus_applied`` back to the customer's ``bonus_balance``,
  (b) flag external (crypto / PromptPay / cash) payments that the customer
      actually paid as needing a manual admin refund,
  (c) write an auditable ``Refund`` record and an ``orders.log`` line.

The function is idempotent: a second call for the same order returns the
existing ``Refund`` row without restoring bonus again, so retries and
overlapping cancel/expire paths can't double-credit a customer.
"""

import logging
from decimal import Decimal

from bot.database.models.main import CryptoPayment, CustomerInfo, Refund
from bot.export.custom_logging import log_order_refund

logger = logging.getLogger(__name__)

# Payment methods that move real funds and therefore need a manual admin
# refund when an order is reversed after the customer has paid.
_EXTERNAL_METHODS = {"bitcoin", "litecoin", "solana", "usdt_sol", "promptpay", "cash"}

# Crypto methods (subset of external) — these have a CryptoPayment row.
_CRYPTO_METHODS = {"bitcoin", "litecoin", "solana", "usdt_sol"}

# Order states in which an external payment is considered already received and
# thus actually needs reversing (vs. an unpaid pending/reserved order, where
# nothing left the customer's wallet and only bonus needs returning).
_PAID_STATES = {"confirmed", "preparing", "ready", "out_for_delivery", "delivered"}


def reverse_payment(order, session, *, reason: str = "Order cancelled",
                    created_by: int = None) -> Refund:
    """Reverse a payment for ``order`` within an open ``session``.

    The caller owns the transaction (this function does not commit), so the
    bonus restoration, the ``Refund`` row, and the order state change all land
    atomically with whatever cancellation the caller is performing.

    Returns the ``Refund`` row (existing one if already reversed).
    """
    existing = session.query(Refund).filter_by(order_id=order.id).first()
    if existing is not None:
        logger.info(
            "reverse_payment: order %s already reversed (refund #%s) — no-op",
            order.id, existing.id,
        )
        return existing

    # (a) Restore referral/loyalty bonus to the customer's balance.
    bonus = order.bonus_applied or Decimal("0")
    bonus_restored = Decimal("0")
    if bonus and bonus > 0:
        customer = (
            session.query(CustomerInfo)
            .filter_by(telegram_id=order.buyer_id)
            .first()
        )
        if customer is not None:
            if customer.bonus_balance is None:
                customer.bonus_balance = Decimal("0")
            customer.bonus_balance += bonus
            bonus_restored = bonus
        else:
            logger.warning(
                "reverse_payment: no CustomerInfo for buyer %s (order %s); "
                "bonus %s not restored",
                order.buyer_id, order.id, bonus,
            )

    method = order.payment_method or "unknown"

    # (b) Determine whether real funds left the customer and need a manual refund.
    external_amount = Decimal("0")
    needs_manual = False
    if method in _EXTERNAL_METHODS and order.order_status in _PAID_STATES:
        external_amount = (order.total_price or Decimal("0")) - bonus
        if external_amount < 0:
            external_amount = Decimal("0")
        needs_manual = external_amount > 0

    status = "pending_manual" if needs_manual else "completed"

    refund = Refund(
        order_id=order.id,
        method=method,
        bonus_restored=bonus_restored,
        amount=external_amount,
        status=status,
        reason=reason,
        created_by=created_by,
    )
    session.add(refund)

    # Mirror the reversal state onto the order so admin tooling can find rows
    # that still need a manual payout (refund_status == 'pending').
    order.refund_status = "pending" if needs_manual else "completed"

    # Surface the crypto payment row in the same 'awaiting admin' sense by
    # leaving a clear log marker; there is no on-chain auto-reversal.
    if method in _CRYPTO_METHODS and needs_manual:
        crypto = (
            session.query(CryptoPayment)
            .filter_by(order_id=order.id)
            .first()
        )
        if crypto is not None:
            logger.info(
                "reverse_payment: crypto payment for order %s (%s, tx=%s) "
                "flagged for manual refund of %s",
                order.id, method, crypto.tx_hash, external_amount,
            )

    # (c) Audit trail.
    log_order_refund(
        order_id=order.id,
        buyer_id=order.buyer_id,
        method=method,
        bonus_restored=float(bonus_restored),
        amount=float(external_amount),
        status=status,
        reason=reason,
        order_code=getattr(order, "order_code", None),
        created_by=created_by,
    )

    logger.info(
        "reverse_payment: order %s reversed (method=%s, bonus_restored=%s, "
        "manual_amount=%s, status=%s)",
        order.id, method, bonus_restored, external_amount, status,
    )
    return refund
