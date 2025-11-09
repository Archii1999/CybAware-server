from pydantic import BaseModel
from typing import Optional

class OrgStatsOut(BaseModel):
    org_id: int
    active_members: int
    companies_count: int
    trainings_count: int
    enrollments_count: int
    avg_progress_percent: float        # 0..100
    progress_completed_rate: float     # 0..1
    enrollments_completed_rate: float  # 0..1

class TrainingStatsOut(BaseModel):
    org_id: int
    training_id: int
    enrolled_users: int
    modules_count: int
    avg_progress_percent: float        # 0..100
    progress_completed_rate: float     # 0..1
    enrollments_completed_rate: float  # 0..1
