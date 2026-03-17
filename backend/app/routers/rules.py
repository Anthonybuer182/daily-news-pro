from fastapi import APIRouter, Depends, HTTPException
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
def get_rules(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    rules = db.query(Rule).offset(skip).limit(limit).all()
    return rules


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
    """Trigger a crawl task for a rule"""
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

    # Run crawler asynchronously
    try:
        engine = CrawlerEngine(db, job.id)
        await engine.crawl_rule(rule_id)
    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        job.finished_at = datetime.utcnow()
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))

    return {"job_id": job.id, "status": job.status}


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
