from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError 
from typing import Dict, Any, Optional, List

# --- 核心模块导入 ---
from app import crud, database
from app.auth import schemas as auth_schemas
from app.database import get_db
from app.services import email_service, permission_service
from app.dependencies import get_current_user
from app.schemas.profile import Profile, ProfileUpdate
from pydantic import BaseModel
from fastapi import Response # <-- 确保在文件顶部导入 Response
from fastapi.responses import JSONResponse # <-- 确保导入 JSONResponse

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

class PublicProfile(BaseModel):
    id: int
    name: str
    avatar_url: Optional[str] = None
    user_type: str
    
    class Config:
        from_attributes = True

@router.get("/{user_id}/profile", response_model=PublicProfile)
def get_public_user_profile(user_id: int, db: Session = Depends(database.get_db)):
    user = db.query(database.User).filter(database.User.id == user_id).first()
    if not user or not user.profile:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Pydantic 会自动从 profile 中提取 name 和 avatar_url
    response_data = user.profile
    response_data.id = user.id
    response_data.user_type = user.user_type
    return response_data

@router.options("/", include_in_schema=False)
async def options_users():
    return JSONResponse(content={"detail": "OK"}, headers={
        "Access-Control-Allow-Origin": "*", # 简单起见，我们允许所有来源
        "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
    })

@router.post("/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def create_user_signup(user: auth_schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Handles new user registration and sends a verification email.
    """
    # 2. 我们将把预先检查的代码移到 try...except 块中
    try:
        # 在创建用户前，先检查邮箱是否已存在
        if crud.get_user_by_email(db, email=user.email):
            raise HTTPException(status_code=400, detail="Email already registered")

        new_user = crud.create_user(db=db, user=user)
        
        verification_code = crud.create_verification_code(
            db, user_id=new_user.id, purpose="signup_verification"
        )
        
        email_service.send_verification_email(
            recipient_email=new_user.email, code=verification_code
        )
        
        return {
            "message": "Signup successful! A verification code has been 'sent' (check your debug terminal).",
            "user_id": new_user.id
        }
    # 3. 【【【 核心修复 】】】
    # 捕获数据库完整性错误
    except IntegrityError as e:
        db.rollback() # 回滚失败的事务
        error_message = str(e.orig)
        # 根据数据库返回的错误信息，判断是哪个字段重复了
        if "users.email" in error_message:
            raise HTTPException(status_code=400, detail="Email already registered")
        elif "profiles.ic_no" in error_message:
            raise HTTPException(status_code=400, detail="IC number already registered")
        elif "profiles.phone_number" in error_message:
            raise HTTPException(status_code=400, detail="Phone number already registered")
        else:
            # 如果是其他未知的唯一性冲突，返回一个通用错误
            raise HTTPException(status_code=500, detail="A database integrity error occurred.")

@router.post("/verify-email", status_code=status.HTTP_200_OK)
def verify_email_with_code(
    user_id: int = Query(...), 
    code: str = Query(...), 
    db: Session = Depends(get_db)
):
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
    # 【【【 核心修复 】】】
    try:
        if not current_user:
            # 理论上 get_current_user 依赖会处理，但这里加一道保险
            raise HTTPException(status_code=401, detail="User not found or invalid token")

        permissions = permission_service.get_user_permissions(current_user)
        
        # 确保所有需要的字段都存在
        response_data = {
            "id": current_user.id,
            "email": current_user.email,
            "user_type": current_user.user_type,
            "subscription_tier": current_user.subscription_tier,
            "permissions": permissions
        }
        
        return response_data
    except Exception as e:
        # 捕获任何可能的意外错误，并返回一个标准的 500 错误
        print(f"ERROR in /users/me: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while fetching user profile.")

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

class UserForChat(BaseModel):
    id: int
    profile: Profile

    class Config:
        from_attributes = True

@router.get("/", response_model=List[UserForChat])
def read_all_users(
    db: Session = Depends(database.get_db),
    current_user: database.User = Depends(get_current_user)
):
    """获取所有用户列表以供聊天选择 (排除当前用户)"""
    users = db.query(database.User).filter(database.User.id != current_user.id).all()
    return users