from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.schemas.rule_level import RuleLevel


class RuleBase(BaseModel):
    name: str
    site_url: Optional[str] = None
    list_url: Optional[str] = None
    list_selector_type: str = "css"
    list_selector: Optional[str] = None
    list_item_selector: Optional[str] = None
    detail_url_pattern: Optional[str] = None
    title_selector_type: str = "css"
    title_selector: Optional[str] = None
    content_selector_type: str = "css"
    content_selector: Optional[str] = None
    author_selector_type: str = "css"
    author_selector: Optional[str] = None
    publish_time_selector_type: str = "css"
    publish_time_selector: Optional[str] = None
    cover_image_selector: Optional[str] = None
    exclude_patterns: Optional[str] = None
    cookie_config: Optional[str] = None
    headers_config: Optional[str] = None
    auth_type: str = "none"
    auth_config: Optional[str] = None
    proxy_config: Optional[str] = None
    crawl_method: str = "playwright"
    crawl_mode: str = "hybrid"
    delay_min: int = 1
    delay_max: int = 3
    user_agent: Optional[str] = None
    status: str = "disabled"
    cron_expression: Optional[str] = None


class RuleCreate(RuleBase):
    pass


class RuleUpdate(RuleBase):
    pass


class Rule(RuleBase):
    id: int
    created_at: datetime
    updated_at: datetime
    levels: List[RuleLevel] = []

    class Config:
        from_attributes = True
