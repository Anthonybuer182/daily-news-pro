import os
import logging
import httpx
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

MAX_TEXT_LENGTH = 50000  # Maximum text length for translation


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
        else:
            self.api_type = os.getenv("LLM_API_TYPE", "openai")
            self.api_base = os.getenv("LLM_API_BASE", "https://api.openai.com/v1")
            self.api_key = os.getenv("LLM_API_KEY", "")
            self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")
            self.timeout = int(os.getenv("LLM_TIMEOUT", "60"))

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
1. Preserve the original formatting and line breaks
2. Keep technical terms, proper nouns, and brand names in their original form
3. Maintain HTML tags if present (do not translate inside tags)
4. Provide accurate, natural translations
5. Only output the translated text, no explanations"""

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
        concurrency: int = 3
    ) -> Dict[str, str]:
        """
        Translate multiple fields in an article.

        Args:
            article_data: Dict with fields like 'title', 'summary', 'content'
            fields: List of field names to translate
            target_lang: Target language code
            source_lang: Source language code
            concurrency: Number of concurrent translation requests (default 3)

        Returns:
            Dict with translated fields (original fields preserved for non-translated ones)
        """
        result = article_data.copy()

        # Translate each field
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
                    # Log error but continue with other fields
                    logger.warning(f"Failed to translate field '{field}': {e}")
                    # Keep original text on failure

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
