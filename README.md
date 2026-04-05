# Finance Dashboard Backend

A clean, production-style **REST API** for managing financial records with **Role-Based Access Control**, built with FastAPI and SQLite.

> Designed to run instantly — no Docker, no external database server, no complex setup. Clone → Install → Run.

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Framework** | FastAPI | Auto-generates interactive API docs, built-in request validation, high performance |
| **Database** | SQLite (Raw SQL) | Zero setup — demonstrates strong SQL skills (`JOIN`, `GROUP BY`, `SUM()`) without requiring a DB server |
| **Validation** | Pydantic v2 | Type-safe request/response schemas with automatic error messages |
| **Language** | Python 3.10+ | Clean, readable, well-structured |

---

## Project Structure

```
├── app/
│   ├── main.py                  # FastAPI app entry point & router registration
│   ├── database/
│   │   └── setup.py             # DB initialization, table creation & seed data
│   ├── models/
│   │   └── schemas.py           # Pydantic models (request/response validation)
│   ├── routers/
│   │   ├── records.py           # CRUD endpoints for financial records
│   │   └── dashboard.py         # Aggregated analytics endpoint
│   └── services/
│       └── auth.py              # Role lookup & access control logic
├── tests/
│   ├── conftest.py              # Test fixtures (DB setup)
│   └── test_api.py              # 37 comprehensive API tests
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Quick Start

### 1. Clone the repository
```bash
git clone <repo-url>
cd finance-dashboard-backend
```

### 2. Create a virtual environment (recommended)
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Start the server
```bash
uvicorn app.main:app --reload
```

The database (`finance.db`) is **automatically created and seeded** with sample data on first launch.

### 5. Open the interactive docs
Navigate to **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)** — you can test every endpoint directly from the browser, no Postman needed.

---

## API Endpoints

### Records (`/records`)

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| `GET` | `/records/` | List all records (supports filtering) | All roles |
| `POST` | `/records/` | Create a new record | Admin only |
| `PUT` | `/records/{id}` | Update an existing record | Admin only |
| `DELETE` | `/records/{id}` | Delete a record | Admin only |

**Query Filters** — `GET /records/?category=Salary&type=INCOME`

### Dashboard (`/dashboard`)

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| `GET` | `/dashboard/summary` | Aggregated financial summary | Analyst, Admin |

Returns: `total_income`, `total_expense`, `net_balance`, and `expenses_by_category` breakdown.

---

## Role-Based Access Control (RBAC)

Authentication is simulated via a `user-id` header on every request. Three pre-seeded users exist:

| `user-id` | Username | Role | Permissions |
|-----------|----------|------|-------------|
| `1` | john_viewer | **Viewer** | Read records |
| `2` | sarah_analyst | **Analyst** | Read records + View dashboard |
| `3` | admin_user | **Admin** | Full CRUD + View dashboard |

### Example: Making a request as Admin
```bash
curl -H "user-id: 3" http://127.0.0.1:8000/records/
```

### Access Matrix

| Action | Viewer | Analyst | Admin |
|--------|--------|---------|-------|
| Read records | ✅ | ✅ | ✅ |
| Filter records | ✅ | ✅ | ✅ |
| Create record | ❌ 403 | ❌ 403 | ✅ |
| Update record | ❌ 403 | ❌ 403 | ✅ |
| Delete record | ❌ 403 | ❌ 403 | ✅ |
| View dashboard | ❌ 403 | ✅ | ✅ |

---

## Database Design

Two tables, created automatically with `CHECK` constraints for data integrity:

```sql
-- Users: role is enforced at the DB level
CREATE TABLE users (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    role     TEXT NOT NULL CHECK(role IN ('Viewer', 'Analyst', 'Admin'))
);

-- Financial Records: type is enforced at the DB level
CREATE TABLE financial_records (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    amount   REAL NOT NULL,
    type     TEXT NOT NULL CHECK(type IN ('INCOME', 'EXPENSE')),
    category TEXT NOT NULL,
    date     TEXT NOT NULL,
    notes    TEXT
);
```

The database is auto-seeded with 3 users and 4 sample records on first startup.

---

## Input Validation & Error Handling

The API returns proper HTTP status codes for every scenario:

| Status Code | Meaning | Example |
|-------------|---------|---------|
| `200` | Success | Record updated, records fetched |
| `201` | Created | New record created |
| `204` | No Content | Record deleted |
| `400` | Bad Request | Negative amount, invalid type |
| `401` | Unauthorized | Missing or invalid `user-id` |
| `403` | Forbidden | Viewer trying to create a record |
| `404` | Not Found | Updating/deleting a non-existent record |
| `422` | Validation Error | Missing required fields in request body |

---

## Running Tests

A comprehensive test suite with **37 tests** covers every feature:

```bash
pip install pytest httpx
pytest tests/ -v
```

### Test Coverage

| Area | Tests |
|------|-------|
| Root Endpoint | 1 |
| Authentication & RBAC | 6 |
| Read Records | 4 |
| Filter Records | 4 |
| Create Records | 5 |
| Update Records | 4 |
| Delete Records | 3 |
| Dashboard Analytics | 5 |
| Edge Cases & Validation | 5 |
| **Total** | **37** |

```
=================== 37 passed in 0.85s ===================
```

---

## Design Decisions

1. **SQLite over PostgreSQL/MySQL** — Eliminates setup friction. Reviewers can run it in seconds, not minutes.
2. **Raw SQL over ORM** — Intentionally chosen to demonstrate direct SQL proficiency (`GROUP BY`, `SUM()`, parameterized queries).
3. **Header-based mock auth over JWT** — Simplifies testing while still enforcing proper RBAC at every endpoint.
4. **Auto-seeded database** — No migration scripts or manual setup. The app is ready to test the moment it starts.
5. **Layered architecture** — Clean separation between routing (`routers/`), business logic (`services/`), data access (`database/`), and validation (`models/`).
