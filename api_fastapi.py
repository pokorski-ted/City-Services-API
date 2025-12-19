# api_fastapi.py
# Purpose: FastAPI entrypoint + route definitions.
# Routes should focus on HTTP concerns and delegate business logic to services.

from fastapi import FastAPI, Depends, HTTPException
from typing import List

from app.models.product import ProductCreate, Product
from app.services.product_service import ProductService

from sqlalchemy.orm import Session
from app.db.deps import get_db

# Create the FastAPI app (also powers /docs via OpenAPI)
app = FastAPI(title="City Services API")

from app.db.init_db import init_db

# Create DB tables on startup (simple dev approach)
init_db()


def get_product_service(db: Session = Depends(get_db)) -> ProductService:
    # For each request, FastAPI gives us a fresh DB session,
    # and we create a service that uses that session.
    return ProductService(db)


@app.get("/health")
def health():
    # Simple liveness endpoint
    return {"status": "ok"}


@app.get("/products", response_model=List[Product])
def get_products(service: ProductService = Depends(get_product_service)):
    # Route (HTTP layer): calls into service (business layer)
    return service.get_all()


@app.get("/products/{product_id}", response_model=Product)
def get_product(product_id: int, service: ProductService = Depends(get_product_service)):
    # Get one product; return 404 if not found
    product = service.get_by_id(product_id)

    if product is None:
        raise HTTPException(status_code=404, detail=f"No product found with id={product_id}")

    return product


@app.post("/products", response_model=Product, status_code=201)
def create_product(request: ProductCreate, service: ProductService = Depends(get_product_service)):
    # Create a product from validated request data
    return service.create(request)

@app.put("/products/{product_id}", response_model=Product)
def update_product(
    product_id: int,
    request: ProductCreate,
    service: ProductService = Depends(get_product_service),
):
    # Ask service to update; return 404 if not found
    updated = service.update(product_id, request)
    if updated is None:
        raise HTTPException(status_code=404, detail=f"No product found with id={product_id}")
    return updated


@app.delete("/products/{product_id}", status_code=200)
def delete_product(
    product_id: int,
    service: ProductService = Depends(get_product_service),
):
    deleted = service.delete(product_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"No product found with id={product_id}")

    # Return a friendly message (optional)
    return {"message": f"Deleted product id={product_id}"}