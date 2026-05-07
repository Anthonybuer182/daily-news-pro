from pydantic import BaseModel, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import json


class ArticleBase(BaseModel):
    rule_id: int
    url: str
    title: Optional[str] = None
    summary: Optional[str] = None
    author: Optional[str] = None
    publish_time: Optional[datetime] = None
    cover_image: Optional[str] = None
    markdown_file: Optional[str] = None
    status: str = "pending"
    error_message: Optional[str] = None


class ArticleCreate(ArticleBase):
    pass


class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    author: Optional[str] = None
    publish_time: Optional[datetime] = None
    cover_image: Optional[str] = None
    images: Optional[List[str]] = None
    markdown_content: Optional[str] = None  # Not stored in DB, used to update markdown file
    status: Optional[str] = None
    error_message: Optional[str] = None
    tags: Optional[List[str]] = None
    extra: Optional[Dict[str, Any]] = None


class Article(ArticleBase):
    id: int
    created_at: datetime
    updated_at: datetime
    rule_render: Optional[str] = None
    rule_name: Optional[str] = None
    tags: Optional[List[str]] = []
    images: Optional[List[str]] = []
    extra: Optional[Dict[str, Any]] = {}

    @field_validator('tags', mode='before')
    @classmethod
    def parse_tags(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                return []
        return v or []

    @field_validator('images', mode='before')
    @classmethod
    def parse_images(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                return []
        return v or []

    @field_validator('extra', mode='before')
    @classmethod
    def parse_extra(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                return {}
        return v or {}

    class Config:
        from_attributes = True
