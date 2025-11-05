# app/routers/projects.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models
from app.schemas import ProjectCreate, ProjectOut
from app.deps import require_role
from app.db import get_db

router = APIRouter(prefix="/projects", tags=["projects"])

@router.post("", response_model=ProjectOut)
def create_project(payload: ProjectCreate,
                   ctx = Depends(require_role(models.Role.OWNER, models.Role.ADMIN, models.Role.MANAGER)),
                   db: Session = Depends(get_db)):
    project = models.Project(org_id=ctx["org_id"], name=payload.name, description=payload.description)
    db.add(project); db.commit(); db.refresh(project)
    return ProjectOut(id=project.id, name=project.name, description=project.description)

@router.get("", response_model=list[ProjectOut])
def list_projects(ctx = Depends(require_role(models.Role.OWNER, models.Role.ADMIN, models.Role.MANAGER, models.Role.EMPLOYEE)),
                  db: Session = Depends(get_db)):
    rows = db.query(models.Project).filter_by(org_id=ctx["org_id"]).all()
    return [ProjectOut(id=p.id, name=p.name, description=p.description) for p in rows]
