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
from app.routes import data_routes, search_routes, index_routes


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
    ],
)

# Allow React dev server to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(data_routes.router)
app.include_router(search_routes.router)
app.include_router(index_routes.router)


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Smartphone Catalog API — Person 1",
        "docs": "/docs",
        "redoc": "/redoc",
    }
