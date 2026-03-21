"""Tests for Thai address format JSON fields (Card 7)"""
import pytest
from datetime import datetime, timezone
from decimal import Decimal

from bot.database.models.main import Order, CustomerInfo, User


@pytest.mark.unit
@pytest.mark.models
class TestThaiAddressFields:
    """Test structured Thai address JSON columns"""

    def test_order_address_structured_json(self, db_with_roles, db_session):
        """Order can store and retrieve structured Thai address"""
        user = User(telegram_id=600001, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        thai_address = {
            "house": "123/45",
            "soi": "สุขุมวิท 23",
            "road": "ถ.สุขุมวิท",
            "subdistrict": "คลองเตยเหนือ",
            "district": "วัฒนา",
            "province": "กรุงเทพมหานคร",
            "postal_code": "10110"
        }

        order = Order(
            buyer_id=600001,
            total_price=Decimal("100.00"),
            payment_method="cash",
            delivery_address="123/45 สุขุมวิท 23",
            phone_number="0812345678"
        )
        order.address_structured = thai_address
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        assert order.address_structured is not None
        assert order.address_structured["soi"] == "สุขุมวิท 23"
        assert order.address_structured["postal_code"] == "10110"
        assert order.address_structured["province"] == "กรุงเทพมหานคร"

    def test_customer_info_address_structured(self, db_with_roles, db_session):
        """CustomerInfo saves structured address for reuse"""
        user = User(telegram_id=600002, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        customer = CustomerInfo(telegram_id=600002, phone_number="0812345678")
        customer.address_structured = {"house": "99", "soi": "ลาดพร้าว 71", "district": "บางกะปิ"}
        db_session.add(customer)
        db_session.commit()
        db_session.refresh(customer)

        assert customer.address_structured["soi"] == "ลาดพร้าว 71"

    def test_address_structured_nullable(self, db_with_roles, db_session):
        """Address structured field defaults to None (backward compatible)"""
        user = User(telegram_id=600003, registration_date=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()

        order = Order(
            buyer_id=600003,
            total_price=Decimal("50.00"),
            payment_method="cash",
            delivery_address="Free text address",
            phone_number="0812345678"
        )
        db_session.add(order)
        db_session.commit()

        assert order.address_structured is None
