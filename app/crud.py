# app/crud.py
from sqlalchemy.orm import Session
from app import database # <--- 改为导入 database
from app.auth import schemas as auth_schemas
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_user_by_email(db: Session, email: str):
    # 使用 database.User
    return db.query(database.User).filter(database.User.email == email).first()

def create_user(db: Session, user: auth_schemas.UserCreate):
    # 将密码编码为 bytes，然后截断到72字节
    truncated_password = user.password.encode('utf-8')[:72]
    
    # 对截断后的密码进行哈希
    hashed_password = pwd_context.hash(truncated_password)
    
    db_user = database.User(
        email=user.email, 
        hashed_password=hashed_password, 
        user_type=user.user_type
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # 使用全名 sql_models.Profile
    db_profile = database.Profile(
        user_id=db_user.id,
        name=user.name,
        ic_no=user.ic_no,
        phone_number=user.phone_number,
        organization=user.organization,
        company_type=user.company_type
    )
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)

    return db_user