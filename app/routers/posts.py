# app/routers/posts.py (完整版)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app import database, crud
from app.dependencies import get_current_user
from app.schemas.post import Post, PostCreate, Comment, CommentCreate
from app.services import permission_service

router = APIRouter(prefix="/posts", tags=["Posts"])

@router.post("/", response_model=Post, status_code=status.HTTP_201_CREATED)
def create_new_post(post: PostCreate, db: Session = Depends(database.get_db), current_user: database.User = Depends(get_current_user)):
    permissions = permission_service.get_user_permissions(current_user)
    if not permissions.get('can_post'):
        raise HTTPException(status_code=403, detail="Your plan does not allow creating posts.")
    return crud.create_post(db=db, post=post, user_id=current_user.id)

@router.get("/", response_model=List[Post])
def read_all_posts(db: Session = Depends(database.get_db)):
    return crud.get_posts(db=db)

@router.get("/{post_id}", response_model=Post)
def read_post_details(post_id: int, db: Session = Depends(database.get_db)):
    # (在 crud.py 中您需要添加 get_post_by_id 函数)
    post = db.query(database.Post).filter(database.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

@router.post("/{post_id}/comments", response_model=Comment)
def create_comment_for_post(
    post_id: int, 
    comment: CommentCreate, 
    db: Session = Depends(database.get_db), 
    current_user: database.User = Depends(get_current_user)
):
    permissions = permission_service.get_user_permissions(current_user)
    if not permissions.get('can_comment'):
        raise HTTPException(status_code=403, detail="Your plan does not allow commenting.")
    return crud.create_comment(db=db, content=comment.content, post_id=post_id, user_id=current_user.id)