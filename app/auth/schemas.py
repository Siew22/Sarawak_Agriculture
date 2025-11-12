from pydantic import BaseModel, EmailStr, Field
from typing import Optional

# ====================================================================
# User & Authentication Schemas
# ====================================================================

class UserCreate(BaseModel):
    """
    Schema for creating a new user. This is what the API expects as input.
    """
    email: EmailStr = Field(..., description="用户的电子邮箱，将作为登录名")
    password: str = Field(..., min_length=8, description="用户密码，最少8位")
    
    # User Type Selection
    user_type: str = Field("public", description="用户类型 ('public' 或 'business')")
    
    # Common profile info
    name: str = Field(..., max_length=100, description="用户或企业名称")
    phone_number: Optional[str] = Field(None, description="联系电话")
    
    # Business-only profile info
    ic_no: Optional[str] = Field(None, description="身份证或商业注册号")
    organization: Optional[str] = Field(None, description="组织/公司全名")
    company_type: Optional[str] = Field(None, description="公司类型 (e.g., Small Business)")


class UserOut(BaseModel):
    """
    Schema for returning user information. This safely excludes the password.
    """
    id: int
    email: EmailStr
    user_type: str

    class Config:
        orm_mode = True # This allows the model to be created from SQLAlchemy objects

# --- Schemas for Login (JWT Token) ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None