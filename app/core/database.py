"""
core/database.py
----------------
Manages the Motor async MongoDB client lifecycle.
Called once on FastAPI startup and shutdown.
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from pymongo import TEXT, ASCENDING, DESCENDING
from app.core.config import settings

class Database:
    client: AsyncIOMotorClient = None


db_state = Database()


def get_collection() -> AsyncIOMotorCollection:
    """Return the phones collection — injected via FastAPI Depends."""
    return db_state.client[settings.DB_NAME][settings.COLLECTION_NAME]


async def connect_db():
    """Open connection and ensure all required indexes exist."""
    db_state.client = AsyncIOMotorClient(settings.MONGO_URI)
    collection = get_collection()
    await _ensure_indexes(collection)
    print(f"[DB] Connected → {settings.MONGO_URI} / {settings.DB_NAME}")


async def close_db():
    """Gracefully close the Motor client."""
    if db_state.client:
        db_state.client.close()
        print("[DB] Connection closed.")


# ── Index helpers ─────────────────────────────────────────────────────────────

async def _ensure_indexes(collection: AsyncIOMotorCollection):
    """
    Create all indexes used by Person 1 queries.
    Motor's create_index is idempotent — safe to call on every startup.

    Indexes created:
      1. text_search_idx  — compound TEXT index on name, brand, description
      2. brand_price_idx  — compound ascending index on brand + price
      3. unique_name_idx  — unique index on name
      4. price_idx        — single-field index on price (for range queries)
    """
    # 1. TEXT index (the core index of this project)
    await collection.create_index(
        [("name", TEXT), ("brand", TEXT), ("description", TEXT)],
        name="text_search_idx",
        default_language="english",
        weights={"name": 10, "brand": 5, "description": 1},
    )

    # 2. Compound index — supports brand filter + price sort queries
    await collection.create_index(
        [("brand", ASCENDING), ("price", ASCENDING)],
        name="brand_price_idx",
    )

    # 3. Unique index — enforces no duplicate phone names
    await collection.create_index(
        [("name", ASCENDING)],
        name="unique_name_idx",
        unique=True,
    )

    # 4. Single-field index on price — accelerates range filter queries
    await collection.create_index(
        [("price", ASCENDING)],
        name="price_idx",
    )

    print("[DB] Indexes verified / created.")
