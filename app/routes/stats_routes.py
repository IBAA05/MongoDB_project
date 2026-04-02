"""
routes/stats_routes.py
-----------------------
FastAPI router for collection statistics endpoints — Person 2.
These are read-only reporting endpoints with no query parameters —
they always describe the entire catalog.

Base prefix: /phones/stats
Swagger tag: "📊 Statistics"
"""

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorCollection

from app.core.database import get_collection
from app.services import stats_service

router = APIRouter(prefix="/phones/stats", tags=["📊 Statistics"])


# ── 1. Total document count ───────────────────────────────────────────────────

@router.get(
    "/count",
    summary="Total number of phones in the catalog [PLUS]",
    description="Returns the total count of documents in the phones collection.",
)
async def total_count(
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    return await stats_service.get_total_count(collection)


# ── 2. Global price stats ─────────────────────────────────────────────────────

@router.get(
    "/price",
    summary="Average, min and max price across the entire catalog [PLUS]",
    description=(
        "Computes global price statistics in a single aggregation pass. "
        "Returns: total_phones, avg_price, min_price, max_price."
    ),
)
async def price_stats(
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    return await stats_service.get_price_stats(collection)


# ── 3. Brand with the most phones ─────────────────────────────────────────────

@router.get(
    "/top-brand-count",
    summary="Brand with the most phones listed [PLUS]",
    description="Returns the brand that has the highest number of phones in the catalog.",
)
async def brand_most_phones(
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    return await stats_service.get_brand_with_most(collection)


# ── 4. Brand with highest avg price ──────────────────────────────────────────

@router.get(
    "/top-brand-price",
    summary="Brand with the highest average price [PLUS]",
    description="Returns the brand whose phones are most expensive on average.",
)
async def brand_highest_avg(
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    return await stats_service.get_brand_highest_avg(collection)


# ── 5. Price distribution ─────────────────────────────────────────────────────

@router.get(
    "/price-distribution",
    summary="Count of phones per price bracket [PLUS]",
    description=(
        "Splits the catalog into price brackets and counts phones in each. "
        "Brackets: under $300 · $300-$599 · $600-$999 · $1000+"
    ),
)
async def price_distribution(
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    results = await stats_service.get_price_distribution(collection)
    return {"distribution": results}


# ── 6. Collection metadata ────────────────────────────────────────────────────

@router.get(
    "/collection",
    summary="Collection metadata and storage statistics [PLUS]",
    description=(
        "Runs the MongoDB `collStats` command — equivalent to `db.phones.stats()` "
        "in the shell. Returns document count, data size, index size, and more."
    ),
)
async def collection_stats(
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    return await stats_service.get_collection_stats(collection)