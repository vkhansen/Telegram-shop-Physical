"""
E2E tests for multi-location shop setup, GPS-based store selection,
full order flow with store context, and cascade/cleanup behaviour.

Tests operate at the database/model level — no Telegram API mocking.
"""
import math
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from bot.database.models.main import (
    Brand,
    Categories,
    Goods,
    Order,
    OrderItem,
    ShoppingCart,
    Store,
    User,
)
from bot.handlers.user.store_selection import _haversine


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_user(session: Session, telegram_id: int, role_id: int = 1) -> User:
    user = User(
        telegram_id=telegram_id,
        role_id=role_id,
        registration_date=datetime.now(UTC),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def _create_brand(session: Session, name: str, slug: str, description: str = None) -> Brand:
    brand = Brand(name=name, slug=slug, description=description)
    session.add(brand)
    session.commit()
    session.refresh(brand)
    return brand


def _create_store(
    session: Session,
    brand: Brand,
    name: str,
    address: str = None,
    latitude: float = None,
    longitude: float = None,
    is_default: bool = False,
) -> Store:
    store = Store(
        name=name,
        brand_id=brand.id,
        address=address,
        latitude=latitude,
        longitude=longitude,
        is_default=is_default,
    )
    session.add(store)
    session.commit()
    session.refresh(store)
    return store


def _create_order(
    session: Session,
    buyer: User,
    brand: Brand,
    store: Store = None,
    total_price: Decimal = Decimal("100.00"),
    delivery_type: str = "door",
    bonus_applied: Decimal = Decimal("0"),
) -> Order:
    order = Order(
        buyer_id=buyer.telegram_id,
        total_price=total_price,
        payment_method="cash",
        delivery_address="123 Test Street",
        phone_number="+66812345678",
        order_code=f"T{buyer.telegram_id % 10000:05d}",
        delivery_type=delivery_type,
        bonus_applied=bonus_applied,
    )
    order.brand_id = brand.id
    if store:
        order.store_id = store.id
    session.add(order)
    session.commit()
    session.refresh(order)
    return order


# ===================================================================
# 1. TestMultiLocationSetup
# ===================================================================

@pytest.mark.e2e
class TestMultiLocationSetup:
    """Verify brand/store creation and product linkage."""

    def test_brand_with_multiple_stores(self, db_session: Session):
        """Create brand 'TestCoffee' with 2 stores, verify both persisted with correct brand_id."""
        brand = _create_brand(db_session, "TestCoffee", "testcoffee", "Best coffee")

        store_bkk = _create_store(db_session, brand, "Bangkok Central", address="Silom Rd")
        store_phuket = _create_store(db_session, brand, "Phuket Beach", address="Patong Beach Rd")

        stores = db_session.query(Store).filter_by(brand_id=brand.id).all()
        assert len(stores) == 2

        store_names = {s.name for s in stores}
        assert store_names == {"Bangkok Central", "Phuket Beach"}
        for s in stores:
            assert s.brand_id == brand.id

    def test_store_gps_coordinates(self, db_session: Session):
        """Verify store GPS lat/lng are stored correctly."""
        brand = _create_brand(db_session, "GPSBrand", "gpsbrand")
        store = _create_store(
            db_session, brand, "GPS Store",
            latitude=13.7563, longitude=100.5018,
        )

        fetched = db_session.query(Store).filter_by(id=store.id).one()
        assert fetched.latitude == pytest.approx(13.7563, abs=1e-4)
        assert fetched.longitude == pytest.approx(100.5018, abs=1e-4)

    def test_products_linked_to_brand(self, db_session: Session):
        """Create products under a brand, verify category/goods belong to brand."""
        brand = _create_brand(db_session, "ProductBrand", "productbrand")

        cat = Categories(name="Coffee", brand_id=brand.id)
        db_session.add(cat)
        db_session.commit()

        goods = Goods(
            name="Espresso",
            price=Decimal("59.00"),
            description="Single shot",
            category_name=cat.name,
            stock_quantity=200,
            reserved_quantity=0,
            brand_id=brand.id,
            item_type="prepared",
        )
        db_session.add(goods)
        db_session.commit()

        fetched_cat = db_session.query(Categories).filter_by(brand_id=brand.id).one()
        assert fetched_cat.name == "Coffee"

        fetched_goods = db_session.query(Goods).filter_by(brand_id=brand.id).all()
        assert len(fetched_goods) == 1
        assert fetched_goods[0].name == "Espresso"
        assert fetched_goods[0].category_name == cat.name


# ===================================================================
# 2. TestLocationSelection
# ===================================================================

@pytest.mark.e2e
class TestLocationSelection:
    """Test auto-select and GPS-nearest logic for store selection."""

    def test_single_store_auto_selects(self, db_session: Session):
        """Brand with 1 store -> store_id auto-selected (only one option)."""
        brand = _create_brand(db_session, "SingleStore", "singlestore")
        store = _create_store(db_session, brand, "Only Branch")

        stores = db_session.query(Store).filter_by(brand_id=brand.id, is_active=True).all()
        assert len(stores) == 1
        # With a single store the handler auto-selects it
        auto_selected = stores[0]
        assert auto_selected.id == store.id

    def test_multiple_stores_listed(self, db_session: Session):
        """Brand with 2+ stores -> both appear in selection."""
        brand = _create_brand(db_session, "MultiStore", "multistore")
        s1 = _create_store(db_session, brand, "Branch A")
        s2 = _create_store(db_session, brand, "Branch B")

        stores = db_session.query(Store).filter_by(brand_id=brand.id, is_active=True).all()
        assert len(stores) == 2
        store_ids = {s.id for s in stores}
        assert s1.id in store_ids
        assert s2.id in store_ids

    def test_nearest_store_by_gps(self, db_session: Session):
        """Given user GPS coords, verify haversine calculation picks nearest store."""
        brand = _create_brand(db_session, "NearBrand", "nearbrand")
        # Bangkok Central — 13.7563, 100.5018
        store_bkk = _create_store(
            db_session, brand, "Bangkok Central",
            latitude=13.7563, longitude=100.5018,
        )
        # Phuket Beach — 7.8804, 98.3923
        store_phuket = _create_store(
            db_session, brand, "Phuket Beach",
            latitude=7.8804, longitude=98.3923,
        )

        # User is near Bangkok (13.75, 100.50)
        user_lat, user_lng = 13.75, 100.50
        stores = db_session.query(Store).filter_by(brand_id=brand.id, is_active=True).all()
        stores_with_gps = [s for s in stores if s.latitude and s.longitude]

        nearest = min(
            stores_with_gps,
            key=lambda s: _haversine(user_lat, user_lng, s.latitude, s.longitude),
        )
        assert nearest.id == store_bkk.id

        # User near Phuket (7.88, 98.40)
        user_lat, user_lng = 7.88, 98.40
        nearest = min(
            stores_with_gps,
            key=lambda s: _haversine(user_lat, user_lng, s.latitude, s.longitude),
        )
        assert nearest.id == store_phuket.id


# ===================================================================
# 3. TestFullOrderFlowWithLocation
# ===================================================================

@pytest.mark.e2e
class TestFullOrderFlowWithLocation:
    """Test order creation with store context."""

    def test_create_order_with_store_id(self, db_with_roles: Session):
        """Create a full order with store_id set, verify it persists."""
        brand = _create_brand(db_with_roles, "OrderBrand", "orderbrand")
        store = _create_store(db_with_roles, brand, "Order Branch")
        user = _create_user(db_with_roles, telegram_id=7001)

        order = _create_order(db_with_roles, user, brand, store=store)

        fetched = db_with_roles.query(Order).filter_by(id=order.id).one()
        assert fetched.store_id == store.id
        assert fetched.brand_id == brand.id

    def test_order_items_match_cart(self, db_with_roles: Session):
        """Add items to cart, create order, verify OrderItem rows match."""
        brand = _create_brand(db_with_roles, "CartBrand", "cartbrand")
        store = _create_store(db_with_roles, brand, "Cart Branch")
        user = _create_user(db_with_roles, telegram_id=7002)

        cat = Categories(name="Beverages", brand_id=brand.id)
        db_with_roles.add(cat)
        db_with_roles.commit()

        item_a = Goods(
            name="Latte", price=Decimal("89.00"), description="Hot latte",
            category_name=cat.name, stock_quantity=100, reserved_quantity=0,
            brand_id=brand.id, item_type="prepared",
        )
        item_b = Goods(
            name="Mocha", price=Decimal("99.00"), description="Hot mocha",
            category_name=cat.name, stock_quantity=100, reserved_quantity=0,
            brand_id=brand.id, item_type="prepared",
        )
        db_with_roles.add_all([item_a, item_b])
        db_with_roles.commit()

        # Simulate cart
        cart_items = [
            ShoppingCart(user_id=user.telegram_id, item_name="Latte", quantity=2,
                         brand_id=brand.id, store_id=store.id),
            ShoppingCart(user_id=user.telegram_id, item_name="Mocha", quantity=1,
                         brand_id=brand.id, store_id=store.id),
        ]
        db_with_roles.add_all(cart_items)
        db_with_roles.commit()

        # Create order from cart
        total = Decimal("89.00") * 2 + Decimal("99.00")  # 277.00
        order = _create_order(db_with_roles, user, brand, store=store, total_price=total)

        # Create order items mirroring cart
        for ci in cart_items:
            goods = db_with_roles.query(Goods).filter_by(name=ci.item_name).one()
            oi = OrderItem(
                order_id=order.id,
                item_name=ci.item_name,
                price=goods.price,
                quantity=ci.quantity,
            )
            db_with_roles.add(oi)
        db_with_roles.commit()

        order_items = db_with_roles.query(OrderItem).filter_by(order_id=order.id).all()
        assert len(order_items) == 2

        oi_map = {oi.item_name: oi for oi in order_items}
        assert oi_map["Latte"].quantity == 2
        assert oi_map["Latte"].price == Decimal("89.00")
        assert oi_map["Mocha"].quantity == 1
        assert oi_map["Mocha"].price == Decimal("99.00")

    def test_order_status_starts_pending(self, db_with_roles: Session):
        """New order starts with status 'pending'."""
        brand = _create_brand(db_with_roles, "PendBrand", "pendbrand")
        user = _create_user(db_with_roles, telegram_id=7003)
        order = _create_order(db_with_roles, user, brand)

        assert order.order_status == "pending"

    def test_order_has_correct_brand_and_store(self, db_with_roles: Session):
        """Order's brand_id and store_id match selections."""
        brand = _create_brand(db_with_roles, "MatchBrand", "matchbrand")
        store = _create_store(db_with_roles, brand, "Match Branch")
        user = _create_user(db_with_roles, telegram_id=7004)
        order = _create_order(db_with_roles, user, brand, store=store)

        fetched = db_with_roles.query(Order).filter_by(id=order.id).one()
        assert fetched.brand_id == brand.id
        assert fetched.store_id == store.id
        assert fetched.brand.name == "MatchBrand"
        assert fetched.store.name == "Match Branch"


# ===================================================================
# 4. TestSmartNavigation (behavioral / contract tests)
# ===================================================================

@pytest.mark.e2e
class TestSmartNavigation:
    """Contract-level tests for cart context and order variations."""

    def test_cart_has_brand_and_store_context(self, db_with_roles: Session):
        """ShoppingCart entries include brand_id and store_id."""
        brand = _create_brand(db_with_roles, "CtxBrand", "ctxbrand")
        store = _create_store(db_with_roles, brand, "Ctx Branch")
        user = _create_user(db_with_roles, telegram_id=8001)

        cat = Categories(name="Snacks", brand_id=brand.id)
        db_with_roles.add(cat)
        db_with_roles.commit()

        goods = Goods(
            name="Cookie", price=Decimal("35.00"), description="Choc chip",
            category_name=cat.name, stock_quantity=50, reserved_quantity=0,
            brand_id=brand.id, item_type="product",
        )
        db_with_roles.add(goods)
        db_with_roles.commit()

        cart_item = ShoppingCart(
            user_id=user.telegram_id,
            item_name="Cookie",
            quantity=3,
            brand_id=brand.id,
            store_id=store.id,
        )
        db_with_roles.add(cart_item)
        db_with_roles.commit()
        db_with_roles.refresh(cart_item)

        assert cart_item.brand_id == brand.id
        assert cart_item.store_id == store.id

    def test_order_delivery_types(self, db_with_roles: Session):
        """Create orders with each delivery_type, verify persisted."""
        brand = _create_brand(db_with_roles, "DelBrand", "delbrand")
        user = _create_user(db_with_roles, telegram_id=8002)

        for dtype in ("door", "dead_drop", "pickup"):
            order = _create_order(
                db_with_roles, user, brand,
                delivery_type=dtype,
                total_price=Decimal("50.00"),
            )
            # Each call generates the same order_code from telegram_id, make unique
            order.order_code = f"D{dtype[:4].upper()}"
            db_with_roles.commit()

            fetched = db_with_roles.query(Order).filter_by(id=order.id).one()
            assert fetched.delivery_type == dtype

    def test_order_with_bonus_applied(self, db_with_roles: Session):
        """Order with bonus_applied > 0 reduces effective total."""
        brand = _create_brand(db_with_roles, "BonusBrand", "bonusbrand")
        user = _create_user(db_with_roles, telegram_id=8003)

        total = Decimal("500.00")
        bonus = Decimal("50.00")
        order = _create_order(
            db_with_roles, user, brand,
            total_price=total,
            bonus_applied=bonus,
        )

        fetched = db_with_roles.query(Order).filter_by(id=order.id).one()
        assert fetched.total_price == Decimal("500.00")
        assert fetched.bonus_applied == Decimal("50.00")
        effective_total = fetched.total_price - fetched.bonus_applied
        assert effective_total == Decimal("450.00")


# ===================================================================
# 5. TestDataCleanup
# ===================================================================

@pytest.mark.e2e
class TestDataCleanup:
    """Test cascade and SET NULL behaviours on deletion."""

    def test_cascade_delete_brand_removes_stores(self, db_session: Session):
        """Deleting a brand cascades to its stores."""
        brand = _create_brand(db_session, "CascBrand", "cascbrand")
        _create_store(db_session, brand, "CascStore1")
        _create_store(db_session, brand, "CascStore2")

        assert db_session.query(Store).filter_by(brand_id=brand.id).count() == 2

        db_session.delete(brand)
        db_session.commit()

        remaining = db_session.query(Store).filter_by(brand_id=brand.id).count()
        assert remaining == 0

    def test_order_survives_store_deletion(self, db_with_roles: Session):
        """Order with store_id SET NULL survives store deletion."""
        brand = _create_brand(db_with_roles, "SurvBrand", "survbrand")
        store = _create_store(db_with_roles, brand, "SurvStore")
        user = _create_user(db_with_roles, telegram_id=9001)
        order = _create_order(db_with_roles, user, brand, store=store)
        order_id = order.id

        assert order.store_id == store.id

        # Delete the store — FK is SET NULL
        db_with_roles.delete(store)
        db_with_roles.commit()
        # Expire cached objects so the ORM re-reads from DB
        db_with_roles.expire_all()

        fetched = db_with_roles.query(Order).filter_by(id=order_id).one()
        assert fetched.store_id is None  # SET NULL
        assert fetched.brand_id == brand.id  # brand still intact
        assert fetched.order_status == "pending"
