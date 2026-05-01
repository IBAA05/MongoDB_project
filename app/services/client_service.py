"""
services/client_service.py
--------------------------
Business logic for Client CRUD and Review management.

Design decisions:
  - Clients are stored in a separate `clients` collection.
  - Reviews are embedded inside each phone document (array field `reviews`).
  - Each review stores `client_id` (ObjectId reference) + `client_name`
    (snapshot) so the phone document is self-descriptive without a join,
    while still being linkable back to the client.
  - No full client object is duplicated — only id + name snapshot.

Functions:
  create_client           → insert a new client document
  get_all_clients         → list all clients
  get_client_by_id        → fetch a single client
  update_client           → partial update ($set) on a client
  delete_client           → remove a client document
  add_review_to_phone     → embed a review in a phone document
  get_reviews_for_phone   → return all reviews for a phone, enriched with client info
  get_reviews_by_client   → return all reviews written by a given client (cross-collection)
"""
from bson import ObjectId
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.client import ClientCreate, ReviewCreate

CLIENTS_COLLECTION = "clients"


def _str_id(doc: dict) -> dict:
    """Convert ObjectId _id to string in-place."""
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


# ── Client CRUD ───────────────────────────────────────────────────────────────

async def create_client(db: AsyncIOMotorDatabase, data: ClientCreate) -> dict:
    col = db[CLIENTS_COLLECTION]
    doc = data.model_dump()
    result = await col.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return doc


async def get_all_clients(db: AsyncIOMotorDatabase, limit: int = 100) -> list[dict]:
    col = db[CLIENTS_COLLECTION]
    cursor = col.find({}).limit(limit)
    return [_str_id(doc) async for doc in cursor]


async def get_client_by_id(db: AsyncIOMotorDatabase, client_id: str) -> dict:
    if not ObjectId.is_valid(client_id):
        raise HTTPException(status_code=400, detail="Invalid client ID format")
    col = db[CLIENTS_COLLECTION]
    doc = await col.find_one({"_id": ObjectId(client_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Client not found")
    return _str_id(doc)


async def update_client(
    db: AsyncIOMotorDatabase, client_id: str, data: dict
) -> dict:
    if not ObjectId.is_valid(client_id):
        raise HTTPException(status_code=400, detail="Invalid client ID format")
    if not data:
        raise HTTPException(status_code=400, detail="No fields provided for update")
    col = db[CLIENTS_COLLECTION]
    result = await col.update_one(
        {"_id": ObjectId(client_id)}, {"$set": data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Client not found")
    return {"message": "Client updated successfully", "updated_fields": list(data.keys())}


async def delete_client(db: AsyncIOMotorDatabase, client_id: str) -> dict:
    if not ObjectId.is_valid(client_id):
        raise HTTPException(status_code=400, detail="Invalid client ID format")
    col = db[CLIENTS_COLLECTION]
    result = await col.delete_one({"_id": ObjectId(client_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Client not found")
    return {"message": f"Client {client_id} deleted successfully"}


# ── Review logic ──────────────────────────────────────────────────────────────

async def add_review_to_phone(
    db: AsyncIOMotorDatabase,
    phone_id: str,
    client_id: str,
    review: ReviewCreate,
) -> dict:
    """
    Embed a review inside the phone document.

    Storage shape (one element of `reviews` array):
    {
        "client_id":   "64f...",   ← ObjectId string — links to clients collection
        "client_name": "Alice",    ← snapshot to avoid join on every read
        "rating":      4.5,
        "comment":     "Great phone!"
    }
    """
    if not ObjectId.is_valid(phone_id):
        raise HTTPException(status_code=400, detail="Invalid phone ID format")
    if not ObjectId.is_valid(client_id):
        raise HTTPException(status_code=400, detail="Invalid client ID format")

    phones_col  = db["phones"]
    clients_col = db[CLIENTS_COLLECTION]

    # Validate both documents exist
    phone = await phones_col.find_one({"_id": ObjectId(phone_id)})
    if not phone:
        raise HTTPException(status_code=404, detail="Phone not found")

    client = await clients_col.find_one({"_id": ObjectId(client_id)})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Prevent duplicate review from the same client
    existing_reviews = phone.get("reviews", [])
    for r in existing_reviews:
        if r.get("client_id") == client_id:
            raise HTTPException(
                status_code=409,
                detail="This client has already reviewed this phone. Use PATCH to update.",
            )

    review_doc = {
        "client_id":   client_id,
        "client_name": client["name"],   # snapshot — no full duplication
        "rating":      review.rating,
        "comment":     review.comment,
    }

    await phones_col.update_one(
        {"_id": ObjectId(phone_id)},
        {"$push": {"reviews": review_doc}},
    )

    return {
        "message": "Review added successfully",
        "phone_id": phone_id,
        "review": review_doc,
    }


async def update_review_on_phone(
    db: AsyncIOMotorDatabase,
    phone_id: str,
    client_id: str,
    review: ReviewCreate,
) -> dict:
    """Update an existing review (matched by client_id inside the reviews array)."""
    if not ObjectId.is_valid(phone_id):
        raise HTTPException(status_code=400, detail="Invalid phone ID format")
    if not ObjectId.is_valid(client_id):
        raise HTTPException(status_code=400, detail="Invalid client ID format")

    phones_col = db["phones"]

    phone = await phones_col.find_one({"_id": ObjectId(phone_id)})
    if not phone:
        raise HTTPException(status_code=404, detail="Phone not found")

    # Check review exists
    found = any(r.get("client_id") == client_id for r in phone.get("reviews", []))
    if not found:
        raise HTTPException(
            status_code=404,
            detail="No review from this client found on this phone.",
        )

    result = await phones_col.update_one(
        {"_id": ObjectId(phone_id), "reviews.client_id": client_id},
        {
            "$set": {
                "reviews.$.rating":  review.rating,
                "reviews.$.comment": review.comment,
            }
        },
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Review update failed")

    return {"message": "Review updated successfully", "phone_id": phone_id, "client_id": client_id}


async def delete_review_from_phone(
    db: AsyncIOMotorDatabase, phone_id: str, client_id: str
) -> dict:
    """Remove a review from the phone's reviews array by client_id."""
    if not ObjectId.is_valid(phone_id):
        raise HTTPException(status_code=400, detail="Invalid phone ID format")
    if not ObjectId.is_valid(client_id):
        raise HTTPException(status_code=400, detail="Invalid client ID format")

    phones_col = db["phones"]

    phone = await phones_col.find_one({"_id": ObjectId(phone_id)})
    if not phone:
        raise HTTPException(status_code=404, detail="Phone not found")

    result = await phones_col.update_one(
        {"_id": ObjectId(phone_id)},
        {"$pull": {"reviews": {"client_id": client_id}}},
    )
    if result.modified_count == 0:
        raise HTTPException(
            status_code=404,
            detail="No review from this client found on this phone.",
        )

    return {"message": "Review deleted successfully", "phone_id": phone_id, "client_id": client_id}


async def get_reviews_for_phone(
    db: AsyncIOMotorDatabase, phone_id: str
) -> dict:
    """
    Return all reviews embedded in a phone document.
    Each review already contains client_id + client_name snapshot,
    so no additional join is needed for display.
    """
    if not ObjectId.is_valid(phone_id):
        raise HTTPException(status_code=400, detail="Invalid phone ID format")

    phones_col = db["phones"]
    phone = await phones_col.find_one(
        {"_id": ObjectId(phone_id)},
        {"name": 1, "brand": 1, "reviews": 1},
    )
    if not phone:
        raise HTTPException(status_code=404, detail="Phone not found")

    reviews = phone.get("reviews", [])
    return {
        "phone_id":   phone_id,
        "phone_name": phone.get("name"),
        "brand":      phone.get("brand"),
        "count":      len(reviews),
        "reviews":    reviews,
    }


async def get_reviews_by_client(
    db: AsyncIOMotorDatabase, client_id: str
) -> dict:
    """
    Find all phones that have a review from this client.
    Uses a query on the embedded array field `reviews.client_id`.
    Returns phone name + brand + the specific review — no data duplication.
    """
    if not ObjectId.is_valid(client_id):
        raise HTTPException(status_code=400, detail="Invalid client ID format")

    clients_col = db[CLIENTS_COLLECTION]
    client = await clients_col.find_one({"_id": ObjectId(client_id)})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    phones_col = db["phones"]
    cursor = phones_col.find(
        {"reviews.client_id": client_id},
        {"name": 1, "brand": 1, "reviews.$": 1},  # project only matching review
    )

    results = []
    async for phone in cursor:
        review = phone.get("reviews", [{}])[0]
        results.append({
            "phone_id":   str(phone["_id"]),
            "phone_name": phone.get("name"),
            "brand":      phone.get("brand"),
            "rating":     review.get("rating"),
            "comment":    review.get("comment"),
        })

    return {
        "client_id":   client_id,
        "client_name": client["name"],
        "count":       len(results),
        "reviews":     results,
    }