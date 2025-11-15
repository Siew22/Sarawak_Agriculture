# app/routers/products.py (完整版)
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form, Body
from typing import Optional 
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app import database, crud
from app.dependencies import get_current_user
from app.schemas.product import Product, ProductCreate
from app.services import permission_service
import shutil
from pathlib import Path
import uuid

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
    product_data: ProductCreate = Depends(get_product_create_form), # <--- 使用依赖项
    current_user: database.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.user_type != 'business':
        raise HTTPException(status_code=403, detail="Only business users can create products.")
    
    # --- File Upload Logic ---
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
    
    # 现在 product_data 已经是一个验证过的 Pydantic 模型
    return crud.create_user_product(
        db=db, 
        product=product_data, 
        user_id=current_user.id, 
        image_url=image_url
    )

# --- 关键修复：为 "my products" 添加一个明确的 /me 路径 ---
@router.get("/me", response_model=List[Product])
def read_my_products(
    current_user: database.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    """
    Retrieve all products for the current logged-in business user.
    """
    if current_user.user_type != 'business':
        return [] # Public users have no products to sell
    return crud.get_products_by_seller(db=db, seller_id=current_user.id)