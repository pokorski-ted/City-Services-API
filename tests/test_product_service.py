# tests/test_product_service.py
# Purpose:
# Unit tests for ProductService (no HTTP).
# Faster and more targeted than API tests.

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base
from app.services.product_service import ProductService
from app.models.product import ProductCreate


def test_service_create_and_get_all():
    # Create a temporary SQLite DB for this unit test
    engine = create_engine("sqlite:///./test_service.db", connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Inject the DB session into the service (DI pattern)
        service = ProductService(db)

        created = service.create(ProductCreate(name="Service Mango"))
        assert created.id > 0
        assert created.name == "Service Mango"

        all_products = service.get_all()
        assert any(p.name == "Service Mango" for p in all_products)
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
