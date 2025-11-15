# app/schemas/order.py (新建)
from pydantic import BaseModel
from typing import List
from datetime import datetime
from .product import Product

class OrderItemBase(BaseModel):
    product_id: int
    quantity: int

class OrderCreate(BaseModel):
    recipient_name: str
    recipient_phone: str
    shipping_address: str
    items: List[OrderItemBase]

class OrderItem(OrderItemBase):
    id: int
    price_at_purchase: float
    product: Product

    class Config:
        from_attributes = True

class Order(BaseModel):
    id: int
    buyer_id: int
    recipient_name: str
    recipient_phone: str
    shipping_address: str
    total_amount: float
    status: str
    created_at: datetime
    items: List[OrderItem]

    class Config:
        from_attributes = True