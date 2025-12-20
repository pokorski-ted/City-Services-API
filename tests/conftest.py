# tests/conftest.py
# Purpose:
# - Create an isolated test database for EACH test
# - Override FastAPI dependency injection so the API uses the test DB
# - Provide a TestClient to call your API endpoints (no real server needed)

import sys
import os

# Add project root to PYTHONPATH so pytest can import api_fastapi.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api_fastapi import app  # Your FastAPI app instance
from app.db.models import Base
from app.db.deps import get_db


@pytest.fixture(scope="function")
def client():
    # Use a dedicated SQLite file for tests to avoid collisions on Windows
    TEST_DB_FILE = "./test_city_services.db"
    TEST_DB_URL = f"sqlite:///{TEST_DB_FILE}"

    # Create a new SQLAlchemy engine for the test DB
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})

    # Build a session factory bound to the test engine
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create tables fresh for this test
    Base.metadata.create_all(bind=engine)

    # Dependency override:
    # Whenever FastAPI asks for get_db(), give it a Session from the test DB.
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Create a test client (acts like a browser/Postman but in code)
    with TestClient(app) as c:
        yield c

    # Cleanup after test
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)

    # Remove the test DB file so each test starts clean
    try:
        os.remove(TEST_DB_FILE)
    except OSError:
        pass
