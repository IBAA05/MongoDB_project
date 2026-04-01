"""
tests/test_search.py
---------------------
Async integration tests for all Person 1 endpoints.
Uses httpx.AsyncClient against a real local MongoDB instance.

Run:
    pytest tests/ -v --asyncio-mode=auto
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from main import app

BASE = "http://test"


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture(scope="module")
async def client():
    """Shared async HTTP client for all tests in this module."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE) as c:
        yield c


@pytest_asyncio.fixture(scope="module", autouse=True)
async def seed_db(client):
    """Seed the database once before any test in this module runs."""
    resp = await client.post("/phones/seed")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_in_db"] >= 22


# ── Root ──────────────────────────────────────────────────────────────────────

class TestRoot:
    async def test_root_returns_200(self, client):
        resp = await client.get("/")
        assert resp.status_code == 200
        assert "docs" in resp.json()


# ── Data endpoints ────────────────────────────────────────────────────────────

class TestDataEndpoints:
    async def test_list_phones_default(self, client):
        resp = await client.get("/phones")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] >= 22
        assert isinstance(data["phones"], list)

    async def test_list_phones_limit(self, client):
        resp = await client.get("/phones?limit=5")
        assert resp.status_code == 200
        assert resp.json()["count"] == 5

    async def test_add_phone_success(self, client):
        resp = await client.post("/phones", json={
            "name": "Test Phone X1",
            "brand": "TestBrand",
            "description": "A test phone with great camera and long battery life.",
            "price": 299.99,
            "category": "mid-range",
            "stock": 10,
            "rating": 4.0,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Test Phone X1"
        assert "_id" in data

    async def test_add_phone_invalid_price(self, client):
        """Pydantic should reject price <= 0."""
        resp = await client.post("/phones", json={
            "name": "Bad Phone",
            "brand": "None",
            "description": "This has a bad price.",
            "price": -50,
        })
        assert resp.status_code == 422

    async def test_add_phone_missing_required_field(self, client):
        resp = await client.post("/phones", json={
            "brand": "Samsung",
            "price": 500,
        })
        assert resp.status_code == 422

    async def test_seed_is_idempotent(self, client):
        """Second seed call should skip all existing documents."""
        resp = await client.post("/phones/seed")
        assert resp.status_code == 200
        assert resp.json()["inserted"] == 0


# ── Text Search endpoints ─────────────────────────────────────────────────────

class TestKeywordSearch:
    async def test_keyword_camera(self, client):
        resp = await client.get("/phones/search/keyword?q=camera")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] > 0
        # All results should have a score field
        for r in data["results"]:
            assert "score" in r

    async def test_keyword_battery(self, client):
        resp = await client.get("/phones/search/keyword?q=battery")
        assert resp.status_code == 200
        assert resp.json()["count"] > 0

    async def test_keyword_no_results(self, client):
        resp = await client.get("/phones/search/keyword?q=xyznonexistentkeyword999")
        assert resp.status_code == 200
        assert resp.json()["count"] == 0

    async def test_keyword_limit_respected(self, client):
        resp = await client.get("/phones/search/keyword?q=camera&limit=2")
        assert resp.status_code == 200
        assert len(resp.json()["results"]) <= 2

    async def test_keyword_results_sorted_by_score(self, client):
        """textScore should be descending."""
        resp = await client.get("/phones/search/keyword?q=camera&limit=10")
        scores = [r["score"] for r in resp.json()["results"]]
        assert scores == sorted(scores, reverse=True)


class TestExcludeSearch:
    async def test_exclude_samsung(self, client):
        resp = await client.get("/phones/search/exclude?q=camera&exclude=Samsung")
        assert resp.status_code == 200
        data = resp.json()
        brands = [r["brand"] for r in data["results"]]
        assert "Samsung" not in brands

    async def test_exclude_multiple_words(self, client):
        resp = await client.get("/phones/search/exclude?q=battery&exclude=Samsung Apple")
        assert resp.status_code == 200
        brands = [r["brand"] for r in resp.json()["results"]]
        assert "Samsung" not in brands
        assert "Apple" not in brands


class TestPhraseSearch:
    async def test_phrase_fast_charging(self, client):
        resp = await client.get("/phones/search/phrase?phrase=fast charging")
        assert resp.status_code == 200
        data = resp.json()
        # All returned descriptions must contain the exact phrase
        for r in data["results"]:
            assert "fast charging" in r["description"].lower()

    async def test_phrase_no_match(self, client):
        resp = await client.get("/phones/search/phrase?phrase=this phrase does not exist anywhere")
        assert resp.status_code == 200
        assert resp.json()["count"] == 0


class TestFilteredSearch:
    async def test_filter_brand_samsung(self, client):
        resp = await client.get("/phones/search/filter?q=camera&brand=Samsung")
        assert resp.status_code == 200
        for r in resp.json()["results"]:
            assert r["brand"].lower() == "samsung"

    async def test_filter_max_price(self, client):
        resp = await client.get("/phones/search/filter?q=battery&max_price=500")
        assert resp.status_code == 200
        for r in resp.json()["results"]:
            assert r["price"] <= 500

    async def test_filter_price_range(self, client):
        resp = await client.get("/phones/search/filter?q=camera&min_price=200&max_price=800")
        assert resp.status_code == 200
        for r in resp.json()["results"]:
            assert 200 <= r["price"] <= 800

    async def test_filter_brand_and_price(self, client):
        resp = await client.get("/phones/search/filter?q=camera&brand=Apple&max_price=900")
        assert resp.status_code == 200
        for r in resp.json()["results"]:
            assert r["brand"].lower() == "apple"
            assert r["price"] <= 900


class TestFieldSearch:
    async def test_field_description(self, client):
        resp = await client.get("/phones/search/field?field=description&q=AMOLED")
        assert resp.status_code == 200
        for r in resp.json()["results"]:
            assert "amoled" in r["description"].lower()

    async def test_field_brand(self, client):
        resp = await client.get("/phones/search/field?field=brand&q=xiaomi")
        assert resp.status_code == 200
        for r in resp.json()["results"]:
            assert "xiaomi" in r["brand"].lower()

    async def test_field_invalid(self, client):
        """Invalid field name should return 500 (ValueError from service)."""
        resp = await client.get("/phones/search/field?field=nonexistent&q=test")
        assert resp.status_code == 500


class TestPaginatedSearch:
    async def test_pagination_page1(self, client):
        resp = await client.get("/phones/search/paginated?q=camera&page=1&page_size=3")
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 1
        assert len(data["results"]) <= 3
        assert "total_results" in data
        assert "total_pages" in data

    async def test_pagination_page2_differs_from_page1(self, client):
        r1 = await client.get("/phones/search/paginated?q=battery&page=1&page_size=2")
        r2 = await client.get("/phones/search/paginated?q=battery&page=2&page_size=2")
        ids1 = [r["_id"] for r in r1.json()["results"]]
        ids2 = [r["_id"] for r in r2.json()["results"]]
        # Pages must not overlap
        assert not set(ids1) & set(ids2)

    async def test_pagination_metadata(self, client):
        resp = await client.get("/phones/search/paginated?q=camera&page=1&page_size=5")
        data = resp.json()
        assert data["total_pages"] == -(-data["total_results"] // 5)


class TestScoreSearch:
    async def test_score_threshold_filters(self, client):
        resp_low  = await client.get("/phones/search/score?q=camera&min_score=0.5")
        resp_high = await client.get("/phones/search/score?q=camera&min_score=5.0")
        # Higher threshold should return fewer results
        assert resp_low.json()["count"] >= resp_high.json()["count"]

    async def test_score_all_above_threshold(self, client):
        resp = await client.get("/phones/search/score?q=camera&min_score=1.0")
        for r in resp.json()["results"]:
            assert r["score"] >= 1.0


# ── Index & Performance endpoints ─────────────────────────────────────────────

class TestIndexEndpoints:
    async def test_list_indexes(self, client):
        resp = await client.get("/phones/indexes")
        assert resp.status_code == 200
        data = resp.json()
        names = [idx["name"] for idx in data["indexes"]]
        assert "text_search_idx" in names
        assert "unique_name_idx" in names
        assert "brand_price_idx" in names

    async def test_recreate_text_index(self, client):
        resp = await client.post("/phones/indexes/recreate-text")
        assert resp.status_code == 200
        assert resp.json()["recreated"] == "text_search_idx"

    async def test_index_stats(self, client):
        resp = await client.get("/phones/indexes/stats")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_performance_with_index(self, client):
        resp = await client.get("/phones/indexes/performance/with-index?q=camera")
        assert resp.status_code == 200
        data = resp.json()
        assert data["text_index_present"] is True
        assert "docs_examined" in data
        assert "execution_time_ms" in data

    async def test_performance_without_index(self, client):
        resp = await client.get("/phones/indexes/performance/without-index?q=camera")
        assert resp.status_code == 200
        data = resp.json()
        assert data["text_index_present"] is False
        assert "docs_examined" in data

    async def test_performance_compare(self, client):
        resp = await client.get("/phones/indexes/performance/compare?q=battery")
        assert resp.status_code == 200
        data = resp.json()
        assert "with_text_index" in data
        assert "without_text_index" in data
        assert "speedup_factor" in data
        assert data["speedup_factor"] >= 0

    async def test_drop_and_recreate_index(self, client):
        # Drop the price index
        resp = await client.delete("/phones/indexes/price_idx")
        assert resp.status_code == 200
        assert resp.json()["dropped"] == "price_idx"
        # Recreate text index to ensure DB is clean for next tests
        await client.post("/phones/indexes/recreate-text")
