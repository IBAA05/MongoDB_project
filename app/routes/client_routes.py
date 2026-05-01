"""
routes/client_routes.py
------------------------
FastAPI router for Client CRUD and Review management.

Base prefixes:
  /clients          → client collection endpoints
  /phones/{id}/reviews → review endpoints (phone-scoped)

Swagger tag: "👤 Clients & Reviews"

Review design (no-redundancy approach):
─────────────────────────────────────────────────────────────────
  • Clients live in their own `clients` collection (name, phone_number).
  • Reviews are embedded inside each phone document as an array.
  • Each review stores only `client_id` (reference) + `client_name`
    (lightweight snapshot for display) — no full client document copy.
  • This gives fast reads (no join needed) while keeping a live link
    to the source-of-truth client record via `client_id`.
─────────────────────────────────────────────────────────────────
"""
from fastapi import APIRouter, Depends, Query, Path
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_db
from app.models.client import ClientCreate, ReviewCreate
from app.controllers import client_controller

router = APIRouter(tags=["👤 Clients & Reviews"])


# ── Dependency: get the raw DB object (not just one collection) ───────────────

# We need the full DB so client_service can access both `phones` and `clients`.


# ═══════════════════════════════════════════════════════════
#  CLIENT CRUD
# ═══════════════════════════════════════════════════════════

@router.post(
    "/clients",
    summary="Create a new client",
    description=(
        "Registers a new client in the `clients` collection. "
        "The MongoDB `_id` is auto-generated and returned in the response."
    ),
    status_code=201,
)
async def create_client(
    client: ClientCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await client_controller.create_client(db, client)


@router.get(
    "/clients",
    summary="List all clients",
    description="Returns up to `limit` client documents from the clients collection.",
)
async def list_clients(
    limit: int = Query(100, ge=1, le=500, description="Max number of clients to return"),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await client_controller.list_clients(db, limit)


@router.get(
    "/clients/{client_id}",
    summary="Get a client by ID",
    description="Fetch a single client document by its MongoDB ObjectId.",
)
async def get_client(
    client_id: str = Path(..., description="MongoDB ObjectId of the client"),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await client_controller.get_client(db, client_id)


@router.patch(
    "/clients/{client_id}",
    summary="Update a client",
    description=(
        "Partially updates a client's fields using `$set`. "
        "Only the fields provided in the request body are modified."
    ),
)
async def update_client(
    client: ClientCreate,
    client_id: str = Path(..., description="MongoDB ObjectId of the client"),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await client_controller.update_client(db, client_id, client)


@router.delete(
    "/clients/{client_id}",
    summary="Delete a client",
    description=(
        "Removes a client document from the `clients` collection. "
        "Existing reviews on phones that reference this client_id are **not** removed automatically — "
        "they keep `client_id` as a tombstone reference."
    ),
)
async def delete_client(
    client_id: str = Path(..., description="MongoDB ObjectId of the client"),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await client_controller.delete_client(db, client_id)


# ═══════════════════════════════════════════════════════════
#  REVIEWS  (phone-scoped)
# ═══════════════════════════════════════════════════════════

@router.post(
    "/phones/{phone_id}/reviews",
    summary="Add a review to a phone",
    description=(
        "Embeds a new review in the phone document's `reviews` array.\n\n"
        "**How the link works (no redundancy):**\n"
        "- The review stores `client_id` (a reference to the `clients` collection) "
        "and `client_name` (a lightweight name snapshot).\n"
        "- No full client document is duplicated inside the phone.\n"
        "- A client can only leave **one** review per phone (HTTP 409 if already reviewed).\n\n"
        "**Required query param:** `client_id` — the ObjectId of the reviewing client."
    ),
    status_code=201,
)
async def add_review(
    review: ReviewCreate,
    phone_id: str = Path(..., description="MongoDB ObjectId of the phone"),
    client_id: str = Query(..., description="MongoDB ObjectId of the client leaving the review"),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await client_controller.add_review(db, phone_id, client_id, review)


@router.patch(
    "/phones/{phone_id}/reviews",
    summary="Update a client's review on a phone",
    description=(
        "Updates the `rating` and/or `comment` of an existing review. "
        "The review is identified by `phone_id` + `client_id` combination.\n\n"
        "Uses MongoDB's positional `$` operator to update only the matched array element."
    ),
)
async def update_review(
    review: ReviewCreate,
    phone_id: str = Path(..., description="MongoDB ObjectId of the phone"),
    client_id: str = Query(..., description="MongoDB ObjectId of the client whose review to update"),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await client_controller.update_review(db, phone_id, client_id, review)


@router.delete(
    "/phones/{phone_id}/reviews",
    summary="Delete a client's review from a phone",
    description=(
        "Removes the review matching `client_id` from the phone's `reviews` array "
        "using MongoDB's `$pull` operator."
    ),
)
async def delete_review(
    phone_id: str = Path(..., description="MongoDB ObjectId of the phone"),
    client_id: str = Query(..., description="MongoDB ObjectId of the client whose review to delete"),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await client_controller.delete_review(db, phone_id, client_id)


@router.get(
    "/phones/{phone_id}/reviews",
    summary="Get all reviews for a phone",
    description=(
        "Returns the full `reviews` array embedded in the phone document. "
        "Each review includes `client_id`, `client_name`, `rating`, and `comment`. "
        "No extra query to the clients collection is required for display."
    ),
)
async def get_phone_reviews(
    phone_id: str = Path(..., description="MongoDB ObjectId of the phone"),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await client_controller.get_phone_reviews(db, phone_id)


@router.get(
    "/clients/{client_id}/reviews",
    summary="Get all reviews written by a client",
    description=(
        "Cross-collection lookup: queries the `phones` collection for documents "
        "that contain a review with the given `client_id`.\n\n"
        "Returns each matched phone's name, brand, and the client's specific review. "
        "This is the **reverse lookup** — from client → their reviews across all phones."
    ),
)
async def get_client_reviews(
    client_id: str = Path(..., description="MongoDB ObjectId of the client"),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await client_controller.get_client_reviews(db, client_id)