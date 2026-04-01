# 📱 Smartphone Catalog API — Person 1
**Text Search · Indexing · Performance Analysis**  
Stack: **MongoDB 7** · **FastAPI** · **Python 3.11** · **Motor (async)**

---

## 📁 Project Structure

```
smartphone_catalog/
├── main.py                        ← FastAPI app entry point
├── .env                           ← Environment variables
├── requirements.txt               ← Pinned dependencies
├── pytest.ini                     ← Pytest configuration
│
├── app/
│   ├── core/
│   │   ├── config.py             ← Pydantic settings (reads .env)
│   │   └── database.py           ← Motor client + index bootstrap
│   │
│   ├── models/
│   │   └── phone.py              ← Pydantic schemas (input/output)
│   │
│   ├── services/                 ← Business logic / raw MongoDB queries
│   │   ├── seed_service.py       ← 22-document bulk seeder
│   │   ├── search_service.py     ← All 7 text search functions
│   │   └── index_service.py      ← Index management + explain()
│   │
│   ├── controllers/              ← Thin orchestration layer
│   │   ├── data_controller.py
│   │   ├── search_controller.py
│   │   └── index_controller.py
│   │
│   └── routes/                   ← FastAPI routers + Swagger docs
│       ├── data_routes.py        ← /phones  (seed, add, list)
│       ├── search_routes.py      ← /phones/search/*
│       └── index_routes.py       ← /phones/indexes/*
│
└── tests/
    └── test_search.py            ← Full async integration test suite
```

---

## ⚙️ 1. Install MongoDB

### Ubuntu / Debian
```bash
sudo apt install -y gnupg curl
curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc \
  | sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor

echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] \
  https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" \
  | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list

sudo apt update && sudo apt install -y mongodb-org
sudo systemctl start mongod
sudo systemctl enable mongod          # start on boot

# Verify
mongosh --eval "db.runCommand({ connectionStatus: 1 })"
```

### Windows
Download the MSI installer from https://www.mongodb.com/try/download/community  
Add `C:\Program Files\MongoDB\Server\7.0\bin` to your PATH.

### macOS
```bash
brew tap mongodb/brew
brew install mongodb-community@7.0
brew services start mongodb-community@7.0
```

---

## 🐍 2. Set Up Python Environment

```bash
# Clone / navigate to the project folder
cd smartphone_catalog

# Create virtual environment with Python 3.11
python3.11 -m venv venv

# Activate
source venv/bin/activate          # Linux / macOS
# venv\Scripts\activate           # Windows PowerShell

# Install all dependencies
pip install -r requirements.txt
```

---

## 🔑 3. Configure Environment

The `.env` file is pre-configured for a local MongoDB instance:

```env
MONGO_URI=mongodb://localhost:27017
DB_NAME=smartphone_catalog
COLLECTION_NAME=phones
```

Change `MONGO_URI` if you use MongoDB Atlas or a non-default port.

---

## 🚀 4. Run the API

```bash
uvicorn main:app --reload --port 8000
```

On startup the app will:
1. Connect to MongoDB
2. Auto-create all 4 indexes (idempotent)
3. Print `[DB] Connected` and `[DB] Indexes verified`

---

## 🌱 5. Seed the Database

```bash
# Using curl
curl -X POST http://localhost:8000/phones/seed

# Or visit Swagger UI → POST /phones/seed → Execute
```

This inserts **22 real-world smartphones** (Samsung, Apple, Xiaomi, Google, OnePlus, Sony, Motorola, Nothing, Realme, Oppo, Vivo, Honor).  
Running it again is safe — duplicate names are skipped automatically.

---

## 📖 6. API Documentation

| Interface | URL |
|-----------|-----|
| **Swagger UI** (interactive) | http://localhost:8000/docs |
| **ReDoc** (readable) | http://localhost:8000/redoc |
| **OpenAPI JSON** | http://localhost:8000/openapi.json |

---

## 🔍 7. All Endpoints — Quick Reference

### 📱 Data & Seeding
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/phones/seed` | Bulk insert 22 sample smartphones |
| `POST` | `/phones` | Add a single smartphone |
| `GET`  | `/phones?limit=50` | List all phones |

### 🔍 Text Search
| Method | Path | Key Params |
|--------|------|------------|
| `GET` | `/phones/search/keyword` | `q`, `limit` |
| `GET` | `/phones/search/exclude` | `q`, `exclude`, `limit` |
| `GET` | `/phones/search/phrase` | `phrase`, `limit` |
| `GET` | `/phones/search/filter` | `q`, `brand`, `min_price`, `max_price` |
| `GET` | `/phones/search/field` | `field`, `q`, `limit` |
| `GET` | `/phones/search/paginated` | `q`, `page`, `page_size` |
| `GET` | `/phones/search/score` | `q`, `min_score`, `limit` |

### 📊 Indexes & Performance
| Method | Path | Description |
|--------|------|-------------|
| `GET`    | `/phones/indexes` | List all indexes |
| `DELETE` | `/phones/indexes/{name}` | Drop a named index |
| `POST`   | `/phones/indexes/recreate-text` | Drop + recreate text index |
| `GET`    | `/phones/indexes/stats` | Index usage statistics |
| `GET`    | `/phones/indexes/performance/with-index?q=` | explain() WITH index |
| `GET`    | `/phones/indexes/performance/without-index?q=` | explain() WITHOUT index |
| `GET`    | `/phones/indexes/performance/compare?q=` | Side-by-side comparison |

---

## 🧪 8. Running Tests

```bash
# Activate venv first
source venv/bin/activate

# Run all tests with verbose output
pytest tests/ -v

# Run only search tests
pytest tests/test_search.py::TestKeywordSearch -v

# Run with coverage
pip install pytest-cov
pytest tests/ -v --cov=app --cov-report=term-missing
```

> **Note:** Tests require a running local MongoDB instance on port 27017.

---

## 🗃️ 9. MongoDB Indexes Explained

### text_search_idx
```javascript
db.phones.createIndex(
  { name: "text", brand: "text", description: "text" },
  {
    name: "text_search_idx",
    weights: { name: 10, brand: 5, description: 1 },
    default_language: "english"
  }
)
```
**Purpose:** Enables `$text` search across 3 fields. Field weights control relevance scoring — a match in `name` scores 10× more than one in `description`.

### brand_price_idx
```javascript
db.phones.createIndex({ brand: 1, price: 1 }, { name: "brand_price_idx" })
```
**Purpose:** Accelerates queries that filter by brand and sort or range-filter by price (used by Person 2 aggregations).

### unique_name_idx
```javascript
db.phones.createIndex({ name: 1 }, { name: "unique_name_idx", unique: true })
```
**Purpose:** Enforces that no two phones share the same name. Insertion of a duplicate raises a `DuplicateKeyError`.

### price_idx
```javascript
db.phones.createIndex({ price: 1 }, { name: "price_idx" })
```
**Purpose:** Speeds up price range queries (`$gte` / `$lte`) and sort-by-price operations.

---

## 🧩 10. Postman Collection — Import-Ready Requests

Copy this JSON into **Postman → Import → Raw Text**:

```json
{
  "info": { "name": "Smartphone Catalog - Person 1", "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json" },
  "item": [
    { "name": "Seed DB",          "request": { "method": "POST", "url": "http://localhost:8000/phones/seed" } },
    { "name": "List Phones",      "request": { "method": "GET",  "url": "http://localhost:8000/phones?limit=10" } },
    { "name": "Search: keyword",  "request": { "method": "GET",  "url": "http://localhost:8000/phones/search/keyword?q=camera&limit=5" } },
    { "name": "Search: exclude",  "request": { "method": "GET",  "url": "http://localhost:8000/phones/search/exclude?q=camera&exclude=Samsung&limit=5" } },
    { "name": "Search: phrase",   "request": { "method": "GET",  "url": "http://localhost:8000/phones/search/phrase?phrase=fast+charging" } },
    { "name": "Search: filter",   "request": { "method": "GET",  "url": "http://localhost:8000/phones/search/filter?q=battery&brand=Apple&max_price=900" } },
    { "name": "Search: field",    "request": { "method": "GET",  "url": "http://localhost:8000/phones/search/field?field=description&q=AMOLED" } },
    { "name": "Search: paginated","request": { "method": "GET",  "url": "http://localhost:8000/phones/search/paginated?q=camera&page=1&page_size=3" } },
    { "name": "Search: score",    "request": { "method": "GET",  "url": "http://localhost:8000/phones/search/score?q=camera&min_score=1.5" } },
    { "name": "List Indexes",     "request": { "method": "GET",  "url": "http://localhost:8000/phones/indexes" } },
    { "name": "Recreate Text Idx","request": { "method": "POST", "url": "http://localhost:8000/phones/indexes/recreate-text" } },
    { "name": "Perf: with index", "request": { "method": "GET",  "url": "http://localhost:8000/phones/indexes/performance/with-index?q=camera" } },
    { "name": "Perf: no index",   "request": { "method": "GET",  "url": "http://localhost:8000/phones/indexes/performance/without-index?q=camera" } },
    { "name": "Perf: compare",    "request": { "method": "GET",  "url": "http://localhost:8000/phones/indexes/performance/compare?q=battery" } }
  ]
}
