# ====================================================================
#  Part 1: Imports - 导入所有需要的工具
# ====================================================================
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from urllib.parse import quote_plus
import datetime

from .config import settings

# ====================================================================
#  Part 2: Database Connection - 数据库连接设置
# ====================================================================

# 手动构建并编码数据库URL，以处理密码中的特殊字符
encoded_password = quote_plus(settings.DB_PASSWORD)
SQLALCHEMY_DATABASE_URL = (
    f"mysql+pymysql://{settings.DB_USER}:{encoded_password}@"
    f"{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ====================================================================
#  Part 3: ORM Models - 所有数据库表的定义
#  (之前在 sql_models.py 中的内容)
# ====================================================================

# --- 用户模型 ---
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    user_type = Column(String(50), nullable=False, default='public')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    profile = relationship("Profile", back_populates="owner", uselist=False)
    diagnoses = relationship("DiagnosisHistory", back_populates="user")
    products = relationship("Product", back_populates="seller")

# --- 用户详细信息模型 ---
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
    seller_id = Column(Integer, ForeignKey("users.id"))

    name = Column(String(255), nullable=False)
    description = Column(Text)
    location = Column(String(255))
    price = Column(Float, nullable=False)
    image_url = Column(String(512))
    quantity_available = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    seller = relationship("User", back_populates="products")

# ====================================================================
#  Part 4: Dependency - 数据库会话依赖注入
# ====================================================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()