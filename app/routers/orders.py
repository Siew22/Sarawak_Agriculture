# app/routers/orders.py (新建文件)

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app import database, crud
from app.dependencies import get_current_user
from app.schemas.order import Order, OrderCreate

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.post("/", response_model=Order, status_code=status.HTTP_201_CREATED)
def create_new_order(
    order: OrderCreate,
    db: Session = Depends(database.get_db),
    current_user: database.User = Depends(get_current_user)
):
    """处理新的订单创建请求"""
    # 在真实应用中，这里会先去支付网关验证支付是否成功
    # 我们这里直接调用crud函数创建订单
    try:
        return crud.create_order(db=db, order_data=order, buyer_id=current_user.id)
    except HTTPException as e:
        raise e
    except Exception as e:
        # 捕获其他未知错误
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@router.get("/my-orders", response_model=List[Order])
def read_my_orders(
    db: Session = Depends(database.get_db),
    current_user: database.User = Depends(get_current_user)
):
    """获取当前登录用户的所有历史订单"""
    return crud.get_orders_by_user(db=db, user_id=current_user.id)