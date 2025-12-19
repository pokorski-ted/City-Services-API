# app/db/init_db.py
# Purpose: Create tables in the SQLite database.
# Equivalent idea to EF Core EnsureCreated / migrations (without migrations yet).

from app.db.session import engine
from app.db.models import Base


def init_db() -> None:
    # Creates tables if they do not exist
    Base.metadata.create_all(bind=engine)
