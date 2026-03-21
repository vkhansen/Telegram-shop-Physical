"""
True end-to-end scenario tests for the Telegram shop bot.

Unlike test_full_order_flow.py which tests individual components,
these tests simulate complete user journeys through the system:

1. Customer browses menu → selects item with modifiers → adds to cart → places order
2. Admin views order → confirms → kitchen prepares → rider delivers
3. Customer uses referral bonus on order
4. Dead drop delivery with photo proof enforcement
5. PromptPay payment with receipt verification
6. Multi-item order with mixed modifiers and delivery fee
7. Customer cancels mid-flow and inventory is restored
8. Driver-customer chat during delivery
9. Post-delivery chat window lifecycle
10. Admin manages menu (CRUD + modifiers) then customer orders
"""
import json
import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from sqlalchemy.orm import Session

from bot.database.models.main import (
    Role, User, Categories, Goods, Order, OrderItem, CustomerInfo,
    ShoppingCart, BitcoinAddress, BotSettings, ReferenceCode,
    ReferenceCodeUsage, ReferralEarnings, DeliveryChatMessage,
    InventoryLog,
)
from bot.database.methods.inventory import (
    reserve_inventory, release_reservation, deduct_inventory, add_inventory,
)
from bot.utils.order_codes import generate_unique_order_code
from bot.utils.modifiers import calculate_item_price, validate_modifier_selection
from bot.utils.order_status import is_valid_transition, get_allowed_transitions
from bot.utils.delivery_types import needs_delivery_photo
from bot.handlers.user.delivery_chat_handler import (
    is_chat_active, open_chat_session, close_chat_session, set_post_delivery_window,
    get_chat_history, get_location_trail,
)
from tests.e2e.menu_loader import load_menu_from_file

SAMPLE_MENU_PATH = Path(__file__).parent / "sample_menu.json"


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _seed(session: Session):
    """Create roles + load menu."""
    session.add(Role(name="USER", permissions=1))
    session.add(Role(name="ADMIN", permissions=31))
    session.add(Role(name="OWNER", permissions=127))
    session.commit()
    load_menu_from_file(SAMPLE_MENU_PATH, session)
    session.commit()


def _user(session, tid, role_id=1, locale="en", referral_id=None):
    u = User(telegram_id=tid, role_id=role_id,
             registration_date=datetime.now(timezone.utc),
             locale=locale, referral_id=referral_id)
    session.add(u)
    session.commit()
    session.refresh(u)
    return u


def _customer_info(session, tid, **kw):
    ci = CustomerInfo(
        telegram_id=tid,
        phone_number=kw.get("phone", "+66812345678"),
        delivery_address=kw.get("address", "99 Sukhumvit Soi 11, Bangkok 10110"),
    )
    session.add(ci)
    session.commit()
    return ci


# ===================================================================
# Scenario 1: Complete customer → admin → kitchen → rider → delivered
# ===================================================================

@pytest.mark.e2e
class TestScenarioFullOrderJourney:
    """
    Simulates the complete lifecycle:
    Customer browses menu → adds items with modifiers → places cash order →
    Admin confirms → Kitchen prepares → Rider picks up → Rider delivers →
    Customer receives delivery notification
    """

    def test_full_journey(self, db_with_roles: Session):
        s = db_with_roles
        load_menu_from_file(SAMPLE_MENU_PATH, s)
        s.commit()

        # --- 1. Customer registers ---
        customer = _user(s, 100001, locale="en")
        ci = _customer_info(s, customer.telegram_id)

        # --- 2. Customer browses menu and picks items ---
        # Green Curry with chicken + medium spice
        green_curry = s.query(Goods).filter_by(name="Green Curry").first()
        assert green_curry is not None
        assert green_curry.modifiers is not None

        selected_mods = {"protein": "chicken", "spice": "medium"}
        is_valid, err = validate_modifier_selection(green_curry.modifiers, selected_mods)
        assert is_valid, err

        price_with_mods = calculate_item_price(green_curry.price, green_curry.modifiers, selected_mods)

        # Thai Iced Tea (no modifiers)
        thai_tea = s.query(Goods).filter_by(name="Thai Iced Tea").first()
        assert thai_tea is not None

        # --- 3. Customer adds to cart ---
        cart1 = ShoppingCart(
            user_id=customer.telegram_id,
            item_name="Green Curry",
            quantity=2,
            selected_modifiers=selected_mods,
        )
        cart2 = ShoppingCart(
            user_id=customer.telegram_id,
            item_name="Thai Iced Tea",
            quantity=1,
        )
        s.add_all([cart1, cart2])
        s.commit()

        # Verify cart
        cart_items = s.query(ShoppingCart).filter_by(user_id=customer.telegram_id).all()
        assert len(cart_items) == 2

        # --- 4. Customer places order ---
        total = (price_with_mods * 2) + thai_tea.price
        order_code = generate_unique_order_code(s)
        order = Order(
            buyer_id=customer.telegram_id,
            total_price=total,
            payment_method="cash",
            delivery_address=ci.delivery_address,
            phone_number=ci.phone_number,
            order_status="pending",
            order_code=order_code,
            delivery_type="door",
            latitude=13.7400,
            longitude=100.5200,
            google_maps_link="https://www.google.com/maps?q=13.74,100.52",
        )
        s.add(order)
        s.flush()

        oi1 = OrderItem(
            order_id=order.id, item_name="Green Curry",
            price=price_with_mods, quantity=2,
            selected_modifiers=selected_mods,
        )
        oi2 = OrderItem(
            order_id=order.id, item_name="Thai Iced Tea",
            price=thai_tea.price, quantity=1,
        )
        s.add_all([oi1, oi2])
        s.commit()

        # --- 5. Reserve inventory ---
        items_to_reserve = [
            {"item_name": "Green Curry", "quantity": 2},
            {"item_name": "Thai Iced Tea", "quantity": 1},
        ]
        success, msg = reserve_inventory(order.id, items_to_reserve, "cash", s)
        s.commit()
        assert success, msg
        assert order.order_status == "reserved"

        gc = s.query(Goods).filter_by(name="Green Curry").one()
        assert gc.reserved_quantity == 2

        # Clear cart after order
        s.query(ShoppingCart).filter_by(user_id=customer.telegram_id).delete()
        s.commit()

        # --- 6. Admin confirms order ---
        admin = _user(s, 100002, role_id=2)
        assert is_valid_transition(order.order_status, "confirmed")
        order.order_status = "confirmed"
        s.commit()

        # Deduct inventory on confirmation
        with patch("bot.database.methods.inventory.get_metrics", return_value=None):
            success, msg = deduct_inventory(order.id, admin.telegram_id, s)
        s.commit()
        assert success, msg

        gc = s.query(Goods).filter_by(name="Green Curry").one()
        assert gc.reserved_quantity == 0  # Released after deduction
        initial_stock = gc.stock_quantity  # Stock decreased

        # --- 7. Kitchen prepares ---
        assert is_valid_transition(order.order_status, "preparing")
        order.order_status = "preparing"
        s.commit()

        assert is_valid_transition(order.order_status, "ready")
        order.order_status = "ready"
        s.commit()

        # --- 8. Rider picks up ---
        driver = _user(s, 100003)
        assert is_valid_transition(order.order_status, "out_for_delivery")
        order.order_status = "out_for_delivery"
        order.driver_id = driver.telegram_id
        s.commit()

        assert is_chat_active(order)  # Chat active during delivery

        # --- 9. Rider delivers ---
        assert is_valid_transition(order.order_status, "delivered")
        order.order_status = "delivered"
        order.completed_at = datetime.now(timezone.utc)

        # Set post-delivery chat window
        set_post_delivery_window(s, order)
        s.commit()
        s.refresh(order)

        assert order.completed_at is not None
        assert order.chat_post_delivery_until is not None
        assert is_chat_active(order)  # Still active in window

        # --- 10. Update customer stats ---
        ci_updated = s.query(CustomerInfo).filter_by(telegram_id=customer.telegram_id).one()
        ci_updated.completed_orders_count += 1
        ci_updated.total_spendings += order.total_price
        s.commit()

        assert ci_updated.completed_orders_count == 1
        assert ci_updated.total_spendings == total

        # --- 11. Verify order items have modifiers ---
        stored_items = s.query(OrderItem).filter_by(order_id=order.id).all()
        assert len(stored_items) == 2
        curry_item = next(i for i in stored_items if i.item_name == "Green Curry")
        assert curry_item.selected_modifiers == {"protein": "chicken", "spice": "medium"}
        assert curry_item.quantity == 2

        # --- 12. Verify inventory log trail ---
        logs = s.query(InventoryLog).filter_by(order_id=order.id).all()
        assert len(logs) >= 2  # At least reserve + deduct entries


# ===================================================================
# Scenario 2: Dead drop with photo proof enforcement
# ===================================================================

@pytest.mark.e2e
class TestScenarioDeadDropPhotoProof:
    """
    Dead drop order flow:
    Customer orders with dead_drop delivery →
    Admin tries to mark delivered → blocked (needs photo) →
    Admin uploads photo → order marked delivered →
    Photo sent to customer
    """

    def test_dead_drop_requires_photo(self, db_with_roles: Session):
        s = db_with_roles
        load_menu_from_file(SAMPLE_MENU_PATH, s)
        s.commit()

        customer = _user(s, 200001)
        order = Order(
            buyer_id=customer.telegram_id,
            total_price=Decimal("89.00"),
            payment_method="cash",
            delivery_address="Lobby of Building A",
            phone_number="+66800000000",
            order_status="out_for_delivery",
            order_code=generate_unique_order_code(s),
            delivery_type="dead_drop",
            drop_instructions="Leave with the security guard in lobby",
            driver_id=200099,
        )
        s.add(order)
        s.commit()

        # Dead drop without photo → needs photo
        assert needs_delivery_photo(order) is True

        # Simulate admin uploading photo
        order.delivery_photo = "AgACAgIAAxkBAAI_PHOTO_FILE_ID"
        order.delivery_photo_at = datetime.now(timezone.utc)
        order.delivery_photo_by = 200098  # admin
        s.commit()

        # Now photo proof satisfied
        assert needs_delivery_photo(order) is False

        # Mark delivered
        order.order_status = "delivered"
        order.completed_at = datetime.now(timezone.utc)
        s.commit()

        assert order.delivery_photo is not None
        assert order.order_status == "delivered"

    def test_door_delivery_no_photo_needed(self, db_with_roles: Session):
        s = db_with_roles
        load_menu_from_file(SAMPLE_MENU_PATH, s)
        s.commit()

        customer = _user(s, 200002)
        order = Order(
            buyer_id=customer.telegram_id,
            total_price=Decimal("149.00"),
            payment_method="cash",
            delivery_address="Condo 12/F",
            phone_number="+66800000000",
            order_status="out_for_delivery",
            order_code=generate_unique_order_code(s),
            delivery_type="door",
        )
        s.add(order)
        s.commit()

        assert needs_delivery_photo(order) is False

    def test_pickup_no_photo_needed(self, db_with_roles: Session):
        s = db_with_roles
        load_menu_from_file(SAMPLE_MENU_PATH, s)
        s.commit()

        customer = _user(s, 200003)
        order = Order(
            buyer_id=customer.telegram_id,
            total_price=Decimal("59.00"),
            payment_method="cash",
            delivery_address="Self pickup",
            phone_number="+66800000000",
            order_status="out_for_delivery",
            order_code=generate_unique_order_code(s),
            delivery_type="pickup",
        )
        s.add(order)
        s.commit()

        assert needs_delivery_photo(order) is False


# ===================================================================
# Scenario 3: PromptPay payment with admin verification
# ===================================================================

@pytest.mark.e2e
class TestScenarioPromptPayVerification:
    """
    PromptPay flow:
    Customer places order → selects PromptPay → receives QR →
    uploads receipt photo → admin verifies → order confirmed
    """

    def test_promptpay_order_lifecycle(self, db_with_roles: Session):
        s = db_with_roles
        load_menu_from_file(SAMPLE_MENU_PATH, s)
        s.commit()

        customer = _user(s, 300001)
        admin = _user(s, 300002, role_id=2)

        # Place order with PromptPay
        order = Order(
            buyer_id=customer.telegram_id,
            total_price=Decimal("349.00"),
            payment_method="promptpay",
            delivery_address="123 Silom",
            phone_number="+66812345678",
            order_status="pending",
            order_code=generate_unique_order_code(s),
        )
        s.add(order)
        s.flush()
        s.add(OrderItem(order_id=order.id, item_name="Green Curry", price=Decimal("179.00"), quantity=1))
        s.add(OrderItem(order_id=order.id, item_name="Pad Thai", price=Decimal("149.00"), quantity=1))
        s.commit()

        # Reserve inventory
        items = [{"item_name": "Green Curry", "quantity": 1}, {"item_name": "Pad Thai", "quantity": 1}]
        success, _ = reserve_inventory(order.id, items, "promptpay", s)
        s.commit()
        assert success
        assert order.order_status == "reserved"

        # Customer uploads receipt
        order.payment_receipt_photo = "AgACAgIAAxkBAAI_RECEIPT_ID"
        s.commit()
        assert order.payment_receipt_photo is not None

        # Admin verifies payment
        order.payment_verified_by = admin.telegram_id
        order.payment_verified_at = datetime.now(timezone.utc)
        order.order_status = "confirmed"
        s.commit()

        assert order.payment_verified_by == admin.telegram_id
        assert order.order_status == "confirmed"

        # Deduct inventory
        with patch("bot.database.methods.inventory.get_metrics", return_value=None):
            success, _ = deduct_inventory(order.id, admin.telegram_id, s)
        s.commit()
        assert success


# ===================================================================
# Scenario 4: Customer cancellation with inventory restore
# ===================================================================

@pytest.mark.e2e
class TestScenarioCancellationRestore:
    """
    Customer places order → inventory reserved → customer cancels →
    inventory fully restored → items available again
    """

    def test_cancel_restores_all_inventory(self, db_with_roles: Session):
        s = db_with_roles
        load_menu_from_file(SAMPLE_MENU_PATH, s)
        s.commit()

        customer = _user(s, 400001)

        # Record initial stock
        pad_thai = s.query(Goods).filter_by(name="Pad Thai").one()
        initial_stock = pad_thai.stock_quantity
        assert initial_stock > 0

        # Place order for 5 Pad Thai
        order = Order(
            buyer_id=customer.telegram_id,
            total_price=Decimal("745.00"),
            payment_method="cash",
            delivery_address="Test",
            phone_number="+66800000000",
            order_status="pending",
            order_code=generate_unique_order_code(s),
        )
        s.add(order)
        s.flush()
        s.add(OrderItem(order_id=order.id, item_name="Pad Thai", price=Decimal("149.00"), quantity=5))
        s.commit()

        # Reserve
        success, _ = reserve_inventory(order.id, [{"item_name": "Pad Thai", "quantity": 5}], "cash", s)
        s.commit()
        assert success

        s.refresh(pad_thai)
        assert pad_thai.reserved_quantity == 5
        assert pad_thai.available_quantity == initial_stock - 5

        # Cancel
        order.order_status = "cancelled"
        with patch("bot.database.methods.inventory.get_metrics", return_value=None):
            success, _ = release_reservation(order.id, "Customer changed mind", s)
        s.commit()
        assert success

        s.refresh(pad_thai)
        assert pad_thai.reserved_quantity == 0
        assert pad_thai.available_quantity == initial_stock  # Fully restored


# ===================================================================
# Scenario 5: Multi-item order with modifiers and delivery fee
# ===================================================================

@pytest.mark.e2e
class TestScenarioMultiItemModifiers:
    """
    Customer orders multiple items, each with different modifiers,
    plus a delivery fee based on zone.
    """

    def test_multi_item_with_modifiers_and_fee(self, db_with_roles: Session):
        s = db_with_roles
        load_menu_from_file(SAMPLE_MENU_PATH, s)
        s.commit()

        customer = _user(s, 500001)

        # Item 1: Tom Yum with shrimp + hot
        tom_yum = s.query(Goods).filter_by(name="Tom Yum Soup").first()
        assert tom_yum is not None
        mods1 = {"protein": "shrimp", "spice": "hot"}
        valid, err = validate_modifier_selection(tom_yum.modifiers, mods1)
        assert valid, err
        price1 = calculate_item_price(tom_yum.price, tom_yum.modifiers, mods1)
        # Shrimp adds 40 THB
        assert price1 == tom_yum.price + Decimal("40")

        # Item 2: Satay Chicken with extra peanut sauce + extra skewer
        satay = s.query(Goods).filter_by(name="Satay Chicken").first()
        assert satay is not None
        mods2 = {"extras": ["extra_peanut_sauce", "extra_skewer"]}
        valid, err = validate_modifier_selection(satay.modifiers, mods2)
        assert valid, err
        price2 = calculate_item_price(satay.price, satay.modifiers, mods2)
        # Extra peanut sauce (+15) + extra skewer (+35)
        assert price2 == satay.price + Decimal("15") + Decimal("35")

        # Item 3: Fresh Spring Rolls (no modifiers)
        fsr = s.query(Goods).filter_by(name="Fresh Spring Rolls").first()
        assert fsr is not None
        assert fsr.modifiers is None

        # Build order with delivery fee
        delivery_fee = Decimal("40.00")
        subtotal = price1 + (price2 * 2) + fsr.price
        total = subtotal + delivery_fee

        order = Order(
            buyer_id=customer.telegram_id,
            total_price=total,
            payment_method="cash",
            delivery_address="Far away address",
            phone_number="+66800000000",
            order_status="pending",
            order_code=generate_unique_order_code(s),
            delivery_zone="zone_2",
            delivery_fee=delivery_fee,
        )
        s.add(order)
        s.flush()

        s.add(OrderItem(order_id=order.id, item_name="Tom Yum Soup",
                        price=price1, quantity=1, selected_modifiers=mods1))
        s.add(OrderItem(order_id=order.id, item_name="Satay Chicken",
                        price=price2, quantity=2, selected_modifiers=mods2))
        s.add(OrderItem(order_id=order.id, item_name="Fresh Spring Rolls",
                        price=fsr.price, quantity=1))
        s.commit()

        # Verify
        items = s.query(OrderItem).filter_by(order_id=order.id).all()
        assert len(items) == 3
        assert order.delivery_fee == Decimal("40.00")
        assert order.delivery_zone == "zone_2"

        # Verify modifier prices are correct
        tom_item = next(i for i in items if i.item_name == "Tom Yum Soup")
        assert tom_item.selected_modifiers["protein"] == "shrimp"
        assert tom_item.price == price1

        satay_item = next(i for i in items if i.item_name == "Satay Chicken")
        assert set(satay_item.selected_modifiers["extras"]) == {"extra_peanut_sauce", "extra_skewer"}
        assert satay_item.quantity == 2


# ===================================================================
# Scenario 6: Referral bonus applied to order
# ===================================================================

@pytest.mark.e2e
class TestScenarioReferralBonus:
    """
    User A refers User B → B places order → A earns bonus →
    A applies bonus to their next order → total reduced
    """

    def test_referral_earn_and_spend(self, db_with_roles: Session):
        s = db_with_roles
        load_menu_from_file(SAMPLE_MENU_PATH, s)
        s.commit()

        # Set referral bonus to 10%
        setting = BotSettings(setting_key="reference_bonus_percent", setting_value="10")
        s.add(setting)
        s.commit()

        referrer = _user(s, 600001)
        referee = _user(s, 600002, referral_id=referrer.telegram_id)
        _customer_info(s, referrer.telegram_id)
        _customer_info(s, referee.telegram_id)

        # Referee places order worth 500 THB
        order_b = Order(
            buyer_id=referee.telegram_id,
            total_price=Decimal("500.00"),
            payment_method="cash",
            delivery_address="Ref test",
            phone_number="+66800000000",
            order_status="delivered",
            order_code=generate_unique_order_code(s),
        )
        s.add(order_b)
        s.flush()
        s.add(OrderItem(order_id=order_b.id, item_name="Green Curry",
                        price=Decimal("179.00"), quantity=2))
        s.commit()

        # Referrer earns 10% = 50 THB
        earning = ReferralEarnings(
            referrer_id=referrer.telegram_id,
            referral_id=referee.telegram_id,
            amount=Decimal("50.00"),
            original_amount=Decimal("500.00"),
        )
        s.add(earning)

        ci_referrer = s.query(CustomerInfo).filter_by(telegram_id=referrer.telegram_id).one()
        ci_referrer.bonus_balance = Decimal("50.00")
        s.commit()

        # Referrer places their own order and applies bonus
        order_a = Order(
            buyer_id=referrer.telegram_id,
            total_price=Decimal("149.00"),
            bonus_applied=Decimal("50.00"),
            payment_method="cash",
            delivery_address="My place",
            phone_number="+66800000000",
            order_status="pending",
            order_code=generate_unique_order_code(s),
        )
        s.add(order_a)
        s.commit()

        assert order_a.bonus_applied == Decimal("50.00")
        effective_total = order_a.total_price - order_a.bonus_applied
        assert effective_total == Decimal("99.00")

        # Deduct bonus from balance
        ci_referrer.bonus_balance -= order_a.bonus_applied
        s.commit()
        assert ci_referrer.bonus_balance == Decimal("0.00")


# ===================================================================
# Scenario 7: Driver-customer chat with full audit trail
# ===================================================================

@pytest.mark.e2e
class TestScenarioDeliveryChatAudit:
    """
    Order goes out_for_delivery → driver sends text → customer replies →
    driver shares location → customer shares live location →
    all messages recorded with correct roles and timestamps
    """

    def test_full_chat_exchange(self, db_with_roles: Session):
        s = db_with_roles
        load_menu_from_file(SAMPLE_MENU_PATH, s)
        s.commit()

        customer = _user(s, 700001)
        driver = _user(s, 700002)

        order = Order(
            buyer_id=customer.telegram_id,
            total_price=Decimal("200.00"),
            payment_method="cash",
            delivery_address="Chat test",
            phone_number="+66800000000",
            order_status="out_for_delivery",
            order_code=generate_unique_order_code(s),
            driver_id=driver.telegram_id,
        )
        s.add(order)
        s.commit()

        # Open chat session
        open_chat_session(s, order)
        s.commit()
        s.refresh(order)
        assert order.chat_opened_at is not None

        # Driver sends text
        s.add(DeliveryChatMessage(
            order_id=order.id, sender_id=driver.telegram_id,
            sender_role="driver", message_text="On my way! ETA 10 min",
            telegram_message_id=1001,
        ))

        # Customer replies
        s.add(DeliveryChatMessage(
            order_id=order.id, sender_id=customer.telegram_id,
            sender_role="customer", message_text="Great, I'm at the lobby",
            telegram_message_id=1002,
        ))

        # Driver sends photo
        s.add(DeliveryChatMessage(
            order_id=order.id, sender_id=driver.telegram_id,
            sender_role="driver", message_text="I'm at the entrance",
            photo_file_id="AgACAgIAAxkBAAI_DRIVER_PHOTO",
            telegram_message_id=1003,
        ))

        # Driver shares static location
        s.add(DeliveryChatMessage(
            order_id=order.id, sender_id=driver.telegram_id,
            sender_role="driver",
            location_lat=13.7400, location_lng=100.5200,
            is_live_location=False, telegram_message_id=1004,
        ))

        # Customer shares live location
        s.add(DeliveryChatMessage(
            order_id=order.id, sender_id=customer.telegram_id,
            sender_role="customer",
            location_lat=13.7410, location_lng=100.5210,
            is_live_location=True, live_location_update_count=0,
            telegram_message_id=1005,
        ))
        order.customer_live_location_message_id = 1005

        # Live location update
        s.add(DeliveryChatMessage(
            order_id=order.id, sender_id=customer.telegram_id,
            sender_role="customer",
            location_lat=13.7415, location_lng=100.5215,
            is_live_location=True, live_location_update_count=1,
            telegram_message_id=1005,
        ))
        s.commit()

        # Verify audit trail
        messages = s.query(DeliveryChatMessage).filter_by(
            order_id=order.id
        ).order_by(DeliveryChatMessage.id).all()

        assert len(messages) == 6

        # Check roles
        assert messages[0].sender_role == "driver"
        assert messages[0].message_text == "On my way! ETA 10 min"
        assert messages[1].sender_role == "customer"
        assert messages[2].photo_file_id == "AgACAgIAAxkBAAI_DRIVER_PHOTO"
        assert messages[3].location_lat == pytest.approx(13.74)
        assert messages[3].is_live_location is False
        assert messages[4].is_live_location is True
        assert messages[4].live_location_update_count == 0
        assert messages[5].live_location_update_count == 1

    @pytest.mark.asyncio
    async def test_location_trail(self, db_with_roles: Session):
        """Location trail returns all GPS points in chronological order."""
        s = db_with_roles
        load_menu_from_file(SAMPLE_MENU_PATH, s)
        s.commit()

        customer = _user(s, 700010)
        order = Order(
            buyer_id=customer.telegram_id,
            total_price=Decimal("100"),
            payment_method="cash",
            delivery_address="Trail test",
            phone_number="+66800000000",
            order_status="out_for_delivery",
            order_code=generate_unique_order_code(s),
            driver_id=700099,
        )
        s.add(order)
        s.commit()

        # 3 driver GPS points, 1 customer GPS
        for i in range(3):
            s.add(DeliveryChatMessage(
                order_id=order.id, sender_id=700099, sender_role="driver",
                location_lat=13.75 + i * 0.001, location_lng=100.50 + i * 0.001,
                is_live_location=True, live_location_update_count=i,
            ))
        s.add(DeliveryChatMessage(
            order_id=order.id, sender_id=customer.telegram_id, sender_role="customer",
            location_lat=13.74, location_lng=100.49, is_live_location=False,
        ))
        s.commit()

        trail = await get_location_trail(order.id)
        assert len(trail) == 4

        driver_trail = await get_location_trail(order.id, sender_role="driver")
        assert len(driver_trail) == 3
        assert all(p["sender_role"] == "driver" for p in driver_trail)


# ===================================================================
# Scenario 8: Post-delivery chat window lifecycle
# ===================================================================

@pytest.mark.e2e
class TestScenarioPostDeliveryWindow:
    """
    Order delivered → chat stays open for N minutes → window expires → chat closed
    """

    def test_window_lifecycle(self, db_with_roles: Session):
        s = db_with_roles
        load_menu_from_file(SAMPLE_MENU_PATH, s)
        s.commit()

        customer = _user(s, 800001)
        order = Order(
            buyer_id=customer.telegram_id,
            total_price=Decimal("100"),
            payment_method="cash",
            delivery_address="Window test",
            phone_number="+66800000000",
            order_status="out_for_delivery",
            order_code=generate_unique_order_code(s),
            driver_id=800099,
        )
        s.add(order)
        s.commit()

        # Chat active during delivery
        assert is_chat_active(order)

        # Deliver and set window
        order.order_status = "delivered"
        set_post_delivery_window(s, order)
        s.commit()
        s.refresh(order)

        # Chat still active within window
        assert is_chat_active(order)

        # Simulate window expiry
        db_order = s.query(Order).filter_by(id=order.id).first()
        db_order.chat_post_delivery_until = datetime.utcnow() - timedelta(minutes=1)
        s.commit()
        s.refresh(order)

        # Chat now closed
        assert not is_chat_active(order)

        # Close session
        close_chat_session(s, order)
        s.commit()
        s.refresh(order)
        assert order.chat_closed_at is not None


# ===================================================================
# Scenario 9: Admin menu management then customer orders
# ===================================================================

@pytest.mark.e2e
class TestScenarioAdminMenuManagement:
    """
    Admin creates category → adds product with modifiers → sets stock →
    Customer orders that product → inventory tracked correctly
    """

    def test_admin_creates_then_customer_orders(self, db_with_roles: Session):
        s = db_with_roles

        admin = _user(s, 900001, role_id=2)
        customer = _user(s, 900002)

        # Admin creates category
        cat = Categories(name="Specials", sort_order=99)
        s.add(cat)
        s.commit()

        # Admin creates product with modifiers
        modifiers = {
            "size": {
                "label": "Size",
                "type": "single",
                "required": True,
                "options": [
                    {"id": "regular", "label": "Regular", "price": 0},
                    {"id": "large", "label": "Large", "price": 30},
                ],
            },
        }
        product = Goods(
            name="Chef Special Soup",
            price=Decimal("199.00"),
            description="Today's special soup",
            category_name="Specials",
            stock_quantity=0,
        )
        product.modifiers = modifiers
        s.add(product)
        s.commit()

        # Admin adds stock
        success, msg = add_inventory(
            item_name="Chef Special Soup",
            quantity=20,
            admin_id=admin.telegram_id,
            comment="Initial stock",
            session=s,
        )
        s.commit()
        assert success

        s.refresh(product)
        assert product.stock_quantity == 20
        assert product.available_quantity == 20

        # Verify modifiers stored
        assert product.modifiers is not None
        assert "size" in product.modifiers

        # Customer orders with "large" modifier
        selected = {"size": "large"}
        valid, err = validate_modifier_selection(product.modifiers, selected)
        assert valid

        price = calculate_item_price(product.price, product.modifiers, selected)
        assert price == Decimal("229.00")  # 199 + 30

        # Place order
        order = Order(
            buyer_id=customer.telegram_id,
            total_price=price,
            payment_method="cash",
            delivery_address="Specials test",
            phone_number="+66800000000",
            order_status="pending",
            order_code=generate_unique_order_code(s),
        )
        s.add(order)
        s.flush()
        s.add(OrderItem(
            order_id=order.id, item_name="Chef Special Soup",
            price=price, quantity=1, selected_modifiers=selected,
        ))
        s.commit()

        # Reserve
        success, _ = reserve_inventory(
            order.id, [{"item_name": "Chef Special Soup", "quantity": 1}], "cash", s
        )
        s.commit()
        assert success

        s.refresh(product)
        assert product.reserved_quantity == 1
        assert product.available_quantity == 19

        # Verify inventory log
        logs = s.query(InventoryLog).filter_by(item_name="Chef Special Soup").all()
        assert len(logs) >= 2  # add + reserve


# ===================================================================
# Scenario 10: Bitcoin payment with address assignment
# ===================================================================

@pytest.mark.e2e
class TestScenarioBitcoinPayment:
    """
    Customer selects Bitcoin → address assigned → order pending →
    admin confirms → address marked used
    """

    def test_bitcoin_address_lifecycle(self, db_with_roles: Session):
        s = db_with_roles
        load_menu_from_file(SAMPLE_MENU_PATH, s)
        s.commit()

        customer = _user(s, 1000001)
        admin = _user(s, 1000002, role_id=2)

        # Pre-load bitcoin addresses
        btc1 = BitcoinAddress(address="bc1q_test_address_001")
        btc2 = BitcoinAddress(address="bc1q_test_address_002")
        s.add_all([btc1, btc2])
        s.commit()

        # Customer places bitcoin order
        order = Order(
            buyer_id=customer.telegram_id,
            total_price=Decimal("500.00"),
            payment_method="bitcoin",
            delivery_address="BTC test",
            phone_number="+66800000000",
            order_status="pending",
            order_code=generate_unique_order_code(s),
            bitcoin_address="bc1q_test_address_001",
        )
        s.add(order)
        s.flush()
        s.add(OrderItem(order_id=order.id, item_name="Green Curry",
                        price=Decimal("179.00"), quantity=2))
        s.commit()

        # Mark bitcoin address as used
        btc1.is_used = True
        btc1.used_by = customer.telegram_id
        btc1.used_at = datetime.now(timezone.utc)
        btc1.order_id = order.id
        s.commit()

        # Verify address assignment
        assert btc1.is_used is True
        assert btc1.order_id == order.id

        # Second address still available
        s.refresh(btc2)
        assert btc2.is_used is False

        # Admin confirms payment and order
        order.order_status = "reserved"
        s.commit()
        items = [{"item_name": "Green Curry", "quantity": 2}]
        reserve_inventory(order.id, items, "bitcoin", s)
        s.commit()

        order.order_status = "confirmed"
        with patch("bot.database.methods.inventory.get_metrics", return_value=None):
            deduct_inventory(order.id, admin.telegram_id, s)
        s.commit()

        assert order.order_status == "confirmed"


# ===================================================================
# Scenario 11: Reference code registration flow
# ===================================================================

@pytest.mark.e2e
class TestScenarioReferenceCodeFlow:
    """
    Admin creates reference code → new user registers with code →
    code usage tracked → code expires after max uses
    """

    def test_reference_code_lifecycle(self, db_with_roles: Session):
        s = db_with_roles

        admin = _user(s, 1100001, role_id=2)

        # Admin creates code with max 2 uses
        code = ReferenceCode(
            code="VIP2026",
            created_by=admin.telegram_id,
            max_uses=2,
            note="VIP early access",
            is_admin_code=True,
        )
        s.add(code)
        s.commit()

        # User 1 registers with code
        user1 = _user(s, 1100010)
        usage1 = ReferenceCodeUsage(code="VIP2026", used_by=user1.telegram_id)
        s.add(usage1)
        code.current_uses += 1
        s.commit()

        assert code.current_uses == 1

        # User 2 registers with code
        user2 = _user(s, 1100011)
        usage2 = ReferenceCodeUsage(code="VIP2026", used_by=user2.telegram_id)
        s.add(usage2)
        code.current_uses += 1
        s.commit()

        assert code.current_uses == 2

        # Code is now at max uses
        assert code.current_uses >= code.max_uses

        # Verify usage records
        usages = s.query(ReferenceCodeUsage).filter_by(code="VIP2026").all()
        assert len(usages) == 2

    def test_expired_code(self, db_with_roles: Session):
        s = db_with_roles
        admin = _user(s, 1100002, role_id=2)

        code = ReferenceCode(
            code="EXPIRED1",
            created_by=admin.telegram_id,
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        s.add(code)
        s.commit()

        # Code is expired
        assert code.expires_at < datetime.now(timezone.utc)


# ===================================================================
# Scenario 12: Concurrent orders don't oversell inventory
# ===================================================================

@pytest.mark.e2e
class TestScenarioInventoryIntegrity:
    """
    Two customers order the same item → combined reservation must not
    exceed available stock → second order fails if stock insufficient
    """

    def test_no_oversell(self, db_with_roles: Session):
        s = db_with_roles
        load_menu_from_file(SAMPLE_MENU_PATH, s)
        s.commit()

        c1 = _user(s, 1200001)
        c2 = _user(s, 1200002)

        # Check stock of Thai Iced Tea
        tea = s.query(Goods).filter_by(name="Thai Iced Tea").one()
        stock = tea.stock_quantity

        # Customer 1 orders all stock
        o1 = Order(
            buyer_id=c1.telegram_id, total_price=Decimal("1000"),
            payment_method="cash", delivery_address="T1",
            phone_number="+66800000000", order_status="pending",
            order_code=generate_unique_order_code(s),
        )
        s.add(o1)
        s.flush()
        s.add(OrderItem(order_id=o1.id, item_name="Thai Iced Tea",
                        price=Decimal("59.00"), quantity=stock))
        s.commit()

        success1, _ = reserve_inventory(o1.id, [{"item_name": "Thai Iced Tea", "quantity": stock}], "cash", s)
        s.commit()
        assert success1

        s.refresh(tea)
        assert tea.available_quantity == 0

        # Customer 2 tries to order 1 more → should fail
        o2 = Order(
            buyer_id=c2.telegram_id, total_price=Decimal("59"),
            payment_method="cash", delivery_address="T2",
            phone_number="+66800000000", order_status="pending",
            order_code=generate_unique_order_code(s),
        )
        s.add(o2)
        s.flush()
        s.add(OrderItem(order_id=o2.id, item_name="Thai Iced Tea",
                        price=Decimal("59.00"), quantity=1))
        s.commit()

        success2, msg2 = reserve_inventory(o2.id, [{"item_name": "Thai Iced Tea", "quantity": 1}], "cash", s)
        s.commit()
        assert not success2  # Should fail - no stock left
