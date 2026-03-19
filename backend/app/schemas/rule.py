from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.schemas.rule_level import RuleLevel


class RuleBase(BaseModel):
    name: str = Field(..., description="规则名称，用于标识抓取任务，例如：'Pakistan Today 新闻'")
    source_type: str = Field(default="playwright", description="数据源类型：playwright(浏览器渲染抓取，适用于JS加载的页面)、http(直接HTTP请求，速度快)、rss(RSS订阅源)")
    source_url: Optional[str] = Field(default=None, description="要抓取的网页URL，例如：'https://example.com/news'")

    # 通用配置字段 (JSON 格式)
    field_mapping: Optional[str] = Field(default=None, description="字段映射配置，JSON格式。用于将抓取的原始数据映射到目标字段，格式：{'原始字段': '目标字段'}")
    extract_config: Optional[str] = Field(default=None, description="Playwright抓取配置，JSON格式。最重要的配置项，包含列表选择器、内容选择器、分页等。示例：\n{\n  'list': {\n    'url': 'https://example.com/',\n    'selector': 'a.article-title',  // CSS选择器\n    'max_items': 10  // 最大抓取数量\n  },\n  'detail': {\n    'title': {'selector': 'h1', 'type': 'text'},\n    'content': {'selector': '.article-body', 'type': 'html'}\n  }\n}")
    request_config: Optional[str] = Field(default=None, description="API请求配置，JSON格式。当source_type为http时使用，可配置请求方法、参数、认证等")

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
    auth_config: Optional[str] = Field(default=None, description="认证配置，JSON格式。根据auth_type配置用户名密码或Token等")
    proxy_config: Optional[str] = Field(default=None, description="代理配置，JSON格式。格式：{'server': 'http://proxy:8080', 'username': 'xxx', 'password': 'xxx'}")

    # 延迟配置
    delay_min: int = Field(default=1, description="抓取间隔最小秒数。设置随机延迟的下限，防止请求过快被封")
    delay_max: int = Field(default=3, description="抓取间隔最大秒数。设置随机延迟的上限，例如设为1-3秒表示每次请求后等待1-3秒")
    user_agent: Optional[str] = Field(default=None, description="自定义User-Agent字符串。不设置则使用默认浏览器的User-Agent")

    # 定时任务
    status: str = Field(default="disabled", description="规则状态：disabled(禁用)、enabled(启用)。启用后会根据cron_expression执行定时抓取")
    cron_expression: Optional[str] = Field(default=None, description="Cron表达式，用于定时抓取。格式：'0 * * * *' (每小时)，'0 8 * * *' (每天早上8点)，'*/30 * * * *' (每30分钟)")


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
