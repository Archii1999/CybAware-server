from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_membership
from app import models
from app.schemas.progress import ProgressUpdateIn, ProgressOut
from app.schemas.trainings import TrainingCreate, TrainingOut, ModuleCreate, ModuleOut, EnrollUsersIn, EnrollmentOut, UserTrainingOut


router = APIRouter(prefix="/progress", tags=["progress"])


# ─────────────────────────────────────────────
#   Eigen voortgang (alle modules)
# ─────────────────────────────────────────────
@router.get("/me", response_model=List[ProgressOut])
def my_progress(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Geeft alle progress-records van de ingelogde gebruiker terug.
    """
    return (
        db.query(models.Progress)
        .filter(models.Progress.user_id == current_user.id)
        .order_by(models.Progress.module_id)
        .all()
    )


# ─────────────────────────────────────────────
#   Voortgang bijwerken
# ─────────────────────────────────────────────
@router.post("/", response_model=ProgressOut, status_code=status.HTTP_200_OK)
def update_progress(
    payload: ProgressUpdateIn,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Update de voortgang van een specifieke module.
    """
    pr = (
        db.query(models.Progress)
        .filter_by(user_id=current_user.id, module_id=payload.module_id)
        .first()
    )

    if not pr:
        raise HTTPException(status_code=404, detail="Geen voortgangsrecord gevonden voor deze module")

    # Bijwerken van status, score en percent
    pr.status = payload.status
    pr.percent = payload.percent
    pr.score = payload.score
    now = datetime.utcnow()

    # Automatisch timestamps bijhouden
    if pr.status == models.ProgressStatus.IN_PROGRESS and pr.started_at is None:
        pr.started_at = now
    pr.last_event_at = now

    if pr.status == models.ProgressStatus.COMPLETED:
        pr.completed_at = now
        pr.percent = 100.0

    db.commit()
    db.refresh(pr)
    return pr


# ─────────────────────────────────────────────
#  Lijst met trainingen + status
# ─────────────────────────────────────────────
# app/routers/progress.py

@router.get("/me/trainings", response_model=List[UserTrainingOut])
def my_trainings(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    enrolls = (
        db.query(models.Enrollment)
        .filter(models.Enrollment.user_id == current_user.id)
        .all()
    )

    out: list[UserTrainingOut] = []
    for e in enrolls:
        if not e.training:
            continue
        tr_out = TrainingOut.model_validate(e.training)  # ⬅️ expliciet casten naar schema
        out.append(UserTrainingOut(training=tr_out, status=e.status))
    return out



# ─────────────────────────────────────────────
# 🔒 4. Optioneel — org-level check
# ─────────────────────────────────────────────
@router.get("/org/{slug}", response_model=List[ProgressOut],
            dependencies=[Depends(require_membership())])
def org_progress(slug: str, db: Session = Depends(get_db)):
    """
    (Optioneel) Haalt alle voortgangsrecords binnen een organisatie op.
    Alleen leden mogen dit endpoint gebruiken.
    """
    org_id = (
        db.query(models.Organization.id)
        .filter(models.Organization.slug == slug)
        .scalar()
    )
    if not org_id:
        raise HTTPException(status_code=404, detail="Organisatie niet gevonden")

    progresses = (
        db.query(models.Progress)
        .join(models.Module, models.Module.id == models.Progress.module_id)
        .join(models.Training, models.Training.id == models.Module.training_id)
        .filter(models.Training.org_id == org_id)
        .all()
    )
    return progresses
