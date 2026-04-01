"""
services/index_service.py
--------------------------
Index management and performance analysis (explain) logic.

Functions:
  list_indexes          → list all indexes on the collection
  drop_index            → drop a named index
  recreate_text_index   → drop + recreate the text search index
  get_index_sizes       → report storage size of each index
  explain_with_index    → run explain() WITH text index present
  explain_without_index → drop text index, explain, recreate it
  compare_performance   → run both and return side-by-side comparison
"""
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import TEXT, ASCENDING
from app.core.database import _ensure_indexes


TEXT_INDEX_NAME = "text_search_idx"


# ── Index management ──────────────────────────────────────────────────────────

async def list_indexes(collection: AsyncIOMotorCollection) -> list[dict]:
    """Return all indexes defined on the phones collection."""
    indexes = []
    async for idx in collection.list_indexes():
        indexes.append(dict(idx))
    return indexes


async def drop_index(collection: AsyncIOMotorCollection, index_name: str) -> dict:
    """Drop a named index. Raises if index does not exist."""
    await collection.drop_index(index_name)
    return {"dropped": index_name}


async def recreate_text_index(collection: AsyncIOMotorCollection) -> dict:
    """Drop the text index (if present) then recreate it with original weights."""
    # Try to drop — ignore error if it doesn't exist
    try:
        await collection.drop_index(TEXT_INDEX_NAME)
    except Exception:
        pass

    await collection.create_index(
        [("name", TEXT), ("brand", TEXT), ("description", TEXT)],
        name=TEXT_INDEX_NAME,
        default_language="english",
        weights={"name": 10, "brand": 5, "description": 1},
    )
    return {"recreated": TEXT_INDEX_NAME}


async def get_index_sizes(collection: AsyncIOMotorCollection) -> list[dict]:
    """
    Use the indexStats aggregation stage to report usage and size info
    for every index on the collection.
    """
    pipeline = [{"$indexStats": {}}]
    stats = []
    async for doc in collection.aggregate(pipeline):
        stats.append({
            "name": doc.get("name"),
            "accesses": doc.get("accesses", {}).get("ops", 0),
            "since": str(doc.get("accesses", {}).get("since", "")),
        })
    return stats


# ── Performance / explain helpers ─────────────────────────────────────────────

def _parse_explain(explain_result: dict) -> dict:
    """
    Extract the key metrics from an explain('executionStats') result.
    Works for both find and aggregate explain shapes.
    """
    stats = explain_result.get("executionStats", {})
    winning_plan = (
        explain_result
        .get("queryPlanner", {})
        .get("winningPlan", {})
    )

    # Walk the winning plan tree to find the stage name
    def find_stage(plan: dict) -> str:
        if not plan:
            return "UNKNOWN"
        stage = plan.get("stage", "")
        if stage in ("TEXT", "IXSCAN", "COLLSCAN"):
            return stage
        return find_stage(plan.get("inputStage", {}))

    index_name = winning_plan.get("indexName") or (
        winning_plan.get("inputStage", {}).get("indexName")
    )

    return {
        "stage": find_stage(winning_plan),
        "index_used": index_name,
        "docs_examined": stats.get("totalDocsExamined", 0),
        "docs_returned": stats.get("nReturned", 0),
        "execution_time_ms": stats.get("executionTimeMillis", 0),
        "index_keys_examined": stats.get("totalKeysExamined", 0),
    }


async def explain_with_index(
    collection: AsyncIOMotorCollection,
    keyword: str,
) -> dict:
    """
    Run explain('executionStats') on a $text search while the text index EXISTS.
    """
    # Ensure text index is present
    await recreate_text_index(collection)

    raw = await collection.find(
        {"$text": {"$search": keyword}},
        {"score": {"$meta": "textScore"}},
    ).explain("executionStats")

    return {"text_index_present": True, **_parse_explain(raw)}


async def explain_without_index(
    collection: AsyncIOMotorCollection,
    keyword: str,
) -> dict:
    """
    Temporarily drop the text index, explain a $text query, then restore the index.
    Without a text index MongoDB CANNOT run $text — so we fall back to a
    case-insensitive regex scan to simulate a full-collection scan scenario.
    """
    # Drop text index
    try:
        await collection.drop_index(TEXT_INDEX_NAME)
    except Exception:
        pass

    # Simulate equivalent full-scan query (regex — no text index)
    raw = await collection.find(
        {"$or": [
            {"name":        {"$regex": keyword, "$options": "i"}},
            {"brand":       {"$regex": keyword, "$options": "i"}},
            {"description": {"$regex": keyword, "$options": "i"}},
        ]}
    ).explain("executionStats")

    result = {"text_index_present": False, **_parse_explain(raw)}

    # Restore text index
    await recreate_text_index(collection)

    return result


async def compare_performance(
    collection: AsyncIOMotorCollection,
    keyword: str,
) -> dict:
    """
    Run both explain variants and return a side-by-side comparison dict.
    The 'speedup' field shows how many times faster the indexed query was.
    """
    with_idx    = await explain_with_index(collection, keyword)
    without_idx = await explain_without_index(collection, keyword)

    t_with    = max(with_idx["execution_time_ms"], 1)
    t_without = max(without_idx["execution_time_ms"], 1)

    return {
        "keyword": keyword,
        "with_text_index":    with_idx,
        "without_text_index": without_idx,
        "speedup_factor":     round(t_without / t_with, 2),
        "docs_scanned_reduction": (
            without_idx["docs_examined"] - with_idx["docs_examined"]
        ),
    }
