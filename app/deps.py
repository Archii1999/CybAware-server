# app/deps.py
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from app.security import decode_token
from app.db import get_db
from app import models


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



def get_org_id(x_org_id: int | None = Header(None)) -> int:
    if not x_org_id:
        raise HTTPException(status_code=400, detail="Missing X-Org-Id header")
    return x_org_id



def require_role(*allowed_roles: models.Role):
    """
    Gebruik:
    ctx = Depends(require_role(models.Role.OWNER, models.Role.ADMIN))
    -> returnt {"user": ..., "org_id": ..., "role": ...}
    """
    def _inner(
        user: models.User = Depends(get_current_user),
        org_id: int = Depends(get_org_id),
        db: Session = Depends(get_db),
    ):
        membership = db.query(models.Membership).filter_by(user_id=user.id, org_id=org_id).first()
        if not membership:
            raise HTTPException(status_code=403, detail="User is not a member of this organization")

        if allowed_roles and membership.role not in {r.value for r in allowed_roles}:
            raise HTTPException(status_code=403, detail="Insufficient role permissions")

        return {"user": user, "org_id": org_id, "role": membership.role}
    return _inner

def org_scope(query, org_id: int, model):
    return query.filter(getattr(model, "org_id") == org_id)