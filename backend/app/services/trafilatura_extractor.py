import trafilatura
from typing import Optional, Dict
import asyncio


class TrafilaturaExtractor:
    """Trafilatura-based content extractor"""

    TIMEOUT_SECONDS = 30

    @staticmethod
    async def extract_async(html: str, include_comments: bool = False) -> Optional[Dict]:
        """Extract article content using Trafilatura with timeout"""
        if not html:
            return None

        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(
                    TrafilaturaExtractor._extract_sync,
                    html,
                    include_comments
                ),
                timeout=TrafilaturaExtractor.TIMEOUT_SECONDS
            )
            return result
        except asyncio.TimeoutError:
            return {"title": None, "author": None, "date": None, "text": None, "comments": None, "image": None, "url": None}

    @staticmethod
    def _extract_sync(html: str, include_comments: bool = False) -> Optional[Dict]:
        text = trafilatura.extract(
            html,
            include_comments=include_comments,
            include_images=True,
            output_format="json"
        )

        if not text:
            return None

        import json
        try:
            data = json.loads(text)
            return {
                "title": data.get("title"),
                "author": data.get("author"),
                "date": data.get("date"),
                "text": data.get("text"),
                "comments": data.get("comments"),
                "image": data.get("image"),
                "url": data.get("url"),
            }
        except (json.JSONDecodeError, TypeError):
            return TrafilaturaExtractor.extract_basic(html)

    @staticmethod
    def extract(html: str, include_comments: bool = False) -> Optional[Dict]:
        """Extract article content using Trafilatura (sync, with timeout via thread)"""
        if not html:
            return None

        try:
            result = TrafilaturaExtractor._extract_with_timeout(
                html, include_comments, TrafilaturaExtractor.TIMEOUT_SECONDS
            )
            return result
        except Exception:
            return None

    @staticmethod
    def _extract_with_timeout(html: str, include_comments: bool, timeout: int) -> Optional[Dict]:
        """Run extraction with timeout using thread"""
        import threading
        result = {"data": None, "error": None}

        def run():
            try:
                result["data"] = TrafilaturaExtractor._extract_sync(html, include_comments)
            except Exception as e:
                result["error"] = e

        thread = threading.Thread(target=run)
        thread.daemon = True
        thread.start()
        thread.join(timeout=timeout)

        if thread.is_alive():
            return None

        if result["error"]:
            return None

        return result["data"]

    @staticmethod
    def extract_basic(html: str) -> Dict:
        """Basic extraction fallback"""
        try:
            text = trafilatura.extract(html, include_comments=False)
        except Exception:
            text = None
        return {
            "title": None,
            "author": None,
            "date": None,
            "text": text,
            "comments": None,
            "image": None,
            "url": None,
        }

    @staticmethod
    def extract_markdown(html: str) -> Optional[str]:
        """Extract content as Markdown"""
        if not html:
            return None

        try:
            markdown = trafilatura.extract(
                html,
                output_format="markdown",
                include_comments=False
            )
        except Exception:
            markdown = None

        return markdown

    @staticmethod
    def extract_with_fallback(html: str) -> Dict:
        """Extract with fallback"""
        result = TrafilaturaExtractor.extract(html)
        if result:
            return result

        basic = TrafilaturaExtractor.extract_basic(html)
        return basic if basic else {
            "title": None, "author": None, "date": None,
            "text": None, "comments": None, "image": None, "url": None
        }
