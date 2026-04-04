"""
routes/crud_routes.py
---------------------
Full CRUD (update/delete/bulk) operations (Person 3 scope).
"""
from fastapi import APIRouter, Depends, Query, Path
from motor.motor_asyncio import AsyncIOMotorCollection
from app.core.database import get_collection
from app.controllers import crud_controller
from app.models.phone import PhoneCreate, PhoneUpdate

router = APIRouter(prefix="/phones", tags=["🛠️ Full CRUD Operations"])


@router.patch(
    "/{id}",
    summary="Partial update a document",
    description="Updates specific fields of an existing smartphone ($set). Only provided fields are modified.",
)
async def update_phone_partial(
    phone: PhoneUpdate,
    id: str = Path(..., description="MongoDB ObjectId"),
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    return await crud_controller.update_phone_partial(collection, id, phone)


@router.put(
    "/{id}",
    summary="Replace an entire document",
    description="Updates existing smartphone by replacing its entire document ($replaceOne).",
)
async def update_phone(
    phone: PhoneCreate,
    id: str = Path(..., description="MongoDB ObjectId"),
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    return await crud_controller.replace_phone(collection, id, phone)


@router.delete(
    "/bulk/delete",
    summary="Delete by name or brand",
    description="Deletes multiple documents that match the provided name or brand.",
)
async def delete_phones_by_name_or_brand(
    name: str = Query(None, description="Exact name to match"),
    brand: str = Query(None, description="Exact brand to match"),
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    return await crud_controller.delete_phones_by_name_or_brand(collection, name, brand)


@router.delete(
    "/{id}",
    summary="Delete a single smartphone",
    description="Deletes a smartphone by its ObjectId.",
)
async def delete_phone(
    id: str = Path(..., description="MongoDB ObjectId"),
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    return await crud_controller.delete_phone(collection, id)


@router.patch(
    "/brand/{brand}/price",
    summary="Bulk price update by brand",
    description="Increases the price of all phones of a specific brand by +X%.",
)
async def bulk_update_price_by_brand(
    brand: str = Path(..., description="The brand of phones to update"),
    percentage: float = Query(..., description="Percentage increase, e.g., 5.0 for 5%"),
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    return await crud_controller.bulk_update_price_by_brand(collection, brand, percentage)


@router.patch(
    "/bulk/add-fields",
    summary="Add new fields to all documents",
    description="Adds stock, rating, and category fields to all documents using $set.",
)
async def add_fields_to_all(
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    return await crud_controller.add_fields_to_all(collection)


@router.patch(
    "/bulk/remove-field",
    summary="Remove a field from all documents",
    description="Removes a specific field from all documents using $unset.",
)
async def remove_field_from_all(
    field_name: str = Query(..., description="Name of the field to remove"),
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    return await crud_controller.remove_field_from_all(collection, field_name)
