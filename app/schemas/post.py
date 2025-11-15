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

# --- (新) Like Schema ---
class Like(BaseModel):
    user_id: int
    post_id: int

    class Config:
        from_attributes = True # or orm_mode = True

class ProfileForPost(BaseModel):
    name: str
    avatar_url: Optional[str] = None
    class Config:
        from_attributes = True

class PostOwner(BaseModel):
    id: int
    email: str
    profile: ProfileForPost # <--- 嵌套 Profile 信息
    class Config:
        from_attributes = True

class Post(PostBase):
    id: int
    owner_id: int
    created_at: datetime
    image_url: Optional[str] = None
    location: Optional[str] = None
    owner: PostOwner # <--- 确保 owner 是 PostOwner 类型
    comments: List['Comment'] = [] # 使用前向引用
    likes: List['Like'] = []
    class Config:
        from_attributes = True

# 确保 Comment Schema 也在文件底部更新
Comment.model_rebuild()