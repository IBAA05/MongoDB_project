"""
controllers/crud_controller.py
-------------------------------
Controller for full CRUD operations (update, delete, bulk update).
"""
from motor.motor_asyncio import AsyncIOMotorCollection
from app.models.phone import PhoneCreate, PhoneUpdate
from bson.objectid import ObjectId
from fastapi import HTTPException
from app.core.notifications import manager


async def update_phone_partial(collection: AsyncIOMotorCollection, phone_id: str, phone: PhoneUpdate):
    """Update a single document with partial data ($set)"""
    if not ObjectId.is_valid(phone_id):
        raise HTTPException(status_code=400, detail="Invalid phone ID format")

    # exclude_unset=True ensures we only $set fields provide in the request body
    update_data = phone.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    result = await collection.update_one(
        {"_id": ObjectId(phone_id)},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Phone not found")
    
    # Notify clients
    await manager.broadcast({
        "type": "UPDATE",
        "title": "Phone Updated",
        "message": f"Successfully updated fields for phone {phone_id}.",
        "id": phone_id
    })
    
    return {"message": "Phone updated successfully", "updated_fields": list(update_data.keys())}


async def replace_phone(collection: AsyncIOMotorCollection, phone_id: str, phone: PhoneCreate):
    """Replace an entire document ($replaceOne) or update price/description by document ID"""
    if not ObjectId.is_valid(phone_id):
        raise HTTPException(status_code=400, detail="Invalid phone ID format")

    doc = phone.model_dump()
    result = await collection.replace_one(
        {"_id": ObjectId(phone_id)},
        doc
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Phone not found")
    
    doc["_id"] = phone_id

    # Notify clients
    await manager.broadcast({
        "type": "UPDATE",
        "title": "Phone Replaced",
        "message": f"Successfully replaced phone: {doc.get('name', phone_id)}",
        "id": phone_id
    })

    return doc


async def delete_phone(collection: AsyncIOMotorCollection, phone_id: str):
    """Delete a single document by ID"""
    if not ObjectId.is_valid(phone_id):
        raise HTTPException(status_code=400, detail="Invalid phone ID format")

    result = await collection.delete_one({"_id": ObjectId(phone_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Phone not found")

    # Notify clients
    await manager.broadcast({
        "type": "DELETE",
        "title": "Phone Deleted",
        "message": f"Phone {phone_id} was successfully deleted.",
        "id": phone_id
    })

    return {"message": f"Phone {phone_id} successfully deleted"}


async def delete_phones_by_name_or_brand(collection: AsyncIOMotorCollection, name: str = None, brand: str = None):
    """Delete phones by name or brand"""
    query = {}
    if name:
        query["name"] = name
    if brand:
        query["brand"] = brand
    
    if not query:
        raise HTTPException(status_code=400, detail="Must provide name or brand to delete")

    result = await collection.delete_many(query)

    # Notify clients
    await manager.broadcast({
        "type": "DELETE",
        "title": "Bulk Deletion",
        "message": f"Deleted {result.deleted_count} phones matching criteria.",
        "query": query
    })

    return {"message": f"Deleted {result.deleted_count} phones matching criteria"}


async def bulk_update_price_by_brand(collection: AsyncIOMotorCollection, brand: str, percentage_increase: float):
    """Bulk update prices for a specific brand by +X%"""
    if percentage_increase <= 0:
        raise HTTPException(status_code=400, detail="Percentage increase must be > 0. E.g., 5 for 5% increase.")
    multiplier = 1 + (percentage_increase / 100)
    
    result = await collection.update_many(
        {"brand": brand},
        {"$mul": {"price": multiplier}}
    )

    # Notify clients
    await manager.broadcast({
        "type": "UPDATE",
        "title": "Price Update",
        "message": f"Updated price for {result.modified_count} {brand} phones by {percentage_increase}%."
    })

    return {"message": f"Updated price for {result.modified_count} {brand} phones."}


async def add_fields_to_all(collection: AsyncIOMotorCollection):
    """Add new fields to all docs (stock, rating, category)"""
    result = await collection.update_many(
        {},
        {"$set": {
            "stock": 100,
            "rating": 4.5,
            "category": "mid-range"
        }}
    )
    return {"message": f"Added fields to {result.modified_count} documents"}


async def remove_field_from_all(collection: AsyncIOMotorCollection, field_name: str):
    """Remove a field from all documents ($unset)"""
    # Prevent removing essential fields
    if field_name in ["_id", "name", "brand"]:
        raise HTTPException(status_code=400, detail=f"Cannot remove essential field: {field_name}")

    result = await collection.update_many(
        {},
        {"$unset": {field_name: ""}}
    )
    return {"message": f"Removed field '{field_name}' from {result.modified_count} documents"}
