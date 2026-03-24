from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class LogResponse(BaseModel):
    id: int
    job_id: int
    level: str
    message: str
    created_at: datetime
    job_name: Optional[str] = None

    class Config:
        from_attributes = True