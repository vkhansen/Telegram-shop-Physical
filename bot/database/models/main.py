import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from bot.database.main import Database


class Permission:
    USE = 1
    BROADCAST = 2
    SETTINGS_MANAGE = 4
    USERS_MANAGE = 8
    SHOP_MANAGE = 16
    ADMINS_MANAGE = 32
    OWN = 64
    SUPER = 128  # Platform superadmin


class Role(Database.BASE):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True)
    default = Column(Boolean, default=False, index=True)
    permissions = Column(Integer)
    users = relationship('User', backref='role', lazy='dynamic')

    def __init__(self, name: str, permissions=None, **kwargs):
        super().__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0
        self.name = name
        self.permissions = permissions

    @staticmethod
    def insert_roles():
        roles = {
            'USER': [Permission.USE],
            'ADMIN': [Permission.USE, Permission.BROADCAST,
                      Permission.SETTINGS_MANAGE, Permission.USERS_MANAGE, Permission.SHOP_MANAGE],
            'OWNER': [Permission.USE, Permission.BROADCAST,
                      Permission.SETTINGS_MANAGE, Permission.USERS_MANAGE, Permission.SHOP_MANAGE,
                      Permission.ADMINS_MANAGE, Permission.OWN],
            'SUPERADMIN': [Permission.USE, Permission.BROADCAST,
                           Permission.SETTINGS_MANAGE, Permission.USERS_MANAGE, Permission.SHOP_MANAGE,
                           Permission.ADMINS_MANAGE, Permission.OWN, Permission.SUPER],
        }
        default_role = 'USER'
        with Database().session() as s:
            for r, perms in roles.items():
                role = s.query(Role).filter_by(name=r).first()
                if role is None:
                    role = Role(name=r)
                    s.add(role)
                role.reset_permissions()
                for perm in perms:
                    role.add_permission(perm)
                role.default = (role.name == default_role)

    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm

    def reset_permissions(self):
        self.permissions = 0

    def has_permission(self, perm):
        return self.permissions & perm == perm

    def __repr__(self):
        return '<Role %r>' % self.name


class User(Database.BASE):
    __tablename__ = 'users'
    telegram_id = Column(BigInteger, primary_key=True)
    role_id = Column(Integer, ForeignKey('roles.id', ondelete="RESTRICT"), default=1, index=True)
    referral_id = Column(BigInteger, ForeignKey('users.telegram_id', ondelete="SET NULL"), nullable=True, index=True)
    locale = Column(String(5), nullable=True)  # Per-user language: th, en, ru, ar, fa, ps, fr (Card 14)
    registration_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    is_banned = Column(Boolean, nullable=False, default=False, index=True)
    banned_at = Column(DateTime(timezone=True), nullable=True)
    banned_by = Column(BigInteger, ForeignKey('users.telegram_id', ondelete="SET NULL"), nullable=True)
    ban_reason = Column(Text, nullable=True)
    user_goods = relationship("BoughtGoods", back_populates="user_telegram_id")

    referral_earnings_received = relationship(
        "ReferralEarnings",
        foreign_keys=lambda: [ReferralEarnings.referrer_id],
        back_populates="referrer"
    )
    referral_earnings_generated = relationship(
        "ReferralEarnings",
        foreign_keys=lambda: [ReferralEarnings.referral_id],
        back_populates="referral"
    )

    def __init__(self, telegram_id: int, registration_date: datetime.datetime, referral_id=None,
                 role_id: int = 1, is_banned: bool = False, banned_at=None, banned_by=None,
                 ban_reason: str = None, locale: str = None, **kw: Any):
        super().__init__(**kw)
        self.telegram_id = telegram_id
        self.role_id = role_id
        self.referral_id = referral_id
        self.locale = locale
        self.registration_date = registration_date
        self.is_banned = is_banned
        self.banned_at = banned_at
        self.banned_by = banned_by
        self.ban_reason = ban_reason


class Brand(Database.BASE):
    """Brand / restaurant entity. Each brand is an independent business."""
    __tablename__ = 'brands'

    id = Column(Integer, primary_key=True)
    name = Column(String(200), unique=True, nullable=False)
    slug = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    logo_file_id = Column(String(255), nullable=True)  # Telegram photo file_id
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    promptpay_id = Column(String(20), nullable=True)
    promptpay_name = Column(String(200), nullable=True)
    timezone = Column(String(50), nullable=True)  # Override, null = platform default
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    stores = relationship("Store", back_populates="brand", cascade="all, delete-orphan")
    staff = relationship("BrandStaff", back_populates="brand", cascade="all, delete-orphan")
    categories = relationship("Categories", back_populates="brand")
    goods = relationship("Goods", back_populates="brand")

    def __init__(self, name: str, slug: str, description: str = None,
                 logo_file_id: str = None, promptpay_id: str = None,
                 promptpay_name: str = None, timezone: str = None, **kw: Any):
        super().__init__(**kw)
        self.name = name
        self.slug = slug
        self.description = description
        self.logo_file_id = logo_file_id
        self.promptpay_id = promptpay_id
        self.promptpay_name = promptpay_name
        self.timezone = timezone


class BrandStaff(Database.BASE):
    """Staff assignment per brand/branch."""
    __tablename__ = 'brand_staff'

    id = Column(Integer, primary_key=True)
    brand_id = Column(Integer, ForeignKey('brands.id', ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(BigInteger, ForeignKey('users.telegram_id', ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # 'owner', 'admin', 'kitchen', 'rider'
    store_id = Column(Integer, ForeignKey('stores.id', ondelete="SET NULL"), nullable=True)  # null = all branches
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    brand = relationship("Brand", back_populates="staff")
    user = relationship("User", foreign_keys=lambda: [BrandStaff.user_id])
    store = relationship("Store", foreign_keys=lambda: [BrandStaff.store_id])

    __table_args__ = (
        UniqueConstraint('brand_id', 'user_id', 'store_id', name='uq_brand_user_store'),
        Index('ix_brand_staff_brand_role', 'brand_id', 'role'),
    )

    def __init__(self, brand_id: int, user_id: int, role: str, store_id: int = None, **kw: Any):
        super().__init__(**kw)
        self.brand_id = brand_id
        self.user_id = user_id
        self.role = role
        self.store_id = store_id


class Categories(Database.BASE):
    __tablename__ = 'categories'
    name = Column(String(100), primary_key=True)
    brand_id = Column(Integer, ForeignKey('brands.id', ondelete="CASCADE"), nullable=True, index=True)
    sort_order = Column(Integer, nullable=False, default=0)  # Menu ordering (Card 8)
    description = Column(Text, nullable=True)  # Category description
    image_file_id = Column(String(255), nullable=True)  # Telegram file_id for category cover
    available_from = Column(String(5), nullable=True)  # "06:00" - breakfast menu starts
    available_until = Column(String(5), nullable=True)  # "11:00" - breakfast menu ends
    item = relationship("Goods", back_populates="category")
    brand = relationship("Brand", back_populates="categories")

    def __init__(self, name: str, sort_order: int = 0, description: str = None,
                 image_file_id: str = None, available_from: str = None,
                 available_until: str = None, brand_id: int = None, **kw: Any):
        super().__init__(**kw)
        self.name = name
        self.sort_order = sort_order
        self.description = description
        self.image_file_id = image_file_id
        self.available_from = available_from
        self.available_until = available_until
        self.brand_id = brand_id


class Goods(Database.BASE):
    __tablename__ = 'goods'
    name = Column(String(100), primary_key=True)
    brand_id = Column(Integer, ForeignKey('brands.id', ondelete="CASCADE"), nullable=True, index=True)
    price = Column(Numeric(12, 2), nullable=False)
    description = Column(Text, nullable=False)
    category_name = Column(String(100), ForeignKey('categories.name', ondelete="CASCADE", onupdate="CASCADE"),
                           nullable=False, index=True)
    # Item type: distinguishes packaged goods from prepared food
    # 'product' = shelf-stable / pre-packaged (e.g., bottled water, snacks) — tracked by inventory count
    # 'prepared' = made-to-order / perishable (e.g., pad thai, coffee) — tracked by daily limit & prep time
    item_type = Column(String(20), nullable=False, default='prepared', index=True)

    stock_quantity = Column(Integer, nullable=False, default=0)  # Total stock (fallback for single-branch)
    reserved_quantity = Column(Integer, nullable=False, default=0)  # Reserved (fallback for single-branch)
    modifiers = Column(JSON, nullable=True)  # Modifier schema for restaurant items (Card 8)

    # Restaurant-specific fields (primarily for item_type='prepared')
    image_file_id = Column(String(255), nullable=True)  # Telegram file_id for menu photo
    media = Column(JSON, nullable=True)  # Multiple media: [{"file_id": str, "type": "photo"|"video", "caption": str}]
    prep_time_minutes = Column(Integer, nullable=True)  # Kitchen prep time in minutes
    allergens = Column(String(500), nullable=True)  # Comma-separated: "gluten,dairy,nuts"
    is_active = Column(Boolean, nullable=False, default=True, index=True)  # Permanent on/off
    sold_out_today = Column(Boolean, nullable=False, default=False)  # Temporary "86'd" flag
    daily_limit = Column(Integer, nullable=True)  # Max units per day (NULL = unlimited)
    daily_sold_count = Column(Integer, nullable=False, default=0)  # Reset daily by scheduler
    available_from = Column(String(5), nullable=True)  # "06:00" HH:MM availability start
    available_until = Column(String(5), nullable=True)  # "22:00" HH:MM availability end
    calories = Column(Integer, nullable=True)  # Nutritional info

    category = relationship("Categories", back_populates="item")
    brand = relationship("Brand", back_populates="goods")

    @property
    def available_quantity(self) -> int:
        """Calculate available stock (total - reserved)"""
        return max(0, self.stock_quantity - self.reserved_quantity)

    @property
    def daily_remaining(self) -> int | None:
        """How many more can be sold today. None if no daily limit."""
        if self.daily_limit is None:
            return None
        return max(0, self.daily_limit - self.daily_sold_count)

    @property
    def is_product(self) -> bool:
        """True if this is a packaged/shelf-stable item (e.g., bottled water)."""
        return self.item_type == 'product'

    @property
    def is_prepared(self) -> bool:
        """True if this is a made-to-order/perishable item (e.g., pad thai)."""
        return self.item_type == 'prepared'

    @property
    def is_currently_available(self) -> bool:
        """Check if item is orderable right now (ignores time window - use check_time_window())."""
        if not self.is_active or self.sold_out_today:
            return False
        if self.daily_limit is not None and self.daily_sold_count >= self.daily_limit:
            return False
        # Products require inventory; prepared items may have unlimited stock (stock_quantity=0 means unlimited for prepared)
        if self.is_product and self.available_quantity <= 0:
            return False
        return True

    def __init__(self, name: str, price, description: str, category_name: str,
                 stock_quantity: int = 0, image_file_id: str = None,
                 media: list = None, prep_time_minutes: int = None,
                 allergens: str = None, daily_limit: int = None,
                 available_from: str = None, available_until: str = None,
                 calories: int = None, brand_id: int = None,
                 item_type: str = 'prepared', **kw: Any):
        super().__init__(**kw)
        self.name = name
        self.brand_id = brand_id
        self.item_type = item_type
        self.price = price
        self.description = description
        self.category_name = category_name
        self.stock_quantity = stock_quantity
        self.image_file_id = image_file_id
        self.media = media
        self.prep_time_minutes = prep_time_minutes
        self.allergens = allergens
        self.daily_limit = daily_limit
        self.available_from = available_from
        self.available_until = available_until
        self.calories = calories


class BoughtGoods(Database.BASE):
    __tablename__ = 'bought_goods'
    id = Column(Integer, primary_key=True)
    item_name = Column(String(100), nullable=False, index=True)
    value = Column(Text, nullable=False)
    price = Column(Numeric(12, 2), nullable=False)
    buyer_id = Column(BigInteger, ForeignKey('users.telegram_id', ondelete="SET NULL"), nullable=True, index=True)
    bought_datetime = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    unique_id = Column(BigInteger, nullable=False, unique=True)
    user_telegram_id = relationship("User", back_populates="user_goods")

    def __init__(self, name: str, value: str, price, bought_datetime, unique_id, buyer_id: int = 0, **kw: Any):
        super().__init__(**kw)
        self.item_name = name
        self.value = value
        self.price = price
        self.buyer_id = buyer_id
        self.bought_datetime = bought_datetime
        self.unique_id = unique_id


class Operations(Database.BASE):
    __tablename__ = 'operations'
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.telegram_id', ondelete="CASCADE"), nullable=False, index=True)
    operation_value = Column(Numeric(12, 2), nullable=False)
    operation_time = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    user_telegram_id = relationship("User")

    def __init__(self, user_id: int, operation_value, operation_time, **kw: Any):
        super().__init__(**kw)
        self.user_id = user_id
        self.operation_value = operation_value
        self.operation_time = operation_time


class ReferralEarnings(Database.BASE):
    __tablename__ = 'referral_earnings'

    id = Column(Integer, primary_key=True)
    referrer_id = Column(BigInteger, ForeignKey('users.telegram_id', ondelete="CASCADE"), nullable=False)
    referral_id = Column(BigInteger, ForeignKey('users.telegram_id', ondelete="CASCADE"),
                         nullable=True)  # NULL for admin bonuses
    amount = Column(Numeric(12, 2), nullable=False)
    original_amount = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    referrer = relationship(
        "User",
        foreign_keys=lambda: [ReferralEarnings.referrer_id],
        back_populates="referral_earnings_received"
    )
    referral = relationship(
        "User",
        foreign_keys=lambda: [ReferralEarnings.referral_id],
        back_populates="referral_earnings_generated"
    )

    __table_args__ = (
        Index('ix_referral_earnings_referrer_created', 'referrer_id', 'created_at'),
        Index('ix_referral_earnings_referral_created', 'referral_id', 'created_at'),
    )

    def __init__(self, referrer_id: int, referral_id: int | None, amount, original_amount, **kw: Any):
        super().__init__(**kw)
        self.referrer_id = referrer_id
        self.referral_id = referral_id
        self.amount = amount
        self.original_amount = original_amount


class ReferenceCode(Database.BASE):
    __tablename__ = 'reference_codes'

    code = Column(String(8), primary_key=True)
    created_by = Column(BigInteger, ForeignKey('users.telegram_id', ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    max_uses = Column(Integer, nullable=True)  # None means unlimited
    current_uses = Column(Integer, nullable=False, default=0)
    note = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    is_admin_code = Column(Boolean, nullable=False, default=False)

    creator = relationship("User", foreign_keys=lambda: [ReferenceCode.created_by])
    usages = relationship("ReferenceCodeUsage", back_populates="reference_code", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_reference_codes_active_expires', 'is_active', 'expires_at'),
    )

    def __init__(self, code: str, created_by: int, expires_at=None, max_uses=None, note=None,
                 is_admin_code=False, **kw: Any):
        super().__init__(**kw)
        self.code = code
        self.created_by = created_by
        self.expires_at = expires_at
        self.max_uses = max_uses
        self.note = note
        self.is_admin_code = is_admin_code


class ReferenceCodeUsage(Database.BASE):
    __tablename__ = 'reference_code_usages'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), ForeignKey('reference_codes.code', ondelete="CASCADE"), nullable=False, index=True)
    used_by = Column(BigInteger, ForeignKey('users.telegram_id', ondelete="CASCADE"), nullable=False, index=True)
    used_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    reference_code = relationship("ReferenceCode", back_populates="usages")
    user = relationship("User", foreign_keys=lambda: [ReferenceCodeUsage.used_by])

    __table_args__ = (
        UniqueConstraint('code', 'used_by', name='uq_code_user'),
        Index('ix_reference_code_usages_used_at', 'used_at'),
    )

    def __init__(self, code: str, used_by: int, **kw: Any):
        super().__init__(**kw)
        self.code = code
        self.used_by = used_by


class Order(Database.BASE):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    order_code = Column(String(6), unique=True, nullable=True)  # Unique 6-char code (e.g., ECBDJI)
    buyer_id = Column(BigInteger, ForeignKey('users.telegram_id', ondelete="SET NULL"), nullable=True, index=True)
    total_price = Column(Numeric(12, 2), nullable=False)
    bonus_applied = Column(Numeric(12, 2), nullable=True, default=0)  # Referral bonus applied to this order
    payment_method = Column(String(20), nullable=False)  # 'bitcoin', 'cash', or 'promptpay'
    delivery_address = Column(Text, nullable=False)
    phone_number = Column(String(50), nullable=False)
    delivery_note = Column(Text, nullable=True)
    bitcoin_address = Column(String(100), nullable=True)
    order_status = Column(String(20), nullable=False,
                          default='pending')  # pending, reserved, confirmed, preparing, ready, out_for_delivery, delivered, cancelled, expired
    reserved_until = Column(DateTime(timezone=True),
                            nullable=True)  # Reservation expiration time (configurable timeout)
    delivery_time = Column(DateTime(timezone=True), nullable=True)  # Planned delivery time set by admin
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # GPS location (Card 2)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    google_maps_link = Column(String(255), nullable=True)

    # Thai address format (Card 7)
    address_structured = Column(JSON, nullable=True)  # {house, soi, road, subdistrict, district, province, postal_code}

    # Kitchen & delivery workflow (Card 9)
    kitchen_group_message_id = Column(Integer, nullable=True)
    rider_group_message_id = Column(Integer, nullable=True)
    estimated_ready_at = Column(DateTime(timezone=True), nullable=True)  # Calculated from prep times
    total_prep_time_minutes = Column(Integer, nullable=True)  # Sum/max of item prep times

    # Delivery zones & time slots (Card 10)
    delivery_zone = Column(String(50), nullable=True)
    delivery_fee = Column(Numeric(12, 2), nullable=True, default=0)
    preferred_time_slot = Column(String(50), nullable=True)

    # Driver live location (Card 13)
    driver_live_location_message_id = Column(Integer, nullable=True)  # Message ID of live location shared with customer
    driver_id = Column(BigInteger, nullable=True)  # Telegram ID of assigned driver/rider

    # Customer live location + chat session (Card 15)
    customer_live_location_message_id = Column(Integer, nullable=True)  # Message ID of customer's live location
    chat_opened_at = Column(DateTime(timezone=True), nullable=True)  # When chat session started
    chat_closed_at = Column(DateTime(timezone=True), nullable=True)  # When chat session ended
    chat_post_delivery_until = Column(DateTime(timezone=True), nullable=True)  # Post-delivery chat window end

    # PromptPay payment (Card 1)
    payment_receipt_photo = Column(String(255), nullable=True)  # Telegram file_id of payment slip
    payment_verified_by = Column(BigInteger, nullable=True)  # Admin who verified
    payment_verified_at = Column(DateTime(timezone=True), nullable=True)

    # Slip auto-verification (SlipOK/EasySlip/RDCW)
    slip_verify_status = Column(String(30), nullable=True)  # verified, amount_mismatch, etc.
    slip_verify_bank = Column(String(20), nullable=True)  # slipok, easyslip, rdcw (provider used)
    slip_transaction_id = Column(String(100), nullable=True)  # Bank transaction reference
    slip_verified_amount = Column(Numeric(precision=12, scale=2), nullable=True)  # Amount from bank
    slip_sender_name = Column(String(255), nullable=True)
    slip_receiver_name = Column(String(255), nullable=True)
    slip_verified_at = Column(DateTime(timezone=True), nullable=True)

    # Delivery type (Card 3)
    delivery_type = Column(String(20), nullable=False, default="door")  # door | dead_drop | pickup
    drop_instructions = Column(Text, nullable=True)
    drop_location_photo = Column(String(255), nullable=True)  # Telegram file_id (legacy single photo)
    drop_latitude = Column(Float, nullable=True)   # Dead drop GPS lat
    drop_longitude = Column(Float, nullable=True)  # Dead drop GPS lng
    drop_media = Column(JSON, nullable=True)  # List of {"file_id": str, "type": "photo"|"video"}

    # Delivery photo proof (Card 4)
    delivery_photo = Column(String(255), nullable=True)  # Telegram file_id
    delivery_photo_at = Column(DateTime(timezone=True), nullable=True)
    delivery_photo_by = Column(BigInteger, nullable=True)

    # Coupon / promo code
    coupon_code = Column(String(32), nullable=True)
    coupon_discount = Column(Numeric(12, 2), nullable=True, default=0)

    # Multi-brand / multi-store
    brand_id = Column(Integer, ForeignKey('brands.id', ondelete="SET NULL"), nullable=True, index=True)
    store_id = Column(Integer, ForeignKey('stores.id', ondelete="SET NULL"), nullable=True)

    buyer = relationship("User", foreign_keys=lambda: [Order.buyer_id])
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    brand = relationship("Brand", foreign_keys=lambda: [Order.brand_id])
    store = relationship("Store", foreign_keys=lambda: [Order.store_id])

    __table_args__ = (
        Index('ix_orders_buyer_status', 'buyer_id', 'order_status'),
        Index('ix_orders_created_at', 'created_at'),
        Index('ix_orders_order_code', 'order_code'),
        Index('ix_orders_reserved_until', 'reserved_until'),  # For cleanup task
    )

    def __init__(self, buyer_id: int, total_price, payment_method: str,
                 delivery_address: str, phone_number: str, delivery_note: str = None,
                 bitcoin_address: str = None, order_status: str = 'pending',
                 order_code: str = None, reserved_until=None, delivery_time=None,
                 bonus_applied=0, latitude: float = None, longitude: float = None,
                 google_maps_link: str = None, delivery_type: str = 'door',
                 drop_instructions: str = None, drop_location_photo: str = None,
                 drop_latitude: float = None, drop_longitude: float = None,
                 drop_media: list = None,
                 **kw: Any):
        super().__init__(**kw)
        self.buyer_id = buyer_id
        self.order_code = order_code
        self.total_price = total_price
        self.bonus_applied = bonus_applied
        self.payment_method = payment_method
        self.delivery_address = delivery_address
        self.phone_number = phone_number
        self.delivery_note = delivery_note
        self.bitcoin_address = bitcoin_address
        self.order_status = order_status
        self.reserved_until = reserved_until
        self.delivery_time = delivery_time
        self.latitude = latitude
        self.longitude = longitude
        self.google_maps_link = google_maps_link
        self.delivery_type = delivery_type
        self.drop_instructions = drop_instructions
        self.drop_location_photo = drop_location_photo
        self.drop_latitude = drop_latitude
        self.drop_longitude = drop_longitude
        self.drop_media = drop_media


class OrderItem(Database.BASE):
    __tablename__ = 'order_items'

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id', ondelete="CASCADE"), nullable=False)
    item_name = Column(String(100), nullable=False)
    price = Column(Numeric(12, 2), nullable=False)  # Price per unit
    quantity = Column(Integer, nullable=False, default=1)
    selected_modifiers = Column(JSON, nullable=True)  # Selected modifier choices (Card 8)

    order = relationship("Order", back_populates="items")

    __table_args__ = (
        Index('ix_order_items_order_id', 'order_id'),
    )

    def __init__(self, order_id: int, item_name: str, price, quantity: int = 1,
                 selected_modifiers: dict = None, **kw: Any):
        super().__init__(**kw)
        self.order_id = order_id
        self.item_name = item_name
        self.price = price
        self.selected_modifiers = selected_modifiers
        self.quantity = quantity


class CustomerInfo(Database.BASE):
    __tablename__ = 'customer_info'

    telegram_id = Column(BigInteger, ForeignKey('users.telegram_id', ondelete="CASCADE"), primary_key=True)
    phone_number = Column(String(50), nullable=True)
    delivery_address = Column(Text, nullable=True)
    delivery_note = Column(Text, nullable=True)
    total_spendings = Column(Numeric(12, 2), nullable=False, default=0)
    completed_orders_count = Column(Integer, nullable=False, default=0)
    bonus_balance = Column(Numeric(12, 2), nullable=False, default=0)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # GPS location (Card 2)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # Thai address format (Card 7)
    address_structured = Column(JSON, nullable=True)

    user = relationship("User", foreign_keys=lambda: [CustomerInfo.telegram_id])

    def __init__(self, telegram_id: int, phone_number: str = None, delivery_address: str = None,
                 delivery_note: str = None, **kw: Any):
        super().__init__(**kw)
        self.telegram_id = telegram_id
        self.phone_number = phone_number
        self.delivery_address = delivery_address
        self.delivery_note = delivery_note
        # Explicitly initialize numeric fields to prevent None values
        if not hasattr(self, 'total_spendings') or self.total_spendings is None:
            self.total_spendings = Decimal('0')
        if not hasattr(self, 'completed_orders_count') or self.completed_orders_count is None:
            self.completed_orders_count = 0
        if not hasattr(self, 'bonus_balance') or self.bonus_balance is None:
            self.bonus_balance = Decimal('0')


class BitcoinAddress(Database.BASE):
    __tablename__ = 'bitcoin_addresses'

    address = Column(String(100), primary_key=True)
    is_used = Column(Boolean, nullable=False, default=False, index=True)
    used_by = Column(BigInteger, ForeignKey('users.telegram_id', ondelete="SET NULL"), nullable=True)
    used_at = Column(DateTime(timezone=True), nullable=True)
    order_id = Column(Integer, ForeignKey('orders.id', ondelete="SET NULL"), nullable=True)

    user = relationship("User", foreign_keys=lambda: [BitcoinAddress.used_by])
    order = relationship("Order", foreign_keys=lambda: [BitcoinAddress.order_id])

    def __init__(self, address: str, **kw: Any):
        super().__init__(**kw)
        self.address = address


class BotSettings(Database.BASE):
    __tablename__ = 'bot_settings'

    id = Column(Integer, primary_key=True)
    setting_key = Column(String(100), nullable=False, index=True)
    setting_value = Column(Text, nullable=True)
    brand_id = Column(Integer, ForeignKey('brands.id', ondelete="CASCADE"), nullable=True, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    brand = relationship("Brand", foreign_keys=lambda: [BotSettings.brand_id])

    __table_args__ = (
        UniqueConstraint('setting_key', 'brand_id', name='uq_setting_key_brand'),
    )

    def __init__(self, setting_key: str, setting_value: str = None, brand_id: int = None, **kw: Any):
        super().__init__(**kw)
        self.setting_key = setting_key
        self.setting_value = setting_value
        self.brand_id = brand_id


class ShoppingCart(Database.BASE):
    __tablename__ = 'shopping_cart'

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.telegram_id', ondelete="CASCADE"), nullable=False)
    item_name = Column(String(100), ForeignKey('goods.name', ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    selected_modifiers = Column(JSON, nullable=True)  # Selected modifier choices (Card 8)
    brand_id = Column(Integer, ForeignKey('brands.id', ondelete="CASCADE"), nullable=True, index=True)
    store_id = Column(Integer, ForeignKey('stores.id', ondelete="SET NULL"), nullable=True, index=True)
    added_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    user = relationship("User", foreign_keys=lambda: [ShoppingCart.user_id])
    item = relationship("Goods", foreign_keys=lambda: [ShoppingCart.item_name])
    brand = relationship("Brand", foreign_keys=lambda: [ShoppingCart.brand_id])
    store = relationship("Store", foreign_keys=lambda: [ShoppingCart.store_id])

    __table_args__ = (
        UniqueConstraint('user_id', 'item_name', 'brand_id', name='uq_cart_user_item_brand'),
        Index('ix_shopping_cart_user_added', 'user_id', 'added_at'),
        Index('ix_shopping_cart_user_brand', 'user_id', 'brand_id'),
    )

    def __init__(self, user_id: int, item_name: str, quantity: int = 1,
                 selected_modifiers: dict = None, brand_id: int = None,
                 store_id: int = None, **kw: Any):
        super().__init__(**kw)
        self.user_id = user_id
        self.item_name = item_name
        self.quantity = quantity
        self.selected_modifiers = selected_modifiers
        self.brand_id = brand_id
        self.store_id = store_id


class DeliveryChatMessage(Database.BASE):
    """Recorded messages between driver and customer during delivery (Card 13)."""
    __tablename__ = 'delivery_chat_messages'

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id', ondelete="CASCADE"), nullable=False)
    sender_id = Column(BigInteger, nullable=False)  # Telegram ID of sender
    sender_role = Column(String(20), nullable=False)  # 'driver' or 'customer'
    message_text = Column(Text, nullable=True)
    photo_file_id = Column(String(255), nullable=True)  # If photo was sent
    location_lat = Column(Float, nullable=True)  # If location was shared
    location_lng = Column(Float, nullable=True)
    is_live_location = Column(Boolean, nullable=False, default=False)  # True if from live location share (Card 15)
    live_location_update_count = Column(Integer, nullable=True)  # Nth update of a live location session (Card 15)
    telegram_message_id = Column(Integer, nullable=True)  # Original message ID
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    order = relationship("Order", foreign_keys=lambda: [DeliveryChatMessage.order_id])

    __table_args__ = (
        Index('ix_delivery_chat_order_created', 'order_id', 'created_at'),
    )

    def __init__(self, order_id: int, sender_id: int, sender_role: str,
                 message_text: str = None, photo_file_id: str = None,
                 location_lat: float = None, location_lng: float = None,
                 is_live_location: bool = False, live_location_update_count: int = None,
                 telegram_message_id: int = None, **kw: Any):
        super().__init__(**kw)
        self.order_id = order_id
        self.sender_id = sender_id
        self.sender_role = sender_role
        self.message_text = message_text
        self.photo_file_id = photo_file_id
        self.location_lat = location_lat
        self.location_lng = location_lng
        self.is_live_location = is_live_location
        self.live_location_update_count = live_location_update_count
        self.telegram_message_id = telegram_message_id


class InventoryLog(Database.BASE):
    __tablename__ = 'inventory_log'

    id = Column(Integer, primary_key=True)
    item_name = Column(String(100), ForeignKey('goods.name', ondelete="CASCADE"), nullable=False)
    change_type = Column(String(20), nullable=False)  # reserve, release, deduct, add, manual, expired
    quantity_change = Column(Integer, nullable=False)  # Can be negative or positive
    order_id = Column(Integer, ForeignKey('orders.id', ondelete="SET NULL"), nullable=True, index=True)
    admin_id = Column(BigInteger, ForeignKey('users.telegram_id', ondelete="SET NULL"), nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    comment = Column(Text, nullable=True)

    item = relationship("Goods", foreign_keys=lambda: [InventoryLog.item_name])
    order = relationship("Order", foreign_keys=lambda: [InventoryLog.order_id])
    admin = relationship("User", foreign_keys=lambda: [InventoryLog.admin_id])

    __table_args__ = (
        Index('ix_inventory_log_item_timestamp', 'item_name', 'timestamp'),
        Index('ix_inventory_log_type_timestamp', 'change_type', 'timestamp'),
    )

    def __init__(self, item_name: str, change_type: str, quantity_change: int,
                 order_id: int = None, admin_id: int = None, comment: str = None, **kw: Any):
        super().__init__(**kw)
        self.item_name = item_name
        self.change_type = change_type
        self.quantity_change = quantity_change
        self.order_id = order_id
        self.admin_id = admin_id
        self.comment = comment


class Coupon(Database.BASE):
    """Coupon / promo code for discounts."""
    __tablename__ = 'coupons'

    id = Column(Integer, primary_key=True)
    code = Column(String(32), unique=True, nullable=False, index=True)
    discount_type = Column(String(10), nullable=False)  # 'percent' or 'fixed'
    discount_value = Column(Numeric(12, 2), nullable=False)  # % or fixed amount
    min_order = Column(Numeric(12, 2), nullable=True, default=0)  # Minimum order to apply
    max_discount = Column(Numeric(12, 2), nullable=True)  # Cap for percent discounts
    valid_from = Column(DateTime(timezone=True), nullable=True)
    valid_until = Column(DateTime(timezone=True), nullable=True)
    max_uses = Column(Integer, nullable=True)  # None = unlimited
    current_uses = Column(Integer, nullable=False, default=0)
    max_uses_per_user = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_by = Column(BigInteger, ForeignKey('users.telegram_id', ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    note = Column(Text, nullable=True)

    usages = relationship("CouponUsage", back_populates="coupon", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_coupons_active_valid', 'is_active', 'valid_until'),
    )

    def __init__(self, code: str, discount_type: str, discount_value, created_by: int = None,
                 min_order=0, max_discount=None, valid_from=None, valid_until=None,
                 max_uses=None, max_uses_per_user=1, note=None, **kw: Any):
        super().__init__(**kw)
        self.code = code.upper()
        self.discount_type = discount_type
        self.discount_value = discount_value
        self.min_order = min_order
        self.max_discount = max_discount
        self.valid_from = valid_from
        self.valid_until = valid_until
        self.max_uses = max_uses
        self.max_uses_per_user = max_uses_per_user
        self.created_by = created_by
        self.note = note


class CouponUsage(Database.BASE):
    __tablename__ = 'coupon_usages'

    id = Column(Integer, primary_key=True)
    coupon_id = Column(Integer, ForeignKey('coupons.id', ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(BigInteger, ForeignKey('users.telegram_id', ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(Integer, ForeignKey('orders.id', ondelete="SET NULL"), nullable=True)
    discount_applied = Column(Numeric(12, 2), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    coupon = relationship("Coupon", back_populates="usages")

    __table_args__ = (
        Index('ix_coupon_usages_user_coupon', 'user_id', 'coupon_id'),
    )

    def __init__(self, coupon_id: int, user_id: int, discount_applied, order_id: int = None, **kw: Any):
        super().__init__(**kw)
        self.coupon_id = coupon_id
        self.user_id = user_id
        self.order_id = order_id
        self.discount_applied = discount_applied


class Review(Database.BASE):
    """Product / order review with rating."""
    __tablename__ = 'reviews'

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id', ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(BigInteger, ForeignKey('users.telegram_id', ondelete="CASCADE"), nullable=False, index=True)
    item_name = Column(String(100), ForeignKey('goods.name', ondelete="CASCADE"), nullable=True)
    rating = Column(Integer, nullable=False)  # 1-5
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    order = relationship("Order", foreign_keys=lambda: [Review.order_id])
    user = relationship("User", foreign_keys=lambda: [Review.user_id])

    __table_args__ = (
        UniqueConstraint('order_id', 'user_id', name='uq_review_order_user'),
        Index('ix_reviews_item_rating', 'item_name', 'rating'),
    )

    def __init__(self, order_id: int, user_id: int, rating: int, comment: str = None,
                 item_name: str = None, **kw: Any):
        super().__init__(**kw)
        self.order_id = order_id
        self.user_id = user_id
        self.rating = rating
        self.comment = comment
        self.item_name = item_name


class SupportTicket(Database.BASE):
    """Support ticket for customer issues."""
    __tablename__ = 'support_tickets'

    id = Column(Integer, primary_key=True)
    ticket_code = Column(String(8), unique=True, nullable=False, index=True)
    user_id = Column(BigInteger, ForeignKey('users.telegram_id', ondelete="CASCADE"), nullable=False, index=True)
    subject = Column(String(200), nullable=False)
    status = Column(String(20), nullable=False, default='open')  # open, in_progress, resolved, closed
    priority = Column(String(10), nullable=False, default='normal')  # low, normal, high, urgent
    order_id = Column(Integer, ForeignKey('orders.id', ondelete="SET NULL"), nullable=True)
    assigned_to = Column(BigInteger, ForeignKey('users.telegram_id', ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", foreign_keys=lambda: [SupportTicket.user_id])
    messages = relationship("TicketMessage", back_populates="ticket", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_support_tickets_user_status', 'user_id', 'status'),
        Index('ix_support_tickets_status', 'status'),
    )

    def __init__(self, ticket_code: str, user_id: int, subject: str, status: str = 'open',
                 priority: str = 'normal', order_id: int = None, **kw: Any):
        super().__init__(**kw)
        self.ticket_code = ticket_code
        self.user_id = user_id
        self.subject = subject
        self.status = status
        self.priority = priority
        self.order_id = order_id


class TicketMessage(Database.BASE):
    __tablename__ = 'ticket_messages'

    id = Column(Integer, primary_key=True)
    ticket_id = Column(Integer, ForeignKey('support_tickets.id', ondelete="CASCADE"), nullable=False, index=True)
    sender_id = Column(BigInteger, nullable=False)
    sender_role = Column(String(10), nullable=False)  # 'user' or 'admin'
    message_text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    ticket = relationship("SupportTicket", back_populates="messages")

    def __init__(self, ticket_id: int, sender_id: int, sender_role: str, message_text: str, **kw: Any):
        super().__init__(**kw)
        self.ticket_id = ticket_id
        self.sender_id = sender_id
        self.sender_role = sender_role
        self.message_text = message_text


class Store(Database.BASE):
    """Store / branch location for multi-location support."""
    __tablename__ = 'stores'

    id = Column(Integer, primary_key=True)
    brand_id = Column(Integer, ForeignKey('brands.id', ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String(200), nullable=False)
    address = Column(Text, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    phone = Column(String(50), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    is_default = Column(Boolean, nullable=False, default=False)
    kitchen_group_id = Column(BigInteger, nullable=True)  # Per-branch kitchen Telegram group
    rider_group_id = Column(BigInteger, nullable=True)  # Per-branch rider Telegram group
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    brand = relationship("Brand", back_populates="stores")
    inventory = relationship("BranchInventory", back_populates="store", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('brand_id', 'name', name='uq_store_brand_name'),
    )

    def __init__(self, name: str, address: str = None, latitude: float = None,
                 longitude: float = None, phone: str = None, is_default: bool = False,
                 brand_id: int = None, kitchen_group_id: int = None,
                 rider_group_id: int = None, **kw: Any):
        super().__init__(**kw)
        self.name = name
        self.brand_id = brand_id
        self.address = address
        self.latitude = latitude
        self.longitude = longitude
        self.phone = phone
        self.is_default = is_default
        self.kitchen_group_id = kitchen_group_id
        self.rider_group_id = rider_group_id


class BranchInventory(Database.BASE):
    """Per-branch inventory tracking. Overrides Goods.stock_quantity for multi-branch brands."""
    __tablename__ = 'branch_inventory'

    id = Column(Integer, primary_key=True)
    store_id = Column(Integer, ForeignKey('stores.id', ondelete="CASCADE"), nullable=False, index=True)
    item_name = Column(String(100), ForeignKey('goods.name', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    stock_quantity = Column(Integer, nullable=False, default=0)
    reserved_quantity = Column(Integer, nullable=False, default=0)

    store = relationship("Store", back_populates="inventory")
    item = relationship("Goods", foreign_keys=lambda: [BranchInventory.item_name])

    __table_args__ = (
        UniqueConstraint('store_id', 'item_name', name='uq_branch_inventory_store_item'),
        Index('ix_branch_inventory_item', 'item_name'),
    )

    @property
    def available_quantity(self) -> int:
        return max(0, self.stock_quantity - self.reserved_quantity)

    def __init__(self, store_id: int, item_name: str, stock_quantity: int = 0,
                 reserved_quantity: int = 0, **kw: Any):
        super().__init__(**kw)
        self.store_id = store_id
        self.item_name = item_name
        self.stock_quantity = stock_quantity
        self.reserved_quantity = reserved_quantity


def register_models():
    """Create all database tables and insert default roles"""
    import logging
    import time

    from sqlalchemy.exc import OperationalError

    max_retries = 5
    retry_delay = 2  # seconds

    for attempt in range(1, max_retries + 1):
        try:
            db = Database()
            logging.info(f"Creating database tables (attempt {attempt}/{max_retries})...")
            Database.BASE.metadata.create_all(db.engine)

            # Verify tables were created
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            logging.info(f"Tables created successfully: {tables}")

            # Insert default roles
            Role.insert_roles()
            logging.info("Default roles inserted")

            # Ensure a default brand exists for migration
            _ensure_default_brand(db)
            logging.info("Default brand ensured")

            # Assign SUPERADMIN role to OWNER_ID
            _assign_superadmin_role(db)

            return  # Success - exit function

        except OperationalError as e:
            if "could not translate host name" in str(e) or "Temporary failure in name resolution" in str(e):
                if attempt < max_retries:
                    wait_time = retry_delay * (2 ** (attempt - 1))  # Exponential backoff: 2s, 4s, 8s, 16s
                    logging.warning(
                        f"Database connection failed (attempt {attempt}/{max_retries}): {e}. "
                        f"Retrying in {wait_time} seconds..."
                    )
                    time.sleep(wait_time)
                else:
                    logging.error(
                        f"Failed to connect to database after {max_retries} attempts. "
                        f"Please check if PostgreSQL container is running and network is configured correctly.",
                        exc_info=True
                    )
                    raise
            else:
                # Different OperationalError - raise immediately
                logging.error(f"Database operational error: {e}", exc_info=True)
                raise
        except Exception as e:
            logging.error(f"Failed to create database tables: {e}", exc_info=True)
            raise


def _ensure_default_brand(db):
    """Create a default brand and assign all existing unbranded data to it."""
    import logging

    from sqlalchemy import exists

    with db.session() as s:
        # Check if any brand exists
        has_brand = s.query(exists().where(Brand.id.isnot(None))).scalar()
        if has_brand:
            return

        # Create default brand
        default_brand = Brand(
            name="Default Brand",
            slug="default",
            description="Default brand (auto-created during migration)",
        )
        s.add(default_brand)
        s.flush()  # Get the ID

        brand_id = default_brand.id

        # Assign all unbranded categories to the default brand
        s.query(Categories).filter(Categories.brand_id.is_(None)).update(
            {Categories.brand_id: brand_id}, synchronize_session=False
        )

        # Assign all unbranded goods to the default brand
        s.query(Goods).filter(Goods.brand_id.is_(None)).update(
            {Goods.brand_id: brand_id}, synchronize_session=False
        )

        # Assign all unbranded stores to the default brand
        s.query(Store).filter(Store.brand_id.is_(None)).update(
            {Store.brand_id: brand_id}, synchronize_session=False
        )

        # Assign all unbranded orders to the default brand
        s.query(Order).filter(Order.brand_id.is_(None)).update(
            {Order.brand_id: brand_id}, synchronize_session=False
        )

        # Assign all unbranded bot settings to the default brand (leave global ones as null)
        # Don't auto-assign settings — they should remain global unless explicitly scoped

        s.commit()
        logging.info(f"Created default brand (id={brand_id}) and assigned existing data")


def _assign_superadmin_role(db):
    """Assign SUPERADMIN role to OWNER_ID from env."""
    import logging
    import os

    owner_id = os.environ.get('OWNER_ID')
    if not owner_id:
        return

    try:
        owner_id = int(owner_id)
    except (ValueError, TypeError):
        return

    with db.session() as s:
        # Get SUPERADMIN role id
        superadmin_role = s.query(Role).filter_by(name='SUPERADMIN').first()
        if not superadmin_role:
            return

        # Check if user exists and update role
        user = s.query(User).filter_by(telegram_id=owner_id).first()
        if user and user.role_id != superadmin_role.id:
            user.role_id = superadmin_role.id
            s.commit()
            logging.info(f"Assigned SUPERADMIN role to OWNER_ID={owner_id}")
