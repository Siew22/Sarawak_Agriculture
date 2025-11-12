# app/routers/user.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import crud # <--- 绝对路径
from app.auth import schemas as auth_schemas # <--- 绝对路径
from app.database import get_db # <--- 绝对路径

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

@router.post("/", response_model=auth_schemas.UserOut)
def create_user(user: auth_schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)