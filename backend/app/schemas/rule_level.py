from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class RuleLevelBase(BaseModel):
    level: int
    name: Optional[str] = None
    url: Optional[str] = None
    url_type: str = "static"
    selector_type: str = "css"
    link_selector: Optional[str] = None
    content_selector: Optional[str] = None
    exclude_patterns: Optional[str] = None
    is_final: bool = False
    action_type: str = "none"
    action_config: Optional[str] = None
    pagination_type: str = "none"
    pagination_selector: Optional[str] = None
    pagination_max: int = 10


class RuleLevelCreate(RuleLevelBase):
    pass


class RuleLevelUpdate(RuleLevelBase):
    pass


class RuleLevel(RuleLevelBase):
    id: int
    rule_id: int
    created_at: datetime

    class Config:
        from_attributes = True
