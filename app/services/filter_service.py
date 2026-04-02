"""
services/filter_service.py
---------------------------
Advanced filtering queries for Person 2.
These use regular find() queries (not aggregation pipelines) because
we are filtering the collection, not reshaping or grouping it.

Functions:
  filter_by_price_range     → $gte / $lte                              [PLUS]
  filter_by_brands          → $in  (multiple brands at once)           [PLUS]
  exclude_brands            → $nin (exclude specific brands)           [PLUS]
  regex_search_description  → regex substring match on description     [PLUS]
  find_cheapest             → single cheapest phone overall            [PLUS]
  find_most_expensive       → single most expensive phone overall      [PLUS]
  check_field_exists        → $exists (docs that have a given field)   [PLUS]
"""

from typing import Optional
from motor.motor_asyncio import AsyncIOMotorCollection


# ── Shared serializer ─────────────────────────────────────────────────────────

def _serialize(doc: dict) -> dict:
    """Convert ObjectId → string for JSON serialisation."""
    if "_id" in doc and not isinstance(doc["_id"], str):
        doc["_id"] = str(doc["_id"])
    return doc


# ── 1. Filter by exact price range ───────────────────────────────────────────

async def filter_by_price_range(
    collection: AsyncIOMotorCollection,
    min_price: float,
    max_price: float,
    limit: int = 50,
) -> list[dict]:
    """
    Returns all phones whose price falls between min_price and max_price
    (both inclusive).

    MongoDB operators:
      $gte → greater than or equal
      $lte → less than or equal

    Equivalent SQL: WHERE price >= min_price AND price <= max_price
    """
    cursor = collection.find(
        {"price": {"$gte": min_price, "$lte": max_price}},
    ).sort("price", 1).limit(limit)    # cheapest first

    return [_serialize(doc) async for doc in cursor]


# ── 2. Filter by multiple brands ($in) ───────────────────────────────────────

async def filter_by_brands(
    collection: AsyncIOMotorCollection,
    brands: list[str],
    limit: int = 50,
) -> list[dict]:
    """
    Returns phones belonging to ANY of the given brands.

    $in checks if a field value is inside the provided list.
    Equivalent SQL: WHERE brand IN ('Samsung', 'Apple', 'Google')

    The caller passes brands as a comma-separated query param string,
    which the route splits into a list before calling this function.
    """
    cursor = collection.find(
        {"brand": {"$in": brands}}
    ).sort("brand", 1).limit(limit)

    return [_serialize(doc) async for doc in cursor]


# ── 3. Exclude specific brands ($nin) ────────────────────────────────────────

async def exclude_brands(
    collection: AsyncIOMotorCollection,
    brands: list[str],
    limit: int = 50,
) -> list[dict]:
    """
    Returns all phones EXCEPT those from the given brands.

    $nin → "not in" — opposite of $in.
    Equivalent SQL: WHERE brand NOT IN ('Samsung', 'Apple')
    """
    cursor = collection.find(
        {"brand": {"$nin": brands}}
    ).sort("brand", 1).limit(limit)

    return [_serialize(doc) async for doc in cursor]


# ── 4. Regex substring search on description ──────────────────────────────────

async def regex_search_description(
    collection: AsyncIOMotorCollection,
    keyword: str,
    limit: int = 50,
) -> list[dict]:
    """
    Case-insensitive regex search specifically on the description field.

    Unlike the text index search (which uses stemming and tokenisation),
    regex does a raw substring scan — slower but more flexible for
    partial matches, special characters, or patterns.

    $options: "i" → case-insensitive
    """
    cursor = collection.find(
        {"description": {"$regex": keyword, "$options": "i"}}
    ).limit(limit)

    return [_serialize(doc) async for doc in cursor]


# ── 5. Find the cheapest phone overall ───────────────────────────────────────

async def find_cheapest(
    collection: AsyncIOMotorCollection,
) -> Optional[dict]:
    """
    Returns the single cheapest phone in the entire catalog.
    sort(price, 1) = ascending → first result = lowest price.
    """
    doc = await collection.find_one(
        {},                    # no filter — look at all documents
        sort=[("price", 1)]   # ascending price → first = cheapest
    )
    return _serialize(doc) if doc else None


# ── 6. Find the most expensive phone overall ──────────────────────────────────

async def find_most_expensive(
    collection: AsyncIOMotorCollection,
) -> Optional[dict]:
    """
    Returns the single most expensive phone in the entire catalog.
    sort(price, -1) = descending → first result = highest price.
    """
    doc = await collection.find_one(
        {},
        sort=[("price", -1)]   # descending price → first = most expensive
    )
    return _serialize(doc) if doc else None


# ── 7. Check for field existence ($exists) ────────────────────────────────────

async def check_field_exists(
    collection: AsyncIOMotorCollection,
    field: str,
    exists: bool = True,
    limit: int = 50,
) -> list[dict]:
    """
    Finds documents that have (or don't have) a specific field.

    $exists: True  → documents WHERE field IS NOT NULL
    $exists: False → documents WHERE field IS NULL (field missing entirely)

    Useful to find phones that have a rating, or ones missing stock info.

    Allowed fields are restricted to prevent arbitrary key scanning.
    """
    allowed_fields = {"stock", "rating", "category", "description", "price"}
    if field not in allowed_fields:
        raise ValueError(f"field must be one of {allowed_fields}")

    cursor = collection.find(
        {field: {"$exists": exists}}
    ).limit(limit)

    return [_serialize(doc) async for doc in cursor]