# app/models.py

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import relationship
from .database import Base
import datetime

# --- 用户模型 ---
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # 'public' 或 'business'
    user_type = Column(String(50), nullable=False, default='public')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # 关联到Profile
    profile = relationship("Profile", back_populates="owner", uselist=False)
    # 关联到该用户的所有诊断历史
    diagnoses = relationship("DiagnosisHistory", back_populates="user")
    # 关联到该用户发布的商品 (仅限business user)
    products = relationship("Product", back_populates="seller")

# --- 用户详细信息模型 ---
class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    name = Column(String(255), index=True)
    ic_no = Column(String(100), unique=True, nullable=True)
    phone_number = Column(String(50), unique=True, nullable=True)
    
    # Business-only fields
    organization = Column(String(255), nullable=True)
    company_type = Column(String(100), nullable=True)
    halal_cert_url = Column(String(512), nullable=True)
    business_license_url = Column(String(512), nullable=True)
    
    owner = relationship("User", back_populates="profile")


# --- AI诊断历史模型 ---
class DiagnosisHistory(Base):
    __tablename__ = "diagnosis_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    image_url = Column(String(512), nullable=False)
    disease_name = Column(String(255))
    confidence = Column(Float)
    risk_level = Column(String(50))
    report_title = Column(Text)
    report_summary = Column(Text)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="diagnoses")

# --- 商品模型 (电商功能) ---
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("users.id")) # 必须是 business user

    name = Column(String(255), nullable=False)
    description = Column(Text)
    location = Column(String(255))
    price = Column(Float, nullable=False)
    image_url = Column(String(512))
    quantity_available = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    seller = relationship("User", back_populates="products")