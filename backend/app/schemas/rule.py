from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.schemas.rule_level import RuleLevel


class RuleBase(BaseModel):
    name: str
    source_type: str = "playwright"
    source_url: Optional[str] = None

    # 通用配置字段 (JSON 格式)
    field_mapping: Optional[str] = None
    extract_config: Optional[str] = None  # Playwright 抓取配置
    request_config: Optional[str] = None  # API 请求配置

    # 旧的选择器字段 (保留用于兼容)
    list_selector_type: str = "css"
    list_selector: Optional[str] = None
    list_item_selector: Optional[str] = None
    detail_url_pattern: Optional[str] = None

    # Playwright 专用：内容选择器
    title_selector_type: str = "css"
    title_selector: Optional[str] = None
    content_selector_type: str = "css"
    content_selector: Optional[str] = None
    author_selector_type: str = "css"
    author_selector: Optional[str] = None
    publish_time_selector_type: str = "css"
    publish_time_selector: Optional[str] = None
    cover_image_selector: Optional[str] = None

    # 通用配置
    exclude_patterns: Optional[str] = None
    cookie_config: Optional[str] = None
    headers_config: Optional[str] = None
    auth_type: str = "none"
    auth_config: Optional[str] = None
    proxy_config: Optional[str] = None

    # 延迟配置
    delay_min: int = 1
    delay_max: int = 3
    user_agent: Optional[str] = None

    # 定时任务
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
