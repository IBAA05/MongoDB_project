"""
main.py
-------
FastAPI application entry point.
Startup sequence:
  1. Connect to MongoDB (Motor async client)
  2. Ensure all required indexes exist
  3. Mount all routers

Swagger UI available at: http://localhost:8000/docs
ReDoc UI available at:   http://localhost:8000/redoc
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.database import connect_db, close_db

# Person 1 routers
from app.routes import data_routes, search_routes, index_routes

# Person 2 routers
from app.routes import aggregation_routes, filter_routes, stats_routes

# Person 3 routers
from app.routes import crud_routes

# Clients & Reviews router
from app.routes import client_routes

# Notifications
from app.routes import notification_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await close_db()


app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        # ── Person 1 tags ──────────────────────────────────────────────────────
        {
            "name": "📱 Data & Seeding",
            "description": "Insert the sample dataset and add individual phones.",
        },
        {
            "name": "🔍 Text Search",
            "description": (
                "All text-search queries using the MongoDB `$text` index. "
                "Includes keyword, exclusion, phrase, filter, pagination and score queries."
            ),
        },
        {
            "name": "📊 Indexes & Performance",
            "description": (
                "Manage indexes (list, drop, recreate) and run `explain()` "
                "performance comparisons with and without the text index."
            ),
        },
        # ── Person 2 tags ──────────────────────────────────────────────────────
        {
            "name": "📈 Aggregations",
            "description": (
                "MongoDB aggregation pipelines — text search with scoring, "
                "group by brand, price buckets ($bucket), multi-stage pipelines, "
                "brand rankings, and more."
            ),
        },
        {
            "name": "🔎 Filtering",
            "description": (
                "Advanced find() queries — price range ($gte/$lte), "
                "multi-brand ($in), brand exclusion ($nin), "
                "regex on description, cheapest/most expensive, $exists checks."
            ),
        },
        {
            "name": "📊 Statistics",
            "description": (
                "Collection-level reporting — total count, global price stats, "
                "top brands, price distribution, and collection metadata (collStats)."
            ),
        },
        # ── Person 3 tags ──────────────────────────────────────────────────────
        {
            "name": "🛠️ Full CRUD Operations",
            "description": (
                "Document-level CRUD — update, replace, delete by ID, "
                "bulk delete by name/brand, bulk updates using $mul, $set, and $unset."
            ),
        },
        # ── Clients & Reviews tag ──────────────────────────────────────────────
        {
            "name": "👤 Clients & Reviews",
            "description": (
                "**Two-collection design with no redundancy.**\n\n"
                "- `clients` collection stores client profiles (name, phone_number).\n"
                "- Reviews are **embedded** inside each phone document as an array.\n"
                "- Each review stores only `client_id` (reference) + `client_name` "
                "(lightweight snapshot) — the full client object is never duplicated.\n\n"
                "**Endpoints:**\n"
                "- `POST /clients` — register a client\n"
                "- `GET /clients` — list all clients\n"
                "- `GET /clients/{id}` — get one client\n"
                "- `PATCH /clients/{id}` — update a client\n"
                "- `DELETE /clients/{id}` — delete a client\n"
                "- `POST /phones/{id}/reviews?client_id=` — add a review to a phone\n"
                "- `PATCH /phones/{id}/reviews?client_id=` — update a review\n"
                "- `DELETE /phones/{id}/reviews?client_id=` — remove a review\n"
                "- `GET /phones/{id}/reviews` — all reviews for a phone\n"
                "- `GET /clients/{id}/reviews` — all reviews by a client (reverse lookup)"
            ),
        },
    ],
)

# Allow React dev server to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mount routers ──────────────────────────────────────────────────────────────

# Person 1
app.include_router(data_routes.router)
app.include_router(search_routes.router)
app.include_router(index_routes.router)

# Person 2
app.include_router(aggregation_routes.router)
app.include_router(filter_routes.router)
app.include_router(stats_routes.router)

# Person 3
app.include_router(crud_routes.router)

# Clients & Reviews
app.include_router(client_routes.router)

# Notifications
app.include_router(notification_routes.router)


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Smartphone Catalog API",
        "docs": "/docs",
        "redoc": "/redoc",
        "person_1_endpoints": [
            "POST /phones/seed",
            "POST /phones",
            "GET  /phones",
            "GET  /phones/search/keyword",
            "GET  /phones/search/exclude",
            "GET  /phones/search/phrase",
            "GET  /phones/search/filter",
            "GET  /phones/search/field",
            "GET  /phones/search/paginated",
            "GET  /phones/search/score",
            "GET  /phones/indexes",
            "GET  /phones/indexes/stats",
            "GET  /phones/indexes/performance/with-index",
            "GET  /phones/indexes/performance/without-index",
            "GET  /phones/indexes/performance/compare",
        ],
        "person_2_endpoints": [
            "GET  /phones/aggregations/search",
            "GET  /phones/aggregations/search-price",
            "GET  /phones/aggregations/group-by-brand",
            "GET  /phones/aggregations/min-max-per-brand",
            "GET  /phones/aggregations/top",
            "GET  /phones/aggregations/pipeline",
            "GET  /phones/aggregations/price-buckets",
            "GET  /phones/aggregations/brands-min-count",
            "GET  /phones/aggregations/brand-ranking",
            "GET  /phones/filter/price-range",
            "GET  /phones/filter/brands",
            "GET  /phones/filter/exclude-brands",
            "GET  /phones/filter/description",
            "GET  /phones/filter/cheapest",
            "GET  /phones/filter/most-expensive",
            "GET  /phones/filter/field-exists",
            "GET  /phones/stats/count",
            "GET  /phones/stats/price",
            "GET  /phones/stats/top-brand-count",
            "GET  /phones/stats/top-brand-price",
            "GET  /phones/stats/price-distribution",
            "GET  /phones/stats/collection",
        ],
        "person_3_endpoints": [
            "PATCH  /phones/{id}",
            "PUT    /phones/{id}",
            "DELETE /phones/{id}",
            "DELETE /phones/bulk/delete",
            "PATCH  /phones/brand/{brand}/price",
            "PATCH  /phones/bulk/add-fields",
            "PATCH  /phones/bulk/remove-field",
        ],
        "clients_and_reviews_endpoints": [
            "POST   /clients",
            "GET    /clients",
            "GET    /clients/{id}",
            "PATCH  /clients/{id}",
            "DELETE /clients/{id}",
            "POST   /phones/{id}/reviews?client_id=",
            "PATCH  /phones/{id}/reviews?client_id=",
            "DELETE /phones/{id}/reviews?client_id=",
            "GET    /phones/{id}/reviews",
            "GET    /clients/{id}/reviews",
        ],
    }