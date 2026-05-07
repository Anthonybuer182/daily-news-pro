from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Rule(Base):
    __tablename__ = "rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)

    # 所有抓取配置统一在 extract_config 中，按阶段分层：
    # {
    #   "list": {
    #     "url": "https://...",           列表页入口 URL
    #     "fetch_mode": "static|dynamic",  抓取方式（static=HTTP直连, dynamic=Playwright浏览器）
    #     "content_type": "html|json|xml|markdown|text",  响应格式
    #     "max_items": 10,                最大抓取数量
    #     "request": {                    HTTP 请求配置（fetch_mode=static 时使用）
    #       "method": "POST",
    #       "auth": {"type": "bearer", "token": "..."},
    #       "headers": {...},
    #       "body": {...},
    #       "timeout": 30
    #     },
    #     "selector": "article a",        链接选择器
    #     "fields": {...},                列表项字段提取
    #     "url_filters": {...},           链接过滤
    #     "pagination": {...}             分页配置
    #   },
    #   "detail": {
    #     "fetch_mode": "dynamic",        详情页抓取方式（可与 list 不同）
    #     "content_type": "html",         详情页内容格式（默认 html）
    #     "fields": {                     详情页字段提取
    #       "title": {"selector": "h1", "type": "text"},
    #       "content": {"selector": "article", "type": "html"}
    #     }
    #   }
    # }
    extract_config = Column(Text)

    # 通用配置
    proxy_config = Column(String(500))

    # 延迟配置
    delay_min = Column(Integer, default=1)
    delay_max = Column(Integer, default=3)
    user_agent = Column(String(500))

    # 定时任务配置
    status = Column(String(20), default="disabled")
    cron_expression = Column(String(100))

    # 翻译配置
    translation_config = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    articles = relationship("Article", back_populates="rule")
    jobs = relationship("Job", back_populates="rule")
