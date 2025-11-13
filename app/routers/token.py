# app/routers/token.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app import crud # <--- 绝对路径
from app.auth import schemas as auth_schemas # <--- 绝对路径
from app.auth import security # <--- 绝对路径
from app.database import get_db # <--- 绝对路径
from app import database

router = APIRouter(tags=["Authentication"])

@router.post("/token", response_model=auth_schemas.Token)
async def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    # ... (用户验证逻辑保持不变) ...
    user = crud.get_user_by_email(db, email=form_data.username) # 在您的代码中，crud.authenticate_user 可能是这个
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(...)
    if not user.is_active: # 增加检查，确保用户已验证邮箱
        raise HTTPException(status_code=403, detail="Please verify your email first")
    
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # --- 关键改动：在Token中加入更多用户信息 ---
    access_token = security.create_access_token(
        data={"sub": user.email, "id": user.id, "type": user.user_type}, 
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}