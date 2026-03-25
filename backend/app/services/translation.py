import os
import logging
import httpx
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

MAX_TEXT_LENGTH = 50000  # Maximum text length for translation


class TranslationService:
    """LLM-based translation service"""

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize translation service.

        Args:
            config: Model config dict with keys: api_base, api_key, model
                   If None, falls back to environment variables.
        """
        if config:
            self.api_base = config.get("api_base", "https://api.openai.com/v1")
            self.api_key = config.get("api_key", "")
            self.model = config.get("model", "gpt-4o-mini")
            self.timeout = 60
        else:
            self.api_base = os.getenv("LLM_API_BASE", "https://api.openai.com/v1")
            self.api_key = os.getenv("LLM_API_KEY", "")
            self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")
            self.timeout = int(os.getenv("LLM_TIMEOUT", "60"))

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def translate(
        self,
        text: str,
        target_lang: str,
        source_lang: Optional[str] = None
    ) -> str:
        """
        Translate text to target language using LLM.

        Args:
            text: Text to translate
            target_lang: Target language code (e.g., 'zh', 'en', 'ja')
            source_lang: Source language code (auto-detect if None)

        Returns:
            Translated text
        """
        if not text or not text.strip():
            return text

        # Limit text length to prevent abuse
        if len(text) > MAX_TEXT_LENGTH:
            raise ValueError(f"Text too long: {len(text)} chars (max: {MAX_TEXT_LENGTH})")

        if not self.api_key:
            raise ValueError("API key not configured")

        # Build prompt
        system_prompt = self._build_system_prompt(target_lang, source_lang)
        user_prompt = self._build_user_prompt(text)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_base}/chat/completions",
                    headers=self._get_headers(),
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": 0.3,
                    }
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
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
        source_lang: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Translate multiple fields in an article.

        Args:
            article_data: Dict with fields like 'title', 'summary', 'content'
            fields: List of field names to translate
            target_lang: Target language code
            source_lang: Source language code

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
                        source_lang
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
