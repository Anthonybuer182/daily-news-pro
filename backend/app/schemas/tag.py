from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class TagBase(BaseModel):
    name: str = Field(..., description="标签名称")


class TagCreate(TagBase):
    pass


class TagUpdate(BaseModel):
    name: Optional[str] = None


class TagResponse(TagBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


