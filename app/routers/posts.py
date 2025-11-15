import uuid
import shutil
from pathlib import Path
from typing import List, Optional, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form, Response
from sqlalchemy.orm import Session

from app import crud, database
from app.dependencies import get_current_user
from app.schemas.post import Post, PostCreate, Comment, CommentCreate
from app.services import permission_service

router = APIRouter(
    prefix="/posts",
    tags=["Posts"],
)

@router.post("/", response_model=Post, status_code=status.HTTP_201_CREATED)
async def create_new_post(
    content: str = Form(...),
    location: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(database.get_db),
    current_user: database.User = Depends(get_current_user)
):
    permissions = permission_service.get_user_permissions(current_user)
    if not permissions.get('can_post'):
        raise HTTPException(status_code=403, detail="Your plan does not allow creating posts.")
    
    image_url = None
    if image:
        static_path = Path("static/posts")
        static_path.mkdir(parents=True, exist_ok=True)
        unique_filename = f"{uuid.uuid4().hex}{Path(image.filename).suffix.lower()}"
        file_path = static_path / unique_filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        image_url = f"/static/posts/{unique_filename}"
        
    # --- 关键修复：使用正确的参数调用 crud.create_post ---
    return crud.create_post(
        db=db, 
        content=content, 
        image_url=image_url, 
        location=location, 
        user_id=current_user.id
    )

@router.get("/", response_model=List[Post])
def read_all_posts(db: Session = Depends(database.get_db)):
    return crud.get_posts(db=db)

@router.get("/{post_id}", response_model=Post)
def read_post_details(post_id: int, db: Session = Depends(database.get_db)):
    post = crud.get_post_by_id(db=db, post_id=post_id) # Assumes get_post_by_id exists in crud
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

@router.post("/{post_id}/comments/", response_model=Comment)
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

@router.post("/{post_id}/like", status_code=status.HTTP_204_NO_CONTENT)
def toggle_like_on_post(
    post_id: int,
    db: Session = Depends(database.get_db),
    current_user: database.User = Depends(get_current_user)
):
    permissions = permission_service.get_user_permissions(current_user)
    if not permissions.get('can_like_share'):
        raise HTTPException(status_code=403, detail="Your plan does not allow liking posts.")
    
    post = db.query(database.Post).filter(database.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    like = db.query(database.Like).filter(
        database.Like.post_id == post_id,
        database.Like.user_id == current_user.id
    ).first()

    if like:
        db.delete(like)
        db.commit()
    else:
        new_like = database.Like(user_id=current_user.id, post_id=post_id)
        db.add(new_like)
        db.commit()
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)