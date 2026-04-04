from motor.motor_asyncio import AsyncIOMotorCollection

async def search_with_score(collection: AsyncIOMotorCollection, keyword: str):
    pipeline = [
        {"$match": {"$text": {"$search": keyword}}},
        {"$project": {
            "name": 1,
            "brand": 1,
            "price": 1,
            "_id": 0,
            "score": {"$meta": "textScore"}
        }},
        {"$sort": {"score": -1}}
    ]
    return await collection.aggregate(pipeline).to_list(length=100)

async def search_with_price_filter(collection: AsyncIOMotorCollection, keyword: str, min_price: float, max_price: float):
    pipeline = [
        {"$match": {
            "$text": {"$search": keyword},
            "price": {"$gte": min_price, "$lte": max_price}
        }},
        {"$project": {
            "name": 1,
            "brand": 1,
            "price": 1,
            "_id": 0,
            "score": {"$meta": "textScore"}
        }},
        {"$sort": {"score": -1}}
    ]
    return await collection.aggregate(pipeline).to_list(length=100)

async def group_by_brand(collection: AsyncIOMotorCollection):
    pipeline = [
        {"$group": {
            "_id": "$brand",
            "total_phones": {"$sum": 1},
            "avg_price": {"$avg": "$price"}
        }},
        {"$project": {
            "brand": "$_id",
            "total_phones": 1,
            "avg_price": {"$round": ["$avg_price", 2]}
        }},
        {"$sort": {"total_phones": -1}}
    ]
    return await collection.aggregate(pipeline).to_list(length=100)

async def min_max_per_brand(collection: AsyncIOMotorCollection):
    pipeline = [
        {"$group": {
            "_id": "$brand",
            "min_price": {"$min": "$price"},
            "max_price": {"$max": "$price"},
            "total_phones": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]
    return await collection.aggregate(pipeline).to_list(length=100)

async def top_n_results(collection: AsyncIOMotorCollection, keyword: str, n: int):
    pipeline = [
        {"$match": {"$text": {"$search": keyword}}},
        {"$project": {
            "name": 1, "brand": 1, "price": 1, "_id": 0,
            "score": {"$meta": "textScore"}
        }},
        {"$sort": {"score": -1}},
        {"$limit": n}
    ]
    return await collection.aggregate(pipeline).to_list(length=100)

async def multi_stage_pipeline(collection: AsyncIOMotorCollection, keyword: str, min_price: float, max_price: float, sort_order: int, limit: int):
    pipeline = [
        {"$match": {"$text": {"$search": keyword}, "price": {"$gte": min_price, "$lte": max_price}}},
        {"$project": {"name": 1, "brand": 1, "price": 1, "_id": 0, "score": {"$meta": "textScore"}}},
        {"$sort": {"price": sort_order}},
        {"$limit": limit}
    ]
    return await collection.aggregate(pipeline).to_list(length=100)

async def price_buckets(collection: AsyncIOMotorCollection):
    pipeline = [
        {"$bucket": {
            "groupBy": "$price",
            "boundaries": [0, 400, 800],
            "default": 99999,
            "output": {
                "count": {"$sum": 1},
                "titles": {"$push": "$name"}
            }
        }}
    ]
    return await collection.aggregate(pipeline).to_list(length=100)

async def brands_with_min_count(collection: AsyncIOMotorCollection, min_count: int):
    pipeline = [
        {"$group": {"_id": "$brand", "count": {"$sum": 1}}},
        {"$match": {"count": {"$gte": min_count}}},
        {"$sort": {"count": -1}}
    ]
    return await collection.aggregate(pipeline).to_list(length=100)

async def brand_ranking_by_avg_price(collection: AsyncIOMotorCollection):
    pipeline = [
        {"$group": {"_id": "$brand", "avg_price": {"$avg": "$price"}, "total_phones": {"$sum": 1}}},
        {"$sort": {"avg_price": -1}}
    ]
    return await collection.aggregate(pipeline).to_list(length=100)