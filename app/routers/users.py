from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc

from app.schemas.users import UserCreate, UserOut, UserUpdate
from app.database import SessionLocal
from app.models import User
from app.security import hash_password
from app.deps import get_db, get_current_user, require_roles  # <-- JWT dependencies

router = APIRouter(prefix="/users", tags=["users"])


# ------------------------------------------------------------
# Create user (open of alleen admin, afhankelijk van beleid)
# ------------------------------------------------------------
@router.post(
    "/",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("admin"))],  # admin mag users maken
)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email bestaat al!")

    
    new_user = User(
        name=user.name,
        email=user.email,
        password=hash_password(user.password),
        is_active=True,
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Fout bij opslaan gebruiker")


# ------------------------------------------------------------
# List users (met paginatie + filter + sortering)
# ------------------------------------------------------------
@router.get(
    "/",
    response_model=list[UserOut],
    dependencies=[Depends(require_roles("admin"))],  # alleen admin
)
def list_users(
    db: Session = Depends(get_db),
    q: str | None = Query(None, description="Zoek op naam of email"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    order_by: str = Query("id", pattern="^(id|name|email)$"),
    order_dir: str = Query("asc", pattern="^(asc|desc)$"),
):
    query = db.query(User)

    if q:
        like = f"%{q}%"
        query = query.filter((User.name.ilike(like)) | (User.email.ilike(like)))

    col = {"id": User.id, "name": User.name, "email": User.email}[order_by]
    query = query.order_by(asc(col) if order_dir == "asc" else desc(col))

    return query.offset(offset).limit(limit).all()


# ------------------------------------------------------------
# Get own profile OR admin get specific user
# ------------------------------------------------------------
@router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Als admin → alles zien, anders alleen eigen profiel
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Geen toegang")

    obj = db.query(User).filter(User.id == user_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")
    return obj


# ------------------------------------------------------------
#  Update user (self of admin)
# ------------------------------------------------------------
@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    obj = db.query(User).filter(User.id == user_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")

    # alleen admin of eigen account
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Geen toegang")

    if payload.email and payload.email != obj.email:
        if db.query(User).filter(User.email == payload.email).first():
            raise HTTPException(status_code=400, detail="Email is al in gebruik!")
        obj.email = payload.email

    if payload.name is not None:
        obj.name = payload.name

    if payload.password:
        obj.password = hash_password(payload.password)

    db.commit()
    db.refresh(obj)
    return obj


# ------------------------------------------------------------
#  Delete user (alleen admin)
# ------------------------------------------------------------
@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles("admin"))],
)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    obj = db.query(User).filter(User.id == user_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")
    db.delete(obj)
    db.commit()
    return
