from typing import Optional
from pydantic import BaseModel, Field

class CompanyBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    kvk: Optional[str] =Field(None, max_length=50)
    sector: Optional[str] = Field(None, max_length=100)
    email_domain: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = True


class CompanyCreate(CompanyBase):
    pass

class CompanyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    kvk : Optional[str] = Field(None, max_length=50)
    sector : Optional[str] = Field(None, max_length=255)
    email_domain : Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None

class CompanyOut(CompanyBase):
    id: int

    class Config:
        from_attributes = True


