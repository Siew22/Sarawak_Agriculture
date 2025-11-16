# app/routers/token.py (最终修复版)

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app import crud, database
from app.auth import schemas as auth_schemas
from app.auth import security
from app.database import get_db

# 【【【 核心修复 】】】
# 我们给这个路由组添加一个明确的前缀 /auth
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

# 路由路径现在是 /token，结合上面的前缀，完整的地址是 POST /auth/token
@router.post("/token", response_model=auth_schemas.Token)
async def login_for_access_token(
    db: Session = Depends(get_db), 
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    Handles user login and returns a JWT access token.
    """
    user = crud.get_user_by_email(db, email=form_data.username)
    
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user. Please verify your email first.",
        )
    
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    access_token = security.create_access_token(
        data={"sub": user.email, "id": user.id, "type": user.user_type}, 
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}