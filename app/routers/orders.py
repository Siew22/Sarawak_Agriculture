# app/routers/orders.py (最终完整版)

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app import database, crud
from app.dependencies import get_current_user
from app.schemas.order import Order, OrderCreate

# APIRouter 不带 prefix，所有路径都是完整的
router = APIRouter(tags=["Orders"])

@router.post("/orders/", response_model=Order, status_code=status.HTTP_201_CREATED)
def create_new_order(
    order: OrderCreate,
    db: Session = Depends(database.get_db),
    current_user: database.User = Depends(get_current_user)
):
    """处理新的订单创建请求"""
    try:
        return crud.create_order(db=db, order_data=order, buyer_id=current_user.id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@router.get("/orders/my-orders", response_model=List[Order])
def read_my_orders(
    db: Session = Depends(database.get_db),
    current_user: database.User = Depends(get_current_user)
):
    """获取当前登录用户的所有历史订单"""
    return crud.get_orders_by_user(db=db, user_id=current_user.id)

# 【【【 确保这个函数存在 】】】
@router.get("/orders/sales", response_model=List[Order])
def read_my_sales(
    db: Session = Depends(database.get_db),
    current_user: database.User = Depends(get_current_user)
):
    """获取所有包含当前商家产品的订单"""
    if current_user.user_type != 'business':
        raise HTTPException(status_code=403, detail="Only business users can view sales.")
    return crud.get_sales_by_seller(db=db, seller_id=current_user.id)