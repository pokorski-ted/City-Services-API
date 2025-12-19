# app/db/models.py
# Purpose: SQLAlchemy ORM models (database tables).
# Equivalent to EF Core entity classes.

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String


class Base(DeclarativeBase):
    # Base class for all ORM models
    pass


class ProductDB(Base):
    # Table name in SQLite
    __tablename__ = "products"

    # Columns
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
