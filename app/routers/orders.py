# app/routers/orders.py (新建)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app import database, crud
from app.dependencies import get_current_user
from app.schemas.order import Order, OrderCreate # 我们将创建这些 Schema

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.post("/", response_model=Order, status_code=status.HTTP_201_CREATED)
def create_new_order(
    order: OrderCreate,
    current_user: database.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    return crud.create_order(db=db, order_data=order, buyer_id=current_user.id)

@router.get("/me", response_model=List[Order])
def read_my_orders(
    current_user: database.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    return crud.get_orders_by_user(db=db, user_id=current_user.id)