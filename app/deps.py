from fastapi import Depends, HTTPException, status
from jose import JWTError
from sqlalchemy.orm import Session
from typing import Callable

from app.database import SessionLocal
from app.security import oauth2_scheme, decode_token
from app.models import User

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    try:
        payload = decode_token(token)
        sub = payload.get("sub") if isinstance(payload, dict) else getattr(payload, "sub", None)
        if not sub:
            raise ValueError("No subject in token")
        user_id = int(sub)
    except (JWTError, ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    if not getattr(user, "is_active", True):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

    return user

def require_roles(*allowed: str) -> Callable:
    def dep(user: User = Depends(get_current_user)) -> User:
        role = getattr(user, "role", "user")
        if allowed and role not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return user
    return dep
