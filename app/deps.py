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



def _to_role(value: str | models.Role) -> models.Role:
    """Normaliseer naar Role enum, met duidelijke fout bij onbekende waarde."""
    if isinstance(value, models.Role):
        return value
    try:
        return models.Role(value)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown role value: {value!r}",
        )

def require_role(
    *allowed_roles: models.Role,
    allow_owner: bool = True,
):
   
    def _inner(
        user: models.User = Depends(get_current_user),
        org_id: int = Depends(get_org_id),
        db: Session = Depends(get_db),
    ):
        membership = (
            db.query(models.Membership)
            .filter_by(user_id=user.id, org_id=org_id)
            .first()
        )
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not a member of this organization",
            )

        
        try:
            member_role = models.Role(membership.role)
        except ValueError:
            # Onverwachte data in DB; blokkeer toegang i.p.v. stil falen
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid role on membership",
            )

        # OWNER override
        if allow_owner and member_role is models.Role.OWNER:
            return {"user": user, "org_id": org_id, "role": member_role}

        
        if not allowed_roles:
            return {"user": user, "org_id": org_id, "role": member_role}

        # Rol-check
        allowed: set[models.Role] = { _to_role(r) for r in allowed_roles }
        if member_role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role permissions",
            )

        return {"user": user, "org_id": org_id, "role": member_role}

    return _inner


def require_membership(allow_owner: bool = True):
    """Alleen lid zijn (optioneel OWNER override). Handig voor read-only endpoints."""
    return require_role(allow_owner=allow_owner)


def org_scope(query, org_id: int, model):
    """
    Beperk een SQLAlchemy-query naar de meegegeven organisatie.
    Verwacht dat 'model' een kolom 'org_id' heeft.
    """
    try:
        col = getattr(model, "org_id")
    except AttributeError as e:
        raise RuntimeError(f"Model {model!r} has no 'org_id' column") from e
    return query.filter(col == org_id)