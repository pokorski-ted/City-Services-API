# City Services API — FastAPI

A CRUD REST API built with FastAPI, SQLAlchemy, and SQLite. Implements layered architecture (routes → services → data), Dependency Injection, validation via Pydantic, and automated tests.

## Stack
- **Python / FastAPI** (OpenAPI + Swagger UI)
- **SQLAlchemy ORM** + **SQLite**
- **Dependency Injection** via `Depends()`
- **Pydantic** request validation
- **Pytest** automated tests (API + service)

## Run
```bash
pip install -r requirements.txt
python -m uvicorn api_fastapi:app --reload --port 8000

API Docs

Swagger UI: http://localhost:8000/docs

OpenAPI spec: http://localhost:8000/openapi.json

Endpoints

GET /products

GET /products/{id}

POST /products

PUT /products/{id}

DELETE /products/{id}

Tests
pytest -q

Local database file: city_services.db

Tests use an isolated SQLite DB created/dropped per test run.
