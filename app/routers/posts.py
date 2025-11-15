# app/routers/posts.py (新建)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app import database, crud
from app.main import get_current_user
from app.schemas.post import Post, PostCreate # 假设的 Schema
from app.services import permission_service

router = APIRouter(prefix="/posts", tags=["Posts"])

@router.post("/", response_model=Post)
def create_post(
    post: PostCreate,
    current_user: database.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    permissions = permission_service.get_user_permissions(current_user)
    if not permissions.get('can_post'):
        raise HTTPException(status_code=403, detail="Your plan does not allow creating posts.")
    return crud.create_post(db=db, post=post, user_id=current_user.id)

@router.get("/", response_model=List[Post])
def read_posts(db: Session = Depends(database.get_db)):
    return crud.get_posts(db=db)