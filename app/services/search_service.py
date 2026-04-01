"""
services/search_service.py
--------------------------
All text-search business logic for Person 1.
Controllers call these functions — no MongoDB queries live in routes.

Functions:
  search_by_keyword         → basic $text search with score
  search_exclude_words      → keyword search minus excluded terms
  search_phrase             → exact phrase match
  search_with_filters       → keyword + brand and/or price bounds
  search_specific_field     → regex search on a single field
  search_paginated          → keyword search with skip/limit pagination
  search_above_score        → filter results below a relevance threshold
"""
import re
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorCollection


def _serialize(doc: dict) -> dict:
    """Convert ObjectId to string for JSON serialisation."""
    doc["_id"] = str(doc["_id"])
    return doc


# ── 1. Basic keyword search ────────────────────────────────────────────────────

async def search_by_keyword(
    collection: AsyncIOMotorCollection,
    keyword: str,
    limit: int = 20,
) -> list[dict]:
    """
    $text search on the compound text index (name, brand, description).
    Returns documents sorted by relevance score descending.

    MongoDB query equivalent:
        db.phones.find(
            { $text: { $search: "keyword" } },
            { score: { $meta: "textScore" } }
        ).sort({ score: { $meta: "textScore" } })
    """
    cursor = collection.find(
        {"$text": {"$search": keyword}},
        {"score": {"$meta": "textScore"}},
    ).sort([("score", {"$meta": "textScore"})]).limit(limit)

    return [_serialize(doc) async for doc in cursor]


# ── 2. Exclude specific words ─────────────────────────────────────────────────

async def search_exclude_words(
    collection: AsyncIOMotorCollection,
    keyword: str,
    exclude: str,
    limit: int = 20,
) -> list[dict]:
    """
    Prefix excluded terms with '-' and append to the search string.
    MongoDB $text natively supports negation with the minus prefix.

    Example: keyword="camera", exclude="Samsung Apple"
      → $search: "camera -Samsung -Apple"
    """
    excluded_terms = " ".join(f"-{w}" for w in exclude.split())
    search_string = f"{keyword} {excluded_terms}"

    cursor = collection.find(
        {"$text": {"$search": search_string}},
        {"score": {"$meta": "textScore"}},
    ).sort([("score", {"$meta": "textScore"})]).limit(limit)

    return [_serialize(doc) async for doc in cursor]


# ── 3. Exact phrase search ────────────────────────────────────────────────────

async def search_phrase(
    collection: AsyncIOMotorCollection,
    phrase: str,
    limit: int = 20,
) -> list[dict]:
    """
    Wrap phrase in escaped double-quotes for exact-match $text search.

    MongoDB query equivalent:
        db.phones.find({ $text: { $search: '"AMOLED display"' } })
    """
    search_string = f'"{phrase}"'

    cursor = collection.find(
        {"$text": {"$search": search_string}},
        {"score": {"$meta": "textScore"}},
    ).sort([("score", {"$meta": "textScore"})]).limit(limit)

    return [_serialize(doc) async for doc in cursor]


# ── 4. Combined filter: text + brand + price ───────────────────────────────────

async def search_with_filters(
    collection: AsyncIOMotorCollection,
    keyword: str,
    brand: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    limit: int = 20,
) -> list[dict]:
    """
    Combine $text search with optional equality/range filters.
    All filters are ANDed together inside a single $match.
    """
    match: dict = {"$text": {"$search": keyword}}

    if brand:
        match["brand"] = {"$regex": f"^{re.escape(brand)}$", "$options": "i"}

    price_filter: dict = {}
    if min_price is not None:
        price_filter["$gte"] = min_price
    if max_price is not None:
        price_filter["$lte"] = max_price
    if price_filter:
        match["price"] = price_filter

    cursor = collection.find(
        match,
        {"score": {"$meta": "textScore"}},
    ).sort([("score", {"$meta": "textScore"})]).limit(limit)

    return [_serialize(doc) async for doc in cursor]


# ── 5. Single-field regex search ──────────────────────────────────────────────

async def search_specific_field(
    collection: AsyncIOMotorCollection,
    field: str,
    keyword: str,
    limit: int = 20,
) -> list[dict]:
    """
    Case-insensitive regex search restricted to ONE specific field.
    Useful when the caller wants to search only in descriptions, for example.

    Allowed fields: name, brand, description
    """
    allowed = {"name", "brand", "description"}
    if field not in allowed:
        raise ValueError(f"field must be one of {allowed}")

    cursor = collection.find(
        {field: {"$regex": re.escape(keyword), "$options": "i"}},
    ).limit(limit)

    return [_serialize(doc) async for doc in cursor]


# ── 6. Paginated search ───────────────────────────────────────────────────────

async def search_paginated(
    collection: AsyncIOMotorCollection,
    keyword: str,
    page: int = 1,
    page_size: int = 5,
) -> dict:
    """
    Text search with pagination via skip() + limit().
    Returns results for the requested page plus pagination metadata.
    """
    skip = (page - 1) * page_size

    cursor = collection.find(
        {"$text": {"$search": keyword}},
        {"score": {"$meta": "textScore"}},
    ).sort([("score", {"$meta": "textScore"})]).skip(skip).limit(page_size)

    results = [_serialize(doc) async for doc in cursor]

    total = await collection.count_documents({"$text": {"$search": keyword}})

    return {
        "page": page,
        "page_size": page_size,
        "total_results": total,
        "total_pages": -(-total // page_size),  # ceiling division
        "results": results,
    }


# ── 7. Minimum relevance score filter ────────────────────────────────────────

async def search_above_score(
    collection: AsyncIOMotorCollection,
    keyword: str,
    min_score: float = 1.0,
    limit: int = 20,
) -> list[dict]:
    """
    Uses the aggregation pipeline to filter documents whose textScore
    is below the given threshold — not possible with plain find().

    Pipeline:
      $match (text) → $addFields (score) → $match (score >= threshold)
      → $sort (score desc) → $limit
    """
    pipeline = [
        {"$match": {"$text": {"$search": keyword}}},
        {"$addFields": {"score": {"$meta": "textScore"}}},
        {"$match": {"score": {"$gte": min_score}}},
        {"$sort": {"score": -1}},
        {"$limit": limit},
    ]

    cursor = collection.aggregate(pipeline)
    results = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        results.append(doc)
    return results
