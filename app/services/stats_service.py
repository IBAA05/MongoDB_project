"""
services/stats_service.py
--------------------------
Collection-level statistics for Person 2.
These queries answer reporting questions about the whole catalog —
no filtering by user input, just global numbers.

Functions:
  get_total_count          → count all documents                        [PLUS]
  get_price_stats          → avg / min / max price across all phones    [PLUS]
  get_brand_with_most      → brand that has the most listed phones      [PLUS]
  get_brand_highest_avg    → brand with the highest average price       [PLUS]
  get_price_distribution   → count of phones per price bracket          [PLUS]
  get_collection_stats     → general collection metadata                [PLUS]
"""

from motor.motor_asyncio import AsyncIOMotorCollection


# ── 1. Total document count ───────────────────────────────────────────────────

async def get_total_count(
    collection: AsyncIOMotorCollection,
) -> dict:
    """
    Returns the total number of phone documents in the collection.
    count_documents({}) with an empty filter counts everything.
    """
    count = await collection.count_documents({})
    return {"total_phones": count}


# ── 2. Global price statistics ───────────────────────────────────────────────

async def get_price_stats(
    collection: AsyncIOMotorCollection,
) -> dict:
    """
    Computes average, minimum, and maximum price across the entire catalog
    in a single aggregation pass — much more efficient than three queries.

    $group with _id: null means "group ALL documents into one bucket".
    This is the standard pattern for computing global statistics.
    """
    pipeline = [
        {
            "$group": {
                "_id": None,                        # one bucket = whole collection
                "avg_price": {"$avg": "$price"},
                "min_price": {"$min": "$price"},
                "max_price": {"$max": "$price"},
                "total": {"$sum": 1}
            }
        },
        {
            "$project": {
                "_id": 0,
                "total_phones": "$total",
                "avg_price": {"$round": ["$avg_price", 2]},
                "min_price": 1,
                "max_price": 1
            }
        }
    ]

    results = await collection.aggregate(pipeline).to_list(length=1)
    # to_list(1) returns a list with one item — return just that item
    return results[0] if results else {}


# ── 3. Brand with the most listed phones ─────────────────────────────────────

async def get_brand_with_most(
    collection: AsyncIOMotorCollection,
) -> dict:
    """
    Finds the brand that has the highest number of phones in the catalog.

    Pattern: $group by brand → $sort by count desc → $limit 1
    This is more efficient than fetching all brands and sorting in Python.
    """
    pipeline = [
        {
            "$group": {
                "_id": "$brand",
                "count": {"$sum": 1}
            }
        },
        {
            "$sort": {"count": -1}     # most phones first
        },
        {
            "$limit": 1                # we only want the winner
        },
        {
            "$project": {
                "_id": 0,
                "brand": "$_id",
                "count": 1
            }
        }
    ]

    results = await collection.aggregate(pipeline).to_list(length=1)
    return results[0] if results else {}


# ── 4. Brand with the highest average price ───────────────────────────────────

async def get_brand_highest_avg(
    collection: AsyncIOMotorCollection,
) -> dict:
    """
    Finds the brand whose phones are most expensive on average.
    Same pattern as get_brand_with_most but sorting by avg_price.
    """
    pipeline = [
        {
            "$group": {
                "_id": "$brand",
                "avg_price": {"$avg": "$price"},
                "count": {"$sum": 1}
            }
        },
        {
            "$sort": {"avg_price": -1}
        },
        {
            "$limit": 1
        },
        {
            "$project": {
                "_id": 0,
                "brand": "$_id",
                "avg_price": {"$round": ["$avg_price", 2]},
                "count": 1
            }
        }
    ]

    results = await collection.aggregate(pipeline).to_list(length=1)
    return results[0] if results else {}


# ── 5. Price distribution (count per price bracket) ──────────────────────────

async def get_price_distribution(
    collection: AsyncIOMotorCollection,
) -> list[dict]:
    """
    Groups phones into price brackets and counts how many fall in each.
    Uses $bucket — same as price_buckets in aggregation_service but focused
    on a simpler count-only report rather than collecting phone names.

    Brackets:
      under $300    → entry-level
      $300 - $599   → mid
      $600 - $999   → upper-mid
      $1000+        → premium

    Returns a list sorted by bracket low boundary ascending.
    """
    pipeline = [
        {
            "$bucket": {
                "groupBy": "$price",
                "boundaries": [0, 300, 600, 1000, 99999],
                "default": "other",
                "output": {
                    "count": {"$sum": 1},
                    "avg_price": {"$avg": "$price"}
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "bracket": {
                    "$switch": {
                        "branches": [
                            {"case": {"$eq": ["$_id", 0]},    "then": "under $300"},
                            {"case": {"$eq": ["$_id", 300]},  "then": "$300 - $599"},
                            {"case": {"$eq": ["$_id", 600]},  "then": "$600 - $999"},
                            {"case": {"$eq": ["$_id", 1000]}, "then": "$1000+"},
                        ],
                        "default": "other"
                    }
                },
                "count": 1,
                "avg_price": {"$round": ["$avg_price", 2]}
            }
        }
    ]

    cursor = collection.aggregate(pipeline)
    return [doc async for doc in cursor]


# ── 6. Collection metadata ────────────────────────────────────────────────────

async def get_collection_stats(
    collection: AsyncIOMotorCollection,
) -> dict:
    """
    Returns general metadata about the phones collection.
    We use the 'collStats' database command — equivalent to
    db.phones.stats() in the MongoDB shell.

    Key fields returned:
      count        → number of documents
      size         → total uncompressed data size in bytes
      avgObjSize   → average document size in bytes
      totalIndexSize → total size used by all indexes
      nindexes     → number of indexes on the collection
    """
    db = collection.database     # get the Database object from the collection
    raw = await db.command("collStats", collection.name)

    # Extract only the fields relevant for the report
    return {
        "collection": collection.name,
        "document_count": raw.get("count", 0),
        "total_size_bytes": raw.get("size", 0),
        "avg_document_size_bytes": raw.get("avgObjSize", 0),
        "total_index_size_bytes": raw.get("totalIndexSize", 0),
        "number_of_indexes": raw.get("nindexes", 0),
        "storage_size_bytes": raw.get("storageSize", 0),
    }