from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.database import get_db
from app.models import Job
from app.schemas import Job as JobSchema, JobCreate, JobUpdate

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("", response_model=List[JobSchema])
def get_jobs(
    skip: int = 0,
    limit: int = 100,
    rule_id: int = None,
    status: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(Job)
    if rule_id:
        query = query.filter(Job.rule_id == rule_id)
    if status:
        query = query.filter(Job.status == status)
    jobs = query.order_by(Job.created_at.desc()).offset(skip).limit(limit).all()
    return jobs


@router.get("/{job_id}", response_model=JobSchema)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("", response_model=JobSchema)
def create_job(job: JobCreate, db: Session = Depends(get_db)):
    db_job = Job(
        **job.model_dump(),
        status="pending",
        started_at=datetime.utcnow()
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job


@router.put("/{job_id}", response_model=JobSchema)
def update_job(job_id: int, job_update: JobUpdate, db: Session = Depends(get_db)):
    db_job = db.query(Job).filter(Job.id == job_id).first()
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")
    for key, value in job_update.model_dump(exclude_unset=True).items():
        setattr(db_job, key, value)
    db.commit()
    db.refresh(db_job)
    return db_job
