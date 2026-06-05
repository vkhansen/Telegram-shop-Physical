"""CARD-24: duplicate-slip protection + receiver-name hardening."""

from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from bot.database.models.main import Order
from bot.payments.slip_verify import _receiver_matches


def _order(buyer_id, code, status="pending"):
    return Order(
        buyer_id=buyer_id,
        total_price=Decimal("200"),
        payment_method="promptpay",
        delivery_address="123 Test St",
        phone_number="+66800000000",
        order_status=status,
        order_code=code,
    )


@pytest.mark.unit
@pytest.mark.payments
class TestSlipDedup:
    """A verified bank slip can pay for exactly one order."""

    def test_duplicate_txn_rejected(self, db_session, test_user):
        # Order A has already claimed a bank transaction id.
        a = _order(test_user.telegram_id, "DUPA01", status="confirmed")
        a.slip_transaction_id = "TXN-DUP-1"
        db_session.add(a)
        db_session.commit()

        # Order B is a fresh order paying with a slip that resolves to the SAME txn.
        b = _order(test_user.telegram_id, "DUPB01")
        db_session.add(b)
        db_session.commit()

        # The pre-confirm guard query the handler runs finds the prior owner,
        # so order B is never auto-confirmed.
        owner = db_session.query(Order).filter(Order.slip_transaction_id == "TXN-DUP-1", Order.id != b.id).first()
        assert owner is not None
        assert owner.id == a.id

        # And the DB constraint structurally blocks reusing the txn id on B.
        b.slip_transaction_id = "TXN-DUP-1"
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_receiver_name_normalized_match(self):
        # Loose substring used to wrongly accept this; normalized match rejects it.
        assert _receiver_matches("Bank of Bangkok", "Bangkok") is False
        # Genuine matches still pass (case/whitespace/title tolerant, order-independent).
        assert _receiver_matches("Somchai Jaidee", "somchai  jaidee") is True
        assert _receiver_matches("Mr Somchai Jaidee", "Somchai Jaidee") is True
        assert _receiver_matches("Somchai Jaidee", "Jaidee Somchai") is True
        # A single shared word is not enough signal to validate a payment.
        assert _receiver_matches("Somchai", "Somchai Jaidee") is False
