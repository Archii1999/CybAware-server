# app/schemas/trainings.py
from __future__ import annotations
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models import EnrollmentStatus

# ── Module ─────────────────────────────────────────────────────────────
class ModuleCreate(BaseModel):
    title: str
    content_url: Optional[str] = None
    order_index: int = 1
    duration_min: int = 10

class ModuleOut(BaseModel):
    id: int
    title: str
    content_url: Optional[str]
    order_index: int
    duration_min: int

    class Config:
        from_attributes = True

# ── Training ───────────────────────────────────────────────────────────
class TrainingCreate(BaseModel):
    title: str
    description: Optional[str] = None
    is_active: bool = True
    modules: List[ModuleCreate] = []

class TrainingOut(BaseModel):
    id: int
    org_id: int
    title: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    modules: List[ModuleOut] = []

    class Config:
        from_attributes = True

# ── Enrollment ─────────────────────────────────────────────────────────
class EnrollUsersIn(BaseModel):
    emails: List[str]
    due_at: Optional[datetime] = None

class EnrollmentOut(BaseModel):
    id: int
    user_id: int
    training_id: int
    status: EnrollmentStatus
    assigned_at: datetime
    due_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True

# ── Overzicht voor progress-router ─────────────────────────────────────
class UserTrainingOut(BaseModel):
    training: TrainingOut
    status: EnrollmentStatus
