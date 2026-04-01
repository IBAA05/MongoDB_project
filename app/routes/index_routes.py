"""
routes/index_routes.py
-----------------------
Index management and performance analysis endpoints (Person 1 scope).
"""
from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorCollection
from app.core.database import get_collection
from app.controllers import index_controller

router = APIRouter(prefix="/phones/indexes", tags=["📊 Indexes & Performance"])


@router.get(
    "/",
    summary="List all indexes",
    description="Returns all indexes defined on the `phones` collection with their key specs.",
)
async def list_indexes(collection: AsyncIOMotorCollection = Depends(get_collection)):
    return await index_controller.list_all_indexes(collection)


@router.delete(
    "/{index_name}",
    summary="Drop an index by name",
    description="Drops the named index. Use `list indexes` first to see available names.",
)
async def drop_index(
    index_name: str,
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    return await index_controller.drop_named_index(collection, index_name)


@router.post(
    "/recreate-text",
    summary="Recreate the text search index",
    description=(
        "Drops `text_search_idx` (if present) and recreates it with the original "
        "field weights: `name×10`, `brand×5`, `description×1`."
    ),
)
async def recreate_text(collection: AsyncIOMotorCollection = Depends(get_collection)):
    return await index_controller.recreate_text_index(collection)


@router.get(
    "/stats",
    summary="Index usage statistics",
    description="Returns access counts and last-accessed timestamps for every index via `$indexStats`.",
)
async def index_stats(collection: AsyncIOMotorCollection = Depends(get_collection)):
    return await index_controller.get_index_stats(collection)


@router.get(
    "/performance/with-index",
    summary="explain() WITH text index",
    description=(
        "Runs `explain('executionStats')` on a `$text` query **while the text index is active**. "
        "Shows stage, docs examined, keys examined, and execution time in ms."
    ),
)
async def perf_with(
    q: str = Query(..., description="Keyword to analyse"),
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    return await index_controller.performance_with_index(collection, q)


@router.get(
    "/performance/without-index",
    summary="explain() WITHOUT text index",
    description=(
        "Temporarily **drops** the text index, runs an equivalent regex COLLSCAN, "
        "captures explain stats, then **restores** the index. "
        "Use this to demonstrate the performance impact of removing the index."
    ),
)
async def perf_without(
    q: str = Query(..., description="Keyword to analyse"),
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    return await index_controller.performance_without_index(collection, q)


@router.get(
    "/performance/compare",
    summary="Side-by-side performance comparison",
    description=(
        "Runs both explain variants and returns a **side-by-side comparison** including "
        "`speedup_factor` (how many times faster the indexed query was) and "
        "`docs_scanned_reduction` (fewer documents examined)."
    ),
)
async def perf_compare(
    q: str = Query(..., description="Keyword to compare performance for"),
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    return await index_controller.performance_comparison(collection, q)
