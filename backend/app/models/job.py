from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("rules.id", ondelete="CASCADE"))
    status = Column(String(20), default="pending")
    trigger_type = Column(String(20), default="manual")
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    articles_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    rule = relationship("Rule", back_populates="jobs")
    logs = relationship("Log", back_populates="job", cascade="all, delete-orphan")
