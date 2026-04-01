"""
routes/search_routes.py
------------------------
All text-search API endpoints (Person 1 scope).
Each route delegates immediately to the search controller.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorCollection
from app.core.database import get_collection
from app.controllers import search_controller

router = APIRouter(prefix="/phones/search", tags=["🔍 Text Search"])


@router.get(
    "/keyword",
    summary="Search by keyword",
    description=(
        "Uses the MongoDB `$text` index to search across **name**, **brand**, and **description**. "
        "Results are ranked by relevance score (`textScore`) descending."
    ),
)
async def search_keyword(
    q: str = Query(..., description="Search keyword, e.g. `camera`"),
    limit: int = Query(20, ge=1, le=100, description="Max results to return"),
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    return await search_controller.keyword_search(collection, q, limit)


@router.get(
    "/exclude",
    summary="Search with word exclusion",
    description=(
        "Text search for `q` while **excluding** terms listed in `exclude`. "
        "Exclusion uses MongoDB's native `-term` negation syntax. "
        "Example: `q=camera&exclude=Samsung Apple`"
    ),
)
async def search_exclude(
    q: str = Query(..., description="Main search keyword"),
    exclude: str = Query(..., description="Space-separated words to exclude"),
    limit: int = Query(20, ge=1, le=100),
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    return await search_controller.exclude_search(collection, q, exclude, limit)


@router.get(
    "/phrase",
    summary="Exact phrase search",
    description=(
        "Wraps the phrase in escaped quotes for MongoDB exact-phrase matching. "
        'Example: `phrase=fast charging`  →  `$search: "\\"fast charging\\""`'
    ),
)
async def search_phrase(
    phrase: str = Query(..., description="Exact phrase to search, e.g. `fast charging`"),
    limit: int = Query(20, ge=1, le=100),
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    return await search_controller.phrase_search(collection, phrase, limit)


@router.get(
    "/filter",
    summary="Search with brand and price filters",
    description=(
        "Combines `$text` keyword search with optional **brand** equality filter "
        "and **price range** (`min_price` / `max_price`). All filters are ANDed."
    ),
)
async def search_filtered(
    q: str = Query(..., description="Search keyword"),
    brand: Optional[str] = Query(None, description="Filter by brand name (case-insensitive)"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price in USD"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price in USD"),
    limit: int = Query(20, ge=1, le=100),
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    return await search_controller.filtered_search(
        collection, q, brand, min_price, max_price, limit
    )


@router.get(
    "/field",
    summary="Search within a specific field",
    description=(
        "Case-insensitive regex search restricted to **one field**: "
        "`name`, `brand`, or `description`. "
        "Useful when you want to find a keyword only in descriptions."
    ),
)
async def search_field(
    field: str = Query(..., description="Field to search in: name | brand | description"),
    q: str = Query(..., description="Keyword to find"),
    limit: int = Query(20, ge=1, le=100),
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    return await search_controller.field_search(collection, field, q, limit)


@router.get(
    "/paginated",
    summary="Paginated text search",
    description=(
        "Runs a keyword `$text` search with **pagination** via `skip()` + `limit()`. "
        "Returns current page results plus total pages and total result count."
    ),
)
async def search_paginated(
    q: str = Query(..., description="Search keyword"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(5, ge=1, le=50, description="Results per page"),
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    return await search_controller.paginated_search(collection, q, page, page_size)


@router.get(
    "/score",
    summary="Filter by minimum relevance score",
    description=(
        "Returns only documents whose `textScore` exceeds `min_score`. "
        "Uses an aggregation pipeline: `$match` → `$addFields` (score) → `$match` (threshold) → `$sort`."
    ),
)
async def search_score(
    q: str = Query(..., description="Search keyword"),
    min_score: float = Query(1.0, ge=0, description="Minimum textScore threshold"),
    limit: int = Query(20, ge=1, le=100),
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    return await search_controller.score_filtered_search(collection, q, min_score, limit)
