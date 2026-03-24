import httpx
import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from jinja2 import Template

logger = logging.getLogger(__name__)


class HttpSender:
    """通用 HTTP 消息发送器，支持 Jinja2 模板渲染"""

    # 飞书默认模板
    FEISHU_DEFAULT_TEMPLATE = """{
  "msg_type": "interactive",
  "card": {
    "header": {
      "title": {
        "tag": "plain_text",
        "content": "📰 今日新闻汇总（{{ articles|length }}篇）"
      },
      "template": "blue"
    },
    "elements": [
      {% for article in articles %}
      {
        "tag": "div",
        "text": {
          "tag": "lark_md",
          "content": "**【{{ article.title }}】**\\\\n\\\\n摘要：{{ article.summary }}\\\\n\\\\n来源：{{ article.rule_name }}{% if article.publish_time %} | 时间：{{ article.publish_time }}{% endif %}\\\\n\\\\n[查看原文]({{ article.url }})"
        }
      }{% if not loop.last %},{"tag": "hr"}{% endif %}
      {% endfor %}
    ]
  }
}"""

    # 钉钉默认模板
    DINGTALK_DEFAULT_TEMPLATE = """{
  "msgtype": "markdown",
  "markdown": {
    "title": "📰 今日新闻汇总",
    "text": "{% for article in articles %}**【{{ article.title }}】**\\\\n\\\\n> {{ article.summary }}\\\\n\\\\n来源：{{ article.rule_name }}{% if article.publish_time %} | {{ article.publish_time }}{% endif %}\\\\n\\\\n[查看原文]({{ article.url }})\\\\n\\\\n---\\\\n\\\\n{% endfor %}"
  }
}"""

    @classmethod
    def get_default_template(cls, channel_type: str) -> str:
        """获取指定渠道类型的默认模板"""
        templates = {
            "feishu": cls.FEISHU_DEFAULT_TEMPLATE,
            "dingtalk": cls.DINGTALK_DEFAULT_TEMPLATE,
            "http_webhook": cls.FEISHU_DEFAULT_TEMPLATE,  # 默认使用飞书模板
        }
        return templates.get(channel_type, cls.FEISHU_DEFAULT_TEMPLATE)

    @staticmethod
    def render_template(template_str: str, articles: List[Dict[str, Any]]) -> Dict:
        """
        使用 Jinja2 渲染消息模板

        Args:
            template_str: Jinja2 模板字符串
            articles: 文章列表

        Returns:
            渲染后的字典（已解析为 JSON）
        """
        try:
            template = Template(template_str)
            rendered = template.render(articles=articles)
            # 修复 JSON 中不允许的空白模式，如 },{ 之间的换行
            import re
            fixed = re.sub(r'\}\s*\n\s*\{', '},{', rendered)
            return json.loads(fixed)
        except Exception as e:
            logger.error(f"模板渲染失败: {e}")
            raise

    @staticmethod
    def send_http_request(
        webhook_url: str,
        method: str,
        headers: Dict[str, str],
        body: Dict
    ) -> bool:
        """
        发送 HTTP 请求

        Args:
            webhook_url: 请求地址
            method: HTTP 方法 (POST, GET, etc.)
            headers: 请求头
            body: 请求体

        Returns:
            是否成功
        """
        try:
            with httpx.Client(timeout=30) as client:
                if method.upper() == "POST":
                    response = client.post(webhook_url, json=body, headers=headers)
                elif method.upper() == "GET":
                    response = client.get(webhook_url, params=body, headers=headers)
                else:
                    response = client.request(method, webhook_url, json=body, headers=headers)

                if response.status_code == 200:
                    try:
                        result = response.json()
                        # 兼容飞书格式
                        if result.get("code") == 0 or result.get("errcode") == 0:
                            logger.info(f"消息发送成功: {webhook_url}")
                            return True
                        else:
                            logger.error(f"平台返回错误: {result}")
                            return False
                    except json.JSONDecodeError:
                        # 有些平台返回纯文本也算成功
                        logger.info(f"消息发送成功（无 JSON 响应）: {webhook_url}")
                        return True
                else:
                    logger.error(f"HTTP 错误 {response.status_code}: {response.text}")
                    return False
        except Exception as e:
            logger.error(f"发送请求失败: {e}")
            return False

    @classmethod
    def send_news(
        cls,
        webhook_urls: List[str],
        articles: List[Dict[str, Any]],
        http_method: str = "POST",
        request_headers: Optional[str] = None,
        message_template: Optional[str] = None,
        channel_type: str = "http_webhook"
    ) -> Dict[str, Any]:
        """
        向多个 Webhook 发送新闻汇总

        Args:
            webhook_urls: Webhook 地址列表
            articles: 文章列表
            http_method: HTTP 方法
            request_headers: 请求头（JSON 字符串）
            message_template: 消息模板（Jinja2 格式）
            channel_type: 渠道类型

        Returns:
            发送结果统计
        """
        # 解析请求头
        try:
            headers = json.loads(request_headers) if request_headers else {"Content-Type": "application/json"}
        except json.JSONDecodeError:
            headers = {"Content-Type": "application/json"}

        # 获取模板
        template_str = message_template or cls.get_default_template(channel_type)

        # 预处理文章数据（格式化时间、转义控制字符等）
        processed_articles = []
        for article in articles:
            processed = dict(article)
            if isinstance(processed.get("publish_time"), datetime):
                processed["publish_time"] = processed["publish_time"].strftime("%Y-%m-%d %H:%M")
            # 转义内容中的控制字符（换行、回车等）
            for field in ["title", "summary", "rule_name", "url"]:
                if processed.get(field) and isinstance(processed[field], str):
                    # 先处理 \\r\\n 和 \\r，再处理 \\n，确保顺序正确
                    processed[field] = processed[field].replace('\r\n', '\\n').replace('\r', '\\n').replace('\n', '\\n')
            processed_articles.append(processed)

        # 渲染消息
        try:
            message_body = cls.render_template(template_str, processed_articles)
        except Exception as e:
            logger.error(f"渲染消息模板失败: {e}")
            # 降级为简单文本消息
            message_body = {
                "msg_type": "text",
                "content": {"text": f"今日新闻汇总：{len(articles)}篇"}
            }

        # 发送到所有 Webhook
        results = {
            "total": len(webhook_urls),
            "success": 0,
            "failed": 0,
            "failed_urls": []
        }

        for url in webhook_urls:
            if cls.send_http_request(url, http_method, headers, message_body):
                results["success"] += 1
            else:
                results["failed"] += 1
                results["failed_urls"].append(url)

        return results

    @classmethod
    def send_test_message(
        cls,
        webhook_url: str,
        http_method: str = "POST",
        request_headers: Optional[str] = None,
        message_template: Optional[str] = None,
        channel_type: str = "http_webhook"
    ) -> bool:
        """发送测试消息"""
        test_article = {
            "title": "这是一条测试消息",
            "summary": "如果您看到此消息，说明推送通道配置正常。",
            "rule_name": "系统测试",
            "publish_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "url": "https://www.feishu.cn"
        }

        try:
            return cls.send_news(
                webhook_urls=[webhook_url],
                articles=[test_article],
                http_method=http_method,
                request_headers=request_headers,
                message_template=message_template,
                channel_type=channel_type
            )["success"] > 0
        except Exception as e:
            logger.error(f"发送测试消息失败: {e}")
            return False