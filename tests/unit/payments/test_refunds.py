"""CARD-24: payment reversal — bonus restore + Refund audit record."""

from decimal import Decimal
from unittest.mock import patch

import pytest

from bot.database.models.main import Order, Refund
from bot.payments.refunds import reverse_payment


def _order(buyer_id, code, *, status, bonus, method="promptpay", total="200"):
    return Order(
        buyer_id=buyer_id,
        total_price=Decimal(total),
        payment_method=method,
        delivery_address="123 Test St",
        phone_number="+66800000000",
        order_status=status,
        order_code=code,
        bonus_applied=Decimal(bonus),
    )


@pytest.mark.unit
@pytest.mark.payments
class TestRefunds:
    def test_cancel_restores_bonus(self, db_session, test_user, test_customer_info):
        test_customer_info.bonus_balance = Decimal("50")
        db_session.commit()

        # Unpaid reserved order with bonus applied.
        order = _order(test_user.telegram_id, "REF010", status="reserved", bonus="30")
        db_session.add(order)
        db_session.commit()

        refund = reverse_payment(order, db_session, reason="expired")
        db_session.commit()

        db_session.refresh(test_customer_info)
        assert test_customer_info.bonus_balance == Decimal("80")
        assert refund.bonus_restored == Decimal("30")
        # No real funds moved on a reserved order → no manual payout needed.
        assert refund.status == "completed"
        assert order.refund_status == "completed"

    def test_refund_record_created(self, db_session, test_user, test_customer_info):
        test_customer_info.bonus_balance = Decimal("10")
        db_session.commit()

        # Paid (confirmed) PromptPay order — customer paid 200 with 20 bonus applied.
        order = _order(test_user.telegram_id, "REF020", status="confirmed", bonus="20")
        db_session.add(order)
        db_session.commit()

        with patch("bot.payments.refunds.log_order_refund") as mock_log:
            reverse_payment(order, db_session, reason="admin cancel", created_by=999)
            db_session.commit()

        rows = db_session.query(Refund).filter_by(order_id=order.id).all()
        assert len(rows) == 1
        r = rows[0]
        assert r.method == "promptpay"
        assert r.bonus_restored == Decimal("20")
        # Confirmed external order → flag the cash amount (total - bonus) for manual refund.
        assert r.status == "pending_manual"
        assert r.amount == Decimal("180")
        assert r.created_by == 999
        assert order.refund_status == "pending"
        # The reversal is audit-logged.
        mock_log.assert_called_once()

        # Idempotent: a second call neither double-credits bonus nor adds a row.
        db_session.refresh(test_customer_info)
        balance_before = test_customer_info.bonus_balance
        again = reverse_payment(order, db_session, reason="retry")
        db_session.commit()
        assert again.id == r.id
        assert db_session.query(Refund).filter_by(order_id=order.id).count() == 1
        db_session.refresh(test_customer_info)
        assert test_customer_info.bonus_balance == balance_before
