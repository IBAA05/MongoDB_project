"""
routes/filter_routes.py
------------------------
FastAPI router for advanced filtering endpoints — Person 2.
All endpoints use regular find() queries (not pipelines) since we are
filtering, not reshaping or grouping.

Base prefix: /phones/filter
Swagger tag: "🔎 Filtering"
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from motor.motor_asyncio import AsyncIOMotorCollection

from app.core.database import get_collection
from app.services import filter_service

router = APIRouter(prefix="/phones/filter", tags=["🔎 Filtering"])


# ── 1. Price range ────────────────────────────────────────────────────────────

@router.get(
    "/price-range",
    summary="Filter phones by price range ($gte / $lte) [PLUS]",
    description="Returns all phones whose price is between min_price and max_price (inclusive), sorted cheapest first.",
)
async def filter_price_range(
    min_price: float = Query(0, ge=0, description="Minimum price"),
    max_price: float = Query(99999, ge=0, description="Maximum price"),
    limit: int = Query(50, ge=1, le=200),
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    if min_price > max_price:
        raise HTTPException(status_code=400, detail="min_price cannot exceed max_price")

    results = await filter_service.filter_by_price_range(
        collection, min_price, max_price, limit
    )
    return {"min_price": min_price, "max_price": max_price, "count": len(results), "results": results}


# ── 2. Filter by multiple brands ($in) ────────────────────────────────────────

@router.get(
    "/brands",
    summary="Filter by multiple brands at once ($in) [PLUS]",
    description=(
        "Returns phones belonging to any of the specified brands. "
        "Pass brands as a comma-separated string: `?brands=Samsung,Apple,Google`"
    ),
)
async def filter_by_brands(
    brands: str = Query(..., description="Comma-separated list of brands, e.g. Samsung,Apple"),
    limit: int = Query(50, ge=1, le=200),
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    brand_list = [b.strip() for b in brands.split(",") if b.strip()]
    if not brand_list:
        raise HTTPException(status_code=400, detail="Provide at least one brand name")

    results = await filter_service.filter_by_brands(collection, brand_list, limit)
    return {"brands": brand_list, "count": len(results), "results": results}


# ── 3. Exclude brands ($nin) ──────────────────────────────────────────────────

@router.get(
    "/exclude-brands",
    summary="Exclude specific brands from results ($nin) [PLUS]",
    description=(
        "Returns all phones EXCEPT those from the specified brands. "
        "Pass brands as a comma-separated string: `?brands=Samsung,Xiaomi`"
    ),
)
async def exclude_brands(
    brands: str = Query(..., description="Comma-separated brands to exclude"),
    limit: int = Query(50, ge=1, le=200),
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    brand_list = [b.strip() for b in brands.split(",") if b.strip()]
    if not brand_list:
        raise HTTPException(status_code=400, detail="Provide at least one brand name to exclude")

    results = await filter_service.exclude_brands(collection, brand_list, limit)
    return {"excluded_brands": brand_list, "count": len(results), "results": results}


# ── 4. Regex search on description ────────────────────────────────────────────

@router.get(
    "/description",
    summary="Regex substring search on description field [PLUS]",
    description=(
        "Case-insensitive regex search on the description field only. "
        "Unlike the text index, this scans raw substrings — useful for partial matches."
    ),
)
async def regex_description(
    q: str = Query(..., min_length=1, description="Substring or regex pattern to search in description"),
    limit: int = Query(50, ge=1, le=200),
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    results = await filter_service.regex_search_description(collection, q, limit)
    return {"query": q, "count": len(results), "results": results}


# ── 5. Cheapest phone ─────────────────────────────────────────────────────────

@router.get(
    "/cheapest",
    summary="Find the cheapest phone overall [PLUS]",
    description="Returns the single phone with the lowest price in the catalog.",
)
async def get_cheapest(
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    result = await filter_service.find_cheapest(collection)
    if not result:
        raise HTTPException(status_code=404, detail="No phones found in catalog")
    return result


# ── 6. Most expensive phone ───────────────────────────────────────────────────

@router.get(
    "/most-expensive",
    summary="Find the most expensive phone overall [PLUS]",
    description="Returns the single phone with the highest price in the catalog.",
)
async def get_most_expensive(
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    result = await filter_service.find_most_expensive(collection)
    if not result:
        raise HTTPException(status_code=404, detail="No phones found in catalog")
    return result


# ── 7. Field existence check ──────────────────────────────────────────────────

@router.get(
    "/field-exists",
    summary="Filter phones by field existence ($exists) [PLUS]",
    description=(
        "Returns phones that have (or don't have) a specific field. "
        "Allowed fields: stock, rating, category, description, price. "
        "`exists=true` → field is present · `exists=false` → field is missing."
    ),
)
async def field_exists(
    field: str = Query(..., description="Field name to check: stock | rating | category | description | price"),
    exists: bool = Query(True, description="true = field present, false = field missing"),
    limit: int = Query(50, ge=1, le=200),
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    try:
        results = await filter_service.check_field_exists(collection, field, exists, limit)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "field": field,
        "exists": exists,
        "count": len(results),
        "results": results,
    }