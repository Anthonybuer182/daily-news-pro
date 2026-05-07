from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("rules.id", ondelete="CASCADE"))
    url = Column(String(1000), nullable=False)
    title = Column(String(500))
    summary = Column(Text)
    author = Column(String(255))
    publish_time = Column(DateTime)
    cover_image = Column(String(500))
    markdown_file = Column(String(500))
    status = Column(String(20), default="pending")
    error_message = Column(Text)
    tags = Column(Text)   # JSON 格式存储标签数组，如 '["AI", "创业"]'
    images = Column(Text) # JSON 格式存储图片 URL 数组，如 '["url1", "url2"]'
    extra = Column(Text)  # JSON 格式存储扩展字段，如 '{"投票数": 123, "评论数": 45}'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    rule = relationship("Rule", back_populates="articles")
