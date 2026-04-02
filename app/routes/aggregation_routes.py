"""
routes/aggregation_routes.py
-----------------------------
FastAPI router for all aggregation pipeline endpoints — Person 2.
Follows the exact same thin-route pattern as search_routes.py:
  - Route receives query params
  - Calls the service function
  - Returns the result

All endpoints are grouped under the "📈 Aggregations" Swagger tag.
Base prefix: /phones/aggregations
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from motor.motor_asyncio import AsyncIOMotorCollection

from app.core.database import get_collection
from app.services import aggregation_service

router = APIRouter(prefix="/phones/aggregations", tags=["📈 Aggregations"])


# ── 1. Text search + project + sort by textScore ──────────────────────────────

@router.get(
    "/search",
    summary="Text search with relevance score [DEMANDED]",
    description=(
        "Runs a $text search and returns only **name**, **brand**, **price**, "
        "and the MongoDB **textScore** relevance number — sorted best-match first. "
        "Uses an aggregation pipeline instead of find() so the projection "
        "and scoring are explicit and reportable."
    ),
)
async def agg_search_with_score(
    q: str = Query(..., min_length=1, description="Search keyword"),
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    results = await aggregation_service.search_with_score(collection, q)
    return {"keyword": q, "count": len(results), "results": results}


# ── 2. Text search + price range ──────────────────────────────────────────────

@router.get(
    "/search-price",
    summary="Text search filtered by price range [DEMANDED]",
    description=(
        "Combines a $text search with a price range ($gte / $lte) "
        "in a single $match stage. Results sorted by relevance score."
    ),
)
async def agg_search_with_price_filter(
    q: str = Query(..., min_length=1, description="Search keyword"),
    min_price: float = Query(0, ge=0, description="Minimum price (inclusive)"),
    max_price: float = Query(99999, ge=0, description="Maximum price (inclusive)"),
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    if min_price > max_price:
        raise HTTPException(
            status_code=400,
            detail="min_price cannot be greater than max_price"
        )
    results = await aggregation_service.search_with_price_filter(
        collection, q, min_price, max_price
    )
    return {
        "keyword": q,
        "min_price": min_price,
        "max_price": max_price,
        "count": len(results),
        "results": results,
    }


# ── 3. Group by brand ─────────────────────────────────────────────────────────

@router.get(
    "/group-by-brand",
    summary="Count and average price grouped by brand [DEMANDED]",
    description=(
        "Groups all phones by brand and computes the phone count "
        "and average price for each brand. Sorted by count descending."
    ),
)
async def agg_group_by_brand(
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    results = await aggregation_service.group_by_brand(collection)
    return {"count": len(results), "results": results}


# ── 4. Min / max price per brand ──────────────────────────────────────────────

@router.get(
    "/min-max-per-brand",
    summary="Minimum and maximum price per brand [PLUS]",
    description=(
        "For each brand, returns the cheapest and most expensive phone. "
        "Uses $min and $max accumulators inside a $group stage."
    ),
)
async def agg_min_max_per_brand(
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    results = await aggregation_service.min_max_per_brand(collection)
    return {"count": len(results), "results": results}


# ── 5. Top N most relevant results ────────────────────────────────────────────

@router.get(
    "/top",
    summary="Top N most relevant results for a keyword [PLUS]",
    description=(
        "Returns the top N documents with the highest textScore "
        "for a given keyword. N defaults to 3."
    ),
)
async def agg_top_n(
    q: str = Query(..., min_length=1, description="Search keyword"),
    n: int = Query(3, ge=1, le=20, description="Number of top results to return"),
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    results = await aggregation_service.top_n_results(collection, q, n)
    return {"keyword": q, "top_n": n, "results": results}


# ── 6. Multi-stage pipeline ───────────────────────────────────────────────────

@router.get(
    "/pipeline",
    summary="Multi-stage: search → filter → sort by price → limit [PLUS]",
    description=(
        "Demonstrates a full multi-stage aggregation pipeline: "
        "text search, then price range filter, then sort by price, then limit. "
        "`sort_order`: 1 = price ascending, -1 = price descending."
    ),
)
async def agg_multi_stage(
    q: str = Query(..., min_length=1, description="Search keyword"),
    min_price: float = Query(0, ge=0, description="Minimum price filter"),
    max_price: float = Query(99999, ge=0, description="Maximum price filter"),
    sort_order: int = Query(1, description="1 = price asc, -1 = price desc"),
    limit: int = Query(5, ge=1, le=50, description="Max results to return"),
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    if sort_order not in (1, -1):
        raise HTTPException(
            status_code=400,
            detail="sort_order must be 1 (asc) or -1 (desc)"
        )
    results = await aggregation_service.multi_stage_pipeline(
        collection, q, min_price, max_price, sort_order, limit
    )
    return {
        "keyword": q,
        "min_price": min_price,
        "max_price": max_price,
        "sort_order": "asc" if sort_order == 1 else "desc",
        "limit": limit,
        "count": len(results),
        "results": results,
    }


# ── 7. Price buckets ──────────────────────────────────────────────────────────

@router.get(
    "/price-buckets",
    summary="Price bucketing: budget / mid-range / flagship [PLUS]",
    description=(
        "Uses MongoDB's $bucket stage to split the catalog into price tiers. "
        "Budget: under $400 · Mid-range: $400-$799 · Flagship: $800+"
    ),
)
async def agg_price_buckets(
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    results = await aggregation_service.price_buckets(collection)
    return {"tiers": results}


# ── 8. Brands with more than N phones ─────────────────────────────────────────

@router.get(
    "/brands-min-count",
    summary="Brands with more than N smartphones listed [PLUS]",
    description=(
        "Returns only brands that have at least `min_count` phones in the catalog. "
        "Pattern: $group then $match on the computed count field."
    ),
)
async def agg_brands_with_min_count(
    min_count: int = Query(2, ge=1, description="Minimum number of phones"),
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    results = await aggregation_service.brands_with_min_count(collection, min_count)
    return {
        "min_count": min_count,
        "brands_found": len(results),
        "results": results,
    }


# ── 9. Brand ranking by average price ────────────────────────────────────────

@router.get(
    "/brand-ranking",
    summary="Brand ranking by average price descending [PLUS]",
    description=(
        "Ranks all brands from most expensive to cheapest "
        "based on the average price of their phones in the catalog."
    ),
)
async def agg_brand_ranking(
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    results = await aggregation_service.brand_ranking_by_avg_price(collection)
    return {"count": len(results), "results": results}