from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

# For displaying user info without sensitive data
class UserBase(BaseModel):
    id: int
    email: str
    class Config:
        from_attributes = True

class CommentBase(BaseModel):
    content: str

class CommentCreate(CommentBase):
    pass

class Comment(CommentBase):
    id: int
    owner_id: int
    post_id: int
    created_at: datetime
    owner: UserBase
    class Config:
        from_attributes = True

class PostBase(BaseModel):
    content: str

class PostCreate(PostBase):
    pass

class Post(PostBase):
    id: int
    owner_id: int
    created_at: datetime
    owner: UserBase
    comments: List[Comment] = []
    class Config:
        from_attributes = True