
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models
from app.schemas import OrgCreate, OrgOut
from app.deps import get_current_user, require_role
from app.db import get_db

router = APIRouter(prefix="/orgs", tags=["organizations"])

@router.post("", response_model=OrgOut)
def create_org(payload: OrgCreate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    if db.query(models.Organization).filter(
        (models.Organization.name == payload.name) | (models.Organization.slug == payload.slug)
    ).first():
        raise HTTPException(status_code=400, detail="Naam/slug bestaat al")
    org = models.Organization(name=payload.name, slug=payload.slug)
    db.add(org); db.flush()
    # creator wordt OWNER
    m = models.Membership(user_id=user.id, org_id=org.id, role=models.Role.OWNER.value)
    db.add(m); db.commit(); db.refresh(org)
    return OrgOut(id=org.id, name=org.name, slug=org.slug)

@router.post("/{org_id}/invite")
def invite_user(org_id: int, email: str, role: models.Role,
                ctx = Depends(require_role(models.Role.OWNER, models.Role.ADMIN)),
                db: Session = Depends(get_db)):
    
    user = db.query(models.User).filter_by(email=email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User niet gevonden (MVP maakt nog geen pending invite)")
    if db.query(models.Membership).filter_by(user_id=user.id, org_id=org_id).first():
        return {"status": "ok", "message": "User is al lid"}
    db.add(models.Membership(user_id=user.id, org_id=org_id, role=role.value))
    db.commit()
    return {"status": "ok"}
