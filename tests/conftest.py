"""
Pytest configuration and shared fixtures for all tests
"""
import asyncio
import os
from collections.abc import Generator
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Set test environment variables before importing bot modules
os.environ['TOKEN'] = 'test_token_123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ'
os.environ['OWNER_ID'] = '123456789'
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['REDIS_HOST'] = 'localhost'
os.environ['LOG_TO_STDOUT'] = '0'
os.environ['LOG_TO_FILE'] = '0'

from bot.database.main import Database
from bot.database.models.main import (
    BitcoinAddress,
    BotSettings,
    BranchInventory,
    Brand,
    BrandStaff,
    Categories,
    CustomerInfo,
    Goods,
    Order,
    OrderItem,
    ReferenceCode,
    Role,
    ShoppingCart,
    Store,
    User,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_engine():
    """Create a test database engine with in-memory SQLite"""
    # Use in-memory SQLite for testing
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )

    # Enable foreign keys for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Create all tables
    Database.BASE.metadata.create_all(engine)

    yield engine

    # Cleanup
    Database.BASE.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function", autouse=True)
def override_database_singleton(db_engine, monkeypatch):
    """Override the Database singleton to use test SQLite engine"""
    # Get the Database singleton instance
    db = Database()

    # Create a test SessionLocal bound to test engine
    test_session_local = sessionmaker(
        bind=db_engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False
    )

    # Replace the private attributes with test versions
    monkeypatch.setattr(db, '_Database__engine', db_engine)
    monkeypatch.setattr(db, '_Database__SessionLocal', test_session_local)

    return db


@pytest.fixture(scope="function", autouse=True)
def mock_cache_invalidation():
    """Mock all cache invalidation functions to prevent coroutine warnings"""
    with patch('bot.database.methods.update.invalidate_user_cache', new_callable=AsyncMock), \
            patch('bot.database.methods.update.invalidate_item_cache', new_callable=AsyncMock), \
            patch('bot.database.methods.update.invalidate_category_cache', new_callable=AsyncMock), \
            patch('bot.database.methods.inventory.invalidate_item_cache', new_callable=AsyncMock):
        yield


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """Create a test database session"""
    SessionLocal = sessionmaker(bind=db_engine, expire_on_commit=False)
    session = SessionLocal()

    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def db_with_roles(db_session: Session) -> Session:
    """Database session with roles initialized"""
    # Create roles
    user_role = Role(name='USER', permissions=1)
    admin_role = Role(name='ADMIN', permissions=31)  # All permissions except OWN
    owner_role = Role(name='OWNER', permissions=127)  # All permissions
    superadmin_role = Role(name='SUPERADMIN', permissions=255)  # All permissions including SUPER

    db_session.add_all([user_role, admin_role, owner_role, superadmin_role])
    db_session.commit()

    return db_session


@pytest.fixture
def test_user(db_with_roles: Session) -> User:
    """Create a test user"""
    user = User(
        telegram_id=123456789,
        role_id=1,
        registration_date=datetime.now(UTC),
        referral_id=None
    )
    db_with_roles.add(user)
    db_with_roles.commit()
    db_with_roles.refresh(user)
    return user


@pytest.fixture
def test_admin(db_with_roles: Session) -> User:
    """Create a test admin user"""
    admin = User(
        telegram_id=987654321,
        role_id=2,
        registration_date=datetime.now(UTC),
        referral_id=None
    )
    db_with_roles.add(admin)
    db_with_roles.commit()
    db_with_roles.refresh(admin)
    return admin


@pytest.fixture
def test_brand(db_session: Session) -> Brand:
    """Create a test brand"""
    brand = Brand(name="Test Brand", slug="test-brand", description="A test brand")
    db_session.add(brand)
    db_session.commit()
    db_session.refresh(brand)
    return brand


@pytest.fixture
def test_store(db_session: Session, test_brand: Brand) -> Store:
    """Create a test store/branch"""
    store = Store(
        name="Test Branch",
        brand_id=test_brand.id,
        address="123 Test St",
        latitude=13.7563,
        longitude=100.5018,
        phone="+66123456789",
        is_default=True,
    )
    db_session.add(store)
    db_session.commit()
    db_session.refresh(store)
    return store


@pytest.fixture
def test_category(db_session: Session, test_brand: Brand) -> Categories:
    """Create a test category"""
    category = Categories(name="Test Category", brand_id=test_brand.id)
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    return category


@pytest.fixture
def test_goods(db_session: Session, test_category: Categories, test_brand: Brand) -> Goods:
    """Create test goods with stock"""
    goods = Goods(
        name="Test Product",
        price=Decimal("99.99"),
        description="Test product description",
        category_name=test_category.name,
        stock_quantity=100,
        reserved_quantity=0,
        brand_id=test_brand.id,
        item_type='product',
    )
    db_session.add(goods)
    db_session.commit()
    db_session.refresh(goods)
    return goods


@pytest.fixture
def test_goods_low_stock(db_session: Session, test_category: Categories, test_brand: Brand) -> Goods:
    """Create test goods with low stock"""
    goods = Goods(
        name="Low Stock Product",
        price=Decimal("49.99"),
        description="Low stock product",
        category_name=test_category.name,
        stock_quantity=5,
        reserved_quantity=0,
        brand_id=test_brand.id,
        item_type='product',
    )
    db_session.add(goods)
    db_session.commit()
    db_session.refresh(goods)
    return goods


@pytest.fixture
def test_customer_info(db_session: Session, test_user: User) -> CustomerInfo:
    """Create test customer info"""
    customer_info = CustomerInfo(
        telegram_id=test_user.telegram_id,
        phone_number="+1234567890",
        delivery_address="123 Test Street, Test City",
        delivery_note="Ring the doorbell",
        total_spendings=Decimal("0"),
        completed_orders_count=0,
        bonus_balance=Decimal("0")
    )
    db_session.add(customer_info)
    db_session.commit()
    db_session.refresh(customer_info)
    return customer_info


@pytest.fixture
def test_order(db_session: Session, test_user: User, test_goods: Goods) -> Order:
    """Create a test order with items"""
    order = Order(
        buyer_id=test_user.telegram_id,
        total_price=Decimal("199.98"),
        payment_method="cash",
        delivery_address="123 Test Street",
        phone_number="+1234567890",
        order_status="pending",
        order_code="TEST01"
    )
    db_session.add(order)
    db_session.flush()

    # Add order items
    order_item = OrderItem(
        order_id=order.id,
        item_name=test_goods.name,
        price=test_goods.price,
        quantity=2
    )
    db_session.add(order_item)
    db_session.commit()
    db_session.refresh(order)
    return order


@pytest.fixture
def test_bitcoin_address(db_session: Session) -> BitcoinAddress:
    """Create a test Bitcoin address"""
    btc_addr = BitcoinAddress(address="bc1qtest123456789abcdefghijklmnop")
    db_session.add(btc_addr)
    db_session.commit()
    db_session.refresh(btc_addr)
    return btc_addr


@pytest.fixture
def test_reference_code(db_session: Session, test_admin: User) -> ReferenceCode:
    """Create a test reference code"""
    ref_code = ReferenceCode(
        code="TESTCODE",
        created_by=test_admin.telegram_id,
        expires_at=None,
        max_uses=None,
        note="Test reference code",
        is_admin_code=True
    )
    db_session.add(ref_code)
    db_session.commit()
    db_session.refresh(ref_code)
    return ref_code


@pytest.fixture
def test_shopping_cart(db_session: Session, test_user: User, test_goods: Goods) -> ShoppingCart:
    """Create a test shopping cart item"""
    cart_item = ShoppingCart(
        user_id=test_user.telegram_id,
        item_name=test_goods.name,
        quantity=2
    )
    db_session.add(cart_item)
    db_session.commit()
    db_session.refresh(cart_item)
    return cart_item


@pytest.fixture
def test_bot_settings(db_session: Session) -> BotSettings:
    """Create test bot settings"""
    settings = [
        BotSettings(setting_key='reference_codes_enabled', setting_value='true'),
        BotSettings(setting_key='reference_bonus_percent', setting_value='5'),
        BotSettings(setting_key='cash_order_timeout_hours', setting_value='24'),
        BotSettings(setting_key='timezone', setting_value='Asia/Bangkok'),
    ]
    for setting in settings:
        db_session.add(setting)
    db_session.commit()
    return settings[0]


# Helper fixtures for complex test scenarios
@pytest.fixture
def populated_database(
        db_with_roles: Session,
        test_user: User,
        test_admin: User,
        test_category: Categories,
        test_goods: Goods,
        test_customer_info: CustomerInfo
) -> Session:
    """Database populated with test data"""
    return db_with_roles


@pytest.fixture
def multiple_products(db_session: Session, test_category: Categories, test_brand: Brand) -> list[Goods]:
    """Create multiple test products"""
    products = []
    for i in range(5):
        goods = Goods(
            name=f"Product {i + 1}",
            price=Decimal(f"{10 * (i + 1)}.99"),
            description=f"Description for product {i + 1}",
            category_name=test_category.name,
            stock_quantity=50 + i * 10,
            reserved_quantity=0,
            brand_id=test_brand.id,
            item_type='prepared' if i % 2 == 0 else 'product',
        )
        db_session.add(goods)
        products.append(goods)

    db_session.commit()
    for product in products:
        db_session.refresh(product)

    return products


@pytest.fixture
def multiple_categories(db_session: Session, test_brand: Brand) -> list[Categories]:
    """Create multiple test categories"""
    categories = []
    for i in range(3):
        category = Categories(name=f"Category {i + 1}", brand_id=test_brand.id)
        db_session.add(category)
        categories.append(category)

    db_session.commit()
    for category in categories:
        db_session.refresh(category)

    return categories


@pytest.fixture
def test_brand_staff(db_session: Session, test_brand: Brand, test_admin: User) -> BrandStaff:
    """Create a test brand staff entry (admin as brand owner)"""
    staff = BrandStaff(
        brand_id=test_brand.id,
        user_id=test_admin.telegram_id,
        role='owner',
    )
    db_session.add(staff)
    db_session.commit()
    db_session.refresh(staff)
    return staff


@pytest.fixture
def test_branch_inventory(db_session: Session, test_store: Store, test_goods: Goods) -> BranchInventory:
    """Create test branch inventory"""
    inv = BranchInventory(
        store_id=test_store.id,
        item_name=test_goods.name,
        stock_quantity=50,
        reserved_quantity=0,
    )
    db_session.add(inv)
    db_session.commit()
    db_session.refresh(inv)
    return inv


@pytest.fixture
def second_brand(db_session: Session) -> Brand:
    """Create a second brand for multi-brand tests"""
    brand = Brand(name="Second Brand", slug="second-brand", description="Another brand")
    db_session.add(brand)
    db_session.commit()
    db_session.refresh(brand)
    return brand


# Async fixtures
@pytest.fixture
async def async_db_session(db_engine):
    """Async database session for async tests"""
    SessionLocal = sessionmaker(bind=db_engine, expire_on_commit=False)
    session = SessionLocal()

    try:
        yield session
    finally:
        session.rollback()
        session.close()
