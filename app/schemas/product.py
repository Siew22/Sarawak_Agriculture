from pydantic import BaseModel, Field
from typing import Optional

class ProductBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    location: Optional[str] = None

# app/schemas/product.py
class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    location: Optional[str] = None

class Product(ProductBase):
    id: int
    seller_id: int
    image_url: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True