from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models import ProgressStatus

class ProgressUpdateIn(BaseModel):
    module_id: int
    status: ProgressStatus
    percent: float = Field(ge=0, le=100)
    score: Optional[float] = Field(default=None, ge=0, le=100)

class ProgressOut(BaseModel):
    id: int
    user_id: int
    module_id: int
    status: ProgressStatus
    percent: float
    score: Optional[float]
    started_at: Optional[datetime]
    last_event_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True
        