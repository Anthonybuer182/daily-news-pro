from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Rule, Job, Channel, Article
from app.services.crawler import CrawlerEngine
from app.services.http_sender import HttpSender
from datetime import datetime, timezone
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
        self._load_schedule_push()

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

    def _load_schedule_push(self):
        """Load scheduled push jobs for channels"""
        db = SessionLocal()
        try:
            channels = db.query(Channel).filter(
                Channel.status == "enabled",
                Channel.push_on_schedule == True
            ).all()

            # 按时间分组
            channels_by_time = {}
            for channel in channels:
                schedule_time = channel.schedule_time or "09:00"
                if schedule_time not in channels_by_time:
                    channels_by_time[schedule_time] = []
                channels_by_time[schedule_time].append(channel)

            # 为每个时间点添加一个定时任务
            for schedule_time, chs in channels_by_time.items():
                parts = schedule_time.split(":")
                if len(parts) != 2:
                    continue
                hour, minute = int(parts[0]), int(parts[1])

                trigger = CronTrigger(hour=hour, minute=minute)
                job_id = f"push_{schedule_time.replace(':', '_')}"

                def make_push_job(channel_ids):
                    def push_job():
                        asyncio.create_task(self._run_scheduled_push(channel_ids))
                    return push_job

                self.scheduler.add_job(
                    make_push_job([c.id for c in chs]),
                    trigger,
                    id=job_id,
                    replace_existing=True
                )
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

            # 爬取完成后，检查是否需要实时推送
            await self._notify_crawl_channels(rule_id)
        finally:
            db.close()

    async def _notify_crawl_channels(self, rule_id: int):
        """通知启用了实时推送的渠道"""
        db = SessionLocal()
        try:
            # 查找启用了 push_on_crawl 的渠道
            channels = db.query(Channel).filter(
                Channel.status == "enabled",
                Channel.push_on_crawl == True
            ).all()

            if not channels:
                return

            # 获取刚爬取的文章（当天新文章，使用本地时间）
            now = datetime.now()  # 本地时间
            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
            articles = db.query(Article).filter(
                Article.rule_id == rule_id,
                Article.status == "success",
                Article.created_at >= start_of_day
            ).all()

            if not articles:
                return

            for channel in channels:
                enabled_webhooks = [w.webhook_url for w in channel.webhooks if w.is_enabled]
                if not enabled_webhooks:
                    continue

                articles_data = []
                for article in articles:
                    articles_data.append({
                        "title": article.title or "",
                        "summary": article.summary or "",
                        "rule_name": article.rule.name if article.rule else "未知来源",
                        "publish_time": article.publish_time,
                        "url": article.url or ""
                    })

                HttpSender.send_news(
                    webhook_urls=enabled_webhooks,
                    articles=articles_data,
                    http_method=channel.http_method or "POST",
                    request_headers=channel.request_headers,
                    message_template=channel.message_template,
                    channel_type=channel.channel_type or "http_webhook"
                )
        finally:
            db.close()

    async def _run_scheduled_push(self, channel_ids: list):
        """执行定时推送"""
        db = SessionLocal()
        try:
            channels = db.query(Channel).filter(
                Channel.id.in_(channel_ids),
                Channel.status == "enabled",
                Channel.push_on_schedule == True
            ).all()

            if not channels:
                return

            # 获取当天的文章（使用本地时间）
            now = datetime.now()  # 本地时间，不用 timezone.utc
            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
            articles = db.query(Article).filter(
                Article.status == "success",
                Article.created_at >= start_of_day
            ).all()

            for channel in channels:
                enabled_webhooks = [w.webhook_url for w in channel.webhooks if w.is_enabled]
                if not enabled_webhooks:
                    continue

                articles_data = []
                for article in articles:
                    articles_data.append({
                        "title": article.title or "",
                        "summary": article.summary or "",
                        "rule_name": article.rule.name if article.rule else "未知来源",
                        "publish_time": article.publish_time,
                        "url": article.url or ""
                    })

                HttpSender.send_news(
                    webhook_urls=enabled_webhooks,
                    articles=articles_data,
                    http_method=channel.http_method or "POST",
                    request_headers=channel.request_headers,
                    message_template=channel.message_template,
                    channel_type=channel.channel_type or "http_webhook"
                )
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
