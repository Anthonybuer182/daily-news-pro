"""统一请求配置管理器 - 支持任意 HTTP API 抓取（包括 GraphQL）"""

import base64
import json
from typing import Dict, Optional


class RequestConfigManager:
    """统一请求配置管理器"""

    # 支持的 body 类型
    BODY_TYPES = ["json", "form", "graphql", "raw"]

    @classmethod
    def build_request_kwargs(
        cls,
        config: dict,
        source_url: str,
        headers: dict
    ) -> dict:
        """
        构建 httpx 请求参数

        Args:
            config: request_config JSON 配置
            source_url: 请求 URL
            headers: 已构建的请求头

        Returns:
            dict: 包含 method, url, params, headers, content/json/data, timeout 等
        """
        kwargs = {
            "url": source_url,
            "headers": headers,
            "timeout": config.get("timeout", 30),
        }

        # 请求方法，默认 GET
        method = config.get("method", "GET").upper()
        kwargs["method"] = method

        # URL 参数
        if "params" in config:
            kwargs["params"] = config["params"]

        # 请求体
        if "body" in config:
            body_config = config["body"]
            body_type = body_config.get("type", "json")

            if body_type == "json":
                kwargs["json"] = body_config.get("data", {})
            elif body_type == "form":
                kwargs["data"] = body_config.get("data", {})
            elif body_type == "graphql":
                # GraphQL 请求体格式
                graphql_body = {
                    "query": body_config.get("query", ""),
                }
                variables = body_config.get("variables")
                if variables:
                    graphql_body["variables"] = variables
                kwargs["json"] = graphql_body
            elif body_type == "raw":
                kwargs["content"] = body_config.get("data", "").encode("utf-8")

        return kwargs

    @classmethod
    def apply_auth(
        cls,
        kwargs: dict,
        auth_type: str,
        auth_config: Optional[dict]
    ) -> dict:
        """
        应用认证配置

        Args:
            kwargs: 请求参数字典
            auth_type: 认证类型 (bearer/basic/custom)
            auth_config: 认证配置

        Returns:
            dict: 更新后的请求参数
        """
        if not auth_config:
            return kwargs

        auth_type = auth_type.lower()
        headers = kwargs.get("headers", {})

        if auth_type == "bearer":
            token = auth_config.get("token", "")
            if token:
                headers["Authorization"] = f"Bearer {token}"
        elif auth_type == "basic":
            # HTTP Basic 认证
            username = auth_config.get("username", "")
            password = auth_config.get("password", "")
            if username:
                credentials = f"{username}:{password}"
                encoded = base64.b64encode(credentials.encode()).decode()
                headers["Authorization"] = f"Basic {encoded}"
        elif auth_type == "custom":
            # 自定义请求头（支持多个）
            custom_headers = auth_config.get("headers", {})
            if isinstance(custom_headers, dict):
                for header_name, header_value in custom_headers.items():
                    if header_name and header_value:
                        headers[header_name] = header_value

        kwargs["headers"] = headers
        return kwargs

    @classmethod
    def apply_proxy(cls, proxy_config: Optional[dict]) -> Optional[dict]:
        """
        应用代理配置

        Args:
            proxy_config: 代理配置

        Returns:
            dict: httpx 代理配置 或 None
        """
        if not proxy_config:
            return None

        server = proxy_config.get("server")
        if not server:
            return None

        proxy = {"server": server}

        username = proxy_config.get("username")
        password = proxy_config.get("password")
        if username and password:
            proxy["username"] = username
            proxy["password"] = password

        return proxy

    @classmethod
    def get_unused_config_warning(cls, rule_name: str, fields: list) -> Optional[str]:
        """
        检查未使用的配置字段并返回警告信息

        Args:
            rule_name: 规则名称
            fields: 未使用的配置字段列表

        Returns:
            str: 警告信息 或 None
        """
        if not fields:
            return None

        return (
            f"规则 '{rule_name}' 中以下配置字段未使用: {', '.join(fields)}。"
            f"请使用 request_config 字段来配置这些选项。"
        )
