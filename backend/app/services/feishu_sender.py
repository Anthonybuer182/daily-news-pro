import httpx
import logging
from typing import List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class FeishuSender:
    """飞书消息发送服务"""

    @staticmethod
    def build_article_element(article) -> dict:
        """构建单个文章的消息元素"""
        title = article.get("title", "无标题")
        summary = article.get("summary", "无摘要")
        source = article.get("rule_name", article.get("source", "未知来源"))
        publish_time = ""
        if article.get("publish_time"):
            if isinstance(article["publish_time"], datetime):
                publish_time = article["publish_time"].strftime("%Y-%m-%d %H:%M")
            else:
                publish_time = str(article["publish_time"])
        url = article.get("url", "")

        content = f"**【{title}】**\n\n"
        content += f"摘要：{summary}\n\n"
        content += f"来源：{source}"
        if publish_time:
            content += f" | 时间：{publish_time}"

        element = {
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": content
            }
        }

        if url:
            element["text"]["content"] += f"\n\n[查看原文]({url})"

        return element

    @staticmethod
    def build_news_card(articles: List[dict], title: Optional[str] = None) -> dict:
        """构建新闻汇总卡片"""
        if not title:
            title = f"📰 今日新闻汇总（{len(articles)}篇）"

        if not articles:
            title = "📰 今日无新新闻"

        elements = []

        for i, article in enumerate(articles):
            element = FeishuSender.build_article_element(article)
            elements.append(element)
            if i < len(articles) - 1:
                elements.append({"tag": "hr"})

        card = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": title
                    },
                    "template": "blue"
                },
                "elements": elements if articles else [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "plain_text",
                            "content": "今日暂无新抓取的文章"
                        }
                    }
                ]
            }
        }

        return card

    @staticmethod
    def send_to_webhook(webhook_url: str, content: dict) -> bool:
        """发送消息到单个 Webhook"""
        try:
            with httpx.Client(timeout=10) as client:
                response = client.post(webhook_url, json=content)
                if response.status_code == 200:
                    result = response.json()
                    if result.get("code") == 0 or result.get("StatusCode") == 0:
                        logger.info(f"消息发送成功: {webhook_url}")
                        return True
                    else:
                        logger.error(f"飞书返回错误: {result}")
                        return False
                else:
                    logger.error(f"HTTP 错误: {response.status_code} - {response.text}")
                    return False
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            return False

    @classmethod
    def send_news(cls, webhook_urls: List[str], articles: List[dict], title: Optional[str] = None) -> dict:
        """向多个 Webhook 发送新闻汇总"""
        card = cls.build_news_card(articles, title)

        results = {
            "total": len(webhook_urls),
            "success": 0,
            "failed": 0,
            "failed_urls": []
        }

        for url in webhook_urls:
            if cls.send_to_webhook(url, card):
                results["success"] += 1
            else:
                results["failed"] += 1
                results["failed_urls"].append(url)

        return results

    @classmethod
    def send_test_message(cls, webhook_url: str) -> bool:
        """发送测试消息"""
        test_article = {
            "title": "这是一条测试消息",
            "summary": "如果您看到此消息，说明飞书推送通道配置正常。",
            "rule_name": "系统测试",
            "publish_time": datetime.now(),
            "url": "https://www.feishu.cn"
        }
        card = cls.build_news_card([test_article], "🧪 推送测试消息")
        return cls.send_to_webhook(webhook_url, card)