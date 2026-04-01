"""
controllers/search_controller.py
---------------------------------
Controller layer for search operations.
Receives validated inputs from routes, calls service functions,
and returns structured response dicts — no DB logic here.
"""
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorCollection
from app.services import search_service


async def keyword_search(collection: AsyncIOMotorCollection, keyword: str, limit: int):
    results = await search_service.search_by_keyword(collection, keyword, limit)
    return {"query": keyword, "count": len(results), "results": results}


async def exclude_search(
    collection: AsyncIOMotorCollection,
    keyword: str,
    exclude: str,
    limit: int,
):
    results = await search_service.search_exclude_words(collection, keyword, exclude, limit)
    return {
        "query": keyword,
        "excluded": exclude,
        "count": len(results),
        "results": results,
    }


async def phrase_search(collection: AsyncIOMotorCollection, phrase: str, limit: int):
    results = await search_service.search_phrase(collection, phrase, limit)
    return {"phrase": phrase, "count": len(results), "results": results}


async def filtered_search(
    collection: AsyncIOMotorCollection,
    keyword: str,
    brand: Optional[str],
    min_price: Optional[float],
    max_price: Optional[float],
    limit: int,
):
    results = await search_service.search_with_filters(
        collection, keyword, brand, min_price, max_price, limit
    )
    return {
        "query": keyword,
        "filters": {"brand": brand, "min_price": min_price, "max_price": max_price},
        "count": len(results),
        "results": results,
    }


async def field_search(
    collection: AsyncIOMotorCollection,
    field: str,
    keyword: str,
    limit: int,
):
    results = await search_service.search_specific_field(collection, field, keyword, limit)
    return {"field": field, "keyword": keyword, "count": len(results), "results": results}


async def paginated_search(
    collection: AsyncIOMotorCollection,
    keyword: str,
    page: int,
    page_size: int,
):
    return await search_service.search_paginated(collection, keyword, page, page_size)


async def score_filtered_search(
    collection: AsyncIOMotorCollection,
    keyword: str,
    min_score: float,
    limit: int,
):
    results = await search_service.search_above_score(collection, keyword, min_score, limit)
    return {
        "query": keyword,
        "min_score": min_score,
        "count": len(results),
        "results": results,
    }
