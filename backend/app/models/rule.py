from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Rule(Base):
    __tablename__ = "rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    source_url = Column(String(500), nullable=True)

    # ============ 两个维度设计 ============
    # 维度1: render (是否需要浏览器渲染)
    # 可选值: http (直接HTTP请求), browser (浏览器渲染，支持JS)
    render = Column(String(20), nullable=True)

    # 维度2: content_type (返回内容格式)
    # 可选值: html, xml, json, markdown, text
    content_type = Column(String(20), nullable=True)

    def get_render(self) -> str:
        """获取渲染方式，未设置时默认 browser"""
        return self.render or "browser"

    def get_content_type(self) -> str:
        """获取内容格式，未设置时默认 html"""
        return self.content_type or "html"

    # ============ 通用配置字段 (JSON 格式) ============
    # extract_config: Playwright 抓取配置 (替换原有的分散选择器字段)
    # 格式: {
    #   "list": {
    #     "url": "https://example.com/news",  # 列表页URL
    #     "selector": ".article-list a",      # 文章链接选择器
    #     "attr": "href",                # 链接属性 (默认 href)
    #     "type": "attribute",            # 提取类型：attribute(默认) 或 text
    #     "pagination": {                     # 分页配置 (可选)
    #       "type": "next-button",           # next-button, infinite-scroll, page-param
    #       "selector": ".next-page",        # 下一页按钮选择器
    #       "max_pages": 10                  # 最大页数
    #     }
    #   },
    #   "detail": {
    #     "title": { "selector": "h1.title", "type": "text" },
    #     "content": { "selector": ".article-content", "type": "html" },
    #     "author": { "selector": ".author", "type": "text" },
    #     "date": { "selector": ".date", "type": "text", "format": "YYYY-MM-DD" },
    #     "image": { "selector": "img.cover", "type": "attribute", "attr": "src" }
    #   },
    #   "wait": {
    #     "after_navigate": 1000,            # 导航后等待毫秒数
    #     "before_extract": ".loaded"        # 提取前等待元素
    #   }
    # }
    extract_config = Column(Text)

    # request_config: API 请求配置
    request_config = Column(Text)

    # 最大抓取数量
    max_items = Column(Integer, default=10)

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
