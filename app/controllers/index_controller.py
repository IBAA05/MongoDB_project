"""
controllers/index_controller.py
--------------------------------
Controller layer for index management and performance analysis.
"""
from motor.motor_asyncio import AsyncIOMotorCollection
from app.services import index_service


async def list_all_indexes(collection: AsyncIOMotorCollection):
    indexes = await index_service.list_indexes(collection)
    return {"count": len(indexes), "indexes": indexes}


async def drop_named_index(collection: AsyncIOMotorCollection, index_name: str):
    return await index_service.drop_index(collection, index_name)


async def recreate_text_index(collection: AsyncIOMotorCollection):
    return await index_service.recreate_text_index(collection)


async def get_index_stats(collection: AsyncIOMotorCollection):
    return await index_service.get_index_sizes(collection)


async def performance_with_index(collection: AsyncIOMotorCollection, keyword: str):
    return await index_service.explain_with_index(collection, keyword)


async def performance_without_index(collection: AsyncIOMotorCollection, keyword: str):
    return await index_service.explain_without_index(collection, keyword)


async def performance_comparison(collection: AsyncIOMotorCollection, keyword: str):
    return await index_service.compare_performance(collection, keyword)
