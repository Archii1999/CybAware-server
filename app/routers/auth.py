from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.auth import LoginInput, Token
from app.security import verify_password, create_access_token
from app.models import User
from app.deps import get_db, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=Token)
def login(form: LoginInput, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.email).first()
    if not user or not verify_password(form.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive account")

    token = create_access_token(subject=user.id)
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me")
def me(current = Depends(get_current_user)):

    return {"id": current.id, "name": current.name, "email": current.email, "role": getattr(current, "role", "user")}
