from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.schemas.rule_level import RuleLevel


class RuleBase(BaseModel):
    name: str = Field(..., description="规则名称，用于标识抓取任务，例如：'Pakistan Today 新闻'")

    # ============ 两个维度设计 ============
    # 维度1: render (是否需要浏览器渲染)
    # 可选值: http (直接HTTP请求), browser (浏览器渲染，支持JS)
    # 可不设置，会根据 content_type 自动推断
    render: Optional[str] = Field(default=None, description="""渲染方式：
• http：直接HTTP请求，速度快，适用于静态内容（XML、JSON、Markdown等）
• browser：浏览器渲染抓取，适用于JS加载的动态页面
• 不设置：根据 content_type 自动推断""")

    # 维度2: content_type (返回内容格式)
    # 可选值: html, xml, json, markdown, text
    # 可不设置，默认 html
    content_type: Optional[str] = Field(default=None, description="""内容格式：
• html：HTML 网页（默认）
• xml：XML 格式（RSS/Atom）
• json：JSON API 接口
• markdown：Markdown 文件（如 GitHub README）
• text：纯文本
• 不设置：默认 html""")

    source_url: Optional[str] = Field(default=None, description="要抓取的 URL，例如：'https://example.com/news'")

    # 通用配置字段 (JSON 格式) - 统一的 extract_config
    field_mapping: Optional[str] = Field(default=None, description="字段映射配置，JSON格式。用于API/RSS等场景，将原始数据字段映射到目标字段")
    extract_config: Optional[str] = Field(default=None, description="""提取配置，JSON格式。统一配置格式：

【通用结构】
{
  "list": {
    "selector": "CSS选择器",
    "xpath": "XPath表达式",
    "regex": "正则表达式",
    "fields": {
      "url": {"op": "css", "selector": "a", "attr": "href"},
      "title": {"op": "css", "selector": "h2", "type": "text"}
    },
    "max_items": 10,
    "pagination": {...}
  },
  "detail": {
    "fields": {...}
  }
}

【支持的提取操作 (op)】
• css：CSS选择器提取
• xpath：XPath表达式提取
• regex：正则表达式提取
• json_path：JSON路径提取
• template：模板格式化
• nearby：附近内容提取
• chain：链式操作
• switch：条件选择

【示例 - HTML列表】
{
  "list": {
    "selector": "article.item",
    "fields": {
      "title": {"op": "css", "selector": "h2", "type": "text"},
      "url": {"op": "css", "selector": "a", "attr": "href"},
      "desc": {"op": "css", "selector": "p", "type": "text"}
    },
    "max_items": 10
  }
}

【示例 - GitHub README】
{
  "strategy": "markdown_github",
  "list": {
    "url_pattern": "https://github\\.com/[\\w-]+/[\\w-]+",
    "skip_owners": ["solutions"],
    "skip_repos": ["weekly", "monthly"]
  }
}

【示例 - RSS】
{
  "strategy": "rss",
  "list": {
    "fields": {
      "title": "title",
      "link": "link",
      "description": "description"
    }
  }
}""")
    request_config: Optional[str] = Field(default=None, description="""API请求配置，JSON格式。当render为http时使用，可配置请求方法、参数、认证等。

【完整配置示例 - GraphQL】
{
  "method": "POST",
  "headers": {"X-Custom-Header": "value"},
  "body": {
    "type": "graphql",
    "query": "{ posts(first: 20) { edges { node { id name tagline } } } }",
    "variables": {"postedAfter": "2026-03-20T00:00:00Z"}
  },
  "timeout": 30
}

【REST API POST 示例】
{
  "method": "POST",
  "params": {"page": 1, "limit": 10},
  "headers": {"Content-Type": "application/json"},
  "body": {
    "type": "json",
    "data": {"search": "keyword", "filters": {"category": "news"}}
  },
  "timeout": 30
}

【支持的配置项】
• method: 请求方法 (GET/POST/PUT/DELETE)，默认 GET
• params: URL 查询参数 (dict)
• headers: 自定义请求头 (dict)
• body.type: body 类型 (json/form/graphql/raw)
• body.data: 请求体数据
• body.query: GraphQL 查询语句
• body.variables: GraphQL 变量 (dict)
• timeout: 请求超时时间 (秒)""")

    # 旧的选择器字段 (保留用于兼容)
    list_selector_type: str = Field(default="css", description="列表选择器类型：css(CSS选择器) 或 xpath(XPath表达式)")
    list_selector: Optional[str] = Field(default=None, description="文章列表的CSS/XPath选择器，例如：'div.article-list a' 或 '//div[@class=\"article\"]/a'")
    list_item_selector: Optional[str] = Field(default=None, description="列表中每个文章项的选择器，用于精确定位文章链接元素")
    detail_url_pattern: Optional[str] = Field(default=None, description="文章URL正则表达式，用于过滤有效文章链接。例如：'https://example.com/article/\\d+' 只匹配符合条件的URL")

    # Playwright 专用：内容选择器
    title_selector_type: str = Field(default="css", description="标题选择器类型：css 或 xpath")
    title_selector: Optional[str] = Field(default=None, description="文章标题选择器，例如：'h1.entry-title' 或 '//h1[@class=\"title\"]'")
    content_selector_type: str = Field(default="css", description="内容选择器类型：css 或 xpath")
    content_selector: Optional[str] = Field(default=None, description="文章内容选择器，例如：'div.article-content'。type可设为'html'(保留HTML标签)或'text'(纯文本)")
    author_selector_type: str = Field(default="css", description="作者选择器类型：css 或 xpath")
    author_selector: Optional[str] = Field(default=None, description="文章作者选择器，例如：'span.author-name' 或 '//a[@rel=\"author\"]'")
    publish_time_selector_type: str = Field(default="css", description="发布时间选择器类型：css 或 xpath")
    publish_time_selector: Optional[str] = Field(default=None, description="文章发布时间选择器，例如：'time.publish-date'。抓取后会自动解析常见日期格式")
    cover_image_selector: Optional[str] = Field(default=None, description="封面图片选择器，例如：'img.article-cover'。支持从src或data-src属性获取图片URL")

    # 通用配置
    exclude_patterns: Optional[str] = Field(default=None, description="排除URL正则表达式，多个用逗号分隔。例如：'\\/category\\/ads,\\/tag\\/sponsored' 排除广告和赞助内容")
    cookie_config: Optional[str] = Field(default=None, description="Cookie配置，JSON格式。用于需要登录认证的网站，例如：{'name': 'session', 'value': 'xxx'}")
    headers_config: Optional[str] = Field(default=None, description="自定义请求头，JSON格式。例如：{'Referer': 'https://example.com', 'Accept-Language': 'en-US'}")
    auth_type: str = Field(default="none", description="认证类型：none(无认证)、basic(HTTP Basic)、bearer(Bearer Token)、cookie(Cookie认证)")
    auth_config: Optional[str] = Field(default=None, description="""认证配置，JSON格式。根据auth_type配置用户名密码或Token等。

【Bearer Token 示例】
{"type": "bearer", "token": "your-token-here"}

【Basic Auth 示例】
{"type": "basic", "username": "user", "password": "pass"}

【Cookie 认证示例】
{"type": "cookie", "name": "session", "value": "xxx"}""")
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
  "enabled": true,
  "target_lang": "zh",
  "source_lang": "en",
  "fields": ["title", "summary", "content"],
  "translate_summary": true,
  "translate_content": true
}

【字段说明】
• enabled: 是否启用翻译
• target_lang: 目标语言 (zh/en/ja/ko/fr/de/es/ru/ar)
• source_lang: 源语言 (空则自动检测)
• fields: 要翻译的字段列表 ["title", "summary"]
• translate_summary: 是否翻译摘要
• translate_content: 是否翻译正文 (markdown)
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
    levels: List[RuleLevel] = []

    class Config:
        from_attributes = True
