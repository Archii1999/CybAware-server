# app/routers/users.py
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user, require_role
from app.models import User, Role
from app.schemas.users import UserCreate, UserOut, UserUpdate
from app.security import hash_password

router = APIRouter(prefix="/users", tags=["users"])



# Admin/Owner: create user

@router.post(
    "",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(Role.ADMIN, Role.OWNER))],
)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email bestaat al")

    new_user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        is_active=True,
    )

    db.add(new_user)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Fout bij opslaan gebruiker")
    db.refresh(new_user)
    return new_user



# Admin/Owner: list users (met zoeken/sorteren/pagineren)

@router.get(
    "",
    response_model=List[UserOut],
    dependencies=[Depends(require_role(Role.ADMIN, Role.OWNER))],
)
def list_users(
    db: Session = Depends(get_db),
    q: Optional[str] = Query(None, description="Zoek op naam of e-mail"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    order_by: str = Query("id", regex="^(id|name|email)$"),
    order_dir: str = Query("asc", regex="^(asc|desc)$"),
):
    query = db.query(User)

    if q:
        like = f"%{q}%"
       
        query = query.filter((User.name.ilike(like)) | (User.email.ilike(like)))

    col = {"id": User.id, "name": User.name, "email": User.email}[order_by]
    query = query.order_by(asc(col) if order_dir == "asc" else desc(col))

    return query.offset(offset).limit(limit).all()



# Self: eigen profiel ophalen

@router.get("/me", response_model=UserOut)
def get_me(current: User = Depends(get_current_user)):
    return current



# Admin/Owner: willekeurige user ophalen

@router.get(
    "/{user_id}",
    response_model=UserOut,
    dependencies=[Depends(require_role(Role.ADMIN, Role.OWNER))],
)
def get_user(user_id: int, db: Session = Depends(get_db)):
    obj = db.query(User).filter(User.id == user_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")
    return obj



# Self: eigen account bijwerken

@router.patch("/me", response_model=UserOut)
def update_me(
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    # e-mail wisselen?
    if payload.email and payload.email != current.email:
        if db.query(User).filter(User.email == payload.email).first():
            raise HTTPException(status_code=400, detail="E-mail is al in gebruik")
        current.email = payload.email

    if payload.name is not None:
        current.name = payload.name

    if payload.password:
        current.password_hash = hash_password(payload.password)

    db.commit()
    db.refresh(current)
    return current



# Admin/Owner: willekeurige user bijwerken

@router.patch(
    "/{user_id}",
    response_model=UserOut,
    dependencies=[Depends(require_role(Role.ADMIN, Role.OWNER))],
)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
):
    obj = db.query(User).filter(User.id == user_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")

    if payload.email and payload.email != obj.email:
        if db.query(User).filter(User.email == payload.email).first():
            raise HTTPException(status_code=400, detail="E-mail is al in gebruik")
        obj.email = payload.email

    if payload.name is not None:
        obj.name = payload.name

    if payload.password:
        obj.password_hash = hash_password(payload.password)

    db.commit()
    db.refresh(obj)
    return obj


# Admin/Owner: user verwijderen

@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role(Role.ADMIN, Role.OWNER))],
)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    obj = db.query(User).filter(User.id == user_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")
    db.delete(obj)
    db.commit()
    return
