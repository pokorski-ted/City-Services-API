# app/db/deps.py
# Purpose: Dependency that provides a DB session per request.
# Equivalent to "scoped DbContext" lifetime in ASP.NET Core.

from typing import Generator
from sqlalchemy.orm import Session
from app.db.session import SessionLocal

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI will call this per request.
    It yields a DB session and guarantees it is closed after the request completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
