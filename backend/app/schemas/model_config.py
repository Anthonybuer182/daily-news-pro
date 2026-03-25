from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ModelConfigBase(BaseModel):
    name: str = Field(..., description="配置名称，如：OpenAI、Claude、本地模型等")
    api_type: str = Field(default="openai", description="API 类型：openai / anthropic / google")
    api_base: str = Field(..., description="API 地址，如：https://api.openai.com/v1")
    api_key: str = Field(..., description="API 密钥")
    model: str = Field(..., description="模型名称，如：gpt-4o-mini、claude-3-sonnet 等")
    is_default: bool = Field(default=False, description="是否设为默认配置")


class ModelConfigCreate(ModelConfigBase):
    pass


class ModelConfigUpdate(BaseModel):
    name: Optional[str] = None
    api_type: Optional[str] = None
    api_base: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    is_default: Optional[bool] = None


class ModelConfigResponse(ModelConfigBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True