# ====================================================================
#  app/crud.py (Final & Complete Version)
# ====================================================================
import random
import string
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import List, Optional

# --- 核心模块导入 (已修正) ---
from app import database
from app.auth import schemas as auth_schemas
# 从具体的 schema 文件中导入需要的 Pydantic 模型
from app.schemas.diagnosis import FullDiagnosisReport, PredictionResult, RiskAssessment
from app.schemas.product import ProductCreate
from app.schemas.post import PostCreate
from app.auth import security
from app.schemas.profile import ProfileUpdate
from app.schemas import order as order_schemas


# ====================================================================
#  User Related CRUD Operations
# ====================================================================

def get_user_by_email(db: Session, email: str) -> Optional[database.User]:
    """
    Retrieves a user from the database by their email.
    """
    return db.query(database.User).filter(database.User.email == email).first()

def get_profile_by_ic_no(db: Session, ic_no: str) -> Optional[database.Profile]:
    """
    Retrieves a profile from the database by its IC number.
    """
    if not ic_no:
        return None
    return db.query(database.Profile).filter(database.Profile.ic_no == ic_no).first()

def create_user(db: Session, user: auth_schemas.UserCreate) -> database.User:
    """
    Creates a new user and their profile in the database.
    """
    hashed_password = security.get_password_hash(user.password)
    
    db_user = database.User(
        email=user.email, 
        hashed_password=hashed_password, 
        user_type=user.user_type
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    db_profile = database.Profile(
        user_id=db_user.id,
        name=user.name,
        ic_no=user.ic_no,
        phone_number=user.phone_number,
        company_type=user.company_type
    )
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)

    return db_user

# ====================================================================
#  Verification Code CRUD Operations
# ====================================================================

def create_verification_code(db: Session, user_id: int, purpose: str) -> str:
    """
    Creates and stores a new verification code for a user.
    """
    db.query(database.VerificationCode).filter(
        database.VerificationCode.user_id == user_id,
        database.VerificationCode.purpose == purpose,
        database.VerificationCode.is_used == False
    ).delete()

    code = ''.join(random.choices(string.digits, k=6))
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    
    db_code = database.VerificationCode(
        user_id=user_id,
        code=code,
        purpose=purpose,
        expires_at=expires_at
    )
    db.add(db_code)
    db.commit()
    db.refresh(db_code)
    return code

def verify_user_code(db: Session, user_id: int, code: str, purpose: str) -> bool:
    """
    Verifies a user's code, marks it as used, and activates the user.
    """
    db_code = db.query(database.VerificationCode).filter(
        database.VerificationCode.user_id == user_id,
        database.VerificationCode.code == code,
        database.VerificationCode.purpose == purpose,
        database.VerificationCode.is_used == False,
        database.VerificationCode.expires_at > datetime.utcnow()
    ).first()

    if db_code:
        db_code.is_used = True
        
        user = db.query(database.User).filter(database.User.id == user_id).first()
        if user:
            user.is_active = True
            user.is_email_verified = True

        db.commit()
        return True
    return False

# ====================================================================
#  Diagnosis History CRUD Operations
# ====================================================================

def create_diagnosis_history(
    db: Session,
    user_id: int,
    report: FullDiagnosisReport,
    prediction: PredictionResult,
    risk: RiskAssessment,
    image_url: str
) -> database.DiagnosisHistory:
    """
    Creates and saves a new diagnosis history record.
    """
    db_history_entry = database.DiagnosisHistory(
        user_id=user_id,
        image_url=image_url,
        disease_name=prediction.disease,
        confidence=prediction.confidence,
        risk_level=risk.risk_level,
        report_title=report.title,
        report_summary=report.diagnosis_summary,
    )
    db.add(db_history_entry)
    db.commit()
    db.refresh(db_history_entry)
    return db_history_entry

def get_diagnosis_history_by_user(db: Session, user_id: int) -> List[database.DiagnosisHistory]:
    """
    Retrieves all diagnosis history for a specific user.
    """
    return db.query(database.DiagnosisHistory).filter(database.DiagnosisHistory.user_id == user_id).order_by(database.DiagnosisHistory.timestamp.desc()).all()

# ====================================================================
#  Product CRUD Operations
# ====================================================================

def create_user_product(db: Session, product: ProductCreate, user_id: int, image_url: str) -> database.Product:
    db_product = database.Product(**product.dict(), seller_id=user_id, image_url=image_url)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def get_products(db: Session, skip: int = 0, limit: int = 100) -> List[database.Product]:
    return db.query(database.Product).filter(database.Product.is_active == True).offset(skip).limit(limit).all()

def create_post(db: Session, post: PostCreate, user_id: int) -> database.Post:
    db_post = database.Post(content=post.content, owner_id=user_id)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

def get_posts(db: Session, skip: int = 0, limit: int = 100) -> List[database.Post]:
    return db.query(database.Post).order_by(database.Post.created_at.desc()).offset(skip).limit(limit).all()

# ====================================================================
#  Post CRUD Operations
# ====================================================================

def create_post(db: Session, post: PostCreate, user_id: int) -> database.Post:
    """
    Creates a new post for a user.
    """
    db_post = database.Post(content=post.content, owner_id=user_id)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

def get_posts(db: Session, skip: int = 0, limit: int = 100) -> List[database.Post]:
    """
    Retrieves a list of all posts, newest first.
    """
    return db.query(database.Post).order_by(database.Post.created_at.desc()).offset(skip).limit(limit).all()

def update_user_profile(db: Session, user: database.User, profile_update: ProfileUpdate):
    profile = user.profile
    update_data = profile_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(profile, key, value)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile

def create_comment(db: Session, content: str, post_id: int, user_id: int) -> database.Comment:
    db_comment = database.Comment(content=content, post_id=post_id, owner_id=user_id)
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment

def get_comments_for_post(db: Session, post_id: int) -> List[database.Comment]:
    return db.query(database.Comment).filter(database.Comment.post_id == post_id).order_by(database.Comment.created_at.asc()).all()

def create_order(db: Session, order_data: order_schemas.OrderCreate, buyer_id: int) -> database.Order:
    total_amount = 0
    order_items_to_create = []

    for item_data in order_data.items:
        product = db.query(database.Product).filter(database.Product.id == item_data.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product with id {item_data.product_id} not found.")
        
        price_at_purchase = product.price
        total_amount += price_at_purchase * item_data.quantity
        
        order_items_to_create.append(database.OrderItem(
            product_id=item_data.product_id,
            quantity=item_data.quantity,
            price_at_purchase=price_at_purchase
        ))

    db_order = database.Order(
        buyer_id=buyer_id,
        recipient_name=order_data.recipient_name,
        recipient_phone=order_data.recipient_phone,
        shipping_address=order_data.shipping_address,
        total_amount=total_amount
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)

    for item in order_items_to_create:
        item.order_id = db_order.id
        db.add(item)
    
    db.commit()
    db.refresh(db_order)
    return db_order

def get_orders_by_user(db: Session, user_id: int) -> List[database.Order]:
    return db.query(database.Order).filter(database.Order.buyer_id == user_id).order_by(database.Order.created_at.desc()).all()

# --- (新) 根据卖家ID获取产品 ---
def get_products_by_seller(db: Session, seller_id: int) -> List[database.Product]:
    return db.query(database.Product).filter(database.Product.seller_id == seller_id).order_by(database.Product.id.desc()).all()