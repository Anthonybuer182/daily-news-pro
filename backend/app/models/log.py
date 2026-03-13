from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"))
    level = Column(String(20), default="info")
    message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("Job", back_populates="logs")
