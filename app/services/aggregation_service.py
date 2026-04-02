from app.core.database import get_collection

async def get_collection_ref():
    return await get_collection()

async def search_with_score(keyword: str):
    """
    Text search → project name/brand/price → sort by relevance score.
    This is the core demanded aggregation.
    """
    col = await get_collection_ref()

    pipeline = [
        # Stage 1: filter to only docs matching the keyword
        {
            "$match": {
                "$text": {"$search": keyword}
            }
        },
        # Stage 2: add the relevance score as a field, keep only useful fields
        {
            "$project": {
                "name": 1,
                "brand": 1,
                "price": 1,
                "_id": 0,
                # MongoDB scores each document based on how many times the keyword appears, in which fields 
                "score": {"$meta": "textScore"}   # this is the relevance number
            }
        },
        # Stage 3: sort — highest score first
        {
            "$sort": {"score": -1}
        }
    ]

    results = await col.aggregate(pipeline).to_list(length=100)
    return results


async def search_with_price_filter(keyword: str, min_price: float, max_price: float):
    """
    Text search + price range filter combined.
    """
    col = await get_collection_ref()

    pipeline = [
        # Stage 1: text match AND price range in one $match
        {
            "$match": {
                "$text": {"$search": keyword},
                "price": {"$gte": min_price, "$lte": max_price}
            }
        },
        {
            "$project": {
                "name": 1,
                "brand": 1,
                "price": 1,
                "_id": 0,
                "score": {"$meta": "textScore"}
            }
        },
        {
            "$sort": {"score": -1}
        }
    ]

    results = await col.aggregate(pipeline).to_list(length=100)
    return results


async def group_by_brand():
    """
    Group all phones by brand.
    Returns: brand name, count of phones, average price.
    """
    col = await get_collection_ref()

    pipeline = [
        {
            "$group": {
                "_id": "$brand",          # group key — one bucket per brand
                "count": {"$sum": 1},     # count documents in each group
                "avg_price": {"$avg": "$price"}
            }
        },
        {
            "$project": {
                "brand": "$_id",          # rename _id to brand for clarity
                "count": 1,
                "avg_price": {"$round": ["$avg_price", 2]},
                "_id": 0
            }
        },
        {
            "$sort": {"count": -1}        # brands with most phones first
        }
    ]

    results = await col.aggregate(pipeline).to_list(length=100)
    return results