from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.deps import get_current_user, require_role, require_min_role
from app import models
from app.schemas.trainings import (
    TrainingCreate, TrainingOut, ModuleCreate, ModuleOut,
    EnrollUsersIn, EnrollmentOut
)

router = APIRouter(  
    prefix="/organizations/{slug}/trainings",
    tags=["trainings"],
    dependencies=[Depends(require_min_role(models.Role.MANAGER))],  # of require_role(...)
)

def _org(db: Session, slug: str) -> models.Organization:
    org = db.query(models.Organization).filter(models.Organization.slug == slug).first()
    if not org:
        raise HTTPException(404, "Organisatie niet gevonden")
    return org

@router.post("/", response_model=TrainingOut, status_code=status.HTTP_201_CREATED)
def create_training(slug: str, data: TrainingCreate, db: Session = Depends(get_db)):
    org = _org(db, slug)
    tr = models.Training(org_id=org.id, title=data.title, description=data.description, is_active=data.is_active)
    db.add(tr); db.flush()
    for i, m in enumerate(data.modules, start=1):
        db.add(models.Module(
            training_id=tr.id, title=m.title, content_url=m.content_url,
            order_index=m.order_index or i, duration_min=m.duration_min or 10
        ))
    db.commit(); db.refresh(tr)
    return tr

@router.get("/", response_model=List[TrainingOut])
def list_trainings(slug: str, db: Session = Depends(get_db)):
    org = _org(db, slug)
    return (db.query(models.Training)
              .filter_by(org_id=org.id, is_active=True)
              .order_by(models.Training.created_at.desc())
              .all())

@router.post("/{training_id}/modules", response_model=ModuleOut, status_code=status.HTTP_201_CREATED)
def add_module(slug: str, training_id: int, body: ModuleCreate, db: Session = Depends(get_db)):
    org = _org(db, slug)
    tr = db.query(models.Training).filter_by(id=training_id, org_id=org.id).first()
    if not tr:
        raise HTTPException(404, "Training niet gevonden")
    mod = models.Module(training_id=tr.id, **body.model_dump())
    db.add(mod); db.commit(); db.refresh(mod)
    return mod

@router.post("/{training_id}/enroll", response_model=List[EnrollmentOut], status_code=status.HTTP_201_CREATED)
def enroll_users(slug: str, training_id: int, body: EnrollUsersIn,
                 db: Session = Depends(get_db), current=Depends(get_current_user)):
    org = _org(db, slug)
    tr = db.query(models.Training).filter_by(id=training_id, org_id=org.id).first()
    if not tr:
        raise HTTPException(404, "Training niet gevonden")

    results: list[models.Enrollment] = []
    for email in body.emails:
        user = db.query(models.User).filter_by(email=email).first()
        if not user:
            continue
        existing = db.query(models.Enrollment).filter_by(user_id=user.id, training_id=tr.id).first()
        if existing:
            results.append(existing); continue
        enr = models.Enrollment(
            user_id=user.id, training_id=tr.id, status=models.EnrollmentStatus.ASSIGNED,
            assigned_by=getattr(current, "id", None), due_at=body.due_at
        )
        db.add(enr)
        for mod in tr.modules:
            db.add(models.Progress(user_id=user.id, module_id=mod.id))
        results.append(enr)

    db.commit()
    return [db.get(models.Enrollment, e.id) for e in results]
