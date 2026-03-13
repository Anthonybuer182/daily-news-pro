from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class JobBase(BaseModel):
    rule_id: int
    trigger_type: str = "manual"


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    status: Optional[str] = None
    finished_at: Optional[datetime] = None
    articles_count: Optional[int] = None
    success_count: Optional[int] = None
    failed_count: Optional[int] = None
    error_message: Optional[str] = None


class Job(JobBase):
    id: int
    status: str
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    articles_count: int
    success_count: int
    failed_count: int
    error_message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
