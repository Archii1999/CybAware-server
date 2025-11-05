
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError
from sqlalchemy.orm import Session
from app.deps import get_db  # alleen de DB-dependency uit deps
from app import models
from app.schemas.users import UserCreate, UserOut
from app.schemas.auth import TokenOut
from app.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
    oauth2_scheme,
)

router = APIRouter(prefix="/auth", tags=["auth"])

# --- Helpers ---
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    try:
        payload: Dict[str, Any] = decode_token(token)
        sub = payload.get("sub")
        if sub is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
        try:
            user_id = int(sub)
        except (TypeError, ValueError):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")
    except JWTError:
        # decode_token kan JWTError gooien; vang af en geef 401
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.get(models.User, user_id)
    if not user:
        # (Je kunt ook 401 teruggeven i.p.v. 404 om user enumeration te vermijden)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive account")
    return user


@router.post("/login", response_model=TokenOut)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),  # username/password uit Authorize
    db: Session = Depends(get_db),
):
    email = form_data.username  # "username" veld bevat je e-mail
    password = form_data.password

    user = db.query(models.User).filter(models.User.email == email).first()
   
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive account")

    token = create_access_token(subject=str(user.id))
    return TokenOut(access_token=token)


@router.get("/me", response_model=UserOut)
def me(current: models.User = Depends(get_current_user)):

    return current


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user = models.User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),  # <-- GEWIJZIGD
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
