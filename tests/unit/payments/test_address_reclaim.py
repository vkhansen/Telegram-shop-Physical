"""CARD-24: crypto reconciliation — address reclaim + overpayment recording."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from bot.database.models.main import CryptoAddress, CryptoPayment, Order
from bot.tasks.address_reclaimer import reclaim_expired_addresses


def _order(buyer_id, code, status):
    return Order(
        buyer_id=buyer_id,
        total_price=Decimal("100"),
        payment_method="bitcoin",
        delivery_address="123 Test St",
        phone_number="+66800000000",
        order_status=status,
        order_code=code,
    )


@pytest.mark.unit
@pytest.mark.payments
class TestAddressReclaim:
    def test_expired_order_releases_address(self, db_session, test_user):
        stale = datetime.now(UTC) - timedelta(hours=48)

        # Expired order holding an address claimed long ago → should be reclaimed.
        expired = _order(test_user.telegram_id, "RCL001", "expired")
        db_session.add(expired)
        db_session.flush()
        held = CryptoAddress(
            coin="btc",
            address="bc1qreclaimtest",
            is_used=True,
            used_by=test_user.telegram_id,
            order_id=expired.id,
            used_at=stale,
        )
        db_session.add(held)

        # Still-pending order holding an address → must NOT be reclaimed.
        active = _order(test_user.telegram_id, "RCL002", "pending")
        db_session.add(active)
        db_session.flush()
        kept = CryptoAddress(
            coin="btc",
            address="bc1qactivekeep",
            is_used=True,
            used_by=test_user.telegram_id,
            order_id=active.id,
            used_at=stale,
        )
        db_session.add(kept)
        db_session.commit()

        with patch("bot.payments.crypto_addresses.readd_address_to_file"):
            count, reclaimed = reclaim_expired_addresses(ttl_hours=24)

        db_session.expire_all()
        held = db_session.query(CryptoAddress).filter_by(address="bc1qreclaimtest").one()
        kept = db_session.query(CryptoAddress).filter_by(address="bc1qactivekeep").one()

        assert count == 1
        assert "bc1qreclaimtest" in reclaimed
        assert held.is_used is False
        assert held.order_id is None
        assert held.used_at is None
        assert kept.is_used is True  # active order kept its address

    def test_not_reclaimed_within_ttl(self, db_session, test_user):
        # Cancelled order, but the address was claimed only an hour ago.
        recent = datetime.now(UTC) - timedelta(hours=1)
        order = _order(test_user.telegram_id, "RCL003", "cancelled")
        db_session.add(order)
        db_session.flush()
        addr = CryptoAddress(
            coin="btc",
            address="bc1qtooyoung",
            is_used=True,
            used_by=test_user.telegram_id,
            order_id=order.id,
            used_at=recent,
        )
        db_session.add(addr)
        db_session.commit()

        with patch("bot.payments.crypto_addresses.readd_address_to_file"):
            count, _reclaimed = reclaim_expired_addresses(ttl_hours=24)

        db_session.expire_all()
        addr = db_session.query(CryptoAddress).filter_by(address="bc1qtooyoung").one()
        assert count == 0
        assert addr.is_used is True

    @pytest.mark.asyncio
    async def test_overpayment_recorded(self, db_session, test_user):
        from bot.payments.chain_verify import TxResult
        from bot.tasks.payment_checker import check_pending_payments

        order = _order(test_user.telegram_id, "OVP001", "pending")
        db_session.add(order)
        db_session.flush()
        payment = CryptoPayment(
            order_id=order.id,
            coin="btc",
            receive_address="bc1qoverpay",
            expected_amount=Decimal("0.00100000"),
            required_confirmations=1,
            status="awaiting",
            expires_at=datetime.now(UTC) + timedelta(hours=2),
        )
        db_session.add(payment)
        db_session.commit()
        payment_id = payment.id

        # Verifier reports MORE than expected was received.
        verifier = AsyncMock()
        verifier.check_payment = AsyncMock(
            return_value=TxResult(
                found=True,
                tx_hash="overpaytx",
                amount=Decimal("0.00150000"),
                confirmations=2,
            )
        )

        bot = AsyncMock()
        with patch("bot.payments.chain_verify.get_verifier", return_value=verifier):
            await check_pending_payments(bot)

        db_session.expire_all()
        updated = db_session.get(CryptoPayment, payment_id)
        assert updated.received_amount == Decimal("0.00150000")
        assert updated.overpaid_amount == Decimal("0.00050000")
        assert updated.status == "confirmed"
