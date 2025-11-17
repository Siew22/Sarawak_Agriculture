# app/routers/products.py (修复并优化顺序后)

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
import shutil
from pathlib import Path
import uuid

from app import database, crud
from app.dependencies import get_current_user
from app.schemas.product import Product, ProductCreate
from app.services import permission_service

router = APIRouter(prefix="/products", tags=["Products"])

# 【【【 核心修复 1: 把更具体的 /me 路由放在最前面 】】】
@router.get("/me", response_model=List[Product])
def read_my_products(
    current_user: database.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    """
    获取当前登录的 business user 的所有产品。
    """
    if current_user.user_type != 'business':
        return [] # Public 用户没有可售卖的产品
    return crud.get_products_by_seller(db=db, seller_id=current_user.id)

# 【【【 核心修复 2: 保持这个通用路由在后面 】】】
@router.get("/", response_model=List[Product])
def read_all_products(db: Session = Depends(database.get_db)):
    return crud.get_products(db=db)

# 创建一个依赖项，它能将Form数据解析为Pydantic模型
def get_product_create_form(
    name: str = Form(...),
    price: float = Form(...),
    description: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
) -> ProductCreate:
    return ProductCreate(name=name, price=price, description=description, location=location)

@router.post("/", response_model=Product, status_code=status.HTTP_201_CREATED)
async def create_new_product(
    image: UploadFile = File(...),
    product_data: ProductCreate = Depends(get_product_create_form),
    current_user: database.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.user_type != 'business':
        raise HTTPException(status_code=403, detail="Only business users can create products.")
    
    static_path = Path("static/products")
    static_path.mkdir(parents=True, exist_ok=True)
    
    unique_filename = f"{uuid.uuid4().hex}{Path(image.filename).suffix.lower()}"
    file_path = static_path / unique_filename
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        image_url = f"/static/products/{unique_filename}"
    except Exception:
        raise HTTPException(status_code=500, detail="Could not save product image.")
    
    return crud.create_user_product(
        db=db, 
        product=product_data, 
        user_id=current_user.id, 
        image_url=str(image_url).replace("\\", "/")
    )

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
    
    print(f"User {current_user.email} 'bought' product {product.name}")
    
    return {"message": f"You have successfully purchased '{product.name}'!"}