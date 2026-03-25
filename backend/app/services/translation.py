import os
import logging
import httpx
import asyncio
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

class TranslationService:
    """LLM-based translation service"""

    def __init__(self):
        self.api_base = os.getenv("LLM_API_BASE", "https://api.openai.com/v1")
        self.api_key = os.getenv("LLM_API_KEY")
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

        if not self.api_key:
            raise ValueError("LLM_API_KEY not configured")

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
        return f"Translate this text:\n\n{text}"

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


# Singleton instance
_translation_service: Optional[TranslationService] = None

def get_translation_service() -> TranslationService:
    """Get or create translation service singleton"""
    global _translation_service
    if _translation_service is None:
        _translation_service = TranslationService()
    return _translation_service
