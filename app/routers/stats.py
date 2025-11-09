from types import SimpleNamespace
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from app.database import get_db
from app.deps import get_org_id, require_min_role
from app import models
from app.schemas.stats import OrgStatsOut, TrainingStatsOut

router = APIRouter(prefix="/organizations/{slug}/stats", tags=["stats"])

def _ensure_training_in_org(db: Session, org_id: int, training_id: int) -> models.Training:
    tr = db.query(models.Training).filter_by(id=training_id, org_id=org_id).first()
    if not tr:
        raise HTTPException(status_code=404, detail="Training niet gevonden binnen deze organisatie")
    return tr

def _safe_first(query, defaults: dict) -> object:
    """
    Retourneert ofwel de eerste rij (row) of een object met default attributen.
    Voorkomt AttributeErrors bij lege aggregaties.
    """
    row = query.first()
    if row is not None:
        return row
    return SimpleNamespace(**defaults)

@router.get("/", response_model=OrgStatsOut,
            dependencies=[Depends(require_min_role(models.Role.MANAGER))])
def org_stats(slug: str, db: Session = Depends(get_db)):
    org_id = get_org_id(slug, db)

    # 1) actieve members binnen org
    active_members = (
        db.query(func.count(models.Membership.id))
        .join(models.User, models.User.id == models.Membership.user_id)
        .filter(models.Membership.org_id == org_id, models.User.is_active.is_(True))
        .scalar()
    ) or 0

    # 2) companies
    companies_count = (
        db.query(func.count(models.Company.id))
        .filter(models.Company.org_id == org_id)
        .scalar()
    ) or 0

    # 3) trainings
    trainings_count = (
        db.query(func.count(models.Training.id))
        .filter(models.Training.org_id == org_id)
        .scalar()
    ) or 0

    # 4) enrollments (alle trainingen in org)
    enrollments_count = (
        db.query(func.count(models.Enrollment.id))
        .join(models.Training, models.Training.id == models.Enrollment.training_id)
        .filter(models.Training.org_id == org_id)
        .scalar()
    ) or 0

    # 5) progress-aggregaties (alle modules uit alle trainingen in org)
    q_prog = _safe_first(
        db.query(
            func.count(models.Progress.id).label("total"),
            func.avg(models.Progress.percent).label("avg_percent"),
            func.sum(
                case((models.Progress.status == models.ProgressStatus.COMPLETED, 1), else_=0)
            ).label("done_cnt"),
        )
        .join(models.Module, models.Module.id == models.Progress.module_id)
        .join(models.Training, models.Training.id == models.Module.training_id)
        .filter(models.Training.org_id == org_id),
        defaults={"total": 0, "avg_percent": 0.0, "done_cnt": 0},
    )
    total_progress = int(getattr(q_prog, "total", 0) or 0)
    avg_progress_percent = float(getattr(q_prog, "avg_percent", 0.0) or 0.0)
    progress_done_cnt = int(getattr(q_prog, "done_cnt", 0) or 0)
    progress_completed_rate = (progress_done_cnt / total_progress) if total_progress else 0.0

    # 6) enrollment completion
    q_enr = _safe_first(
        db.query(
            func.count(models.Enrollment.id).label("total"),
            func.sum(
                case((models.Enrollment.status == models.EnrollmentStatus.COMPLETED, 1), else_=0)
            ).label("done_cnt"),
        )
        .join(models.Training, models.Training.id == models.Enrollment.training_id)
        .filter(models.Training.org_id == org_id),
        defaults={"total": 0, "done_cnt": 0},
    )
    total_enroll = int(getattr(q_enr, "total", 0) or 0)
    enroll_done_cnt = int(getattr(q_enr, "done_cnt", 0) or 0)
    enrollments_completed_rate = (enroll_done_cnt / total_enroll) if total_enroll else 0.0

    return OrgStatsOut(
        org_id=org_id,
        active_members=active_members,
        companies_count=companies_count,
        trainings_count=trainings_count,
        enrollments_count=enrollments_count,
        avg_progress_percent=avg_progress_percent,
        progress_completed_rate=progress_completed_rate,
        enrollments_completed_rate=enrollments_completed_rate,
    )

@router.get("/trainings/{training_id}", response_model=TrainingStatsOut,
            dependencies=[Depends(require_min_role(models.Role.MANAGER))])
def training_stats(slug: str, training_id: int, db: Session = Depends(get_db)):
    org_id = get_org_id(slug, db)
    _ensure_training_in_org(db, org_id, training_id)

    # enrolled users
    enrolled_users = (
        db.query(func.count(models.Enrollment.id))
        .filter(models.Enrollment.training_id == training_id)
        .scalar()
    ) or 0

    # modules in training
    modules_count = (
        db.query(func.count(models.Module.id))
        .filter(models.Module.training_id == training_id)
        .scalar()
    ) or 0

    # progress aggregaties voor dit training_id
    q_prog = _safe_first(
        db.query(
            func.count(models.Progress.id).label("total"),
            func.avg(models.Progress.percent).label("avg_percent"),
            func.sum(
                case((models.Progress.status == models.ProgressStatus.COMPLETED, 1), else_=0)
            ).label("done_cnt"),
        )
        .join(models.Module, models.Module.id == models.Progress.module_id)
        .filter(models.Module.training_id == training_id),
        defaults={"total": 0, "avg_percent": 0.0, "done_cnt": 0},
    )
    total_progress = int(getattr(q_prog, "total", 0) or 0)
    avg_progress_percent = float(getattr(q_prog, "avg_percent", 0.0) or 0.0)
    progress_done_cnt = int(getattr(q_prog, "done_cnt", 0) or 0)
    progress_completed_rate = (progress_done_cnt / total_progress) if total_progress else 0.0

    # enrollment completion
    q_enr = _safe_first(
        db.query(
            func.count(models.Enrollment.id).label("total"),
            func.sum(
                case((models.Enrollment.status == models.EnrollmentStatus.COMPLETED, 1), else_=0)
            ).label("done_cnt"),
        )
        .filter(models.Enrollment.training_id == training_id),
        defaults={"total": 0, "done_cnt": 0},
    )
    total_enroll = int(getattr(q_enr, "total", 0) or 0)
    enroll_done_cnt = int(getattr(q_enr, "done_cnt", 0) or 0)
    enrollments_completed_rate = (enroll_done_cnt / total_enroll) if total_enroll else 0.0

    return TrainingStatsOut(
        org_id=org_id,
        training_id=training_id,
        enrolled_users=enrolled_users,
        modules_count=modules_count,
        avg_progress_percent=avg_progress_percent,
        progress_completed_rate=progress_completed_rate,
        enrollments_completed_rate=enrollments_completed_rate,
    )
