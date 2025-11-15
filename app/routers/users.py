from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

# --- 核心模块导入 ---
from app import crud, database
from app.auth import schemas as auth_schemas
from app.database import get_db
from app.services import email_service, permission_service
from app.dependencies import get_current_user
from app.schemas.profile import Profile, ProfileUpdate
from pydantic import BaseModel

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

@router.post("/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def create_user_signup(user: auth_schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Handles new user registration and sends a verification email.
    """
    if crud.get_user_by_email(db, email=user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    if crud.get_profile_by_ic_no(db, ic_no=user.ic_no):
        raise HTTPException(status_code=400, detail="IC number already registered")

    new_user = crud.create_user(db=db, user=user)
    
    verification_code = crud.create_verification_code(
        db, user_id=new_user.id, purpose="signup_verification"
    )
    
    email_sent_successfully = email_service.send_verification_email(
        recipient_email=new_user.email, code=verification_code
    )
    
    if not email_sent_successfully:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not send verification email. Please ensure the debug email server is running."
        )
    
    return {
        "message": "Signup successful! A verification code has been 'sent' (check your debug terminal).",
        "user_id": new_user.id
    }

@router.post("/verify-email", status_code=status.HTTP_200_OK)
def verify_email_with_code(user_id: int, code: str, db: Session = Depends(get_db)):
    """
    Verifies the email verification code provided by the user.
    """
    success = crud.verify_user_code(db, user_id=user_id, code=code, purpose="signup_verification")
    
    if not success:
        raise HTTPException(status_code=400, detail="Invalid or expired code")
        
    return {"message": "Email verified successfully! You can now log in."}

# --- Pydantic Schema for the /me endpoint response ---
class UserStatus(auth_schemas.UserOut):
    permissions: dict
    class Config:
        from_attributes = True

# --- GET /me endpoint ---
@router.get("/me", response_model=UserStatus)
def read_users_me(current_user: database.User = Depends(get_current_user)):
    """
    Get current logged-in user's essential data and their permissions.
    """
    from app.services import permission_service
    permissions = permission_service.get_user_permissions(current_user)

    # 关键修复：确保返回的数据包含所有 UserStatus 需要的字段
    response_data = {
        "id": current_user.id,
        "email": current_user.email,
        "user_type": current_user.user_type,
        "subscription_tier": current_user.subscription_tier, # <--- 添加这一行
        "permissions": permissions
    }
    
    return response_data

@router.get("/me/profile", response_model=Profile)
def read_user_profile(current_user: database.User = Depends(get_current_user)):
    return current_user.profile

@router.put("/me/profile", response_model=Profile)
def update_user_profile(
    profile_update: ProfileUpdate,
    current_user: database.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return crud.update_user_profile(db=db, user=current_user, profile_update=profile_update)

class PlanUpdate(BaseModel):
    plan: str

@router.put("/me/subscription", response_model=UserStatus)
def update_subscription(
    plan_update: PlanUpdate,
    current_user: database.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Updates the current user's subscription tier.
    """
    new_plan = plan_update.plan
    if new_plan not in ['free', 'tier_10', 'tier_15', 'tier_20']:
        raise HTTPException(status_code=400, detail="Invalid plan selected.")
        
    current_user.subscription_tier = new_plan
    db.commit()
    db.refresh(current_user)
    
    from app.services import permission_service
    permissions = permission_service.get_user_permissions(current_user)
    
    # 关键修复：确保返回的数据包含所有 UserStatus 需要的字段
    response_data = {
        "id": current_user.id,
        "email": current_user.email,
        "user_type": current_user.user_type,
        "subscription_tier": current_user.subscription_tier, # <--- 添加这一行
        "permissions": permissions
    }
    
    return response_data