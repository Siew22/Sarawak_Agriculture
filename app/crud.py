# app/crud.py (最终完整版 v2)

import random
import string
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from app import database
from app.auth import schemas as auth_schemas
from app.schemas.diagnosis import FullDiagnosisReport, PredictionResult, RiskAssessment
from app.schemas.product import ProductCreate
from app.schemas.post import PostCreate, CommentCreate
from app.auth import security
from app.schemas.profile import ProfileUpdate
from app.schemas import order as order_schemas
from fastapi import HTTPException

# ====================================================================
#  User Related CRUD Operations
# ====================================================================

def get_user_by_email(db: Session, email: str) -> Optional[database.User]:
    return db.query(database.User).filter(database.User.email == email).first()

def create_user(db: Session, user: auth_schemas.UserCreate) -> database.User:
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
        user_id=db_user.id, name=user.name, ic_no=user.ic_no,
        phone_number=user.phone_number, organization=user.organization,
        company_type=user.company_type
    )
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_user

def update_user_profile(db: Session, user: database.User, profile_update: ProfileUpdate):
    profile = user.profile
    update_data = profile_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(profile, key, value)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile

# ====================================================================
#  Verification Code CRUD Operations
# ====================================================================

def create_verification_code(db: Session, user_id: int, purpose: str) -> str:
    db.query(database.VerificationCode).filter(
        database.VerificationCode.user_id == user_id,
        database.VerificationCode.purpose == purpose,
        database.VerificationCode.is_used == False
    ).delete()
    code = ''.join(random.choices(string.digits, k=6))
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    db_code = database.VerificationCode(user_id=user_id, code=code, purpose=purpose, expires_at=expires_at)
    db.add(db_code)
    db.commit()
    db.refresh(db_code)
    return code

def verify_user_code(db: Session, user_id: int, code: str, purpose: str) -> bool:
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
#  Diagnosis & History CRUD
# ====================================================================

def create_diagnosis_history(db: Session, user_id: int, report: FullDiagnosisReport, prediction: PredictionResult, risk: RiskAssessment, image_url: str) -> database.DiagnosisHistory:
    db_history_entry = database.DiagnosisHistory(
        user_id=user_id, image_url=image_url, disease_name=prediction.disease,
        confidence=prediction.confidence, risk_level=risk.risk_level,
        report_title=report.title, report_summary=report.diagnosis_summary,
    )
    db.add(db_history_entry)
    db.commit()
    db.refresh(db_history_entry)
    return db_history_entry

def get_diagnosis_history_by_user(db: Session, user_id: int) -> List[database.DiagnosisHistory]:
    return db.query(database.DiagnosisHistory).filter(database.DiagnosisHistory.user_id == user_id).order_by(database.DiagnosisHistory.timestamp.desc()).all()

# ====================================================================
#  Product CRUD
# ====================================================================

def create_user_product(db: Session, product: ProductCreate, user_id: int, image_url: str) -> database.Product:
    db_product = database.Product(**product.model_dump(), seller_id=user_id, image_url=image_url)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def get_products(db: Session, skip: int = 0, limit: int = 100) -> List[database.Product]:
    return db.query(database.Product).filter(database.Product.is_active == True).offset(skip).limit(limit).all()

def get_products_by_seller(db: Session, seller_id: int) -> List[database.Product]:
    return db.query(database.Product).filter(database.Product.seller_id == seller_id).order_by(database.Product.id.desc()).all()

# ====================================================================
#  Post & Comment CRUD
# ====================================================================

def create_post(db: Session, user_id: int, content: str, image_url: Optional[str] = None, location: Optional[str] = None) -> database.Post:
    db_post = database.Post(content=content, owner_id=user_id, image_url=image_url, location=location)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

def get_posts(db: Session, skip: int = 0, limit: int = 100) -> List[database.Post]:
    return db.query(database.Post).options(
        joinedload(database.Post.owner).joinedload(database.User.profile),
        joinedload(database.Post.comments).joinedload(database.Comment.owner),
        joinedload(database.Post.likes)
    ).order_by(database.Post.created_at.desc()).offset(skip).limit(limit).all()

def create_comment(db: Session, content: str, post_id: int, user_id: int) -> database.Comment:
    db_comment = database.Comment(content=content, post_id=post_id, owner_id=user_id)
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment

# ====================================================================
#  Order CRUD
# ====================================================================

def create_order(db: Session, order_data: order_schemas.OrderCreate, buyer_id: int) -> database.Order:
    total_amount = 0.0
    order_items_to_create = []
    for item_data in order_data.items:
        product = db.query(database.Product).filter(database.Product.id == item_data.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product with id {item_data.product_id} not found.")
        price_at_purchase = product.price
        total_amount += price_at_purchase * item_data.quantity
        order_items_to_create.append(database.OrderItem(
            product_id=item_data.product_id, quantity=item_data.quantity,
            price_at_purchase=price_at_purchase
        ))
    db_order = database.Order(
        buyer_id=buyer_id, recipient_name=order_data.recipient_name,
        recipient_phone=order_data.recipient_phone, shipping_address=order_data.shipping_address,
        total_amount=total_amount, status="Processing"
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
    return db.query(database.Order).options(
        joinedload(database.Order.items).joinedload(database.OrderItem.product)
    ).filter(database.Order.buyer_id == user_id).order_by(database.Order.created_at.desc()).all()

def get_sales_by_seller(db: Session, seller_id: int) -> List[database.Order]:
    order_ids_query = db.query(database.OrderItem.order_id).join(database.Product).filter(
        database.Product.seller_id == seller_id
    ).distinct()
    order_ids = [item[0] for item in order_ids_query.all()]
    if not order_ids:
        return []
    return db.query(database.Order).options(
        joinedload(database.Order.items).joinedload(database.OrderItem.product)
    ).filter(database.Order.id.in_(order_ids)).order_by(database.Order.created_at.desc()).all()

# ====================================================================
#  Chat CRUD
# ====================================================================

def create_chat_message(db: Session, sender_id: int, recipient_id: int, content: str) -> database.ChatMessage:
    db_message = database.ChatMessage(sender_id=sender_id, recipient_id=recipient_id, content=content)
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def get_chat_history(db: Session, user1_id: int, user2_id: int) -> List[database.ChatMessage]:
    return db.query(database.ChatMessage).filter(
        ((database.ChatMessage.sender_id == user1_id) & (database.ChatMessage.recipient_id == user2_id)) |
        ((database.ChatMessage.sender_id == user2_id) & (database.ChatMessage.recipient_id == user1_id))
    ).order_by(database.ChatMessage.timestamp.asc()).all()