"""
services/seed_service.py
------------------------
Inserts 22 sample smartphone documents into the phones collection.
Called via POST /phones/seed — idempotent (skips duplicates by name).
"""
from motor.motor_asyncio import AsyncIOMotorCollection
from app.core.notifications import manager

SAMPLE_PHONES = [
    {"name": "Samsung Galaxy S24 Ultra", "brand": "Samsung",
     "description": "Flagship with 200MP camera, Snapdragon 8 Gen 3, S-Pen stylus, 5000mAh battery, 12GB RAM.",
     "price": 1299.99, "category": "flagship", "stock": 150, "rating": 4.7},

    {"name": "Samsung Galaxy A55", "brand": "Samsung",
     "description": "Mid-range phone with 50MP camera, AMOLED display, 5000mAh battery, fast charging.",
     "price": 449.99, "category": "mid-range", "stock": 300, "rating": 4.3},

    {"name": "Samsung Galaxy A15", "brand": "Samsung",
     "description": "Budget smartphone with 50MP triple camera, 5000mAh long-lasting battery.",
     "price": 199.99, "category": "budget", "stock": 500, "rating": 4.0},

    {"name": "Apple iPhone 15 Pro Max", "brand": "Apple",
     "description": "Pro titanium design, A17 Pro chip, 48MP main camera with 5x telephoto, USB-C, Action Button.",
     "price": 1199.99, "category": "flagship", "stock": 200, "rating": 4.8},

    {"name": "Apple iPhone 15", "brand": "Apple",
     "description": "Dynamic Island, 48MP camera, A16 Bionic chip, USB-C port, all-day battery life.",
     "price": 799.99, "category": "mid-range", "stock": 350, "rating": 4.6},

    {"name": "Apple iPhone SE 3rd Gen", "brand": "Apple",
     "description": "Compact budget iPhone with A15 Bionic chip, 4.7-inch display, Touch ID, 5G support.",
     "price": 429.99, "category": "budget", "stock": 180, "rating": 4.1},

    {"name": "Xiaomi 14 Ultra", "brand": "Xiaomi",
     "description": "Leica quad-camera system, Snapdragon 8 Gen 3, 5000mAh battery, 90W fast charging.",
     "price": 999.99, "category": "flagship", "stock": 120, "rating": 4.6},

    {"name": "Xiaomi Redmi Note 13 Pro", "brand": "Xiaomi",
     "description": "200MP camera, Dimensity 7200 Ultra, 5100mAh battery, 67W turbo charging, AMOLED.",
     "price": 349.99, "category": "mid-range", "stock": 400, "rating": 4.4},

    {"name": "Xiaomi Redmi 13C", "brand": "Xiaomi",
     "description": "Budget phone with 50MP camera, MediaTek Helio G85, 5000mAh battery, 6.74-inch display.",
     "price": 149.99, "category": "budget", "stock": 600, "rating": 3.9},

    {"name": "Google Pixel 8 Pro", "brand": "Google",
     "description": "Google Tensor G3 chip, 50MP triple camera, 7 years OS updates, temperature sensor, AI features.",
     "price": 999.99, "category": "flagship", "stock": 90, "rating": 4.7},

    {"name": "Google Pixel 8a", "brand": "Google",
     "description": "Affordable Pixel with Tensor G3, 64MP camera, 4492mAh battery, IP67 water resistance.",
     "price": 499.99, "category": "mid-range", "stock": 220, "rating": 4.5},

    {"name": "OnePlus 12", "brand": "OnePlus",
     "description": "Hasselblad camera system, Snapdragon 8 Gen 3, 100W fast charging, 5400mAh battery.",
     "price": 799.99, "category": "flagship", "stock": 110, "rating": 4.5},

    {"name": "OnePlus Nord CE4", "brand": "OnePlus",
     "description": "Snapdragon 7s Gen 2, 50MP Sony camera, 100W superfast charging, 5500mAh battery.",
     "price": 329.99, "category": "mid-range", "stock": 280, "rating": 4.3},

    {"name": "Sony Xperia 1 VI", "brand": "Sony",
     "description": "Professional-grade camera with Zeiss optics, 4K display, Snapdragon 8 Gen 3, long battery life.",
     "price": 1299.99, "category": "flagship", "stock": 70, "rating": 4.4},

    {"name": "Sony Xperia 10 VI", "brand": "Sony",
     "description": "Compact mid-range with 48MP camera, 6.1-inch OLED, 5000mAh battery, IP68 waterproof.",
     "price": 599.99, "category": "mid-range", "stock": 130, "rating": 4.2},

    {"name": "Motorola Edge 50 Pro", "brand": "Motorola",
     "description": "50MP Pantone-validated camera, Snapdragon 7s Gen 2, 125W TurboPower charging, vegan leather.",
     "price": 599.99, "category": "mid-range", "stock": 160, "rating": 4.3},

    {"name": "Motorola Moto G84", "brand": "Motorola",
     "description": "Budget-friendly with 50MP camera, pOLED display, Snapdragon 695, 5000mAh battery.",
     "price": 249.99, "category": "budget", "stock": 350, "rating": 4.1},

    {"name": "Nothing Phone 2a", "brand": "Nothing",
     "description": "Transparent Glyph interface, Dimensity 7200 Pro, 50MP dual camera, 5000mAh fast-charge battery.",
     "price": 399.99, "category": "mid-range", "stock": 200, "rating": 4.4},

    {"name": "Realme GT 6", "brand": "Realme",
     "description": "Snapdragon 8s Gen 3, 50MP Sony camera, 120W fast charging, 5500mAh battery, gaming focused.",
     "price": 549.99, "category": "mid-range", "stock": 170, "rating": 4.3},

    {"name": "Oppo Find X7 Ultra", "brand": "Oppo",
     "description": "Hasselblad dual-periscope camera, Snapdragon 8 Gen 3, 100W wired and 50W wireless charging.",
     "price": 1099.99, "category": "flagship", "stock": 80, "rating": 4.6},

    {"name": "Vivo X100 Pro", "brand": "Vivo",
     "description": "Zeiss co-engineered camera, Dimensity 9300, 100W fast charging, 5400mAh battery.",
     "price": 899.99, "category": "flagship", "stock": 95, "rating": 4.5},

    {"name": "Honor Magic 6 Pro", "brand": "Honor",
     "description": "HONOR AI camera, Snapdragon 8 Gen 3, eye-tracking technology, 5600mAh silicon-carbon battery.",
     "price": 999.99, "category": "flagship", "stock": 85, "rating": 4.5},
]


async def seed_phones(collection: AsyncIOMotorCollection) -> dict:
    """
    Insert sample documents, skipping names that already exist.
    Returns counts of inserted vs skipped documents.
    """
    inserted = 0
    skipped = 0

    for phone in SAMPLE_PHONES:
        existing = await collection.find_one({"name": phone["name"]})
        if existing:
            skipped += 1
            continue
        await collection.insert_one(phone)
    # Notify clients
    if inserted > 0:
        await manager.broadcast({
            "type": "CREATE",
            "title": "Database Seeded",
            "message": f"Successfully seeded {inserted} new phones. ({skipped} skipped)",
        })

    return {
        "inserted": inserted,
        "skipped": skipped,
        "total_in_db": await collection.count_documents({}),
    }
