"""
通用提取引擎
支持多种提取操作：regex, css, xpath, json_path, template, nearby 等
"""

import re
import json
from typing import List, Dict, Any, Optional, Callable
from bs4 import BeautifulSoup
from lxml import etree
from abc import ABC, abstractmethod


class OperationHandler:
    """操作处理器基类"""

    name: str = None

    def extract(self, content: str, config: dict, context: dict = None) -> Any:
        """提取内容"""
        raise NotImplementedError


class RegexHandler(OperationHandler):
    """正则提取操作"""
    name = "regex"

    def extract(self, content: str, config: dict, context: dict = None) -> Any:
        pattern = config.get("pattern")
        if not pattern:
            return None

        flags = config.get("flags", 0)
        matches = re.findall(pattern, content, flags)

        if config.get("multiple", False):
            # 返回所有匹配
            return matches
        else:
            # 返回第一个匹配
            return matches[0] if matches else None


class CSSTHandler(OperationHandler):
    """CSS 选择器提取操作"""
    name = "css"

    def extract(self, content: str, config: dict, context: dict = None) -> Any:
        selector = config.get("selector")
        if not selector:
            return None

        soup = BeautifulSoup(content, 'lxml')
        elements = soup.select(selector)

        extract_type = config.get("type", "text")  # text, html, attribute
        attr = config.get("attr", "href")

        if config.get("multiple", False):
            results = []
            for el in elements:
                results.append(self._extract_single(el, extract_type, attr))
            return results
        else:
            return self._extract_single(elements[0] if elements else None, extract_type, attr)

    def _extract_single(self, element, extract_type: str, attr: str):
        if element is None:
            return None

        if extract_type == "text":
            return element.get_text(strip=True)
        elif extract_type == "html":
            return str(element)
        elif extract_type == "attribute":
            return element.get(attr)
        return str(element)


class XPathHandler(OperationHandler):
    """XPath 提取操作"""
    name = "xpath"

    def extract(self, content: str, config: dict, context: dict = None) -> Any:
        xpath = config.get("xpath")
        if not xpath:
            return None

        try:
            parser = etree.HTMLParser()
            tree = etree.fromstring(content, parser)

            results = tree.xpath(xpath)

            if config.get("multiple", False):
                return [self._process_result(r) for r in results]
            else:
                return self._process_result(results[0]) if results else None
        except Exception as e:
            print(f"XPath error: {e}")
            return None

    def _process_result(self, result):
        if hasattr(result, 'text'):
            return result.text.strip() if result.text else str(result)
        return str(result)


class JSONPathHandler(OperationHandler):
    """JSON 路径提取操作"""
    name = "json_path"

    def extract(self, content: str, config: dict, context: dict = None) -> Any:
        # 如果 content 不是 JSON 字符串，尝试解析
        if isinstance(content, str):
            try:
                data = json.loads(content)
            except:
                return None
        else:
            data = content

        path = config.get("path", "$")
        multiple = config.get("multiple", False)

        # 简单 JSON path 实现（支持 $.key 和 $[index]）
        try:
            results = self._navigate(data, path)
            if isinstance(results, list):
                return results if multiple else (results[0] if results else None)
            return results
        except:
            return None

    def _navigate(self, data, path: str):
        """简单 JSON path 导航"""
        if path.startswith("$."):
            key = path[2:]
            return data.get(key) if isinstance(data, dict) else None
        elif path.startswith("$["):
            # 数组索引
            idx_str = path[2:-1]
            try:
                idx = int(idx_str)
                return data[idx] if isinstance(data, list) and len(data) > idx else None
            except:
                return None
        elif path.startswith("$"):
            return data
        return data


class TemplateHandler(OperationHandler):
    """模板处理操作"""
    name = "template"

    def extract(self, content: str, config: dict, context: dict = None) -> Any:
        template = config.get("template", "")
        from_field = config.get("from")

        # 从上下文获取数据
        if from_field and context:
            value = context.get(from_field)
            if value is not None:
                return template.format(**context)
        elif context:
            return template.format(**context)

        return template


class NearbyHandler(OperationHandler):
    """附近内容提取操作"""
    name = "nearby"

    def extract(self, content: str, config: dict, context: dict = None) -> Any:
        """从已提取的字段附近查找内容"""
        from_field = config.get("from")  # 基于哪个字段
        direction = config.get("direction", "after")  # before, after
        max_chars = config.get("max_chars", 200)
        pattern = config.get("pattern")  # 可选：正则模式

        if not from_field or not context:
            return None

        anchor = context.get(from_field)
        if not anchor or anchor not in content:
            return None

        idx = content.find(anchor)

        if direction == "before":
            text = content[max(0, idx - max_chars):idx]
        else:  # after
            text = content[idx + len(anchor):idx + len(anchor) + max_chars]

        if pattern:
            match = re.search(pattern, text)
            return match.group(1) if match else text.strip()
        return text.strip()


class SplitHandler(OperationHandler):
    """分割操作"""
    name = "split"

    def extract(self, content: str, config: dict, context: dict = None) -> Any:
        """分割文本并提取部分"""
        separator = config.get("separator", "\n")
        index = config.get("index", 0)
        content_field = config.get("from")

        # 从上下文或直接内容获取
        text = context.get(content_field, content) if context else content

        if not text:
            return None

        parts = text.split(separator)
        try:
            return parts[index].strip()
        except IndexError:
            return None


class ChainHandler(OperationHandler):
    """链式操作"""
    name = "chain"

    def extract(self, content: str, config: dict, context: dict = None) -> Any:
        """组合多个操作"""
        operations = config.get("operations", [])

        current = content
        ctx = context.copy() if context else {}

        for op_config in operations:
            op_name = op_config.get("op")
            handler = ExtractEngine.get_handler(op_name)
            if handler:
                result = handler.extract(current, op_config, ctx)
                field_name = op_config.get("as")
                if field_name:
                    ctx[field_name] = result
                current = result if result else current

        return current


class SwitchHandler(OperationHandler):
    """条件操作"""
    name = "switch"

    def extract(self, content: str, config: dict, context: dict = None) -> Any:
        """根据条件选择不同的提取方式"""
        field = config.get("field")
        value = context.get(field) if context else None

        cases = config.get("cases", {})
        default = config.get("default")

        if value in cases:
            case_config = cases[value]
            op_name = case_config.get("op")
            handler = ExtractEngine.get_handler(op_name)
            if handler:
                return handler.extract(content, case_config, context)

        if default:
            op_name = default.get("op")
            handler = ExtractEngine.get_handler(op_name)
            if handler:
                return handler.extract(content, default, context)

        return None


class ExtractEngine:
    """通用提取引擎"""

    # 操作处理器注册表
    _handlers: Dict[str, OperationHandler] = {}

    @classmethod
    def register(cls, handler: OperationHandler):
        """注册操作处理器"""
        if handler.name:
            cls._handlers[handler.name] = handler

    @classmethod
    def get_handler(cls, name: str) -> Optional[OperationHandler]:
        """获取操作处理器"""
        return cls._handlers.get(name)

    @classmethod
    def list_handlers(cls) -> List[str]:
        """列出所有可用操作"""
        return list(cls._handlers.keys())

    @classmethod
    def extract_field(cls, content: str, config: dict, context: dict = None) -> Any:
        """根据配置提取单个字段"""
        op = config.get("op", config.get("type", "css"))

        handler = cls.get_handler(op)
        if not handler:
            # 默认使用 CSS
            handler = cls.get_handler("css")
            if not handler:
                return None

        return handler.extract(content, config, context)

    @classmethod
    def extract_fields(cls, content: str, fields_config: dict, context: dict = None) -> dict:
        """根据配置提取多个字段"""
        result = {}

        for field_name, field_config in fields_config.items():
            if isinstance(field_config, str):
                # 简单字符串配置，视为 CSS 选择器
                result[field_name] = cls.extract_field(
                    content,
                    {"op": "css", "selector": field_config, "type": "text"},
                    result
                )
            elif isinstance(field_config, dict):
                # 字典配置
                result[field_name] = cls.extract_field(content, field_config, result)
            elif isinstance(field_config, list):
                # 列表配置，多个操作链
                current = content
                for op_config in field_config:
                    current = cls.extract_field(current, op_config, result)
                result[field_name] = current

        return result

    @classmethod
    def extract_list_items(cls, content: str, config: dict) -> List[dict]:
        """提取列表项"""
        # 获取列表选择器
        selector = config.get("selector", config.get("list_selector", "a"))
        item_fields = config.get("fields", config.get("item_fields", {}))

        soup = BeautifulSoup(content, 'lxml')
        elements = soup.select(selector)

        items = []
        for el in elements:
            item = {}

            # 提取每个字段
            for field_name, field_config in item_fields.items():
                if isinstance(field_config, str):
                    item[field_name] = cls.extract_field(
                        str(el),
                        {"op": "css", "selector": field_config, "type": "text"},
                        item
                    )
                elif isinstance(field_config, dict):
                    # 复制配置，但修改 selector 为相对路径
                    op = field_config.get("op", "css")
                    if op == "css":
                        sel = field_config.get("selector", field_config.get("css"))
                        field_copy = dict(field_config)
                        # 在元素内查找
                        found = el.select_one(sel) if sel else None
                        if found:
                            # 兼容旧配置：只有 attr 没有 type 时默认提取属性
                            attr = field_config.get("attr")
                            extract_type = field_config.get("type")

                            if attr and not extract_type:
                                # 有 attr 但没有 type，默认提取属性
                                item[field_name] = found.get(attr)
                            elif extract_type == "text":
                                item[field_name] = found.get_text(strip=True)
                            elif extract_type == "html":
                                item[field_name] = str(found)
                            elif extract_type == "attribute":
                                item[field_name] = found.get(attr or "href")
                            else:
                                item[field_name] = found.get_text(strip=True)
                        else:
                            item[field_name] = None
                    else:
                        item[field_name] = cls.extract_field(str(el), field_config, item)

            # 只添加有 URL 的项
            if item.get("url"):
                items.append(item)

        return items


# 注册内置操作处理器
ExtractEngine.register(RegexHandler())
ExtractEngine.register(CSSTHandler())
ExtractEngine.register(XPathHandler())
ExtractEngine.register(JSONPathHandler())
ExtractEngine.register(TemplateHandler())
ExtractEngine.register(NearbyHandler())
ExtractEngine.register(SplitHandler())
ExtractEngine.register(ChainHandler())
ExtractEngine.register(SwitchHandler())
