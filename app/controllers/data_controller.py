"""
controllers/data_controller.py
-------------------------------
Controller for data seeding and basic phone insertion (Person 1 scope).
Full CRUD (update/delete/bulk) belongs to Person 3.
"""
from motor.motor_asyncio import AsyncIOMotorCollection
from app.services.seed_service import seed_phones
from app.models.phone import PhoneCreate
from bson import ObjectId


async def seed(collection: AsyncIOMotorCollection):
    return await seed_phones(collection)


async def add_phone(collection: AsyncIOMotorCollection, phone: PhoneCreate):
    doc = phone.model_dump()
    result = await collection.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return doc


async def get_all_phones(collection: AsyncIOMotorCollection, limit: int = 50):
    cursor = collection.find({}).limit(limit)
    phones = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        phones.append(doc)
    return {"count": len(phones), "phones": phones}
