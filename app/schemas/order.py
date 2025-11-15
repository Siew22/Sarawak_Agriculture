# app/schemas/order.py (新建文件)

from pydantic import BaseModel, Field
from typing import List
from datetime import datetime
from .product import Product

# ---- 用于接收前端数据的模型 ----

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0) # 数量必须大于0

class OrderCreate(BaseModel):
    recipient_name: str
    recipient_phone: str
    shipping_address: str
    items: List[OrderItemCreate]
    # 我们只在前端做模拟验证，后端不需要关心银行卡号
    # payment_method: str
    # account_number: str

# ---- 用于从数据库返回数据的模型 ----

class OrderItem(BaseModel):
    id: int
    product_id: int
    quantity: int
    price_at_purchase: float
    product: Product # 嵌套Product信息，方便前端展示

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