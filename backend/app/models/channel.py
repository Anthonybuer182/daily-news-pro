from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Channel(Base):
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    channel_type = Column(String(50), default="http_webhook")
    push_on_crawl = Column(Boolean, default=False)
    push_on_schedule = Column(Boolean, default=False)
    schedule_time = Column(String(10), default="09:00")
    status = Column(String(20), default="enabled")
    http_method = Column(String(20), default="POST")
    request_headers = Column(Text, default='{"Content-Type": "application/json"}')
    message_template = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    webhooks = relationship("ChannelWebhook", back_populates="channel", cascade="all, delete-orphan")


class ChannelWebhook(Base):
    __tablename__ = "channel_webhooks"

    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey("channels.id", ondelete="CASCADE"), nullable=False)
    webhook_url = Column(String(500), nullable=False)
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    channel = relationship("Channel", back_populates="webhooks")