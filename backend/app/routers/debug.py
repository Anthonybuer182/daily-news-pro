import asyncio
import re
from typing import Optional, List, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.services.playwright_crawler import PlaywrightCrawler

router = APIRouter(prefix="/api/debug", tags=["debug"])


class TestUrlRequest(BaseModel):
    url: str
    method: str = "auto"  # auto, httpx, playwright, api
    list_selector: Optional[str] = None
    selector_type: str = "css"


class TestUrlResponse(BaseModel):
    url: str
    method_used: str
    content_length: int
    links_found: int
    sample_links: List[str]
    error: Optional[str] = None
    suggestions: Optional[Dict] = None


@router.post("/test-url", response_model=TestUrlResponse)
async def test_url(request: TestUrlRequest, db: Session = Depends(get_db)):
    """Test a URL and auto-detect the best way to crawl it"""

    # Auto-detect method
    method = request.method
    if method == "auto":
        if "api.github.com" in request.url:
            method = "api"
        elif request.url.endswith("/feed") or ".rss" in request.url.lower() or "/feed" in request.url:
            method = "rss"
        else:
            method = "httpx"

    html = None
    try:
        # Try method based on detection
        if method in ["playwright", "rss", "httpx", "auto"]:
            # Try httpx first (faster)
            html = _fetch_httpx(request.url)
            if html and len(html) > 100:
                method = "httpx"
                if "<rss" in html.lower() or "<feed" in html.lower():
                    method = "rss"
            else:
                # Try playwright as fallback
                html = await _fetch_playwright(request.url)
                if html and len(html) > 100:
                    method = "playwright"

        if not html or len(html) < 100:
            raise HTTPException(status_code=400, detail=f"Failed to fetch URL (method: {method}, length: {len(html) if html else 0})")

        # Extract links
        links = _extract_links(html, request.url, request.list_selector, request.selector_type)

        # Generate suggestions
        suggestions = _generate_suggestions(html, request.url)

        return TestUrlResponse(
            url=request.url,
            method_used=method,
            content_length=len(html),
            links_found=len(links),
            sample_links=links[:10],
            suggestions=suggestions
        )

    except Exception as e:
        return TestUrlResponse(
            url=request.url,
            method_used=method,
            content_length=0,
            links_found=0,
            sample_links=[],
            error=str(e)
        )


async def _fetch_playwright(url: str) -> Optional[str]:
    try:
        async with PlaywrightCrawler(delay_min=1, delay_max=2) as crawler:
            return await crawler.fetch(url)
    except:
        return None


def _fetch_httpx(url: str) -> Optional[str]:
    try:
        import httpx
        response = httpx.get(url, timeout=30, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        })
        return response.text
    except:
        return None


def _extract_links(html: str, base_url: str, selector: Optional[str], selector_type: str) -> List[str]:
    links = []

    if selector:
        # Use custom selector
        from app.services.selector import SelectorParser
        if selector_type == "css":
            links = SelectorParser.extract_links_css(html, selector, base_url)
        elif selector_type == "xpath":
            links = SelectorParser.extract_links_xpath(html, selector, base_url)
        else:
            links = []
    else:
        # Auto-extract links
        import re
        from bs4 import BeautifulSoup

        # Check if it's RSS/XML
        is_rss = "<rss" in html.lower() or "<feed" in html.lower() or "<item>" in html.lower()

        if is_rss:
            # For RSS, extract from <link> tags and <guid> tags
            try:
                soup = BeautifulSoup(html, 'xml')
                for link in soup.find_all('link'):
                    text = link.get_text()
                    if text and text.startswith('http'):
                        links.append(text)
                for guid in soup.find_all('guid'):
                    text = guid.get_text()
                    if text and text.startswith('http'):
                        links.append(text)
            except:
                pass
        else:
            # Try to find article links
            article_paths = re.findall(r'(https?://[^\s"\')]+/p/\d+[^\s"\')]*)', html)
            links.extend(article_paths)

            # Try BeautifulSoup
            soup = BeautifulSoup(html, 'lxml')
            for a in soup.find_all('a', href=True):
                href = a['href']
                if href.startswith('http'):
                    links.append(href)

    return list(set(links))


def _generate_suggestions(html: str, url: str) -> Dict:
    """Generate configuration suggestions based on the page content"""
    suggestions = {
        "likely_method": "httpx",
        "selectors": {},
        "tips": []
    }

    from bs4 import BeautifulSoup

    # Check if it's RSS
    if "<rss" in html.lower() or "<feed" in html.lower():
        suggestions["likely_method"] = "rss"
        suggestions["tips"].append("This appears to be an RSS/Atom feed")
        return suggestions

    # Check if it's JSON API
    try:
        import json
        json.loads(html)
        suggestions["likely_method"] = "api"
        suggestions["tips"].append("This appears to be a JSON API response")
        return suggestions
    except:
        pass

    soup = BeautifulSoup(html, 'lxml')

    # Try to find common article patterns
    article_links = soup.find_all('a', href=re.compile(r'/p/|\.html|/article/|/post/'))
    if article_links:
        suggestions["tips"].append(f"Found {len(article_links)} article-like links")

    # Common selectors for news sites
    common_patterns = [
        ("article a", "Article links"),
        (".post-title a", "Post title links"),
        (".entry-title a", "Entry title links"),
        (".news-item a", "News item links"),
        (".product-hunt a", "Product links"),
    ]

    for pattern, desc in common_patterns:
        matches = soup.select(pattern)
        if matches:
            suggestions["selectors"][desc] = pattern
            suggestions["tips"].append(f"Found selector '{pattern}' for {desc}")

    return suggestions


@router.get("/methods")
async def get_methods():
    """Get available crawl methods and when to use them"""
    return {
        "methods": {
            "httpx": {
                "description": "Simple HTTP request - fastest",
                "use_when": [
                    "Page is static HTML (no JavaScript required)",
                    "Has RSS feed",
                    "Simple blog or news site"
                ]
            },
            "playwright": {
                "description": "Browser automation - most capable",
                "use_when": [
                    "Page uses JavaScript to load content",
                    "Need to scroll/infinite load",
                    "Page has anti-scraping protection"
                ]
            },
            "api": {
                "description": "Direct API call - most reliable for specific sites",
                "use_when": [
                    "Site provides public API",
                    "Need structured data"
                ]
            },
            "rss": {
                "description": "RSS/Atom feed - simplest for blogs",
                "use_when": [
                    "Site has RSS feed",
                    "Need only title, summary, link"
                ]
            }
        },
        "selector_types": {
            "css": "CSS selector - e.g., '.article-list a', '#content a'",
            "xpath": "XPath - e.g., '//div[@class=\"article\"]//a'",
            "regex": "Regular expression - e.g., '/p/\\d+'"
        }
    }
