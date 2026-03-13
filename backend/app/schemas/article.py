from pydantic import BaseModel
from typing import Optional
from datetime import datetime


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
    markdown_file: Optional[str] = None
    status: Optional[str] = None
    error_message: Optional[str] = None


class Article(ArticleBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
