from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator
from typing_extensions import Annotated
from pydantic import StringConstraints

PasswordStr = Annotated[str, StringConstraints(min_length=8, max_length=256)]

#Op user basis


class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserCreate(UserBase):
    password: PasswordStr

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[PasswordStr] = None

class UserOut(UserBase):
    id: int
    is_active: bool

#VOOR DE ORGANISATIE

class OrgCreate(BaseModel):
    name: str
    slug: str

class OrgOut(BaseModel):
    id: int
    name: str
    slug: str


#VOOR PROJECTEN

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

#TOKEN

class TokenOut(BaseModel):
    acces_token: str
    token_type: str = "bearer"

