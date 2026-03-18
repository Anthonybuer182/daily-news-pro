from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Rule(Base):
    __tablename__ = "rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)

    # 抓取方式: rss, api, playwright
    source_type = Column(String(20), default="playwright")

    # 统一URL字段（根据 source_type 含义不同）
    source_url = Column(String(500))

    # ============ 通用配置字段 (JSON 格式) ============
    # field_mapping: RSS/API 字段映射配置
    field_mapping = Column(Text)

    # extract_config: Playwright 抓取配置 (替换原有的分散选择器字段)
    # 格式: {
    #   "list": {
    #     "url": "https://example.com/news",  # 列表页URL
    #     "selector": ".article-list a",      # 文章链接选择器
    #     "link_attr": "href",                # 链接属性 (默认 href)
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

    # ============ 旧的选择器字段 (保留用于兼容) ============
    # Playwright 专用：列表页配置
    list_selector_type = Column(String(50), default="css")
    list_selector = Column(String(1000))
    list_item_selector = Column(String(1000))
    detail_url_pattern = Column(String(1000))

    # Playwright 专用：内容选择器
    title_selector_type = Column(String(50), default="css")
    title_selector = Column(String(1000))
    content_selector_type = Column(String(50), default="css")
    content_selector = Column(String(1000))
    author_selector_type = Column(String(50), default="css")
    author_selector = Column(String(1000))
    publish_time_selector_type = Column(String(50), default="css")
    publish_time_selector = Column(String(1000))
    cover_image_selector = Column(String(1000))

    # 通用配置
    exclude_patterns = Column(Text)
    cookie_config = Column(Text)
    headers_config = Column(Text)
    auth_type = Column(String(50), default="none")
    auth_config = Column(Text)
    proxy_config = Column(String(500))

    # 延迟配置
    delay_min = Column(Integer, default=1)
    delay_max = Column(Integer, default=3)
    user_agent = Column(String(500))

    # 定时任务配置
    status = Column(String(20), default="disabled")
    cron_expression = Column(String(100))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    levels = relationship("RuleLevel", back_populates="rule", cascade="all, delete-orphan")
    articles = relationship("Article", back_populates="rule")
    jobs = relationship("Job", back_populates="rule")
