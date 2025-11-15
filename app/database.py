# ====================================================================
#  app/database.py (Final & Complete Version)
# ====================================================================
from sqlalchemy import (create_engine, Column, Integer, String, Boolean, 
                        Float, DateTime, Text, ForeignKey)
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from urllib.parse import quote_plus
import datetime

from app.config import settings

# --- Database Connection Setup ---
encoded_password = quote_plus(settings.DB_PASSWORD)
SQLALCHEMY_DATABASE_URL = (
    f"mysql+pymysql://{settings.DB_USER}:{encoded_password}@"
    f"{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- ORM Models ---

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    user_type = Column(String(50), nullable=False, default='public') # 'public' or 'business'
    
    is_active = Column(Boolean, default=False)
    is_email_verified = Column(Boolean, default=False)
    
    # Subscription tier field
    subscription_tier = Column(String(50), default='free', nullable=False) # 'free', 'tier_10', 'tier_20'
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    profile = relationship("Profile", back_populates="owner", uselist=False)
    diagnoses = relationship("DiagnosisHistory", back_populates="user")
    products = relationship("Product", back_populates="seller")
    api_usage = relationship("ApiUsageLog", back_populates="user")

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    name = Column(String(255), index=True)
    ic_no = Column(String(100), unique=True, nullable=True)
    phone_number = Column(String(50), unique=True, nullable=True)
    
    organization = Column(String(255), nullable=True)
    company_type = Column(String(100), nullable=True)
    halal_cert_url = Column(String(512), nullable=True)
    business_license_url = Column(String(512), nullable=True)
    
    owner = relationship("User", back_populates="profile")

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

# --- 商品模型 (已升级) ---
class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    price = Column(Float, nullable=False)
    location = Column(String(255))
    image_url = Column(String(512))
    is_active = Column(Boolean, default=True) # 是否上架
    
    seller = relationship("User", back_populates="products")

# --- (新) 订单模型 ---
class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey("users.id"))
    
    # 收货信息
    recipient_name = Column(String(255), nullable=False)
    recipient_phone = Column(String(50), nullable=False)
    shipping_address = Column(Text, nullable=False)
    
    total_amount = Column(Float, nullable=False)
    status = Column(String(50), default="Pending", nullable=False) # e.g., Pending, Sorting, Delivering, Completed
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    buyer = relationship("User")
    items = relationship("OrderItem", back_populates="order")

# --- (新) 订单商品项模型 ---
class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, default=1)
    price_at_purchase = Column(Float, nullable=False) # 记录购买时的价格
    
    order = relationship("Order", back_populates="items")
    product = relationship("Product")

class VerificationCode(Base):
    __tablename__ = "verification_codes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    code = Column(String(10), index=True, nullable=False)
    purpose = Column(String(50), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ApiUsageLog(Base):
    __tablename__ = "api_usage_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    endpoint = Column(String(255), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    user = relationship("User", back_populates="api_usage")

# --- (新) 社交帖子模型 ---
class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    owner = relationship("User")
    comments = relationship("Comment", back_populates="post")

# --- (新) 评论模型 ---
class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"))
    post_id = Column(Integer, ForeignKey("posts.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    owner = relationship("User")
    post = relationship("Post", back_populates="comments")

# --- Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()