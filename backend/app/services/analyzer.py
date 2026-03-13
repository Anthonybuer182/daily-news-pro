from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from app.services.playwright_crawler import PlaywrightCrawler
from app.services.selector import SelectorParser


class PageAnalyzer:
    """Smart page structure analyzer"""

    def __init__(self):
        self.common_nav_selectors = [
            "nav a", ".nav a", ".menu a", ".navigation a",
            "header a", ".header a", ".navbar a",
            ".category a", ".channel a", ".section a",
        ]
        self.common_list_selectors = [
            ".article-list", ".post-list", ".news-list",
            ".list-view", ".items", ".articles",
            "article", ".article", ".post", ".news-item",
        ]
        self.common_pagination_selectors = [
            ".pagination a", ".pager a", ".page a",
            ".next", ".next-page", ".load-more",
            "a[rel='next']", "a.next",
        ]
        self.common_title_selectors = [
            "h1", "h1.title", "article h1", ".article-title",
            ".post-title", ".news-title", ".entry-title",
        ]
        self.common_content_selectors = [
            ".article-content", ".article-body", ".post-content",
            ".content", ".entry-content", ".news-content",
            "article", ".article", ".post", ".news-body",
        ]

    async def analyze(self, url: str, analyze_type: str = "detail") -> Dict:
        """Analyze page structure"""
        async with PlaywrightCrawler() as crawler:
            html = await crawler.fetch(url)
            if not html:
                return {"error": "Failed to fetch page"}

            if analyze_type == "detail":
                return await self._analyze_detail_page(html, url)
            else:
                return await self._analyze_list_page(html, url)

    async def _analyze_detail_page(self, html: str, base_url: str) -> Dict:
        """Analyze detail page structure"""
        soup = BeautifulSoup(html, 'lxml')

        result = {
            "levels": [],
            "url": base_url,
        }

        # Find title
        title = None
        for selector in self.common_title_selectors:
            el = soup.select_one(selector)
            if el:
                title = el.get_text(strip=True)
                result["levels"].append({
                    "level": 3,
                    "name": "详情页",
                    "is_final": True,
                    "content_selectors": {
                        "title": selector,
                        "content": self._find_content_selector(soup),
                        "author": self._find_author_selector(soup),
                    }
                })
                break

        # Try to find list page (go back)
        list_url = self._find_list_page_url(soup, base_url)
        if list_url:
            async with PlaywrightCrawler() as crawler:
                list_html = await crawler.fetch(list_url)
                if list_html:
                    list_result = await self._analyze_list_page(list_html, list_url)
                    result["levels"].insert(0, list_result.get("levels", []))

        return result

    async def _analyze_list_page(self, html: str, base_url: str) -> Dict:
        """Analyze list page structure"""
        soup = BeautifulSoup(html, 'lxml')

        # Find list container
        list_selector = None
        for selector in self.common_list_selectors:
            if soup.select(selector):
                list_selector = selector
                break

        # Find pagination
        pagination_selector = None
        for selector in self.common_pagination_selectors:
            if soup.select(selector):
                pagination_selector = selector
                break

        # Find article links
        article_links = soup.find_all('a', href=True)
        article_link_selector = None
        for a in article_links:
            href = a.get('href', '')
            if '/article/' in href or '/news/' in href or '/post/' in href:
                parent = a.parent
                if parent:
                    article_link_selector = f"{parent.name}.{parent.get('class', [''])[0]}" if parent.get('class') else parent.name
                    break

        result = {
            "levels": [{
                "level": 2,
                "name": "列表页",
                "url": base_url,
                "is_final": False,
                "link_selector": article_link_selector or "a",
                "pagination": {
                    "type": "button" if pagination_selector else "none",
                    "selector": pagination_selector,
                }
            }]
        }

        return result

    def _find_content_selector(self, soup: BeautifulSoup) -> Optional[str]:
        """Find content selector"""
        for selector in self.common_content_selectors:
            el = soup.select_one(selector)
            if el and len(el.get_text(strip=True)) > 100:
                return selector
        return None

    def _find_author_selector(self, soup: BeautifulSoup) -> Optional[str]:
        """Find author selector"""
        author_selectors = [
            ".author", ".author-name", ".author-name a",
            "[rel='author']", ".byline", ".by-author",
        ]
        for selector in author_selectors:
            if soup.select_one(selector):
                return selector
        return None

    def _find_list_page_url(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """Find list page URL"""
        # Look for home, category, list links
        links = soup.find_all('a', href=True)
        for link in links:
            href = link.get('href', '')
            text = link.get_text(strip=True).lower()
            if any(kw in text for kw in ['home', 'list', 'category', 'index']):
                from urllib.parse import urljoin
                return urljoin(base_url, href)
        return None
