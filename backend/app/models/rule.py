from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Rule(Base):
    __tablename__ = "rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    site_url = Column(String(500))
    list_url = Column(String(500))
    list_selector_type = Column(String(50), default="css")
    list_selector = Column(String(1000))
    list_item_selector = Column(String(1000))
    detail_url_pattern = Column(String(1000))
    title_selector_type = Column(String(50), default="css")
    title_selector = Column(String(1000))
    content_selector_type = Column(String(50), default="css")
    content_selector = Column(String(1000))
    author_selector_type = Column(String(50), default="css")
    author_selector = Column(String(1000))
    publish_time_selector_type = Column(String(50), default="css")
    publish_time_selector = Column(String(1000))
    cover_image_selector = Column(String(1000))
    exclude_patterns = Column(Text)
    cookie_config = Column(Text)
    headers_config = Column(Text)
    auth_type = Column(String(50), default="none")
    auth_config = Column(Text)
    proxy_config = Column(Text)
    crawl_method = Column(String(50), default="playwright")
    crawl_mode = Column(String(20), default="hybrid")
    delay_min = Column(Integer, default=1)
    delay_max = Column(Integer, default=3)
    user_agent = Column(String(500))
    status = Column(String(20), default="disabled")
    cron_expression = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    levels = relationship("RuleLevel", back_populates="rule", cascade="all, delete-orphan")
    articles = relationship("Article", back_populates="rule")
    jobs = relationship("Job", back_populates="rule")
