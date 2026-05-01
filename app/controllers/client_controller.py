"""
controllers/client_controller.py
---------------------------------
Thin orchestration layer for client and review operations.
Receives validated inputs from routes, delegates to client_service,
and shapes the response. No MongoDB logic lives here.
"""
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.client import ClientCreate, ReviewCreate
from app.services import client_service


# ── Client CRUD ───────────────────────────────────────────────────────────────

async def create_client(db: AsyncIOMotorDatabase, data: ClientCreate):
    return await client_service.create_client(db, data)


async def list_clients(db: AsyncIOMotorDatabase, limit: int):
    clients = await client_service.get_all_clients(db, limit)
    return {"count": len(clients), "clients": clients}


async def get_client(db: AsyncIOMotorDatabase, client_id: str):
    return await client_service.get_client_by_id(db, client_id)


async def update_client(db: AsyncIOMotorDatabase, client_id: str, data: ClientCreate):
    update_fields = data.model_dump(exclude_unset=True)
    return await client_service.update_client(db, client_id, update_fields)


async def delete_client(db: AsyncIOMotorDatabase, client_id: str):
    return await client_service.delete_client(db, client_id)


# ── Review operations ─────────────────────────────────────────────────────────

async def add_review(
    db: AsyncIOMotorDatabase,
    phone_id: str,
    client_id: str,
    review: ReviewCreate,
):
    return await client_service.add_review_to_phone(db, phone_id, client_id, review)


async def update_review(
    db: AsyncIOMotorDatabase,
    phone_id: str,
    client_id: str,
    review: ReviewCreate,
):
    return await client_service.update_review_on_phone(db, phone_id, client_id, review)


async def delete_review(
    db: AsyncIOMotorDatabase, phone_id: str, client_id: str
):
    return await client_service.delete_review_from_phone(db, phone_id, client_id)


async def get_phone_reviews(db: AsyncIOMotorDatabase, phone_id: str):
    return await client_service.get_reviews_for_phone(db, phone_id)


async def get_client_reviews(db: AsyncIOMotorDatabase, client_id: str):
    return await client_service.get_reviews_by_client(db, client_id)