# backend/app/routers/logs.py
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Log
from app.models import Job as JobModel, Rule
from app.schemas.log import LogResponse

router = APIRouter(prefix="/api/logs", tags=["logs"])

@router.get("")
def get_logs(
    skip: int = 0,
    limit: int = 20,
    job_id: Optional[int] = None,
    level: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Log).options(joinedload(Log.job).joinedload(JobModel.rule))

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


class BatchDeleteRequest(BaseModel):
    ids: List[int]


@router.post("/batch-delete")
def batch_delete_logs(request: BatchDeleteRequest, db: Session = Depends(get_db)):
    """批量删除日志"""
    deleted_count = 0
    for log_id in request.ids:
        db_log = db.query(Log).filter(Log.id == log_id).first()
        if db_log:
            db.delete(db_log)
            deleted_count += 1
    db.commit()
    return {"message": f"Deleted {deleted_count} logs", "deleted_count": deleted_count}