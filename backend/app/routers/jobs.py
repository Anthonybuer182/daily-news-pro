from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session, joinedload
from typing import List
from datetime import datetime
from app.database import get_db
from app.models import Job
from app.schemas import Job as JobSchema, JobCreate, JobUpdate
from pydantic import BaseModel


class BatchDeleteRequest(BaseModel):
    ids: List[int]

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("", response_model=List[JobSchema])
def get_jobs(
    skip: int = 0,
    limit: int = 100,
    rule_id: int = None,
    status: str = None,
    keyword: str = None,
    start_date: str = None,
    end_date: str = None,
    db: Session = Depends(get_db)
):
    from fastapi.responses import JSONResponse
    query = db.query(Job).options(joinedload(Job.rule))
    if rule_id:
        query = query.filter(Job.rule_id == rule_id)
    if status:
        query = query.filter(Job.status == status)
    if keyword:
        keyword_pattern = f"%{keyword}%"
        from app.models import Rule
        query = query.outerjoin(Rule).filter(
            (Job.id.ilike(keyword_pattern)) |
            (Rule.name.ilike(keyword_pattern))
        )
    if start_date:
        query = query.filter(Job.created_at >= start_date)
    if end_date:
        query = query.filter(Job.created_at <= end_date)

    total = query.count()
    jobs = query.order_by(Job.created_at.desc()).offset(skip).limit(limit).all()

    for job in jobs:
        if job.rule:
            job.rule_name = job.rule.name

    from app.schemas import Job as JobSchema
    jobs_data = [JobSchema.model_validate(job).model_dump(mode='json') for job in jobs]
    response = JSONResponse(content=jobs_data)
    response.headers["X-Total-Count"] = str(total)
    return response


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


@router.post("/batch-delete")
def batch_delete_jobs(request: BatchDeleteRequest, db: Session = Depends(get_db)):
    """批量删除任务"""
    deleted_count = 0
    for job_id in ids:
        db_job = db.query(Job).filter(Job.id == job_id).first()
        if db_job:
            db.delete(db_job)
            deleted_count += 1
    db.commit()
    return {"message": f"Deleted {deleted_count} jobs", "deleted_count": deleted_count}


@router.post("/batch-run")
async def batch_run_jobs(ids: List[int] = Body(...), db: Session = Depends(get_db)):
    """批量执行任务（重新运行选中的任务）"""
    from app.database import engine as db_engine
    from sqlalchemy.orm import sessionmaker
    import logging
    import threading
    import asyncio

    logger = logging.getLogger(__name__)

    if not ids:
        raise HTTPException(status_code=400, detail="No job IDs provided")

    job_ids = []

    for job_id in ids:
        db_job = db.query(Job).filter(Job.id == job_id).first()
        if not db_job or not db_job.rule_id:
            continue

        new_job = Job(
            rule_id=db_job.rule_id,
            trigger_type="manual",
            status="running",
            started_at=datetime.utcnow()
        )
        db.add(new_job)
        db.commit()
        db.refresh(new_job)

        new_job_id = new_job.id
        job_ids.append({"original_job_id": job_id, "new_job_id": new_job_id})

        def run_crawler_background(rule_id=db_job.rule_id, job_id=new_job_id):
            Session = sessionmaker(bind=db_engine)
            session = Session()
            try:
                from app.services.crawler import CrawlerEngine
                engine = CrawlerEngine(session, job_id)
                asyncio.run(engine.crawl_rule(rule_id))
            except asyncio.TimeoutError:
                logger.error(f"Crawler job {job_id} timed out")
                _update_job_status(session, job_id, "failed", "Job timed out")
            except Exception as e:
                logger.error(f"Crawler job {job_id} failed: {e}")
                _update_job_status(session, job_id, "failed", str(e))
            finally:
                session.close()

        def _update_job_status(session, job_id, status, error_msg):
            try:
                job = session.query(Job).filter(Job.id == job_id).first()
                if job:
                    job.status = status
                    job.error_message = error_msg
                    job.finished_at = datetime.utcnow()
                    session.commit()
                    logger.info(f"Job {job_id} status updated to {status}")
            except Exception as e:
                logger.error(f"Failed to update job {job_id} status: {e}")
                session.rollback()

        thread = threading.Thread(target=run_crawler_background)
        thread.start()

    return {"message": f"Started {len(job_ids)} crawl tasks", "jobs": job_ids}
