import random
import string
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app import database
from app.auth import schemas as auth_schemas
from app.auth import security

# ====================================================================
#  User Related CRUD Operations
# ====================================================================

def get_user_by_email(db: Session, email: str):
    """
    Retrieves a user from the database by their email.
    """
    return db.query(database.User).filter(database.User.email == email).first()

def get_profile_by_ic_no(db: Session, ic_no: str):
    """
    Retrieves a profile from the database by its IC number.
    """
    if not ic_no:
        return None
    return db.query(database.Profile).filter(database.Profile.ic_no == ic_no).first()

def create_user(db: Session, user: auth_schemas.UserCreate):
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
#  Verification Code Related CRUD Operations
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