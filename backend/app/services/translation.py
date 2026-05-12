import os
import json
import logging
import httpx
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

MAX_TEXT_LENGTH = 50000  # Maximum text length for translation

# 最多标签数（硬编码）
DEFAULT_MAX_TAGS = 3


class TranslationService:
    """LLM-based translation service supporting OpenAI, Anthropic and Google Gemini APIs"""

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize translation service.

        Args:
            config: Model config dict with keys: api_base, api_key, model, api_type
                   If None, falls back to environment variables.
        """
        if config:
            self.api_type = config.get("api_type", "openai")
            self.api_base = config.get("api_base", "https://api.openai.com/v1")
            self.api_key = config.get("api_key", "")
            self.model = config.get("model", "gpt-4o-mini")
            self.timeout = 120  # 增加超时时间到 120 秒
            # 标签配置（标签从数据库获取）
            self.generate_tags_enabled = config.get("generate_tags", False)
            self.tag_schema = config.get("tag_schema", [])
            self.max_tags = DEFAULT_MAX_TAGS  # 硬编码
        else:
            self.api_type = os.getenv("LLM_API_TYPE", "openai")
            self.api_base = os.getenv("LLM_API_BASE", "https://api.openai.com/v1")
            self.api_key = os.getenv("LLM_API_KEY", "")
            self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")
            self.timeout = int(os.getenv("LLM_TIMEOUT", "60"))
            # 标签配置（标签从数据库获取，环境变量仅用于调试）
            self.generate_tags_enabled = os.getenv("GENERATE_TAGS", "false").lower() == "true"
            tag_schema_env = os.getenv("TAG_SCHEMA", "")
            self.tag_schema = tag_schema_env.split(",") if tag_schema_env else []
            self.max_tags = DEFAULT_MAX_TAGS  # 硬编码

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers based on API type"""
        if self.api_type == "anthropic":
            return {
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01",
            }
        elif self.api_type == "google":
            # Google Gemini uses API key in URL, not headers
            return {
                "Content-Type": "application/json",
            }
        else:
            return {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

    async def translate(
        self,
        text: str,
        target_lang: str,
        source_lang: Optional[str] = None,
        concurrency: int = 3
    ) -> str:
        """
        Translate text to target language using LLM.

        Args:
            text: Text to translate
            target_lang: Target language code (e.g., 'zh', 'en', 'ja')
            source_lang: Source language code (auto-detect if None)
            concurrency: Number of concurrent translation requests (default 3)

        Returns:
            Translated text
        """
        if not text or not text.strip():
            return text

        # Limit text length to prevent API errors (especially 520 from MiniMax)
        # Use a lower limit for MiniMax since it tends to timeout with very long content
        max_len = 8000 if self.api_type == "openai" and "minimax" in self.api_base.lower() else MAX_TEXT_LENGTH

        if len(text) > max_len:
            # 分块翻译长文本
            return await self._translate_chunked(text, target_lang, source_lang, max_len, concurrency)

        if not self.api_key:
            raise ValueError("API key not configured")

        # Build prompt
        system_prompt = self._build_system_prompt(target_lang, source_lang)
        user_prompt = self._build_user_prompt(text)

        if self.api_type == "anthropic":
            return await self._translate_anthropic(system_prompt, user_prompt)
        elif self.api_type == "google":
            return await self._translate_google(system_prompt, user_prompt)
        else:
            return await self._translate_openai(system_prompt, user_prompt)

    async def _translate_chunked(self, text: str, target_lang: str, source_lang: Optional[str], chunk_size: int, concurrency: int = 3) -> str:
        """分块翻译长文本，按段落分割"""
        import re
        # 按段落分割文本
        paragraphs = re.split(r'\n\n+', text)
        chunks = []
        current_chunk = ""
        current_size = 0

        for para in paragraphs:
            para_size = len(para)
            if current_size + para_size > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""
                current_size = 0
            current_chunk += para + "\n\n"
            current_size += para_size + 2

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        # 如果段落分割后仍然太大，按字符分割
        final_chunks = []
        for chunk in chunks:
            while len(chunk) > chunk_size:
                final_chunks.append(chunk[:chunk_size])
                chunk = chunk[chunk_size:]
            if chunk:
                final_chunks.append(chunk)

        # 翻译每个块（并发处理）
        import asyncio

        translated_parts = [None] * len(final_chunks)
        total_chunks = len(final_chunks)
        system_prompt = self._build_system_prompt(target_lang, source_lang)

        # 信号量限制并发数，避免 API 限流
        semaphore = asyncio.Semaphore(concurrency)

        async def translate_chunk_with_semaphore(idx: int, chunk: str):
            async with semaphore:
                try:
                    user_prompt = self._build_user_prompt(chunk)
                    if self.api_type == "anthropic":
                        result = await self._translate_anthropic(system_prompt, user_prompt)
                    elif self.api_type == "google":
                        result = await self._translate_google(system_prompt, user_prompt)
                    else:
                        result = await self._translate_openai(system_prompt, user_prompt)
                    translated_parts[idx] = result
                except Exception as e:
                    logger.warning(f"Failed to translate chunk {idx+1}/{total_chunks}: {e}")
                    translated_parts[idx] = chunk  # 保留原文

        # 并发执行所有翻译任务
        tasks = [translate_chunk_with_semaphore(i, chunk) for i, chunk in enumerate(final_chunks)]
        await asyncio.gather(*tasks)

        return "\n\n".join(translated_parts)

    async def _translate_openai(self, system_prompt: str, user_prompt: str) -> str:
        """Translate using OpenAI-compatible API"""
        import asyncio
        import logging
        logger = logging.getLogger(__name__)

        max_retries = 3
        retry_delay = 2  # 初始延迟秒

        # 打印完整请求信息，方便用 curl 调试
        request_url = f"{self.api_base}" if self.api_base.endswith('/chat/completions') or '/chatcompletion' in self.api_base else f"{self.api_base}/chat/completions"
        request_headers = self._get_headers()
        request_json = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.3,
        }
        import json
        logger.info(f"=== Translation API Request ===")
        logger.info(f"URL: {request_url}")
        logger.info(f"Headers: {request_headers}")
        logger.info(f"Body: {request_json}")
        logger.info(f"=== End Request ===")
        print(f"\n=== Translation API Request ===")
        print(f"URL: {request_url}")
        print(f"Headers: {json.dumps(request_headers, ensure_ascii=False)}")
        print(f"Body: {json.dumps(request_json, ensure_ascii=False, indent=4)}")
        # 生成可直接复制的 curl 命令
        curl_cmd = f"curl --location '{request_url}' \\\n--header 'Content-Type: application/json' \\\n--header 'Authorization: Bearer {self.api_key}' \\\n--data '{json.dumps(request_json, ensure_ascii=False)}'"
        print(f"\n=== Curl Command (copy and run) ===")
        print(curl_cmd)
        print(f"=== End Curl Command ===\n")

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        request_url,
                        headers=request_headers,
                        json=request_json
                    )
                    response.raise_for_status()
                    data = response.json()
                    print(f"\n=== Translation API Response ===")
                    print(f"Status: {response.status_code}")
                    print(f"Body: {data}")
                    print(f"=== End Response ===\n")

                    # 检查 MiniMax 特定错误
                    if data.get("base_resp", {}).get("status_code", 0) != 0:
                        error_msg = data.get("base_resp", {}).get("status_msg", "Unknown error")
                        raise ValueError(f"MiniMax API error: {error_msg}")

                    # 检查 content 是否为空（某些错误响应会返回空 content）
                    if not data.get("choices") or not data["choices"][0].get("message", {}).get("content"):
                        raise ValueError(f"MiniMax returned empty content. Full response: {data}")

                    if not data or "choices" not in data or not data["choices"]:
                        raise ValueError(f"Invalid API response: {data}")

                    return data["choices"][0]["message"]["content"].strip()

            except ValueError:
                raise
            except Exception as e:
                if attempt == max_retries - 1:
                    import traceback
                    raise ValueError(f"Translation failed after {max_retries} attempts: {type(e).__name__}: {e}\n{traceback.format_exc()}")
                # 指数退避等待
                await asyncio.sleep(retry_delay)
                retry_delay *= 2

    async def _translate_anthropic(self, system_prompt: str, user_prompt: str) -> str:
        """Translate using Anthropic Claude API"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_base}/messages",
                    headers=self._get_headers(),
                    json={
                        "model": self.model,
                        "system": system_prompt,
                        "messages": [
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 4096,
                    }
                )
                response.raise_for_status()
                data = response.json()
                if not data or "content" not in data or not data["content"]:
                    raise ValueError(f"Invalid Anthropic API response: {data}")
                return data["content"][0].text.strip()
        except Exception as e:
            raise ValueError(f"Translation failed: {e}")

    async def _translate_google(self, system_prompt: str, user_prompt: str) -> str:
        """Translate using Google Gemini API"""
        try:
            # Google Gemini API: API key goes in URL, model in endpoint
            url = f"{self.api_base}/models/{self.model}:generateContent?key={self.api_key}"

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    headers=self._get_headers(),
                    json={
                        "contents": [{
                            "parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]
                        }],
                        "generationConfig": {
                            "temperature": 0.3,
                            "maxOutputTokens": 4096,
                        }
                    }
                )
                response.raise_for_status()
                data = response.json()
                # Gemini response format: candidates[0].content.parts[0].text
                if not data or "candidates" not in data or not data["candidates"]:
                    raise ValueError(f"Invalid Gemini API response: {data}")
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            raise ValueError(f"Translation failed: {e}")

    def _build_system_prompt(self, target_lang: str, source_lang: Optional[str]) -> str:
        """Build system prompt for translation"""
        lang_names = {
            "zh": "Chinese (简体中文)",
            "en": "English",
            "ja": "Japanese (日本語)",
            "ko": "Korean (한국어)",
            "fr": "French (Français)",
            "de": "German (Deutsch)",
            "es": "Spanish (Español)",
            "ru": "Russian (Русский)",
            "ar": "Arabic (العربية)",
        }
        target_name = lang_names.get(target_lang, target_lang)
        source_name = lang_names.get(source_lang, source_lang) if source_lang else "the source language"

        return f"""You are a professional translator. Translate the following text from {source_name} to {target_name}.

Rules:
1. Preserve ALL Markdown formatting: headings (#), bold (**), italic (*), lists (-, *), tables, blockquotes (>)
2. Keep code blocks (``` ```) and inline code (` `) completely unchanged — do NOT translate code
3. Keep image syntax ![alt](url) unchanged — do NOT translate or remove images
4. Keep link syntax [text](url) — translate the link text but keep URLs unchanged
5. Keep technical terms, proper nouns, brand names, and CLI commands in their original form
6. Provide accurate, natural translations
7. Only output the translated text, no explanations"""

    def _build_user_prompt(self, text: str) -> str:
        """Build user prompt with text to translate"""
        # Use delimiters to prevent prompt injection
        # User content is confined within delimiters; model should only translate the content between them
        delimiter = "<<<ARTICLE_TO_TRANSLATE>>>"
        return f"""Translate the content between the delimiters to the target language.

{delimiter}
{text}
{delimiter}

Only output the translated text between the delimiters. Do not include the delimiters in your response."""

    async def translate_fields(
        self,
        article_data: Dict[str, str],
        fields: List[str],
        target_lang: str,
        source_lang: Optional[str] = None,
        concurrency: int = 3,
        tag_schema: Optional[List[str]] = None,
        max_tags: int = 3,
        generate_tags: bool = False,
    ) -> Dict[str, str]:
        """
        单次 LLM 调用翻译所有字段，若 generate_tags=True 同时打标签。
        结果中翻译字段同名返回，标签放在 _tags 键下。
        失败时回退到逐字段顺序翻译（不包含标签）。
        """
        fields_to_translate = [f for f in fields if f in article_data and article_data[f]]
        if not fields_to_translate:
            return article_data.copy()

        effective_tag_schema = tag_schema if (generate_tags and tag_schema) else None
        try:
            return await self._translate_fields_batch(
                article_data, fields_to_translate, target_lang, source_lang,
                tag_schema=effective_tag_schema, max_tags=max_tags,
            )
        except Exception as e:
            logger.warning(f"Batch translation failed ({e}), falling back to sequential")
            return await self._translate_fields_sequential(article_data, fields_to_translate, target_lang, source_lang, concurrency)

    async def _translate_fields_batch(
        self,
        article_data: Dict[str, str],
        fields: List[str],
        target_lang: str,
        source_lang: Optional[str] = None,
        tag_schema: Optional[List[str]] = None,
        max_tags: int = 3,
    ) -> Dict[str, str]:
        """单次 LLM 调用翻译所有字段，可选同时生成标签"""
        import re as _re

        lang_names = {
            "zh": "Chinese (简体中文)", "en": "English", "ja": "Japanese (日本語)",
            "ko": "Korean (한국어)", "fr": "French (Français)", "de": "German (Deutsch)",
            "es": "Spanish (Español)", "ru": "Russian (Русский)", "ar": "Arabic (العربية)",
        }
        target_name = lang_names.get(target_lang, target_lang)
        source_name = lang_names.get(source_lang, source_lang) if source_lang else "auto-detected language"

        to_translate = {f: article_data[f] for f in fields if article_data.get(f)}

        # 根据是否需要打标签构建不同的 prompt
        if tag_schema:
            tags_str = ", ".join(f'"{t}"' for t in tag_schema)
            system_prompt = f"""You are a professional translator and content tagger.

Your tasks:
1. Translate the given JSON fields from {source_name} to {target_name}
2. Based on the translated content, select up to {max_tags} tags from the provided tag pool

Rules:
- Preserve all formatting, line breaks, and markdown syntax in translations
- Keep technical terms, proper nouns, code blocks, and URLs untouched
- Tags MUST be chosen from the tag pool only; return an empty array if none fit
- Return a single valid JSON object, no explanations"""

            # 动态生成返回示例，包含所有实际字段
            example_fields = {f: "..." for f in to_translate}
            example_fields["_tags"] = ["tag1", "tag2"]
            example_json = json.dumps(example_fields, ensure_ascii=False, indent=2)

            user_prompt = f"""Translate these fields to {target_name}, and select tags from the pool below.

Tag pool (pick up to {max_tags}): [{tags_str}]

Input fields to translate:
{json.dumps(to_translate, ensure_ascii=False, indent=2)}

Return JSON with ALL the same keys as input plus a "_tags" key (do NOT omit any field):
{example_json}"""
        else:
            system_prompt = f"""You are a professional translator. Translate the JSON fields below from {source_name} to {target_name}.

Rules:
1. Preserve all formatting, line breaks, and markdown syntax
2. Keep technical terms, proper nouns, code blocks, and URLs untouched
3. Return a valid JSON object with exactly the same keys as the input
4. Only output the JSON object, no explanations"""

            user_prompt = f"""Translate these fields to {target_name}. Return JSON only.

Input:
{json.dumps(to_translate, ensure_ascii=False, indent=2)}"""

        if self.api_type == "anthropic":
            raw = await self._translate_anthropic(system_prompt, user_prompt)
        elif self.api_type == "google":
            raw = await self._translate_google(system_prompt, user_prompt)
        else:
            raw = await self._translate_openai(system_prompt, user_prompt)

        # 解析 JSON 结果，去掉可能的 markdown 代码块包裹
        raw = raw.strip()
        raw = _re.sub(r'^```(?:json)?\s*', '', raw)
        raw = _re.sub(r'\s*```$', '', raw)
        translated = json.loads(raw)

        result = article_data.copy()
        for f in fields:
            if f in translated and translated[f]:
                result[f] = translated[f]
        # 保留标签结果（如果有）
        if "_tags" in translated and isinstance(translated["_tags"], list):
            # 只保留在 tag_schema 中存在的标签
            valid_tags = [t for t in translated["_tags"] if not tag_schema or t in tag_schema]
            result["_tags"] = valid_tags[:max_tags]
        return result

    async def _translate_fields_sequential(
        self,
        article_data: Dict[str, str],
        fields: List[str],
        target_lang: str,
        source_lang: Optional[str] = None,
        concurrency: int = 3,
    ) -> Dict[str, str]:
        """兜底：逐字段顺序翻译"""
        result = article_data.copy()
        for field in fields:
            if field in article_data and article_data[field]:
                try:
                    result[field] = await self.translate(
                        article_data[field],
                        target_lang,
                        source_lang,
                        concurrency
                    )
                except Exception as e:
                    logger.warning(f"Failed to translate field '{field}': {e}")
        return result


def get_default_model_config(db) -> Optional[Dict]:
    """Get default model config from database"""
    from app.models.model_config import ModelConfig
    config = db.query(ModelConfig).filter(ModelConfig.is_default == True).first()
    if config:
        return {
            "api_type": config.api_type,
            "api_base": config.api_base,
            "api_key": config.api_key,
            "model": config.model,
        }
    return None


def get_translation_service_with_config(db) -> TranslationService:
    """
    Get translation service with config from database.
    Falls back to environment variables if no config in database.
    """
    model_config = get_default_model_config(db)
    if model_config:
        return TranslationService(config=model_config)
    return TranslationService()


def get_translation_service_with_tag_config(db, rule_translation_config: dict = None) -> TranslationService:
    """
    Get translation service with full config (including tag settings).

    Args:
        db: Database session
        rule_translation_config: Rule's translation_config dict (may contain generate_tags flag)

    Returns:
        TranslationService with tag config
    """
    model_config = get_default_model_config(db)
    if not model_config:
        model_config = {}

    # 如果规则启用了打标签，设置标志
    if rule_translation_config and rule_translation_config.get("generate_tags"):
        model_config["generate_tags"] = True

    # 标签池从数据库 tags 表读取
    from app.models.tag import Tag
    tags = db.query(Tag).all()
    tag_names = [t.name for t in tags] if tags else []
    logger.info(f"[Tag Config] Loaded {len(tag_names)} tags from database: {tag_names}")
    model_config["tag_schema"] = tag_names

    # max_tags 在 TranslationService 内部硬编码为 3

    return TranslationService(config=model_config if model_config else None)


# ==================== 打标签相关方法 ====================

async def generate_tags_with_config(
    db,
    summary: str,
    content: str = None,
    translated_summary: str = None,
    translated_content: str = None,
    rule_translation_config: dict = None
) -> List[str]:
    """
    根据文章内容生成标签（使用规则或全局标签配置）
    """
    logger.info(f"[Tags] generate_tags_with_config called: summary_len={len(summary) if summary else 0}, content_len={len(content) if content else 0}, translated_summary_len={len(translated_summary) if translated_summary else 0}, translated_content_len={len(translated_content) if translated_content else 0}")

    service = get_translation_service_with_tag_config(db, rule_translation_config)
    logger.info(f"[Tags] Service type: {type(service)}, has generate_tags method: {hasattr(service, 'generate_tags')}")
    return await service.generate_tags(
        summary=summary,
        content=content,
        translated_summary=translated_summary,
        translated_content=translated_content
    )


class TranslationService(TranslationService):
    """扩展：添加 generate_tags 方法"""

    async def generate_tags(
        self,
        summary: str,
        content: str = None,
        translated_summary: str = None,
        translated_content: str = None,
    ) -> List[str]:
        """
        根据文章内容生成标签

        Args:
            summary: 原文摘要
            content: 原文内容（前500字）
            translated_summary: 翻译后摘要
            translated_content: 翻译后内容（前500字）

        Returns:
            标签列表，如 ["AI", "科技"]
        """
        if not self.api_key:
            logger.warning("[Tags] No API key configured, skipping tag generation")
            return []

        logger.info(f"[Tags] generate_tags called with tag_schema={self.tag_schema}, max_tags={self.max_tags}")

        # 构建要分析的内容
        text_to_analyze = ""
        if translated_summary:
            text_to_analyze += translated_summary + "\n\n"
            if translated_content:
                text_to_analyze += translated_content[:500]
        elif summary:
            text_to_analyze += summary + "\n\n"
            if content:
                text_to_analyze += content[:500]
        else:
            logger.warning("No content to analyze for tags")
            return []

        if not text_to_analyze.strip():
            return []

        # 构建 prompt
        prompt = self._build_tag_prompt(text_to_analyze)

        # 调用 LLM
        try:
            result = await self._call_llm_for_tags(prompt)
            tags = self._parse_tags(result)
            return tags
        except Exception as e:
            logger.warning(f"Failed to generate tags: {e}")
            return []

    def _build_tag_prompt(self, text: str) -> str:
        """构建打标签 Prompt"""
        tags_str = ", ".join(f'"{t}"' for t in self.tag_schema)
        logger.info(f"[Tags] Building tag prompt with {len(self.tag_schema)} tags in schema")
        return f"""你是一个新闻分类专家。根据以下文章内容，从给定标签池中选择最合适的标签。

标签池（必须仅从以下标签中选择，最多选择 {self.max_tags} 个）：[{tags_str}]

文章内容：
{text}

请选择最合适的标签，输出格式（严格按此格式，只输出JSON数组，不要任何其他内容）：
["标签1", "标签2"]
"""

    def _parse_tags(self, result: str) -> List[str]:
        """解析 LLM 返回的标签结果"""
        logger.info(f"[Tags] Parsing LLM result: {result[:200] if result else 'empty'}")
        if not result:
            return []

        try:
            # 尝试直接解析 JSON
            tags = json.loads(result.strip())
            if isinstance(tags, list):
                # 验证标签是否都在标签池中
                valid_tags = [t for t in tags if t in self.tag_schema]
                logger.info(f"[Tags] Parsed tags: {tags}, valid_tags after filter: {valid_tags}")
                return valid_tags[:self.max_tags]
        except json.JSONDecodeError:
            pass

        # 尝试从文本中提取 JSON
        import re
        json_match = re.search(r'\[.*\]', result, re.DOTALL)
        if json_match:
            try:
                tags = json.loads(json_match.group())
                if isinstance(tags, list):
                    valid_tags = [t for t in tags if t in self.tag_schema]
                    logger.info(f"[Tags] Extracted tags from text: {tags}, valid_tags after filter: {valid_tags}")
                    return valid_tags[:self.max_tags]
            except json.JSONDecodeError:
                pass

        logger.warning("[Tags] Could not parse any valid tags from LLM result")
        return []

    async def _call_llm_for_tags(self, prompt: str) -> str:
        """调用 LLM 生成标签（统一方法）"""
        if self.api_type == "anthropic":
            return await self._call_anthropic(prompt)
        elif self.api_type == "google":
            return await self._call_google(prompt)
        else:
            return await self._call_openai(prompt)

    async def _call_openai(self, prompt: str) -> str:
        """调用 OpenAI API"""
        import asyncio

        request_url = f"{self.api_base}" if self.api_base.endswith('/chat/completions') or '/chatcompletion' in self.api_base else f"{self.api_base}/chat/completions"
        request_headers = self._get_headers()
        request_json = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
        }

        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        request_url,
                        headers=request_headers,
                        json=request_json
                    )
                    response.raise_for_status()
                    data = response.json()

                    if not data or "choices" not in data or not data["choices"]:
                        raise ValueError(f"Invalid API response: {data}")

                    return data["choices"][0]["message"]["content"].strip()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise ValueError(f"OpenAI API failed: {e}")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2

    async def _call_anthropic(self, prompt: str) -> str:
        """调用 Anthropic API"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_base}/messages",
                    headers=self._get_headers(),
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 4096,
                    }
                )
                response.raise_for_status()
                data = response.json()
                if not data or "content" not in data or not data["content"]:
                    raise ValueError(f"Invalid Anthropic API response: {data}")
                return data["content"][0].text.strip()
        except Exception as e:
            raise ValueError(f"Anthropic API failed: {e}")

    async def _call_google(self, prompt: str) -> str:
        """调用 Google Gemini API"""
        try:
            url = f"{self.api_base}/models/{self.model}:generateContent?key={self.api_key}"
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    headers=self._get_headers(),
                    json={
                        "contents": [{
                            "parts": [{"text": prompt}]
                        }],
                        "generationConfig": {
                            "temperature": 0.3,
                            "maxOutputTokens": 4096,
                        }
                    }
                )
                response.raise_for_status()
                data = response.json()
                if not data or "candidates" not in data or not data["candidates"]:
                    raise ValueError(f"Invalid Gemini API response: {data}")
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            raise ValueError(f"Google Gemini API failed: {e}")
