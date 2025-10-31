from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    is_active: bool

    model_config = {"from_attributes": True}

class UserCreate(BaseModel):
    name: str = Field(..., min_length=1)
    email: EmailStr
    password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)
    model_config = {"extra": "ignore"}
