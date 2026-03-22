#!/usr/bin/env python3
"""
Comprehensive test-data loader for Telegram Shop.

Usage:
    python load_test_data.py                  # Load all datasets
    python load_test_data.py --dataset thai   # Load only "thai" dataset
    python load_test_data.py --dataset multi  # Load multi-brand + multi-store
    python load_test_data.py --dataset stress # Load high-volume stress data
    python load_test_data.py --list           # List available datasets
    python load_test_data.py --clean          # Wipe seeded data and start fresh

Datasets:
    thai        – Thai restaurant with full menu, modifiers, time-limited items
    afghan      – Afghan/Middle-Eastern restaurant with separate brand
    cafe        – Coffee & bakery brand with product inventory
    multi       – Multi-brand + multi-store setup with branch inventory
    users       – Fake user accounts across roles and locales
    orders      – Realistic order history across statuses and payment methods
    referrals   – Referral chains and earnings
    coupons     – Promo codes: percent, fixed, expired, exhausted
    reviews     – Product reviews with varied ratings
    support     – Support tickets in various states
    inventory   – Inventory logs and stock edge cases
    stress      – High-volume data (200 users, 500 orders) for perf testing
    all         – Everything above (default)
"""
import argparse
import os
import random
import string
import sys
from datetime import datetime, timedelta
from decimal import Decimal

sys.path.insert(0, os.path.dirname(__file__))

from bot.database.models import register_models

register_models()

from bot.database import Database
from bot.database.models.main import (
    BitcoinAddress,
    BotSettings,
    Brand,
    BrandStaff,
    BranchInventory,
    BoughtGoods,
    Categories,
    Coupon,
    CouponUsage,
    CustomerInfo,
    DeliveryChatMessage,
    Goods,
    InventoryLog,
    Operations,
    Order,
    OrderItem,
    ReferenceCode,
    ReferenceCodeUsage,
    ReferralEarnings,
    Review,
    Role,
    ShoppingCart,
    Store,
    SupportTicket,
    TicketMessage,
    User,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_now = datetime.utcnow()


def _ago(**kw):
    return _now - timedelta(**kw)


def _rand_code(n=6):
    return "".join(random.choices(string.ascii_uppercase, k=n))


def _rand_phone():
    return f"08{random.randint(10000000, 99999999)}"


def _get_or_create_brand(s, name, slug, **kw):
    brand = s.query(Brand).filter_by(slug=slug).first()
    if brand:
        return brand
    brand = Brand(name=name, slug=slug, **kw)
    s.add(brand)
    s.flush()
    return brand


def _get_or_create_category(s, name, brand_id, **kw):
    cat = s.query(Categories).filter_by(name=name).first()
    if cat:
        return cat
    cat = Categories(name=name, brand_id=brand_id, **kw)
    s.add(cat)
    s.flush()
    return cat


def _get_or_create_item(s, name, **kw):
    item = s.query(Goods).filter_by(name=name).first()
    if item:
        return item
    item = Goods(name=name, **kw)
    s.add(item)
    s.flush()
    return item


def _get_or_create_user(s, tid, **kw):
    user = s.query(User).filter_by(telegram_id=tid).first()
    if user:
        return user
    user = User(telegram_id=tid, registration_date=kw.pop("registration_date", _now), **kw)
    s.add(user)
    s.flush()
    return user


def _get_or_create_store(s, brand_id, name, **kw):
    store = s.query(Store).filter_by(brand_id=brand_id, name=name).first()
    if store:
        return store
    store = Store(name=name, brand_id=brand_id, **kw)
    s.add(store)
    s.flush()
    return store


def _get_role_id(s, role_name):
    role = s.query(Role).filter_by(name=role_name).first()
    return role.id if role else 1


# ---------------------------------------------------------------------------
# Bangkok-area GPS coordinates for realistic locations
# ---------------------------------------------------------------------------
BKK_LOCATIONS = [
    # Central Bangkok
    (13.7563, 100.5018, "Siam Square"),
    (13.7466, 100.5347, "Sukhumvit Soi 11"),
    (13.7284, 100.5232, "Silom/Sathorn"),
    (13.7633, 100.5384, "Asok"),
    # Inner ring
    (13.7948, 100.5538, "Chatuchak"),
    (13.7178, 100.5101, "Lumpini"),
    (13.7261, 100.5604, "Ekkamai"),
    (13.7371, 100.5770, "Phra Khanong"),
    # Mid ring
    (13.8511, 100.5621, "Don Mueang"),
    (13.6858, 100.5329, "Bang Na"),
    (13.7747, 100.6350, "Lat Krabang"),
    (13.8024, 100.4960, "Bang Sue"),
    # Outer ring
    (13.9035, 100.5350, "Rangsit"),
    (13.6525, 100.4931, "Samut Prakan"),
    (13.8770, 100.6272, "Min Buri"),
]

THAI_ADDRESSES = [
    "123/4 Sukhumvit Soi 33, Khlong Toei Nuea, Watthana",
    "56 Silom Rd, Suriyawong, Bang Rak",
    "789 Phahonyothin Rd, Chatuchak",
    "10/2 Ratchadaphisek Soi 14, Huai Khwang",
    "321 Thonglor Soi 10, Khlong Tan Nuea",
    "45/1 Rama 9 Rd, Bang Kapi",
    "88 Lat Phrao 71, Wang Thonglang",
    "5 Charoen Krung Soi 42, Bang Rak",
    "200 Petchburi Rd, Makkasan, Ratchathewi",
    "67/3 Ngam Wong Wan Rd, Chatuchak",
    "15 Soi Ari, Phahonyothin 7, Phaya Thai",
    "999 Rama 4 Rd, Phra Khanong",
]

# ---------------------------------------------------------------------------
# Dataset: Thai restaurant
# ---------------------------------------------------------------------------
def load_thai(s):
    print("[thai] Loading Thai restaurant brand...")
    brand = _get_or_create_brand(
        s, "Siam Kitchen", "siam-kitchen",
        description="Authentic Thai cuisine — street food to fine dining",
        promptpay_id="0891234567",
        promptpay_name="Siam Kitchen Co Ltd",
        timezone="Asia/Bangkok",
    )

    # --- Categories ---
    appetizers = _get_or_create_category(s, "Appetizers", brand.id, sort_order=1,
                                         description="Start your meal right")
    mains = _get_or_create_category(s, "Main Dishes", brand.id, sort_order=2,
                                     description="Rice & noodle favourites")
    curries = _get_or_create_category(s, "Curries", brand.id, sort_order=3,
                                       description="Thai curries with steamed rice")
    salads = _get_or_create_category(s, "Salads & Som Tam", brand.id, sort_order=4)
    breakfast = _get_or_create_category(s, "Breakfast Set", brand.id, sort_order=0,
                                         description="Served 06:00–11:00",
                                         available_from="06:00", available_until="11:00")
    drinks_cat = _get_or_create_category(s, "Thai Drinks", brand.id, sort_order=5)
    desserts_cat = _get_or_create_category(s, "Thai Desserts", brand.id, sort_order=6)

    # --- Items ---
    items = [
        # Appetizers
        dict(name="Spring Rolls (4 pcs)", price=65, description="Crispy vegetable spring rolls with sweet chili",
             category_name="Appetizers", brand_id=brand.id, prep_time_minutes=8, calories=280,
             allergens="gluten"),
        dict(name="Satay Chicken (4 skewers)", price=89, description="Grilled chicken skewers with peanut sauce",
             category_name="Appetizers", brand_id=brand.id, prep_time_minutes=12, calories=340,
             allergens="peanuts"),
        dict(name="Tod Mun Pla", price=79, description="Thai fish cakes with cucumber relish",
             category_name="Appetizers", brand_id=brand.id, prep_time_minutes=10, calories=260,
             allergens="fish,gluten"),

        # Mains
        dict(name="Pad Thai Goong", price=120, description="Stir-fried rice noodles with prawns, tamarind sauce, peanuts",
             category_name="Main Dishes", brand_id=brand.id, prep_time_minutes=12, calories=520,
             allergens="peanuts,shellfish",
             modifiers={"Spice Level": {"options": ["Mild", "Medium", "Hot", "Thai Hot"], "required": True},
                        "Extra Protein": {"options": ["None", "Egg +15", "Tofu +20", "Extra Prawn +40"], "required": False}}),
        dict(name="Khao Pad Gai", price=89, description="Thai fried rice with chicken and egg",
             category_name="Main Dishes", brand_id=brand.id, prep_time_minutes=10, calories=480),
        dict(name="Pad See Ew", price=95, description="Wide rice noodles stir-fried with Chinese broccoli and soy",
             category_name="Main Dishes", brand_id=brand.id, prep_time_minutes=10, calories=510,
             allergens="soy,gluten"),
        dict(name="Pad Kra Pao Moo", price=85, description="Holy basil stir-fry with minced pork and fried egg",
             category_name="Main Dishes", brand_id=brand.id, prep_time_minutes=8, calories=460,
             modifiers={"Spice Level": {"options": ["Mild", "Medium", "Hot"], "required": True}}),
        dict(name="Rad Na", price=99, description="Wide noodles in thick gravy with pork and broccoli",
             category_name="Main Dishes", brand_id=brand.id, prep_time_minutes=12, calories=490),

        # Curries
        dict(name="Green Curry Chicken", price=110, description="Coconut green curry with bamboo shoots and Thai basil",
             category_name="Curries", brand_id=brand.id, prep_time_minutes=15, calories=450,
             allergens="dairy"),
        dict(name="Massaman Beef", price=140, description="Rich peanut curry with potato and slow-cooked beef",
             category_name="Curries", brand_id=brand.id, prep_time_minutes=20, calories=580,
             allergens="peanuts,dairy"),
        dict(name="Panang Curry Pork", price=115, description="Thick panang curry with kaffir lime and pork",
             category_name="Curries", brand_id=brand.id, prep_time_minutes=15, calories=470),
        dict(name="Tom Yum Goong", price=130, description="Hot & sour prawn soup with lemongrass and galangal",
             category_name="Curries", brand_id=brand.id, prep_time_minutes=12, calories=210,
             allergens="shellfish"),

        # Salads
        dict(name="Som Tam Thai", price=75, description="Green papaya salad with peanuts and dried shrimp",
             category_name="Salads & Som Tam", brand_id=brand.id, prep_time_minutes=5, calories=180,
             allergens="peanuts,shellfish",
             modifiers={"Spice Level": {"options": ["Mild", "Medium", "Hot", "Fire"], "required": True}}),
        dict(name="Yum Woon Sen", price=95, description="Glass noodle salad with seafood and lime dressing",
             category_name="Salads & Som Tam", brand_id=brand.id, prep_time_minutes=8, calories=230),
        dict(name="Larb Moo", price=85, description="Spicy minced pork salad with herbs and roasted rice",
             category_name="Salads & Som Tam", brand_id=brand.id, prep_time_minutes=7, calories=200),

        # Breakfast (time-limited)
        dict(name="Jok Moo (Rice Porridge)", price=55, description="Breakfast rice porridge with pork and soft egg",
             category_name="Breakfast Set", brand_id=brand.id, prep_time_minutes=8, calories=320,
             available_from="06:00", available_until="11:00"),
        dict(name="Pa Tong Go + Coffee Set", price=49, description="Thai donuts with sweet condensed milk coffee",
             category_name="Breakfast Set", brand_id=brand.id, prep_time_minutes=5, calories=410,
             available_from="06:00", available_until="11:00", allergens="gluten,dairy"),

        # Drinks
        dict(name="Thai Iced Tea", price=45, description="Classic orange Thai tea with condensed milk",
             category_name="Thai Drinks", brand_id=brand.id, prep_time_minutes=3, calories=180,
             allergens="dairy"),
        dict(name="Coconut Water", price=40, description="Fresh young coconut water",
             category_name="Thai Drinks", brand_id=brand.id, item_type="product", stock_quantity=50),
        dict(name="Singha Beer", price=70, description="Thai lager 330ml",
             category_name="Thai Drinks", brand_id=brand.id, item_type="product", stock_quantity=100),
        dict(name="Butterfly Pea Lemonade", price=55, description="Color-changing herbal lemonade",
             category_name="Thai Drinks", brand_id=brand.id, prep_time_minutes=3, calories=90),

        # Desserts
        dict(name="Mango Sticky Rice", price=85, description="Sweet sticky rice with fresh mango and coconut cream",
             category_name="Thai Desserts", brand_id=brand.id, prep_time_minutes=5, calories=380,
             daily_limit=30, allergens="dairy"),
        dict(name="Roti with Banana", price=55, description="Crispy roti with banana, egg and condensed milk",
             category_name="Thai Desserts", brand_id=brand.id, prep_time_minutes=7, calories=450,
             allergens="gluten,dairy,egg"),
        dict(name="Tub Tim Grob", price=60, description="Red rubies (water chestnuts in coconut milk on ice)",
             category_name="Thai Desserts", brand_id=brand.id, prep_time_minutes=3, calories=200),
    ]

    for spec in items:
        _get_or_create_item(s, **spec)

    # Mark one item sold out for testing
    sold_out = s.query(Goods).filter_by(name="Mango Sticky Rice").first()
    if sold_out:
        sold_out.daily_sold_count = 30  # hit the daily limit

    # Mark one item inactive
    inactive = s.query(Goods).filter_by(name="Rad Na").first()
    if inactive:
        inactive.is_active = False

    s.commit()
    print(f"  Brand: {brand.name} (id={brand.id}), {len(items)} items across 7 categories")
    return brand


# ---------------------------------------------------------------------------
# Dataset: Afghan restaurant
# ---------------------------------------------------------------------------
def load_afghan(s):
    print("[afghan] Loading Afghan restaurant brand...")
    brand = _get_or_create_brand(
        s, "Kabul Grill", "kabul-grill",
        description="Traditional Afghan & Middle-Eastern cuisine",
        timezone="Asia/Bangkok",
    )

    _get_or_create_category(s, "Kebabs", brand.id, sort_order=1, description="Charcoal-grilled meats")
    _get_or_create_category(s, "Rice Dishes", brand.id, sort_order=2, description="Kabuli & Biryani")
    _get_or_create_category(s, "Breads & Sides", brand.id, sort_order=3)
    _get_or_create_category(s, "Afghan Drinks", brand.id, sort_order=4)

    items = [
        dict(name="Chapli Kebab", price=110, description="Spiced minced beef patties with herbs",
             category_name="Kebabs", brand_id=brand.id, prep_time_minutes=15, calories=420),
        dict(name="Seekh Kebab (6 pcs)", price=130, description="Minced lamb skewers from the tandoor",
             category_name="Kebabs", brand_id=brand.id, prep_time_minutes=18, calories=480),
        dict(name="Chicken Tikka", price=120, description="Marinated chicken grilled in tandoor",
             category_name="Kebabs", brand_id=brand.id, prep_time_minutes=20, calories=350),
        dict(name="Lamb Chops (4 pcs)", price=220, description="Premium lamb chops with Afghan spices",
             category_name="Kebabs", brand_id=brand.id, prep_time_minutes=25, calories=550),

        dict(name="Kabuli Pulao", price=150, description="Signature Afghan rice with lamb, raisins & carrots",
             category_name="Rice Dishes", brand_id=brand.id, prep_time_minutes=30, calories=620),
        dict(name="Qabili Palau (Chicken)", price=130, description="Fragrant rice with chicken and nuts",
             category_name="Rice Dishes", brand_id=brand.id, prep_time_minutes=25, calories=560),
        dict(name="Mantu (Dumplings)", price=99, description="Steamed dumplings with spiced lamb and yogurt sauce",
             category_name="Rice Dishes", brand_id=brand.id, prep_time_minutes=20, calories=380,
             allergens="gluten,dairy"),

        dict(name="Afghan Naan", price=25, description="Freshly baked flatbread from the tandoor",
             category_name="Breads & Sides", brand_id=brand.id, prep_time_minutes=8, calories=220,
             allergens="gluten"),
        dict(name="Bolani (Potato)", price=45, description="Stuffed flatbread with spiced potato filling",
             category_name="Breads & Sides", brand_id=brand.id, prep_time_minutes=10, calories=310,
             allergens="gluten"),
        dict(name="Salata (Afghan Salad)", price=40, description="Fresh tomato, cucumber, onion with lemon dressing",
             category_name="Breads & Sides", brand_id=brand.id, prep_time_minutes=3, calories=80),

        dict(name="Doogh", price=35, description="Traditional yogurt drink with mint",
             category_name="Afghan Drinks", brand_id=brand.id, prep_time_minutes=2, calories=120,
             allergens="dairy"),
        dict(name="Afghan Green Tea", price=30, description="Cardamom green tea",
             category_name="Afghan Drinks", brand_id=brand.id, prep_time_minutes=5, calories=5),
    ]

    for spec in items:
        _get_or_create_item(s, **spec)

    s.commit()
    print(f"  Brand: {brand.name} (id={brand.id}), {len(items)} items across 4 categories")
    return brand


# ---------------------------------------------------------------------------
# Dataset: Cafe / bakery (product-heavy, inventory-tracked)
# ---------------------------------------------------------------------------
def load_cafe(s):
    print("[cafe] Loading cafe & bakery brand...")
    brand = _get_or_create_brand(
        s, "Bean & Crumb", "bean-crumb",
        description="Specialty coffee and fresh-baked goods",
        timezone="Asia/Bangkok",
    )

    _get_or_create_category(s, "Hot Coffee", brand.id, sort_order=1)
    _get_or_create_category(s, "Cold Coffee", brand.id, sort_order=2)
    _get_or_create_category(s, "Bakery", brand.id, sort_order=3, description="Freshly baked daily")
    _get_or_create_category(s, "Bottled Drinks", brand.id, sort_order=4)

    items = [
        # Hot coffee
        dict(name="Espresso", price=50, description="Double shot espresso",
             category_name="Hot Coffee", brand_id=brand.id, prep_time_minutes=3, calories=10),
        dict(name="Cappuccino", price=75, description="Espresso with steamed milk and foam",
             category_name="Hot Coffee", brand_id=brand.id, prep_time_minutes=4, calories=120,
             allergens="dairy",
             modifiers={"Milk": {"options": ["Regular", "Oat +20", "Soy +15", "Almond +20"], "required": True},
                        "Size": {"options": ["Regular", "Large +25"], "required": True}}),
        dict(name="Latte", price=80, description="Espresso with steamed milk",
             category_name="Hot Coffee", brand_id=brand.id, prep_time_minutes=4, calories=150,
             allergens="dairy",
             modifiers={"Milk": {"options": ["Regular", "Oat +20", "Soy +15", "Almond +20"], "required": True}}),
        dict(name="Matcha Latte", price=90, description="Ceremonial grade matcha with milk",
             category_name="Hot Coffee", brand_id=brand.id, prep_time_minutes=4, calories=170,
             allergens="dairy"),

        # Cold coffee
        dict(name="Iced Americano", price=65, description="Double espresso over ice",
             category_name="Cold Coffee", brand_id=brand.id, prep_time_minutes=2, calories=15),
        dict(name="Cold Brew", price=85, description="16-hour cold brew concentrate",
             category_name="Cold Coffee", brand_id=brand.id, prep_time_minutes=1, calories=10),
        dict(name="Iced Mocha", price=95, description="Espresso, chocolate, milk and ice",
             category_name="Cold Coffee", brand_id=brand.id, prep_time_minutes=4, calories=280,
             allergens="dairy"),

        # Bakery (products — inventory tracked)
        dict(name="Croissant", price=55, description="Butter croissant, baked fresh daily",
             category_name="Bakery", brand_id=brand.id, item_type="product",
             stock_quantity=40, calories=310, allergens="gluten,dairy"),
        dict(name="Banana Bread Slice", price=65, description="Moist banana bread with walnuts",
             category_name="Bakery", brand_id=brand.id, item_type="product",
             stock_quantity=20, calories=350, allergens="gluten,nuts,egg"),
        dict(name="Chocolate Muffin", price=60, description="Double chocolate chip muffin",
             category_name="Bakery", brand_id=brand.id, item_type="product",
             stock_quantity=25, calories=410, allergens="gluten,dairy,egg"),
        dict(name="Almond Cookie (3 pcs)", price=45, description="Chewy almond cookies",
             category_name="Bakery", brand_id=brand.id, item_type="product",
             stock_quantity=30, calories=280, allergens="nuts,gluten"),

        # Bottled (products)
        dict(name="Sparkling Water 500ml", price=30, description="Imported sparkling water",
             category_name="Bottled Drinks", brand_id=brand.id, item_type="product", stock_quantity=60),
        dict(name="Fresh OJ Bottle", price=55, description="Cold-pressed orange juice 300ml",
             category_name="Bottled Drinks", brand_id=brand.id, item_type="product",
             stock_quantity=15, calories=130),
    ]

    for spec in items:
        _get_or_create_item(s, **spec)

    s.commit()
    print(f"  Brand: {brand.name} (id={brand.id}), {len(items)} items across 4 categories")
    return brand


# ---------------------------------------------------------------------------
# Dataset: Multi-store setup
# ---------------------------------------------------------------------------
def load_multi(s):
    print("[multi] Loading multi-brand, multi-store configuration...")

    # Ensure brands exist first
    thai_brand = s.query(Brand).filter_by(slug="siam-kitchen").first()
    cafe_brand = s.query(Brand).filter_by(slug="bean-crumb").first()

    if not thai_brand:
        print("  (auto-loading thai dataset first)")
        thai_brand = load_thai(s)
    if not cafe_brand:
        print("  (auto-loading cafe dataset first)")
        cafe_brand = load_cafe(s)

    # Stores for Siam Kitchen
    stores_thai = [
        dict(name="Siam Kitchen - Siam Square", address="123 Siam Square Soi 5, Pathumwan",
             latitude=13.7450, longitude=100.5340, phone="021234567", is_default=True),
        dict(name="Siam Kitchen - Thonglor", address="55 Thonglor Soi 13, Watthana",
             latitude=13.7320, longitude=100.5780, phone="021234568"),
        dict(name="Siam Kitchen - Chatuchak", address="88 Phahonyothin Rd, Chatuchak",
             latitude=13.7999, longitude=100.5530, phone="021234569"),
    ]
    created_stores = []
    for spec in stores_thai:
        store = _get_or_create_store(s, thai_brand.id, **spec)
        created_stores.append(store)
    print(f"  {len(stores_thai)} stores for {thai_brand.name}")

    # Stores for Bean & Crumb
    stores_cafe = [
        dict(name="Bean & Crumb - Ari", address="15 Soi Ari 1, Phaya Thai",
             latitude=13.7795, longitude=100.5445, phone="029876543", is_default=True),
        dict(name="Bean & Crumb - Ekkamai", address="10 Ekkamai Soi 2, Phra Khanong",
             latitude=13.7261, longitude=100.5604, phone="029876544"),
    ]
    for spec in stores_cafe:
        _get_or_create_store(s, cafe_brand.id, **spec)
    print(f"  {len(stores_cafe)} stores for {cafe_brand.name}")

    # Branch inventory (different stock per store)
    for store in created_stores:
        # Each store has different Singha Beer stock
        existing = s.query(BranchInventory).filter_by(
            store_id=store.id, item_name="Singha Beer").first()
        if not existing:
            s.add(BranchInventory(store_id=store.id, item_name="Singha Beer",
                                  stock_quantity=random.randint(20, 80)))
        existing2 = s.query(BranchInventory).filter_by(
            store_id=store.id, item_name="Coconut Water").first()
        if not existing2:
            s.add(BranchInventory(store_id=store.id, item_name="Coconut Water",
                                  stock_quantity=random.randint(10, 40)))

    s.commit()
    print("  Branch-level inventory set for product items")
    return thai_brand, cafe_brand


# ---------------------------------------------------------------------------
# Dataset: Fake users
# ---------------------------------------------------------------------------
FAKE_USER_BASE_ID = 9000000000  # High range to avoid colliding with real Telegram IDs


def load_users(s, count=50):
    print(f"[users] Creating {count} fake users...")

    locales = ["en", "th", "ru", "ar", "fa", "ps", "fr"]
    role_ids = {name: _get_role_id(s, name) for name in ("USER", "ADMIN", "OWNER")}
    created = 0

    for i in range(count):
        tid = FAKE_USER_BASE_ID + i
        reg_date = _ago(days=random.randint(1, 180))
        locale = random.choice(locales)
        role_id = role_ids["USER"]
        # A few admins
        if i < 3:
            role_id = role_ids["ADMIN"]
        elif i == 3:
            role_id = role_ids["OWNER"]

        is_banned = (i >= count - 2)  # Last 2 users are banned

        user = _get_or_create_user(
            s, tid,
            registration_date=reg_date,
            role_id=role_id,
            locale=locale,
            is_banned=is_banned,
            banned_at=_now if is_banned else None,
            ban_reason="Spam / abusive messages" if is_banned else None,
            privacy_accepted_at=reg_date + timedelta(minutes=2),
        )

        # Customer info
        loc = random.choice(BKK_LOCATIONS)
        existing_ci = s.query(CustomerInfo).filter_by(telegram_id=tid).first()
        if not existing_ci:
            ci = CustomerInfo(
                telegram_id=tid,
                phone_number=_rand_phone(),
                delivery_address=random.choice(THAI_ADDRESSES),
            )
            ci.latitude = loc[0] + random.uniform(-0.005, 0.005)
            ci.longitude = loc[1] + random.uniform(-0.005, 0.005)
            ci.total_spendings = Decimal(str(random.randint(0, 5000)))
            ci.completed_orders_count = random.randint(0, 25)
            ci.bonus_balance = Decimal(str(random.randint(0, 200)))
            s.add(ci)

        created += 1

    # Brand staff assignments
    thai_brand = s.query(Brand).filter_by(slug="siam-kitchen").first()
    if thai_brand:
        for i, role in enumerate(["owner", "admin", "kitchen", "rider"]):
            tid = FAKE_USER_BASE_ID + i
            existing = s.query(BrandStaff).filter_by(brand_id=thai_brand.id, user_id=tid).first()
            if not existing:
                s.add(BrandStaff(brand_id=thai_brand.id, user_id=tid, role=role))

    s.commit()
    print(f"  {created} users created (3 admins, 1 owner, 2 banned, various locales)")
    return [FAKE_USER_BASE_ID + i for i in range(count)]


# ---------------------------------------------------------------------------
# Dataset: Orders across statuses and payment methods
# ---------------------------------------------------------------------------
def load_orders(s, user_ids=None, count=80):
    print(f"[orders] Creating {count} orders across all statuses...")
    if not user_ids:
        user_ids = [FAKE_USER_BASE_ID + i for i in range(50)]

    thai_brand = s.query(Brand).filter_by(slug="siam-kitchen").first()
    afghan_brand = s.query(Brand).filter_by(slug="kabul-grill").first()
    cafe_brand = s.query(Brand).filter_by(slug="bean-crumb").first()

    brands = [b for b in [thai_brand, afghan_brand, cafe_brand] if b]
    if not brands:
        print("  WARN: No brands found — load a menu dataset first")
        return

    statuses = ["pending", "reserved", "confirmed", "preparing", "ready",
                "out_for_delivery", "delivered", "cancelled", "expired"]
    payment_methods = ["promptpay", "cash", "bitcoin"]
    delivery_types = ["door", "dead_drop", "pickup"]

    all_items = s.query(Goods).filter(Goods.is_active.is_(True)).all()
    if not all_items:
        print("  WARN: No active items in DB")
        return

    items_by_brand = {}
    for item in all_items:
        items_by_brand.setdefault(item.brand_id, []).append(item)

    created = 0
    for i in range(count):
        brand = random.choice(brands)
        brand_items = items_by_brand.get(brand.id, [])
        if not brand_items:
            continue

        buyer_id = random.choice(user_ids)
        status = random.choices(statuses, weights=[5, 3, 8, 5, 3, 5, 40, 8, 3])[0]
        payment = random.choices(payment_methods, weights=[60, 30, 10])[0]
        del_type = random.choices(delivery_types, weights=[70, 15, 15])[0]

        loc = random.choice(BKK_LOCATIONS)
        lat = loc[0] + random.uniform(-0.01, 0.01)
        lng = loc[1] + random.uniform(-0.01, 0.01)

        # Pick 1-4 items
        n_items = random.randint(1, 4)
        chosen_items = random.sample(brand_items, min(n_items, len(brand_items)))
        total = sum(float(it.price) * random.randint(1, 3) for it in chosen_items)

        order_date = _ago(days=random.randint(0, 90), hours=random.randint(0, 23))
        completed_at = None
        if status == "delivered":
            completed_at = order_date + timedelta(minutes=random.randint(30, 120))
        elif status == "cancelled":
            completed_at = order_date + timedelta(minutes=random.randint(5, 60))

        order = Order(
            buyer_id=buyer_id,
            total_price=Decimal(str(round(total, 2))),
            payment_method=payment,
            delivery_address=random.choice(THAI_ADDRESSES),
            phone_number=_rand_phone(),
            delivery_note=random.choice([None, "Leave at door", "Call before delivery", "No chili", ""]),
            order_status=status,
            order_code=_rand_code(),
            latitude=lat,
            longitude=lng,
            google_maps_link=f"https://maps.google.com/?q={lat},{lng}",
            delivery_type=del_type,
            brand_id=brand.id,
            bonus_applied=Decimal(str(random.choice([0, 0, 0, 10, 20, 50]))),
        )
        order.created_at = order_date
        order.completed_at = completed_at

        if del_type == "dead_drop":
            order.drop_instructions = "Behind the 7-Eleven, look for the green mailbox"
            order.drop_latitude = lat + 0.001
            order.drop_longitude = lng + 0.001

        if status in ("preparing", "ready", "out_for_delivery", "delivered"):
            order.total_prep_time_minutes = random.randint(10, 40)
            order.estimated_ready_at = order_date + timedelta(minutes=order.total_prep_time_minutes)

        if status in ("out_for_delivery", "delivered"):
            order.driver_id = FAKE_USER_BASE_ID + 3  # rider

        if payment == "promptpay" and status not in ("pending", "expired"):
            order.payment_verified_at = order_date + timedelta(minutes=random.randint(1, 10))
            order.payment_verified_by = FAKE_USER_BASE_ID + 1  # admin
            order.slip_verify_status = random.choice(["verified", "verified", "amount_mismatch"])

        s.add(order)
        s.flush()

        # Order items
        for item in chosen_items:
            qty = random.randint(1, 3)
            s.add(OrderItem(
                order_id=order.id,
                item_name=item.name,
                price=item.price,
                quantity=qty,
            ))

        created += 1

    s.commit()
    print(f"  {created} orders created across {len(statuses)} statuses, "
          f"{len(payment_methods)} payment methods, {len(delivery_types)} delivery types")


# ---------------------------------------------------------------------------
# Dataset: Referrals
# ---------------------------------------------------------------------------
def load_referrals(s, user_ids=None):
    print("[referrals] Creating referral chains and earnings...")
    if not user_ids:
        user_ids = [FAKE_USER_BASE_ID + i for i in range(50)]

    count = 0
    # Create referral chains: user[5] referred by user[0], user[6] by user[1], etc.
    for i in range(5, min(25, len(user_ids))):
        referrer_idx = i % 5  # cycle through first 5 users as referrers
        referrer_id = user_ids[referrer_idx]
        referral_id = user_ids[i]

        # Update user's referral_id
        user = s.query(User).filter_by(telegram_id=referral_id).first()
        if user:
            user.referral_id = referrer_id

        # Create earning record
        original = Decimal(str(random.randint(100, 500)))
        commission = original * Decimal("0.05")
        existing = s.query(ReferralEarnings).filter_by(
            referrer_id=referrer_id, referral_id=referral_id).first()
        if not existing:
            s.add(ReferralEarnings(
                referrer_id=referrer_id,
                referral_id=referral_id,
                amount=commission,
                original_amount=original,
            ))
            count += 1

    # Reference codes
    for i in range(3):
        code = f"REF{_rand_code(4)}"
        existing = s.query(ReferenceCode).filter_by(code=code).first()
        if not existing:
            s.add(ReferenceCode(
                code=code,
                created_by=user_ids[i],
                max_uses=random.choice([None, 10, 50]),
                current_uses=random.randint(0, 5),
                note=f"Referral code from user #{i}",
            ))

    s.commit()
    print(f"  {count} referral earnings, 3 reference codes")


# ---------------------------------------------------------------------------
# Dataset: Coupons
# ---------------------------------------------------------------------------
def load_coupons(s, user_ids=None):
    print("[coupons] Creating coupon/promo codes...")
    if not user_ids:
        user_ids = [FAKE_USER_BASE_ID + i for i in range(50)]

    coupons_spec = [
        # Active percent
        dict(code="WELCOME10", discount_type="percent", discount_value=Decimal("10"),
             min_order=Decimal("100"), max_discount=Decimal("50"),
             valid_until=_now + timedelta(days=30), max_uses=1000,
             note="New user welcome discount"),
        # Active fixed
        dict(code="FLAT50", discount_type="fixed", discount_value=Decimal("50"),
             min_order=Decimal("200"), valid_until=_now + timedelta(days=14),
             max_uses=200, note="Flat 50 off"),
        # High-value percent
        dict(code="VIP25", discount_type="percent", discount_value=Decimal("25"),
             min_order=Decimal("500"), max_discount=Decimal("200"),
             valid_until=_now + timedelta(days=60), max_uses=50,
             max_uses_per_user=2, note="VIP customers only"),
        # Expired
        dict(code="EXPIRED20", discount_type="percent", discount_value=Decimal("20"),
             valid_from=_ago(days=60), valid_until=_ago(days=30),
             max_uses=100, note="This one is expired"),
        # Exhausted (all uses consumed)
        dict(code="SOLDOUT", discount_type="fixed", discount_value=Decimal("30"),
             max_uses=5, note="All uses consumed"),
        # Unlimited, no minimum
        dict(code="FREEDELIVERY", discount_type="fixed", discount_value=Decimal("80"),
             note="Free delivery — unlimited uses"),
    ]

    for spec in coupons_spec:
        existing = s.query(Coupon).filter_by(code=spec["code"]).first()
        if existing:
            continue
        coupon = Coupon(created_by=user_ids[0], **spec)
        s.add(coupon)
        s.flush()

        # Exhaust the SOLDOUT coupon
        if spec["code"] == "SOLDOUT":
            coupon.current_uses = 5
            for j in range(5):
                s.add(CouponUsage(
                    coupon_id=coupon.id,
                    user_id=user_ids[j + 5],
                    discount_applied=Decimal("30"),
                ))

        # Add some usage to WELCOME10
        if spec["code"] == "WELCOME10":
            for j in range(min(8, len(user_ids) - 10)):
                s.add(CouponUsage(
                    coupon_id=coupon.id,
                    user_id=user_ids[j + 10],
                    discount_applied=Decimal(str(random.randint(10, 50))),
                ))
            coupon.current_uses = 8

    s.commit()
    print(f"  {len(coupons_spec)} coupons (active, expired, exhausted, unlimited)")


# ---------------------------------------------------------------------------
# Dataset: Reviews
# ---------------------------------------------------------------------------
def load_reviews(s, user_ids=None):
    print("[reviews] Creating product reviews...")
    if not user_ids:
        user_ids = [FAKE_USER_BASE_ID + i for i in range(50)]

    delivered_orders = s.query(Order).filter_by(order_status="delivered").limit(40).all()
    if not delivered_orders:
        print("  WARN: No delivered orders found — load orders first")
        return

    comments = [
        "Excellent! Will order again.",
        "Good food, fast delivery.",
        "A bit too spicy for me but good.",
        "Portion was smaller than expected.",
        "Amazing flavours, just like back home!",
        "Delivery was late but food was good.",
        "Not fresh. Disappointed.",
        "Best I've had in Bangkok!",
        "Average. Nothing special.",
        "Great value for the price.",
        None, None, None,  # Some reviews without comments
    ]

    count = 0
    for order in delivered_orders:
        if not order.buyer_id:
            continue
        existing = s.query(Review).filter_by(order_id=order.id, user_id=order.buyer_id).first()
        if existing:
            continue

        # Weighted toward positive
        rating = random.choices([1, 2, 3, 4, 5], weights=[3, 5, 10, 30, 52])[0]
        item_name = None
        if order.items:
            item_name = order.items[0].item_name

        s.add(Review(
            order_id=order.id,
            user_id=order.buyer_id,
            rating=rating,
            comment=random.choice(comments),
            item_name=item_name,
        ))
        count += 1

    s.commit()
    print(f"  {count} reviews created (weighted positive distribution)")


# ---------------------------------------------------------------------------
# Dataset: Support tickets
# ---------------------------------------------------------------------------
def load_support(s, user_ids=None):
    print("[support] Creating support tickets...")
    if not user_ids:
        user_ids = [FAKE_USER_BASE_ID + i for i in range(50)]

    tickets_spec = [
        dict(subject="Order never arrived", status="open", priority="high"),
        dict(subject="Wrong item received", status="in_progress", priority="normal"),
        dict(subject="Payment charged twice", status="open", priority="urgent"),
        dict(subject="How to use promo code?", status="resolved", priority="low"),
        dict(subject="Delivery driver was rude", status="in_progress", priority="normal"),
        dict(subject="Request for refund #12345", status="closed", priority="normal"),
        dict(subject="App crash when opening cart", status="open", priority="high"),
        dict(subject="Cannot change delivery address", status="resolved", priority="normal"),
    ]

    admin_id = FAKE_USER_BASE_ID + 1

    count = 0
    for i, spec in enumerate(tickets_spec):
        code = f"TK{_rand_code(5)}"
        uid = user_ids[i + 5]

        existing = s.query(SupportTicket).filter_by(user_id=uid, subject=spec["subject"]).first()
        if existing:
            continue

        ticket = SupportTicket(ticket_code=code, user_id=uid, **spec)
        if spec["status"] in ("resolved", "closed"):
            ticket.resolved_at = _now - timedelta(days=random.randint(1, 10))
        if spec["status"] in ("in_progress", "resolved", "closed"):
            ticket.assigned_to = admin_id

        s.add(ticket)
        s.flush()

        # Add messages
        s.add(TicketMessage(ticket_id=ticket.id, sender_id=uid, sender_role="user",
                            message_text=f"Hi, I have a problem: {spec['subject']}"))
        if spec["status"] != "open":
            s.add(TicketMessage(ticket_id=ticket.id, sender_id=admin_id, sender_role="admin",
                                message_text="Thank you for reporting. We're looking into this."))
        if spec["status"] in ("resolved", "closed"):
            s.add(TicketMessage(ticket_id=ticket.id, sender_id=admin_id, sender_role="admin",
                                message_text="This has been resolved. Please let us know if you need anything else."))

        count += 1

    s.commit()
    print(f"  {count} tickets (open, in-progress, resolved, closed) with messages")


# ---------------------------------------------------------------------------
# Dataset: Inventory logs
# ---------------------------------------------------------------------------
def load_inventory(s, user_ids=None):
    print("[inventory] Creating inventory logs and edge cases...")
    if not user_ids:
        user_ids = [FAKE_USER_BASE_ID + i for i in range(50)]

    admin_id = FAKE_USER_BASE_ID + 1

    product_items = s.query(Goods).filter_by(item_type="product").all()
    if not product_items:
        print("  WARN: No product items found")
        return

    count = 0
    for item in product_items:
        # Simulate restock
        s.add(InventoryLog(item_name=item.name, change_type="add",
                           quantity_change=50, admin_id=admin_id,
                           comment="Weekly restock"))
        # Simulate some sales
        for _ in range(random.randint(2, 8)):
            qty = random.randint(1, 3)
            s.add(InventoryLog(item_name=item.name, change_type="deduct",
                               quantity_change=-qty, comment="Order fulfilled"))
        # Simulate a reservation + release
        s.add(InventoryLog(item_name=item.name, change_type="reserve",
                           quantity_change=-2, comment="Reserved for order"))
        s.add(InventoryLog(item_name=item.name, change_type="release",
                           quantity_change=2, comment="Reservation expired"))
        count += 1

    # Edge case: item with 0 stock
    zero_item = s.query(Goods).filter_by(name="Fresh OJ Bottle").first()
    if zero_item:
        zero_item.stock_quantity = 0
        zero_item.reserved_quantity = 0

    # Edge case: item with reserved > available (data inconsistency to test guards)
    croissant = s.query(Goods).filter_by(name="Croissant").first()
    if croissant:
        croissant.stock_quantity = 5
        croissant.reserved_quantity = 3  # Only 2 truly available

    s.commit()
    print(f"  Inventory logs for {count} product items + edge cases (zero stock, high reservation)")


# ---------------------------------------------------------------------------
# Dataset: Stress test (high volume)
# ---------------------------------------------------------------------------
def load_stress(s):
    print("[stress] Loading high-volume stress-test data...")
    user_ids = load_users(s, count=200)
    load_orders(s, user_ids=user_ids, count=500)
    print("  Stress data loaded: 200 users, 500 orders")


# ---------------------------------------------------------------------------
# Dataset: Bot settings
# ---------------------------------------------------------------------------
def load_settings(s):
    print("[settings] Creating bot settings entries...")
    thai_brand = s.query(Brand).filter_by(slug="siam-kitchen").first()

    settings = [
        ("referral_commission_percent", "5", None),
        ("min_order_amount", "100", None),
        ("reservation_timeout_hours", "24", None),
        ("post_delivery_chat_minutes", "30", None),
    ]
    if thai_brand:
        settings += [
            ("welcome_message", "Welcome to Siam Kitchen! Browse our menu below.", thai_brand.id),
            ("order_confirmation_note", "Your food is being prepared with love!", thai_brand.id),
        ]

    for key, val, bid in settings:
        existing = s.query(BotSettings).filter_by(setting_key=key, brand_id=bid).first()
        if not existing:
            s.add(BotSettings(setting_key=key, setting_value=val, brand_id=bid))

    s.commit()
    print(f"  {len(settings)} settings entries")


# ---------------------------------------------------------------------------
# Dataset: Shopping carts (items left in cart)
# ---------------------------------------------------------------------------
def load_carts(s, user_ids=None):
    print("[carts] Creating abandoned shopping carts...")
    if not user_ids:
        user_ids = [FAKE_USER_BASE_ID + i for i in range(50)]

    items = s.query(Goods).filter(Goods.is_active.is_(True)).limit(10).all()
    if not items:
        return

    count = 0
    for i in range(min(10, len(user_ids))):
        uid = user_ids[i + 15]
        n = random.randint(1, 3)
        chosen = random.sample(items, min(n, len(items)))
        for item in chosen:
            existing = s.query(ShoppingCart).filter_by(
                user_id=uid, item_name=item.name, brand_id=item.brand_id).first()
            if not existing:
                s.add(ShoppingCart(
                    user_id=uid, item_name=item.name,
                    quantity=random.randint(1, 3), brand_id=item.brand_id,
                ))
                count += 1

    s.commit()
    print(f"  {count} cart items across 10 users (abandoned carts)")


# ---------------------------------------------------------------------------
# Clean
# ---------------------------------------------------------------------------
def clean_seeded_data(s):
    """Remove all seeded test data (fake users and their related records)."""
    print("[clean] Removing seeded test data...")

    fake_ids = [FAKE_USER_BASE_ID + i for i in range(500)]

    # Order-dependent deletion
    s.query(DeliveryChatMessage).filter(
        DeliveryChatMessage.order_id.in_(
            s.query(Order.id).filter(Order.buyer_id.in_(fake_ids))
        )).delete(synchronize_session=False)
    s.query(OrderItem).filter(
        OrderItem.order_id.in_(
            s.query(Order.id).filter(Order.buyer_id.in_(fake_ids))
        )).delete(synchronize_session=False)
    s.query(Review).filter(Review.user_id.in_(fake_ids)).delete(synchronize_session=False)
    s.query(CouponUsage).filter(CouponUsage.user_id.in_(fake_ids)).delete(synchronize_session=False)
    s.query(Order).filter(Order.buyer_id.in_(fake_ids)).delete(synchronize_session=False)
    s.query(ShoppingCart).filter(ShoppingCart.user_id.in_(fake_ids)).delete(synchronize_session=False)
    s.query(ReferralEarnings).filter(ReferralEarnings.referrer_id.in_(fake_ids)).delete(synchronize_session=False)
    s.query(ReferenceCodeUsage).filter(ReferenceCodeUsage.used_by.in_(fake_ids)).delete(synchronize_session=False)
    s.query(ReferenceCode).filter(ReferenceCode.created_by.in_(fake_ids)).delete(synchronize_session=False)
    s.query(TicketMessage).filter(
        TicketMessage.ticket_id.in_(
            s.query(SupportTicket.id).filter(SupportTicket.user_id.in_(fake_ids))
        )).delete(synchronize_session=False)
    s.query(SupportTicket).filter(SupportTicket.user_id.in_(fake_ids)).delete(synchronize_session=False)
    s.query(BrandStaff).filter(BrandStaff.user_id.in_(fake_ids)).delete(synchronize_session=False)
    s.query(CustomerInfo).filter(CustomerInfo.telegram_id.in_(fake_ids)).delete(synchronize_session=False)
    s.query(Operations).filter(Operations.user_id.in_(fake_ids)).delete(synchronize_session=False)
    s.query(User).filter(User.telegram_id.in_(fake_ids)).delete(synchronize_session=False)

    # Clean brands we created (cascades take care of categories/items/stores)
    for slug in ("siam-kitchen", "kabul-grill", "bean-crumb", "test-kitchen"):
        brand = s.query(Brand).filter_by(slug=slug).first()
        if brand:
            # Manual cascade for items that use category FK
            s.query(InventoryLog).filter(
                InventoryLog.item_name.in_(
                    s.query(Goods.name).filter(Goods.brand_id == brand.id)
                )).delete(synchronize_session=False)
            s.query(BranchInventory).filter(
                BranchInventory.store_id.in_(
                    s.query(Store.id).filter(Store.brand_id == brand.id)
                )).delete(synchronize_session=False)
            s.query(ShoppingCart).filter(ShoppingCart.brand_id == brand.id).delete(synchronize_session=False)
            s.query(Goods).filter(Goods.brand_id == brand.id).delete(synchronize_session=False)
            s.query(Categories).filter(Categories.brand_id == brand.id).delete(synchronize_session=False)
            s.query(Store).filter(Store.brand_id == brand.id).delete(synchronize_session=False)
            s.query(BotSettings).filter(BotSettings.brand_id == brand.id).delete(synchronize_session=False)
            s.query(Brand).filter(Brand.id == brand.id).delete(synchronize_session=False)

    # Clean coupons we created
    for code in ("WELCOME10", "FLAT50", "VIP25", "EXPIRED20", "SOLDOUT", "FREEDELIVERY"):
        coupon = s.query(Coupon).filter_by(code=code).first()
        if coupon:
            s.query(CouponUsage).filter(CouponUsage.coupon_id == coupon.id).delete(synchronize_session=False)
            s.delete(coupon)

    s.commit()
    print("  All seeded test data removed.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
DATASETS = {
    "thai": lambda s, _: load_thai(s),
    "afghan": lambda s, _: load_afghan(s),
    "cafe": lambda s, _: load_cafe(s),
    "multi": lambda s, _: load_multi(s),
    "users": lambda s, _: load_users(s),
    "orders": lambda s, uids: load_orders(s, user_ids=uids),
    "referrals": lambda s, uids: load_referrals(s, user_ids=uids),
    "coupons": lambda s, uids: load_coupons(s, user_ids=uids),
    "reviews": lambda s, uids: load_reviews(s, user_ids=uids),
    "support": lambda s, uids: load_support(s, user_ids=uids),
    "inventory": lambda s, uids: load_inventory(s, user_ids=uids),
    "carts": lambda s, uids: load_carts(s, user_ids=uids),
    "settings": lambda s, _: load_settings(s),
    "stress": lambda s, _: load_stress(s),
}

ALL_ORDER = ["thai", "afghan", "cafe", "multi", "users", "settings",
             "orders", "referrals", "coupons", "reviews", "support",
             "inventory", "carts"]


def main():
    parser = argparse.ArgumentParser(description="Load test data for Telegram Shop")
    parser.add_argument("--dataset", "-d", type=str, default="all",
                        help="Dataset to load (comma-separated or 'all')")
    parser.add_argument("--list", "-l", action="store_true", help="List available datasets")
    parser.add_argument("--clean", action="store_true", help="Remove all seeded data")
    args = parser.parse_args()

    if args.list:
        print("Available datasets:")
        for name in ALL_ORDER:
            print(f"  {name}")
        print(f"  stress  (high-volume: 200 users, 500 orders)")
        print(f"  all     (everything except stress)")
        return

    with Database().session() as s:
        if args.clean:
            clean_seeded_data(s)
            return

        requested = [d.strip() for d in args.dataset.split(",")]
        if "all" in requested:
            requested = ALL_ORDER

        print(f"Loading datasets: {', '.join(requested)}")
        print("=" * 60)

        user_ids = None
        for name in requested:
            if name not in DATASETS:
                print(f"  WARN: Unknown dataset '{name}', skipping")
                continue
            result = DATASETS[name](s, user_ids)
            # Capture user IDs from the users dataset
            if name == "users" and isinstance(result, list):
                user_ids = result
            elif name == "stress":
                pass  # stress handles its own users

        print("=" * 60)
        print("Done! All test data loaded.")


if __name__ == "__main__":
    main()
