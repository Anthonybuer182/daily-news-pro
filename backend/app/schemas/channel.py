from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ChannelWebhookBase(BaseModel):
    webhook_url: str
    is_enabled: bool = True


class ChannelWebhookCreate(ChannelWebhookBase):
    pass


class ChannelWebhook(ChannelWebhookBase):
    id: int
    channel_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ChannelBase(BaseModel):
    name: str
    channel_type: str = "http_webhook"
    push_on_crawl: bool = False
    push_on_schedule: bool = False
    schedule_time: str = "09:00"
    status: str = "enabled"
    http_method: str = "POST"
    request_headers: str = '{"Content-Type": "application/json"}'
    message_template: Optional[str] = None


class ChannelCreate(ChannelBase):
    webhooks: List[ChannelWebhookCreate] = []


class ChannelUpdate(BaseModel):
    name: Optional[str] = None
    push_on_crawl: Optional[bool] = None
    push_on_schedule: Optional[bool] = None
    schedule_time: Optional[str] = None
    status: Optional[str] = None
    http_method: Optional[str] = None
    request_headers: Optional[str] = None
    message_template: Optional[str] = None


class Channel(ChannelBase):
    id: int
    created_at: datetime
    updated_at: datetime
    webhooks: List[ChannelWebhook] = []

    class Config:
        from_attributes = True