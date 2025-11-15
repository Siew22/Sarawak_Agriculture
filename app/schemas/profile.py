# app/schemas/profile.py (新建)
from pydantic import BaseModel
from typing import Optional

class ProfileBase(BaseModel):
    name: Optional[str] = None
    phone_number: Optional[str] = None

class ProfileUpdate(ProfileBase):
    pass

class Profile(ProfileBase):
    id: int
    user_id: int
    ic_no: Optional[str] = None
    organization: Optional[str] = None
    company_type: Optional[str] = None
    
    class Config:
        from_attributes = True