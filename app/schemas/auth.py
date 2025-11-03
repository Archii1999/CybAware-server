from pydantic import BaseModel, EmailStr

class LoginInput(BaseModel):
    email: EmailStr
    password: str

class TokenOut(BaseModel):               
    access_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: str
