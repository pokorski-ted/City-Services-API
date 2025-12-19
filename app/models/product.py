# app/models/product.py
# Purpose: Pydantic schemas (request/response models) for Product.
# FastAPI uses these for input validation + Swagger/OpenAPI generation.

from pydantic import BaseModel, Field

# Product models. Create name and id fields.
class ProductCreate(BaseModel):
    # Request model for POST/PUT
    # Field(...) => required
    name: str = Field(..., min_length=2, max_length=50)

class Product(ProductCreate):
    # Response model includes server-generated id
    id: int
