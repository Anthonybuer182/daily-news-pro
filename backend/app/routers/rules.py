from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Rule, RuleLevel, Job
from app.schemas import Rule as RuleSchema, RuleCreate, RuleUpdate
from app.schemas import RuleLevel as RuleLevelSchema, RuleLevelCreate, RuleLevelUpdate
from app.services.crawler import CrawlerEngine
from datetime import datetime

router = APIRouter(prefix="/api/rules", tags=["rules"])


@router.get("", response_model=List[RuleSchema])
def get_rules(
    skip: int = 0,
    limit: int = 100,
    keyword: str = None,
    status: str = None,
    db: Session = Depends(get_db)
):
    from fastapi.responses import JSONResponse
    query = db.query(Rule)
    if keyword:
        keyword_pattern = f"%{keyword}%"
        query = query.filter(
            (Rule.name.ilike(keyword_pattern)) |
            (Rule.source_url.ilike(keyword_pattern))
        )
    if status:
        query = query.filter(Rule.status == status)

    total = query.count()
    rules = query.order_by(Rule.created_at.desc()).offset(skip).limit(limit).all()

    rules_data = [RuleSchema.model_validate(rule).model_dump(mode='json') for rule in rules]
    response = JSONResponse(content=rules_data)
    response.headers["X-Total-Count"] = str(total)
    return response


@router.get("/{rule_id}", response_model=RuleSchema)
def get_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.post("", response_model=RuleSchema)
def create_rule(rule: RuleCreate, db: Session = Depends(get_db)):
    db_rule = Rule(**rule.model_dump())
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule


@router.put("/{rule_id}", response_model=RuleSchema)
def update_rule(rule_id: int, rule: RuleUpdate, db: Session = Depends(get_db)):
    db_rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    for key, value in rule.model_dump(exclude_unset=True).items():
        setattr(db_rule, key, value)
    db.commit()
    db.refresh(db_rule)
    return db_rule


@router.delete("/{rule_id}")
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    db_rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    db.delete(db_rule)
    db.commit()
    return {"message": "Rule deleted"}


@router.post("/batch-delete")
def batch_delete_rules(ids: List[int], db: Session = Depends(get_db)):
    """批量删除规则"""
    deleted_count = 0
    for rule_id in ids:
        db_rule = db.query(Rule).filter(Rule.id == rule_id).first()
        if db_rule:
            db.delete(db_rule)
            deleted_count += 1
    db.commit()
    return {"message": f"Deleted {deleted_count} rules", "deleted_count": deleted_count}


@router.post("/batch-run")
async def batch_run_rules(ids: List[int] = Body(...), db: Session = Depends(get_db)):
    """批量执行规则（手动触发抓取任务）"""
    from app.database import engine as db_engine
    from sqlalchemy.orm import sessionmaker
    import logging
    import threading
    import asyncio

    logger = logging.getLogger(__name__)

    if not ids:
        raise HTTPException(status_code=400, detail="No rule IDs provided")

    job_ids = []

    for rule_id in ids:
        db_rule = db.query(Rule).filter(Rule.id == rule_id).first()
        if not db_rule:
            continue

        # Create job
        job = Job(
            rule_id=rule_id,
            trigger_type="manual",
            status="running",
            started_at=datetime.utcnow()
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        job_id = job.id
        job_ids.append({"rule_id": rule_id, "job_id": job_id})

        # Run crawler in background using separate database session
        def run_crawler_background(rule_id=rule_id, job_id=job_id):
            Session = sessionmaker(bind=db_engine)
            session = Session()
            try:
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

        # Start background task
        thread = threading.Thread(target=run_crawler_background)
        thread.start()

    return {"message": f"Started {len(job_ids)} crawl tasks", "jobs": job_ids}


@router.post("/{rule_id}/enable")
def enable_rule(rule_id: int, db: Session = Depends(get_db)):
    db_rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    db_rule.status = "enabled"
    db.commit()
    return {"message": "Rule enabled"}


@router.post("/{rule_id}/disable")
def disable_rule(rule_id: int, db: Session = Depends(get_db)):
    db_rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    db_rule.status = "disabled"
    db.commit()
    return {"message": "Rule disabled"}


@router.post("/{rule_id}/run")
async def run_rule(rule_id: int, db: Session = Depends(get_db)):
    """Trigger a crawl task for a rule (runs in background)"""
    from app.database import engine as db_engine
    from sqlalchemy.orm import sessionmaker
    import logging
    import threading
    import asyncio

    logger = logging.getLogger(__name__)

    db_rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    # Create job
    job = Job(
        rule_id=rule_id,
        trigger_type="manual",
        status="running",
        started_at=datetime.utcnow()
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    job_id = job.id

    # Run crawler in background using separate database session
    def run_crawler_background():
        Session = sessionmaker(bind=db_engine)
        session = Session()
        try:
            engine = CrawlerEngine(session, job_id)
            # Run with timeout to prevent indefinite hanging
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
        """Helper to update job status with proper error handling"""
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

    # Start background task
    thread = threading.Thread(target=run_crawler_background)
    thread.start()

    return {"job_id": job.id, "status": "running"}


# Level endpoints
@router.get("/{rule_id}/levels", response_model=List[RuleLevelSchema])
def get_rule_levels(rule_id: int, db: Session = Depends(get_db)):
    levels = db.query(RuleLevel).filter(RuleLevel.rule_id == rule_id).order_by(RuleLevel.level).all()
    return levels


@router.post("/{rule_id}/levels", response_model=RuleLevelSchema)
def create_rule_level(rule_id: int, level: RuleLevelCreate, db: Session = Depends(get_db)):
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    db_level = RuleLevel(**level.model_dump(), rule_id=rule_id)
    db.add(db_level)
    db.commit()
    db.refresh(db_level)
    return db_level


@router.put("/{rule_id}/levels/{level_id}", response_model=RuleLevelSchema)
def update_rule_level(rule_id: int, level_id: int, level: RuleLevelUpdate, db: Session = Depends(get_db)):
    db_level = db.query(RuleLevel).filter(RuleLevel.id == level_id, RuleLevel.rule_id == rule_id).first()
    if not db_level:
        raise HTTPException(status_code=404, detail="Level not found")
    for key, value in level.model_dump(exclude_unset=True).items():
        setattr(db_level, key, value)
    db.commit()
    db.refresh(db_level)
    return db_level


@router.delete("/{rule_id}/levels/{level_id}")
def delete_rule_level(rule_id: int, level_id: int, db: Session = Depends(get_db)):
    db_level = db.query(RuleLevel).filter(RuleLevel.id == level_id, RuleLevel.rule_id == rule_id).first()
    if not db_level:
        raise HTTPException(status_code=404, detail="Level not found")
    db.delete(db_level)
    db.commit()
    return {"message": "Level deleted"}
