import asyncio
import os
import hashlib
from datetime import datetime
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from app.models import Rule, RuleLevel, Article, Job, Log
from app.services.playwright_crawler import PlaywrightCrawler
from app.services.trafilatura_extractor import TrafilaturaExtractor
from app.services.selector import SelectorParser


class CrawlerEngine:
    """Main crawler engine supporting multi-level crawling"""

    def __init__(self, db: Session, job_id: int):
        self.db = db
        self.job_id = job_id
        self.job = None
        self.rule = None

    async def crawl_rule(self, rule_id: int) -> Dict:
        """Crawl articles based on rule"""
        self.rule = self.db.query(Rule).filter(Rule.id == rule_id).first()
        if not self.rule:
            raise ValueError(f"Rule {rule_id} not found")

        self.job = self.db.query(Job).filter(Job.id == self.job_id).first()
        self.job.status = "running"
        self.job.started_at = datetime.utcnow()
        self.db.commit()

        self._log("info", f"Starting crawl for rule: {self.rule.name}")

        try:
            # Check crawl mode
            if self.rule.crawl_mode == "smart" or self.rule.levels:
                result = await self._crawl_with_levels()
            else:
                result = await self._crawl_simple()

            self.job.status = "success"
            self.job.finished_at = datetime.utcnow()
            self._log("info", f"Crawl completed: {result}")
        except Exception as e:
            self.job.status = "failed"
            self.job.error_message = str(e)
            self.job.finished_at = datetime.utcnow()
            self._log("error", f"Crawl failed: {e}")

        self.db.commit()
        return {"job_id": self.job_id, "status": self.job.status}

    async def _crawl_with_levels(self) -> Dict:
        """Crawl using level configuration"""
        levels = self.db.query(RuleLevel).filter(
            RuleLevel.rule_id == self.rule.id
        ).order_by(RuleLevel.level).all()

        if not levels:
            # Fallback to simple crawl
            return await self._crawl_simple()

        # Start with first level URLs
        current_urls = [levels[0].url] if levels[0].url else []

        for level in levels:
            if level.is_final:
                # Final level: extract content
                return await self._extract_articles(current_urls)
            else:
                # Intermediate level: extract links
                current_urls = await self._extract_links(current_urls, level)

        return {"urls": current_urls}

    async def _crawl_simple(self) -> Dict:
        """Simple single-level crawl"""
        url = self.rule.list_url or self.rule.site_url
        if not url:
            raise ValueError("No URL to crawl")

        # Extract links
        links = await self._extract_links([url], None)

        # Extract content from links
        return await self._extract_articles(links)

    async def _extract_links(self, urls: List[str], level: Optional[RuleLevel]) -> List[str]:
        """Extract links from pages"""
        all_links = []

        async with PlaywrightCrawler(
            user_agent=self.rule.user_agent,
            delay_min=self.rule.delay_min,
            delay_max=self.rule.delay_max,
        ) as crawler:
            for url in urls:
                self._log("info", f"Extracting links from: {url}")

                # Get page content
                html = await crawler.fetch(url)
                if not html:
                    continue

                # Apply pagination if configured
                if level and level.pagination_type != "none":
                    paginated_links = await self._handle_pagination(crawler, url, level)
                    all_links.extend(paginated_links)

                # Extract links using selector
                if level and level.link_selector:
                    selector = level.link_selector
                    selector_type = level.selector_type or "css"
                    base_url = url

                    if selector_type == "css":
                        links = SelectorParser.extract_links_css(html, selector, base_url)
                    elif selector_type == "xpath":
                        links = SelectorParser.extract_links_xpath(html, selector, base_url)
                    elif selector_type == "regex":
                        links = SelectorParser.extract_by_regex(html, selector)
                    else:
                        links = []

                    all_links.extend(links)
                else:
                    # Default: extract all article links
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html, 'lxml')
                    for a in soup.find_all('a', href=True):
                        href = a['href']
                        if href.startswith('http'):
                            all_links.append(href)

        # Filter and deduplicate
        all_links = self._filter_links(all_links)

        self._log("info", f"Extracted {len(all_links)} links")
        return all_links

    async def _handle_pagination(self, crawler: PlaywrightCrawler, url: str, level: RuleLevel) -> List[str]:
        """Handle pagination"""
        links = []
        max_pages = level.pagination_max or 10

        if level.pagination_type == "button":
            for page_num in range(max_pages):
                html = await crawler.fetch(url)
                if html:
                    selector = level.link_selector or "a"
                    selector_type = level.selector_type or "css"
                    if selector_type == "css":
                        page_links = SelectorParser.extract_links_css(html, selector, url)
                    else:
                        page_links = SelectorParser.extract_links_xpath(html, selector, url)
                    links.extend(page_links)

                # Try to find next page button
                # This is simplified - real implementation would click the button
                break

        return links

    async def _extract_articles(self, urls: List[str]) -> Dict:
        """Extract content from article URLs"""
        success_count = 0
        failed_count = 0

        for url in urls:
            try:
                article = await self._extract_single_article(url)
                if article:
                    success_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                self._log("error", f"Failed to extract {url}: {e}")
                failed_count += 1

        self.job.articles_count = len(urls)
        self.job.success_count = success_count
        self.job.failed_count = failed_count

        return {
            "total": len(urls),
            "success": success_count,
            "failed": failed_count,
        }

    async def _extract_single_article(self, url: str) -> Optional[Article]:
        """Extract single article"""
        # Check if already exists
        existing = self.db.query(Article).filter(Article.url == url).first()
        if existing:
            self._log("info", f"Article already exists: {url}")
            return existing

        html = None

        # Fetch based on method
        if self.rule.crawl_method == "playwright" or self.rule.crawl_method == "hybrid":
            async with PlaywrightCrawler(
                user_agent=self.rule.user_agent,
                delay_min=self.rule.delay_min,
                delay_max=self.rule.delay_max,
            ) as crawler:
                html = await crawler.fetch(url)

        if not html and self.rule.crawl_method != "playwright":
            import httpx
            headers = {"User-Agent": self.rule.user_agent} if self.rule.user_agent else {}
            response = httpx.get(url, headers=headers, timeout=30)
            html = response.text

        if not html:
            raise ValueError(f"Failed to fetch: {url}")

        # Extract content
        if self.rule.crawl_method == "trafilatura" or self.rule.crawl_method == "hybrid":
            content = TrafilaturaExtractor.extract_with_fallback(html)
        else:
            content = await self._extract_with_selectors(html)

        # Generate markdown
        markdown_content = self._generate_markdown(content, url)
        markdown_file = self._save_markdown(markdown_content, url)

        # Create article record
        article = Article(
            rule_id=self.rule.id,
            url=url,
            title=content.get("title"),
            summary=content.get("text", "")[:500] if content.get("text") else None,
            author=content.get("author"),
            publish_time=self._parse_date(content.get("date")),
            cover_image=content.get("image"),
            markdown_file=markdown_file,
            status="success",
        )

        self.db.add(article)
        self.db.commit()

        self._log("info", f"Extracted article: {article.title}")
        return article

    async def _extract_with_selectors(self, html: str) -> Dict:
        """Extract using custom selectors"""
        result = {}

        if self.rule.title_selector:
            selector_type = self.rule.title_selector_type or "css"
            if selector_type == "css":
                result["title"] = SelectorParser.extract_text_css(html, self.rule.title_selector)
            else:
                result["title"] = SelectorParser.extract_text_xpath(html, self.rule.title_selector)

        if self.rule.content_selector:
            selector_type = self.rule.content_selector_type or "css"
            if selector_type == "css":
                result["text"] = SelectorParser.extract_text_css(html, self.rule.content_selector)
            else:
                result["text"] = SelectorParser.extract_text_xpath(html, self.rule.content_selector)

        if self.rule.author_selector:
            selector_type = self.rule.author_selector_type or "css"
            if selector_type == "css":
                result["author"] = SelectorParser.extract_text_css(html, self.rule.author_selector)
            else:
                result["author"] = SelectorParser.extract_text_xpath(html, self.rule.author_selector)

        if self.rule.cover_image_selector:
            result["image"] = SelectorParser.extract_attribute_css(html, self.rule.cover_image_selector, "src")

        return result

    def _generate_markdown(self, content: Dict, url: str) -> str:
        """Generate Markdown from content"""
        lines = []

        if content.get("title"):
            lines.append(f"# {content['title']}\n")

        lines.append(f"**Source**: {url}\n")

        if content.get("author"):
            lines.append(f"**Author**: {content['author']}\n")

        if content.get("date"):
            lines.append(f"**Date**: {content['date']}\n")

        if content.get("image"):
            lines.append(f"![Cover]({content['image']})\n")

        lines.append("\n---\n\n")

        if content.get("text"):
            lines.append(content["text"])

        return "\n".join(lines)

    def _save_markdown(self, content: str, url: str) -> str:
        """Save markdown to file"""
        # Generate filename from URL
        url_hash = hashlib.md5(url.encode()).hexdigest()[:10]
        filename = f"{url_hash}.md"

        # Create directory if not exists
        os.makedirs("data/articles", exist_ok=True)

        filepath = f"data/articles/{filename}"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return filepath

    def _filter_links(self, links: List[str]) -> List[str]:
        """Filter and deduplicate links"""
        # Remove duplicates while preserving order
        seen = set()
        filtered = []

        # Get exclude patterns
        exclude_patterns = []
        if self.rule.exclude_patterns:
            import json
            try:
                exclude_patterns = json.loads(self.rule.exclude_patterns)
            except:
                pass

        for link in links:
            # Skip duplicates
            if link in seen:
                continue

            # Check exclude patterns
            skip = False
            for pattern in exclude_patterns:
                if pattern.replace("*", "") in link:
                    skip = True
                    break

            if skip:
                continue

            seen.add(link)
            filtered.append(link)

        return filtered

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string"""
        if not date_str:
            return None

        formats = [
            "%Y-%m-%d",
            "%Y-%m-%d %H:%M:%S",
            "%Y/%m/%d",
            "%m/%d/%Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except:
                continue

        return None

    def _log(self, level: str, message: str):
        """Add log entry"""
        log = Log(job_id=self.job_id, level=level, message=message)
        self.db.add(log)
        self.db.commit()
