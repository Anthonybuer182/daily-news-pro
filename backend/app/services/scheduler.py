from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Rule, Job
from app.services.crawler import CrawlerEngine
from datetime import datetime
import asyncio


class CrawlScheduler:
    """Scheduler for periodic crawling tasks"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.running_jobs = {}

    def start(self):
        """Start the scheduler"""
        self.scheduler.start()
        self._load_rules()

    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()

    def _load_rules(self):
        """Load rules with cron expressions"""
        db = SessionLocal()
        try:
            rules = db.query(Rule).filter(
                Rule.status == "enabled",
                Rule.cron_expression.isnot(None)
            ).all()

            for rule in rules:
                self._add_rule_job(rule)
        finally:
            db.close()

    def _add_rule_job(self, rule: Rule):
        """Add a scheduled job for a rule"""
        if not rule.cron_expression:
            return

        # Parse cron expression
        parts = rule.cron_expression.split()
        if len(parts) != 5:
            return

        trigger = CronTrigger(
            minute=parts[0],
            hour=parts[1],
            day=parts[2],
            month=parts[3],
            day_of_week=parts[4]
        )

        job_id = f"rule_{rule.id}"

        def run_crawl():
            asyncio.create_task(self._run_crawl(rule.id))

        self.scheduler.add_job(
            run_crawl,
            trigger,
            id=job_id,
            replace_existing=True
        )

    async def _run_crawl(self, rule_id: int):
        """Run crawl for a specific rule"""
        db = SessionLocal()
        try:
            # Create job
            job = Job(
                rule_id=rule_id,
                trigger_type="scheduled",
                status="pending"
            )
            db.add(job)
            db.commit()
            db.refresh(job)

            # Run crawler
            engine = CrawlerEngine(db, job.id)
            await engine.crawl_rule(rule_id)
        finally:
            db.close()

    def update_rule(self, rule_id: int):
        """Update scheduled job for a rule"""
        db = SessionLocal()
        try:
            rule = db.query(Rule).filter(Rule.id == rule_id).first()
            if not rule:
                return

            job_id = f"rule_{rule_id}"

            # Remove existing job
            if job_id in self.scheduler.get_jobs():
                self.scheduler.remove_job(job_id)

            # Add new job if enabled
            if rule.status == "enabled" and rule.cron_expression:
                self._add_rule_job(rule)
        finally:
            db.close()

    def remove_rule(self, rule_id: int):
        """Remove scheduled job for a rule"""
        job_id = f"rule_{rule_id}"
        if job_id in self.scheduler.get_jobs():
            self.scheduler.remove_job(job_id)
