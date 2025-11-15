# app/routers/products.py (完整版)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app import database, crud
from app.dependencies import get_current_user
from app.schemas.product import Product, ProductCreate
from app.services import permission_service

router = APIRouter(prefix="/products", tags=["Products"])

@router.get("/", response_model=List[Product])
def read_all_products(db: Session = Depends(database.get_db)):
    return crud.get_products(db=db)

@router.post("/{product_id}/buy", response_model=Dict[str, Any])
def buy_product(
    product_id: int,
    db: Session = Depends(database.get_db),
    current_user: database.User = Depends(get_current_user)
):
    permissions = permission_service.get_user_permissions(current_user)
    if not permissions.get('can_shop'):
        raise HTTPException(status_code=403, detail="Your plan does not allow shopping.")
    
    product = db.query(database.Product).filter(database.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    
    # 在真实应用中，这里会接入支付逻辑
    # 现在我们只记录一个购买事件
    print(f"User {current_user.email} 'bought' product {product.name}")
    
    return {"message": f"You have successfully purchased '{product.name}'!"}

# Business user 的创建产品API保持不变
@router.post("/create", response_model=Product, status_code=status.HTTP_201_CREATED)
def create_new_product(
    product: ProductCreate,
    current_user: database.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.user_type != 'business':
        raise HTTPException(status_code=403, detail="Only business users can create products.")
    return crud.create_user_product(db=db, product=product, user_id=current_user.id)