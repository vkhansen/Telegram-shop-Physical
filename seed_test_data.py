"""Seed script: creates a test brand, categories, and items for debugging."""
import os
import sys

# Ensure the bot package is importable
sys.path.insert(0, os.path.dirname(__file__))

from bot.database.models import register_models
register_models()

from bot.database.methods.create import create_brand, create_category, create_item
from bot.database import Database
from bot.database.models.main import Goods

# 1. Create a brand
brand_id = create_brand(
    name="Test Kitchen",
    slug="test-kitchen",
    description="A test restaurant for debugging",
)
if brand_id is None:
    # Brand may already exist, fetch its ID
    from bot.database.models.main import Brand
    with Database().session() as s:
        existing = s.query(Brand).filter_by(slug="test-kitchen").first()
        brand_id = existing.id if existing else None

print(f"Brand ID: {brand_id}")

# 2. Create categories
categories = ["Burgers", "Drinks", "Desserts"]
for cat in categories:
    create_category(cat, brand_id=brand_id)
    print(f"Category created: {cat}")

# 3. Create items
items = [
    # Burgers
    {
        "item_name": "Classic Burger",
        "item_description": "Beef patty, lettuce, tomato, cheese",
        "item_price": 120,
        "category_name": "Burgers",
        "brand_id": brand_id,
        "item_type": "prepared",
        "prep_time_minutes": 15,
        "calories": 550,
    },
    {
        "item_name": "Chicken Burger",
        "item_description": "Crispy chicken fillet with mayo and pickles",
        "item_price": 99,
        "category_name": "Burgers",
        "brand_id": brand_id,
        "item_type": "prepared",
        "prep_time_minutes": 12,
        "calories": 480,
    },
    {
        "item_name": "Veggie Burger",
        "item_description": "Plant-based patty with avocado and salsa",
        "item_price": 110,
        "category_name": "Burgers",
        "brand_id": brand_id,
        "item_type": "prepared",
        "prep_time_minutes": 10,
        "calories": 380,
    },
    # Drinks
    {
        "item_name": "Iced Coffee",
        "item_description": "Cold brew with milk and ice",
        "item_price": 55,
        "category_name": "Drinks",
        "brand_id": brand_id,
        "item_type": "prepared",
        "prep_time_minutes": 3,
        "calories": 120,
    },
    {
        "item_name": "Fresh Orange Juice",
        "item_description": "Freshly squeezed orange juice",
        "item_price": 65,
        "category_name": "Drinks",
        "brand_id": brand_id,
        "item_type": "prepared",
        "prep_time_minutes": 5,
        "calories": 90,
    },
    {
        "item_name": "Water Bottle",
        "item_description": "500ml bottled water",
        "item_price": 20,
        "category_name": "Drinks",
        "brand_id": brand_id,
        "item_type": "product",
    },
    # Desserts
    {
        "item_name": "Chocolate Cake",
        "item_description": "Rich chocolate layer cake slice",
        "item_price": 85,
        "category_name": "Desserts",
        "brand_id": brand_id,
        "item_type": "prepared",
        "prep_time_minutes": 5,
        "calories": 420,
    },
    {
        "item_name": "Mango Sticky Rice",
        "item_description": "Thai classic dessert with coconut cream",
        "item_price": 75,
        "category_name": "Desserts",
        "brand_id": brand_id,
        "item_type": "prepared",
        "prep_time_minutes": 8,
        "calories": 350,
    },
]

for item in items:
    create_item(**item)
    print(f"Item created: {item['item_name']} - {item['item_price']} THB")

# 4. Set stock for product items (unlimited for prepared items by default)
with Database().session() as s:
    water = s.query(Goods).filter_by(name="Water Bottle").first()
    if water:
        water.stock_quantity = 100
        water.reserved_quantity = 0

print("\nDone! Test data seeded successfully.")
print(f"Brand: Test Kitchen (ID: {brand_id})")
print(f"Categories: {', '.join(categories)}")
print(f"Items: {len(items)} items created")
