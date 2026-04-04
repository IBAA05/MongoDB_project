"""
models/phone.py
---------------
Pydantic v2 schemas for request validation and response serialization.

PhoneCreate  → body of POST /phones  (input)
PhoneOut     → any endpoint response  (output, _id converted to str)
SearchResult → wraps PhoneOut with a relevance score field
"""
from typing import Optional
from pydantic import BaseModel, Field, field_validator


# ── Input schema ──────────────────────────────────────────────────────────────

class PhoneCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Unique smartphone model name")
    brand: str = Field(..., min_length=1, description="Manufacturer brand")
    description: str = Field(..., min_length=5, description="Full product description")
    price: float = Field(..., gt=0, description="Price in USD — must be positive")
    category: Optional[str] = Field(
        None,
        description="Price tier: budget | mid-range | flagship",
        pattern="^(budget|mid-range|flagship)$",
    )
    stock: Optional[int] = Field(None, ge=0, description="Units in stock")
    rating: Optional[float] = Field(None, ge=0, le=5, description="User rating 0-5")

    @field_validator("price")
    @classmethod
    def price_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("price must be a positive number")
        return round(v, 2)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Samsung Galaxy S24 Ultra",
                    "brand": "Samsung",
                    "description": (
                        "Flagship smartphone with 200MP camera, Snapdragon 8 Gen 3, "
                        "5000mAh battery, and S-Pen stylus support."
                    ),
                    "price": 1299.99,
                    "category": "flagship",
                    "stock": 150,
                    "rating": 4.7,
                }
            ]
        }
    }


class PhoneUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, description="New name (optional)")
    brand: Optional[str] = Field(None, min_length=1, description="New brand (optional)")
    description: Optional[str] = Field(None, min_length=5, description="New description (optional)")
    price: Optional[float] = Field(None, gt=0, description="New price (optional)")
    category: Optional[str] = Field(
        None,
        description="New category (optional)",
        pattern="^(budget|mid-range|flagship)$",
    )
    stock: Optional[int] = Field(None, ge=0, description="New stock (optional)")
    rating: Optional[float] = Field(None, ge=0, le=5, description="New rating (optional)")

    @field_validator("price")
    @classmethod
    def price_must_be_positive_optional(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            if v <= 0:
                raise ValueError("price must be a positive number")
            return round(v, 2)
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Samsung Galaxy S24 Ultra",
                    "price": 1199.99,
                }
            ]
        }
    }


# ── Output schema ─────────────────────────────────────────────────────────────

class PhoneOut(BaseModel):
    id: str = Field(..., alias="_id", description="MongoDB document ObjectId as string")
    name: str
    brand: str
    description: str
    price: float
    category: Optional[str] = None
    stock: Optional[int] = None
    rating: Optional[float] = None

    model_config = {"populate_by_name": True}


class SearchResult(BaseModel):
    """Phone document enriched with a text-search relevance score."""
    id: str = Field(..., alias="_id")
    name: str
    brand: str
    description: str
    price: float
    category: Optional[str] = None
    score: float = Field(..., description="MongoDB textScore — higher = more relevant")

    model_config = {"populate_by_name": True}


# ── Performance schema ────────────────────────────────────────────────────────

class ExecutionStats(BaseModel):
    """Subset of MongoDB explain() output returned to the client."""
    index_used: Optional[str] = Field(None, description="Name of the winning index plan")
    docs_examined: int = Field(..., description="Total BSON documents scanned")
    docs_returned: int = Field(..., description="Documents matching the query")
    execution_time_ms: int = Field(..., description="Total server-side execution time")
    index_keys_examined: int = Field(0, description="Index entries scanned")


# ── Index info schema ─────────────────────────────────────────────────────────

class IndexInfo(BaseModel):
    name: str
    key: dict
    unique: bool = False
    sparse: bool = False
