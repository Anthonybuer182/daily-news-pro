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
                # Final level: first extract links using level's selector, then extract content
                if level.link_selector:
                    # Extract links from current URLs using level's selector
                    final_urls = await self._extract_links(current_urls, level)
                    self._log("info", f"Final level extracted {len(final_urls)} links")
                    return await self._extract_articles(final_urls)
                else:
                    # No selector, just extract from current URLs
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

        # Use httpx for link extraction if not playwright
        if self.rule.crawl_method == "playwright":
            async with PlaywrightCrawler(
                user_agent=self.rule.user_agent,
                delay_min=self.rule.delay_min,
                delay_max=self.rule.delay_max,
            ) as crawler:
                html = await self._fetch_with_method(urls[0], crawler)
                if html:
                    all_links = self._extract_links_from_html(html, urls[0], level)
        elif self.rule.crawl_method == "github":
            # GitHub API returns JSON
            for url in urls:
                all_links.extend(self._extract_links_from_github_api(url))
        else:
            # Use httpx
            for url in urls:
                self._log("info", f"Extracting links from: {url}")
                html = self._fetch_with_httpx(url)
                if not html:
                    continue

                # Extract links
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
                    elif selector_type == "rss" or selector == "link":
                        # Special handling for RSS feeds - extract from <link> tags
                        links = []
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(html, 'xml')
                        for link in soup.find_all('link'):
                            text = link.get_text()
                            if text and text.startswith('http'):
                                links.append(text)
                        for guid in soup.find_all('guid'):
                            text = guid.get_text()
                            if text and text.startswith('http'):
                                links.append(text)
                    else:
                        links = []

                    all_links.extend(links)
                else:
                    # Default: extract all article links
                    from bs4 import BeautifulSoup

                    # Try HTML parser first
                    soup = BeautifulSoup(html, 'lxml')
                    links_found = soup.find_all('a', href=True)

                    # If no links found, try XML parser (for RSS content)
                    if not links_found:
                        try:
                            soup = BeautifulSoup(html, 'xml')
                            # For RSS, extract from <link> tags
                            for link in soup.find_all('link'):
                                text = link.get_text()
                                if text and text.startswith('http'):
                                    all_links.append(text)
                            # Also check for <a> tags
                            for link in soup.find_all('a', href=True):
                                href = link.get('href')
                                if href and href.startswith('http'):
                                    all_links.append(href)
                        except:
                            pass

                    # Last resort: regex
                    if not all_links:
                        import re
                        all_links = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', html)

                    for href in links_found:
                        href = href.get('href') if hasattr(href, 'get') else href
                        if href and href.startswith('http'):
                            all_links.append(href)

        # Filter and deduplicate
        # For intermediate levels (not final), only apply exclude_patterns, skip detail_url_pattern
        if level and not level.is_final:
            # Only apply exclude_patterns filtering for intermediate levels
            all_links = self._filter_links(all_links, apply_detail_pattern=False)
        else:
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

        # Special handling for GitHub repositories
        if self.rule.crawl_method == "github":
            return await self._extract_github_repo(url)

        # Fetch based on method
        html = None
        if self.rule.crawl_method == "playwright":
            async with PlaywrightCrawler(
                user_agent=self.rule.user_agent,
                delay_min=self.rule.delay_min,
                delay_max=self.rule.delay_max,
            ) as crawler:
                html = await crawler.fetch(url)

        if not html and self.rule.crawl_method in ["httpx", "hybrid"]:
            import httpx
            headers = {"User-Agent": self.rule.user_agent} if self.rule.user_agent else {}
            response = httpx.get(url, headers=headers, timeout=30)
            html = response.text

        if not html:
            raise ValueError(f"Failed to fetch: {url}")

        # Extract content - use trafilatura for better extraction
        if self.rule.crawl_method in ["trafilatura", "hybrid"] or self.rule.title_selector is None:
            # If no custom selectors configured, use trafilatura for better results
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

    async def _extract_github_repo(self, url: str) -> Optional[Article]:
        """Extract GitHub repository information using API"""
        import httpx

        # Convert URL to API URL
        # https://github.com/user/repo -> https://api.github.com/repos/user/repo
        api_url = url.replace("https://github.com/", "https://api.github.com/repos/")

        try:
            headers = {
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": self.rule.user_agent or "DailyNewsCrawler"
            }
            response = httpx.get(api_url, headers=headers, timeout=30)
            data = response.json()

            if response.status_code != 200:
                self._log("error", f"GitHub API error: {data.get('message', 'Unknown')}")
                return None

            # Extract repo info
            content = {
                "title": data.get("name", ""),
                "text": data.get("description", "") or "",
                "author": data.get("owner", {}).get("login", ""),
                "date": data.get("created_at", ""),
                "image": data.get("owner", {}).get("avatar_url", ""),
            }

            # Add more details
            details = f"""
**Stars**: {data.get("stargazers_count", 0)}
**Forks**: {data.get("forks_count", 0)}
**Language**: {data.get("language", "Unknown")}
**License**: {data.get("license", {}).get("name", "None") if data.get("license") else "None"}
**Topics**: {", ".join(data.get("topics", []))}

[View on GitHub]({url})
"""
            content["text"] = details + "\n\n" + content.get("text", "")

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

            self._log("info", f"Extracted GitHub repo: {content.get('title')}")
            return article

        except Exception as e:
            self._log("error", f"Failed to extract GitHub repo {url}: {e}")
            return None

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

    def _filter_links(self, links: List[str], apply_detail_pattern: bool = True) -> List[str]:
        """Filter and deduplicate links"""
        import re

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

        # Get detail URL pattern for positive matching
        detail_url_pattern = self.rule.detail_url_pattern

        for link in links:
            # Skip duplicates
            if link in seen:
                continue

            # Check detail URL pattern (positive filter)
            if apply_detail_pattern and detail_url_pattern:
                try:
                    if not re.match(detail_url_pattern, link):
                        continue
                except re.error:
                    pass  # If regex is invalid, skip this filter

            # Check exclude patterns (negative filter)
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

    async def _fetch_with_method(self, url: str, crawler) -> Optional[str]:
        """Fetch using specified method (playwright or httpx)"""
        return await crawler.fetch(url)

    def _fetch_with_httpx(self, url: str) -> Optional[str]:
        """Fetch using httpx"""
        import httpx
        headers = {"User-Agent": self.rule.user_agent} if self.rule.user_agent else {}
        try:
            response = httpx.get(url, headers=headers, timeout=30)
            return response.text
        except Exception as e:
            self._log("error", f"Failed to fetch {url}: {e}")
            return None

    def _extract_links_from_html(self, html: str, url: str, level: Optional[RuleLevel]) -> List[str]:
        """Extract links from HTML"""
        links = []

        # Apply pagination if configured
        # Skip for simplicity

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
            elif selector_type == "rss" or selector == "link":
                # Special handling for RSS feeds - extract from <link> tags
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html, 'xml')
                for link in soup.find_all('link'):
                    text = link.get_text()
                    if text and text.startswith('http'):
                        links.append(text)
                for guid in soup.find_all('guid'):
                    text = guid.get_text()
                    if text and text.startswith('http'):
                        links.append(text)
        else:
            # Default: extract all article links
            # For JavaScript-rendered content (Playwright), try regex first
            import re
            # Try to find all /p/XXX patterns first (common for news sites)
            article_paths = re.findall(r'(https?://[^\s"\')]+/p/\d+[^\s"\')]*)', html)
            links.extend(article_paths)

            # Also try BeautifulSoup as fallback
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'lxml')
            for a in soup.find_all('a', href=True):
                href = a['href']
                if href.startswith('http'):
                    links.append(href)

        return list(set(links))  # Deduplicate

    def _extract_links_from_github_api(self, url: str) -> List[str]:
        """Extract repository links from GitHub API JSON response"""
        links = []
        try:
            import httpx
            from datetime import datetime, timedelta

            # Auto-calculate date for dynamic queries
            # Replace {{days_ago}} with date from N days ago
            if "{{days_ago}}" in url:
                days = 7  # default: last 7 days
                # Try to extract number from url like "created:>{{days_ago}}"
                import re
                match = re.search(r'created:>(\d+)', url)
                if match:
                    days = int(match.group(1))

                date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
                url = url.replace("{{days_ago}}", date)
                self._log("info", f"Using date: {date} for GitHub query")

            headers = {"Accept": "application/vnd.github.v3+json"}
            if self.rule.user_agent:
                headers["User-Agent"] = self.rule.user_agent

            response = httpx.get(url, headers=headers, timeout=30)
            data = response.json()

            # Handle rate limiting
            if isinstance(data, dict) and "message" in data:
                if "rate limit" in data["message"].lower():
                    self._log("error", "GitHub API rate limit exceeded")
                else:
                    self._log("error", f"GitHub API error: {data['message']}")
                return []

            # Handle search results
            if "items" in data:
                for item in data["items"]:
                    links.append(item.get("html_url", ""))
            # Handle user's repos
            elif isinstance(data, list):
                for repo in data:
                    links.append(repo.get("html_url", ""))

            self._log("info", f"Extracted {len(links)} GitHub repos")

        except Exception as e:
            self._log("error", f"GitHub API error: {e}")

        return links

    def _log(self, level: str, message: str):
        """Add log entry"""
        log = Log(job_id=self.job_id, level=level, message=message)
        self.db.add(log)
        self.db.commit()
