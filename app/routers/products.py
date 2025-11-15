# app/routers/products.py (新建)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app import database, crud
from app.main import get_current_user
from app.schemas.product import Product, ProductCreate # 假设的 Schema
from app.services import permission_service

router = APIRouter(prefix="/products", tags=["Products"])

@router.post("/", response_model=Product)
def create_product(
    product: ProductCreate,
    current_user: database.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.user_type != 'business':
        raise HTTPException(status_code=403, detail="Only business users can create products.")
    return crud.create_user_product(db=db, product=product, user_id=current_user.id)

@router.get("/", response_model=List[Product])
def read_products(db: Session = Depends(database.get_db)):
    return crud.get_products(db=db)