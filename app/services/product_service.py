# app/services/product_service.py
# Purpose: Business logic for Products (CRUD).
# Now uses SQLite via SQLAlchemy Session (like EF Core DbContext).

from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.product import ProductCreate, Product
from app.db.models import ProductDB


class ProductService:
    def __init__(self, db: Session) -> None:
        # Store the DB session for this request
        self._db = db

    def get_all(self) -> List[Product]:
        # Query all rows from the products table
        rows = self._db.query(ProductDB).all()

        # Convert DB models -> API models (Pydantic)
        return [Product(id=r.id, name=r.name) for r in rows]

    def get_by_id(self, product_id: int) -> Optional[Product]:
        row = self._db.query(ProductDB).filter(ProductDB.id == product_id).first()
        if row is None:
            return None
        return Product(id=row.id, name=row.name)

    def create(self, request: ProductCreate) -> Product:
        # Create the DB row
        row = ProductDB(name=request.name)
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)  # Loads generated id from DB

        return Product(id=row.id, name=row.name)
    
    def update(self, product_id: int, request: ProductCreate) -> Optional[Product]:
        """
        Update an existing product.
        Returns updated Product or None if not found.
        """
        row = self._db.query(ProductDB).filter(ProductDB.id == product_id).first()
        if row is None:
            return None

        row.name = request.name
        self._db.commit()
        self._db.refresh(row)

        return Product(id=row.id, name=row.name)

    def delete(self, product_id: int) -> bool:
        """
        Delete an existing product.
        Returns True if deleted, False if not found.
        """
        row = self._db.query(ProductDB).filter(ProductDB.id == product_id).first()
        if row is None:
            return False

        self._db.delete(row)
        self._db.commit()
        return True
