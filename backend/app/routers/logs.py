# backend/app/routers/logs.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models import Log, Job
from app.schemas.log import LogResponse
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/logs", tags=["logs"])

@router.get("")
def get_logs(
    skip: int = 0,
    limit: int = 20,
    job_id: int = None,
    level: str = None,
    start_time: str = None,
    end_time: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(Log).options(joinedload(Log.job))

    if job_id:
        query = query.filter(Log.job_id == job_id)
    if level:
        query = query.filter(Log.level == level)
    if start_time:
        query = query.filter(Log.created_at >= start_time)
    if end_time:
        query = query.filter(Log.created_at <= end_time)

    total = query.count()
    logs = query.order_by(Log.created_at.desc()).offset(skip).limit(limit).all()

    result = []
    for log in logs:
        job_name = log.job.rule.name if log.job and log.job.rule else f"Job-{log.job_id}"
        result.append({
            "id": log.id,
            "job_id": log.job_id,
            "level": log.level,
            "message": log.message,
            "created_at": log.created_at.isoformat() if log.created_at else None,
            "job_name": job_name
        })

    response = JSONResponse(content=result)
    response.headers["X-Total-Count"] = str(total)
    return response