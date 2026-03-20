"""
策略注册表和基类
所有提取策略都需要注册到这里
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import json
import re


class BaseStrategy(ABC):
    """策略基类"""

    name: str = None  # 策略名称，如 "html_list", "rss", "api"
    description: str = ""  # 策略描述

    @abstractmethod
    def can_handle(self, content: str, config: dict) -> bool:
        """判断是否能处理这个内容"""
        pass

    @abstractmethod
    def extract_list(self, content: str, config: dict) -> List[dict]:
        """提取列表项"""
        pass

    def extract_detail(self, content: str, config: dict) -> dict:
        """提取详情（可选实现）"""
        return {}

    def extract_list_urls(self, content: str, config: dict) -> List[str]:
        """专门提取 URL 列表（用于详情页抓取）"""
        return []


class StrategyRegistry:
    """策略注册表"""

    _strategies: Dict[str, BaseStrategy] = {}
    _aliases: Dict[str, str] = {}  # 别名映射

    @classmethod
    def register(cls, strategy: BaseStrategy, aliases: List[str] = None):
        """注册策略"""
        if strategy.name:
            cls._strategies[strategy.name] = strategy

        # 注册别名
        if aliases:
            for alias in aliases:
                cls._aliases[alias] = strategy.name

    @classmethod
    def get(cls, name: str) -> Optional[BaseStrategy]:
        """获取策略"""
        # 先检查别名
        if name in cls._aliases:
            name = cls._aliases[name]

        return cls._strategies.get(name)

    @classmethod
    def list(cls) -> List[str]:
        """列出所有策略"""
        return list(cls._strategies.keys())

    @classmethod
    def auto_detect(cls, content: str, config: dict) -> BaseStrategy:
        """自动检测合适的策略"""
        for strategy in cls._strategies.values():
            if strategy.can_handle(content, config):
                return strategy

        # 默认返回 HTML 列表策略
        return cls.get("html_list")


# ============================================================
# 内置策略实现
# ============================================================

class HTMLListStrategy(BaseStrategy):
    """HTML 列表提取策略"""

    name = "html_list"
    description = "从 HTML 页面提取列表项"

    def can_handle(self, content: str, config: dict) -> bool:
        # 检查是否是 HTML 内容
        return "<html" in content.lower() or "<div" in content.lower() or "<article" in content.lower()

    def extract_list(self, content: str, config: dict) -> List[dict]:
        from app.services.extract_engine import ExtractEngine

        selector = config.get("selector", "a")
        item_fields = config.get("fields", config.get("item_fields", {}))

        if not item_fields:
            # 默认提取链接
            item_fields = {
                "url": {"op": "css", "selector": "a", "attr": "href"},
                "title": {"op": "css", "selector": "a", "type": "text"}
            }

        return ExtractEngine.extract_list_items(content, {
            "selector": selector,
            "fields": item_fields
        })

    def extract_list_urls(self, content: str, config: dict) -> List[str]:
        from app.services.extract_engine import ExtractEngine

        selector = config.get("selector", "a")
        items = ExtractEngine.extract_list_items(content, {
            "selector": selector,
            "fields": {"url": {"op": "css", "selector": "a", "attr": "href"}}}
        )

        return [item.get("url") for item in items if item.get("url")]


class RSSStrategy(BaseStrategy):
    """RSS 订阅源策略"""

    name = "rss"
    description = "解析 RSS/Atom 订阅源"

    def can_handle(self, content: str, config: dict) -> bool:
        return "<rss" in content.lower() or "<feed" in content.lower() or "<?xml" in content[:100].lower()

    def extract_list(self, content: str, config: dict) -> List[dict]:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(content, 'xml')
        items = soup.find_all(['item', 'entry']) or []

        field_mapping = config.get("field_mapping", {})
        if not field_mapping:
            field_mapping = {
                "title": "title",
                "link": "link",
                "description": "description"
            }

        results = []
        for item in items:
            record = {}
            for target_field, source_field in field_mapping.items():
                element = item.find(source_field.lower())
                if not element:
                    element = item.find(source_field.upper())
                record[target_field] = element.get_text(strip=True) if element else None

            # 获取链接
            link = record.get("link")
            if not link:
                link_elem = item.find("link")
                if link_elem:
                    link = link_elem.get("href") or link_elem.get_text(strip=True)

            record["url"] = link
            results.append(record)

        return results


class APIStrategy(BaseStrategy):
    """API 接口策略"""

    name = "api"
    description = "从 API 接口获取 JSON 数据"

    def can_handle(self, content: str, config: dict) -> bool:
        # 尝试解析为 JSON
        try:
            json.loads(content)
            return True
        except:
            return False

    def extract_list(self, content: str, config: dict) -> List[dict]:
        import json

        data = json.loads(content)
        api_config = config.get("api", {})
        items_path = api_config.get("items_path", "data")
        mapping = api_config.get("mapping", {})

        # 导航到 items
        for key in items_path.split("."):
            if key.startswith("$"):
                continue
            if isinstance(data, dict):
                data = data.get(key, [])
            elif isinstance(data, list):
                try:
                    data = data[int(key)]
                except:
                    data = []

        if not isinstance(data, list):
            data = [data]

        results = []
        for item in data:
            record = {}
            for target_field, source_path in mapping.items():
                value = self._get_nested(item, source_path)
                record[target_field] = value
            results.append(record)

        return results

    def _get_nested(self, data: dict, path: str) -> Any:
        """获取嵌套字段，支持点号路径"""
        parts = path.split(".")
        current = data
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list):
                try:
                    current = current[int(part)]
                except:
                    return None
            else:
                return None
        return current


class MarkdownGitHubStrategy(BaseStrategy):
    """GitHub Markdown 内容策略"""

    name = "markdown_github"
    description = "从 Markdown 文件提取 GitHub 仓库链接"
    aliases = ["github_readme", "markdown"]

    def can_handle(self, content: str, config: dict) -> bool:
        # 检查是否是 Markdown 内容
        is_markdown = (
            content.strip().startswith("#") or
            content.strip().startswith("##") or
            "## " in content[:500]
        )
        has_github_links = "github.com" in content

        return is_markdown and has_github_links

    def extract_list(self, content: str, config: dict) -> List[dict]:
        """从 Markdown 中提取 GitHub 仓库"""
        config = config or {}

        # 提取配置
        url_pattern = config.get("url_pattern", r"https://github\.com/([\w\-\.]+)/([\w\-\.]+)")
        skip_owners = config.get("skip_owners", ["solutions", "security", "features", "resources", "github"])
        skip_repos = config.get("skip_repos", ["github-daily-rank", "weekly", "monthly", "industry", "advanced-security"])

        # 提取所有 GitHub URL
        matches = re.findall(url_pattern, content)

        items = []
        seen = set()

        for owner, repo in matches:
            # 跳过白名单
            if owner in skip_owners or repo in skip_repos:
                continue

            url = f"https://github.com/{owner}/{repo}"
            if url in seen:
                continue
            seen.add(url)

            # 提取标题（URL 前后的粗体文本）
            title = f"{owner} / {repo}"
            desc = None

            # 查找 URL 附近的标题
            url_idx = content.find(url)
            if url_idx > 0:
                before = content[max(0, url_idx - 300):url_idx]
                bold_match = re.search(r'\*\*([^*]+)\*\*', before)
                if bold_match:
                    title = bold_match.group(1)
                    # 清理标题
                    title = re.sub(r'[^\w\s\-\./]', '', title).strip()

                # 查找描述
                after = content[url_idx:url_idx + 200]
                desc_match = re.search(r'([^*`\n]{10,100})', after)
                if desc_match:
                    desc = desc_match.group(1).strip()

            items.append({
                "url": url,
                "title": title,
                "description": desc
            })

        return items


class MarkdownGenericStrategy(BaseStrategy):
    """通用 Markdown 策略"""

    name = "markdown_generic"
    description = "通用 Markdown 内容提取"

    def can_handle(self, content: str, config: dict) -> bool:
        return content.strip().startswith("#") or "## " in content[:100]

    def extract_list(self, content: str, config: dict) -> List[dict]:
        """从 Markdown 提取链接列表"""
        # 提取所有 Markdown 链接
        link_pattern = r'\[([^\]]+)\]\((https?://[^\)]+)\)'
        matches = re.findall(link_pattern, content)

        items = []
        for title, url in matches:
            if url.startswith("http"):
                items.append({
                    "url": url,
                    "title": title.strip()
                })

        return items


class XPathStrategy(BaseStrategy):
    """XPath 提取策略"""

    name = "xpath"
    description = "使用 XPath 提取内容"

    def can_handle(self, content: str, config: dict) -> bool:
        return config.get("list", {}).get("xpath") is not None

    def extract_list(self, content: str, config: dict) -> List[dict]:
        from app.services.extract_engine import ExtractEngine

        xpath = config.get("list", {}).get("xpath")
        fields = config.get("list", {}).get("fields", {})

        # 使用 XPath 提取
        handler = ExtractEngine.get_handler("xpath")
        elements = handler.extract(content, {"xpath": xpath, "multiple": True})

        items = []
        if elements:
            for el in elements:
                if hasattr(el, 'get'):
                    item = {}
                    for field_name, field_config in fields.items():
                        sel = field_config.get("selector")
                        if sel:
                            found = el.xpath(sel) if hasattr(el, 'xpath') else None
                            if found:
                                item[field_name] = str(found[0]) if found else None
                        else:
                            item[field_name] = str(el) if el else None
                    items.append(item)
                elif isinstance(el, str):
                    items.append({"url": el, "title": el})

        return items


class RegexStrategy(BaseStrategy):
    """正则提取策略"""

    name = "regex"
    description = "使用正则表达式提取内容"

    def can_handle(self, content: str, config: dict) -> bool:
        return config.get("list", {}).get("regex") is not None

    def extract_list(self, content: str, config: dict) -> List[dict]:
        regex = config.get("list", {}).get("regex")
        fields = config.get("list", {}).get("fields", {})

        matches = re.finditer(regex, content)

        items = []
        for match in matches:
            item = {}
            if isinstance(match, re.Match):
                groups = match.groups()
                # 尝试填充字段
                for i, (field_name, field_config) in enumerate(fields.items()):
                    if i < len(groups):
                        item[field_name] = groups[i]
                    else:
                        # 使用整个匹配
                        item[field_name] = match.group(0)
                if not fields:
                    item["url"] = match.group(0) if match.groups() else match.group(0)
            items.append(item)

        return items


# ============================================================
# 注册内置策略
# ============================================================

StrategyRegistry.register(HTMLListStrategy())
StrategyRegistry.register(RSSStrategy())
StrategyRegistry.register(APIStrategy())
StrategyRegistry.register(MarkdownGitHubStrategy(), aliases=["github", "markdown_github"])
StrategyRegistry.register(MarkdownGenericStrategy())
StrategyRegistry.register(XPathStrategy())
StrategyRegistry.register(RegexStrategy())
