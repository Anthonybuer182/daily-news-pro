import trafilatura
from typing import Optional, Dict


class TrafilaturaExtractor:
    """Trafilatura-based content extractor"""

    @staticmethod
    def extract(html: str, include_comments: bool = False) -> Optional[Dict]:
        """Extract article content using Trafilatura"""
        if not html:
            return None

        # Extract main content
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
            # Fallback to basic extraction
            return TrafilaturaExtractor.extract_basic(html)

    @staticmethod
    def extract_basic(html: str) -> Dict:
        """Basic extraction fallback"""
        text = trafilatura.extract(html, include_comments=False)
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

        # Try to get markdown format
        markdown = trafilatura.extract(
            html,
            output_format="markdown",
            include_comments=False
        )

        return markdown

    @staticmethod
    def extract_with_fallback(html: str) -> Dict:
        """Extract with fallback"""
        result = TrafilaturaExtractor.extract(html)
        if result:
            return result

        # Try basic extraction
        text = trafilatura.extract(html)
        return {
            "title": None,
            "author": None,
            "date": None,
            "text": text,
            "comments": None,
            "image": None,
            "url": None,
        }
