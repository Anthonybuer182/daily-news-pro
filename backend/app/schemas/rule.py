from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class RuleBase(BaseModel):
    name: str = Field(..., description="规则名称，用于标识抓取任务，例如：'Pakistan Today 新闻'")

    # 所有抓取配置统一在 extract_config 中，按阶段分层
    extract_config: Optional[str] = Field(default=None, description="""抓取配置，JSON格式。list 和 detail 两阶段各自独立配置。

【完整结构】
{
  "list": {
    "url": "https://example.com/news",
    "fetch_mode": "static|dynamic",
    "content_type": "html|json|xml|markdown|text",
    "max_items": 10,
    "request": {
      "method": "POST",
      "auth": {"type": "bearer", "token": "xxx"},
      "headers": {"Content-Type": "application/json"},
      "body": {"type": "graphql", "query": "..."},
      "timeout": 30
    },
    "selector": "article a",
    "fields": {
      "title": {"op": "css", "selector": "h2", "type": "text"},
      "url": {"op": "css", "selector": "a", "attr": "href"}
    },
    "url_filters": {
      "include": "正则表达式",
      "exclude": ["字符串1", "字符串2"]
    },
    "pagination": {"type": "next-button", "selector": ".next", "max_pages": 5}
  },
  "detail": {
    "fetch_mode": "dynamic",
    "content_type": "html",
    "fields": {
      "title": {"selector": "h1", "type": "text"},
      "content": {"selector": "article", "type": "html"},
      "author": {"selector": ".author", "type": "text"},
      "date": {"selector": "time", "type": "text"}
    }
  }
}

【list 字段说明】
• url: 列表页入口 URL
• fetch_mode: 抓取方式，static（HTTP 直连）或 dynamic（Playwright 浏览器）
• content_type: 响应格式，html/json/xml/markdown/text
• max_items: 最大抓取数量，默认 10
• request: HTTP 请求配置（fetch_mode=static 时使用），包含 method/auth/headers/body/timeout
• selector: 列表项链接选择器（CSS）
• fields: 列表项字段提取配置
• url_filters: 链接过滤，include 白名单（正则），exclude 黑名单（字符串数组）
• pagination: 分页配置

【detail 字段说明】
• fetch_mode: 详情页抓取方式，可与 list 不同（混合模式）
• content_type: 详情页响应格式，默认 html
• fields: 详情页各字段的选择器配置

【示例 - 动态抓取 HTML】
{
  "list": {
    "url": "https://example.com",
    "fetch_mode": "dynamic",
    "content_type": "html",
    "max_items": 10,
    "selector": "article.item a",
    "url_filters": {"exclude": ["/tag/", "/sponsor/"]}
  },
  "detail": {
    "fetch_mode": "dynamic",
    "fields": {
      "title": {"selector": "h1", "type": "text"},
      "content": {"selector": ".article-body", "type": "html"}
    }
  }
}

【示例 - 静态抓取 GraphQL API】
{
  "list": {
    "url": "https://api.example.com/graphql",
    "fetch_mode": "static",
    "content_type": "json",
    "max_items": 20,
    "request": {
      "method": "POST",
      "auth": {"type": "bearer", "token": "your-token"},
      "body": {"type": "graphql", "query": "{ posts { edges { node { id title } } } }"}
    }
  }
}

【示例 - RSS 列表 + 动态详情（混合模式）】
{
  "list": {
    "url": "https://example.com/rss.xml",
    "fetch_mode": "static",
    "content_type": "xml",
    "max_items": 10
  },
  "detail": {
    "fetch_mode": "dynamic",
    "fields": {"content": {"selector": ".article-body", "type": "html"}}
  }
}""")

    # 通用配置
    proxy_config: Optional[str] = Field(default=None, description="""代理配置，JSON格式。

【示例 - 无认证代理】
{"server": "http://proxy:8080"}

【示例 - 带认证代理】
{"server": "http://proxy:8080", "username": "user", "password": "pass"}""")

    # 延迟配置
    delay_min: int = Field(default=1, description="抓取间隔最小秒数。设置随机延迟的下限，防止请求过快被封")
    delay_max: int = Field(default=3, description="抓取间隔最大秒数。设置随机延迟的上限，例如设为1-3秒表示每次请求后等待1-3秒")
    user_agent: Optional[str] = Field(default=None, description="自定义User-Agent字符串。不设置则使用默认浏览器的User-Agent")

    # 定时任务
    status: str = Field(default="disabled", description="规则状态：disabled(禁用)、enabled(启用)。启用后会根据cron_expression执行定时抓取")
    cron_expression: Optional[str] = Field(default=None, description="Cron表达式，用于定时抓取。格式：'0 * * * *' (每小时)，'0 8 * * *' (每天早上8点)，'*/30 * * * *' (每30分钟)")

    # 翻译配置
    translation_config: Optional[str] = Field(
        default=None,
        description="""翻译配置，JSON格式。启用后会对抓取的标题、摘要、内容等进行翻译。

【配置示例】
{
  "target_lang": "zh",
  "source_lang": "en",
  "fields": ["title", "summary", "content"],
  "concurrency": 3
}

【字段说明】
• target_lang: 目标语言 (zh/en/ja/ko/fr/de/es/ru/ar)
• source_lang: 源语言 (空则自动检测)
• fields: 要翻译的字段列表 ["title", "summary", "content"]
• concurrency: 并发翻译数，默认3，避免 API 限流
"""
    )


class RuleCreate(RuleBase):
    pass


class RuleUpdate(RuleBase):
    pass


class Rule(RuleBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
