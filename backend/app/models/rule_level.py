from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class RuleLevel(Base):
    __tablename__ = "rule_levels"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("rules.id", ondelete="CASCADE"))
    level = Column(Integer, nullable=False)
    name = Column(String(100))
    url = Column(String(1000))
    url_type = Column(String(20), default="static")
    selector_type = Column(String(20), default="css")
    link_selector = Column(String(1000))
    content_selector = Column(String(1000))
    exclude_patterns = Column(Text)
    is_final = Column(Boolean, default=False)
    action_type = Column(String(20), default="none")
    action_config = Column(Text)
    pagination_type = Column(String(20), default="none")
    pagination_selector = Column(String(500))
    pagination_max = Column(Integer, default=10)
    created_at = Column(DateTime, default=datetime.utcnow)

    rule = relationship("Rule", back_populates="levels")
