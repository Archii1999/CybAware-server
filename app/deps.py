# app/deps.py
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from app.security import decode_token
from app.database import get_db          
from app import models
from typing import Union 


def get_current_user(
    authorization: str = Header(...),
    db: Session = Depends(get_db),
) -> models.User:
    try:
        scheme, token = authorization.split(" ")
        if scheme.lower() != "bearer":
            raise ValueError
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Authorization header")

    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.get(models.User, int(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive or unknown user")

    return user



def get_org_id(slug: str, db: Session = Depends(get_db)) -> int:
    org = db.query(models.Organization).filter(models.Organization.slug == slug).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organisatie niet gevonden")
    return org.id

def _to_role(r: Union[models.Role, str]) -> models.Role:
    if isinstance(r, models.Role):
        return r
    try:
        return models.Role(r)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Onbekende rol: {r!r}")

def require_role(*allowed_roles: Union[models.Role, str], allow_owner: bool = True):
    def _inner(
        user: models.User = Depends(get_current_user),
        org_id: int = Depends(get_org_id),
        db: Session = Depends(get_db),
    ):
        membership = db.query(models.Membership).filter_by(user_id=user.id, org_id=org_id).first()
        if not membership:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not a member of this organization")

        member_role: models.Role = membership.role  # SAEnum(Role) -> Enum al gecast

        if allow_owner and member_role is models.Role.OWNER:
            return {"user": user, "org_id": org_id, "role": member_role}

        if not allowed_roles:
            return {"user": user, "org_id": org_id, "role": member_role}

        allowed: set[models.Role] = {_to_role(r) for r in allowed_roles}
        if member_role not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role permissions")

        return {"user": user, "org_id": org_id, "role": member_role}
    return _inner

def require_membership(allow_owner: bool = True):
    return require_role(allow_owner=allow_owner)

RANK = {
    models.Role.EMPLOYEE: 1,
    models.Role.MANAGER:  2,
    models.Role.ADMIN:    3,
    models.Role.OWNER:    4,
}

def require_min_role(min_role: Union[models.Role, str], allow_owner: bool = True):
    min_role = _to_role(min_role)
    def _inner(
        user: models.User = Depends(get_current_user),
        org_id: int = Depends(get_org_id),
        db: Session = Depends(get_db),
    ):
        membership = db.query(models.Membership).filter_by(user_id=user.id, org_id=org_id).first()
        if not membership:
            raise HTTPException(status_code=403, detail="User is not a member of this organization")
        role: models.Role = membership.role
        if allow_owner and role is models.Role.OWNER:
            return {"user": user, "org_id": org_id, "role": role}
        if RANK[role] < RANK[min_role]:
            raise HTTPException(status_code=403, detail="Insufficient role level")
        return {"user": user, "org_id": org_id, "role": role}
    return _inner

def org_scope(query, org_id: int, model):
    col = getattr(model, "org_id", None)
    if col is None:
        raise RuntimeError(f"Model {model!r} has no 'org_id' column")
    return query.filter(col == org_id)