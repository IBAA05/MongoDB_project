"""
routes/data_routes.py
---------------------
Data seeding and basic read endpoints (Person 1 scope).
"""
from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorCollection
from app.core.database import get_collection
from app.controllers import data_controller
from app.models.phone import PhoneCreate

router = APIRouter(prefix="/phones", tags=["📱 Data & Seeding"])


@router.post(
    "/seed",
    summary="Seed the database with 22 sample smartphones",
    description=(
        "Bulk-inserts 22 real-world smartphone documents (Samsung, Apple, Xiaomi, Google, etc.). "
        "Idempotent — already-existing documents (matched by name) are skipped."
    ),
)
async def seed(collection: AsyncIOMotorCollection = Depends(get_collection)):
    return await data_controller.seed(collection)


@router.post(
    "/",
    summary="Add a single smartphone",
    description="Insert one smartphone document. `name` must be unique (enforced by a unique index).",
    status_code=201,
)
async def add_phone(
    phone: PhoneCreate,
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    return await data_controller.add_phone(collection, phone)


@router.get(
    "/",
    summary="List all smartphones",
    description="Returns up to `limit` documents from the phones collection.",
)
async def list_phones(
    limit: int = Query(50, ge=1, le=200),
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    return await data_controller.get_all_phones(collection, limit)
