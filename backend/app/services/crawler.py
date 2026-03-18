import asyncio
import os
import hashlib
import json
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

        self._log("info", f"Starting crawl for rule: {self.rule.name}, type: {self.rule.source_type}")

        try:
            # 根据 source_type 分发处理
            source_type = self.rule.source_type or "playwright"

            if source_type == "rss":
                result = await self._crawl_rss()
            elif source_type == "api":
                result = await self._crawl_api()
            elif source_type == "playwright":
                result = await self._crawl_playwright()
            else:
                raise ValueError(f"Unknown source_type: {source_type}")

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

    async def _crawl_rss(self) -> Dict:
        """RSS 订阅源抓取"""
        import httpx
        from bs4 import BeautifulSoup

        url = self.rule.source_url
        if not url:
            raise ValueError("No RSS URL provided")

        self._log("info", f"Fetching RSS feed: {url}")

        try:
            # 获取 RSS 内容
            headers = {"User-Agent": self.rule.user_agent or "DailyNewsCrawler/1.0"}
            response = httpx.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            xml_content = response.text

            # 解析 RSS
            soup = BeautifulSoup(xml_content, 'xml')
            items = soup.find_all('item') or soup.find_all('entry')

            if not items:
                self._log("warning", "No items found in RSS feed")
                return {"total": 0, "success": 0, "failed": 0}

            # 获取字段映射配置
            field_mapping = self._get_field_mapping()

            success_count = 0
            failed_count = 0

            for item in items:
                try:
                    article = self._extract_rss_item(item, field_mapping)
                    if article:
                        success_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    self._log("error", f"Failed to extract RSS item: {e}")
                    failed_count += 1

            self.job.articles_count = len(items)
            self.job.success_count = success_count
            self.job.failed_count = failed_count

            return {"total": len(items), "success": success_count, "failed": failed_count}

        except Exception as e:
            raise ValueError(f"RSS crawl failed: {e}")

    def _extract_rss_item(self, item, field_mapping: Dict) -> Optional[Article]:
        """从 RSS item 中提取文章"""
        # 默认字段映射
        title_field = field_mapping.get("title", "title")
        link_field = field_mapping.get("link", "link")
        content_field = field_mapping.get("content", "content") or field_mapping.get("description", "description")
        author_field = field_mapping.get("author", "author")
        date_field = field_mapping.get("date", "date") or field_mapping.get("pubDate", "pubDate")

        # 提取字段
        title = self._get_rss_field(item, title_field)
        url = self._get_rss_field(item, link_field)
        content = self._get_rss_field(item, content_field)
        author = self._get_rss_field(item, author_field)
        date_str = self._get_rss_field(item, date_field)

        if not url:
            return None

        # 检查是否已存在
        existing = self.db.query(Article).filter(Article.url == url).first()
        if existing:
            self._log("info", f"Article already exists: {url}")
            return existing

        # 生成 markdown
        markdown_content = self._generate_markdown({
            "title": title,
            "text": content or "",
            "author": author,
            "date": date_str,
        }, url)
        markdown_file = self._save_markdown(markdown_content, url)

        # 创建文章记录
        article = Article(
            rule_id=self.rule.id,
            url=url,
            title=title,
            summary=content[:500] if content else None,
            author=author,
            publish_time=self._parse_date(date_str),
            markdown_file=markdown_file,
            status="success",
        )

        self.db.add(article)
        self.db.commit()

        self._log("info", f"Extracted RSS article: {title}")
        return article

    def _get_rss_field(self, item, field: str) -> Optional[str]:
        """获取 RSS item 的字段"""
        if not field:
            return None

        # 尝试不同的大小写形式
        element = item.find(field.lower())
        if element:
            return element.get_text(strip=True)

        element = item.find(field.upper())
        if element:
            return element.get_text(strip=True)

        # 尝试直接获取
        return item.get(field)

    def _get_field_mapping(self) -> Dict:
        """获取字段映射配置"""
        if not self.rule.field_mapping:
            return {}

        try:
            return json.loads(self.rule.field_mapping)
        except:
            return {}

    def _get_extract_config(self) -> Dict:
        """获取 Playwright 提取配置"""
        if not self.rule.extract_config:
            return {}

        try:
            return json.loads(self.rule.extract_config)
        except:
            return {}

    def _get_request_config(self) -> Dict:
        """获取 API 请求配置"""
        if not self.rule.request_config:
            return {}

        try:
            return json.loads(self.rule.request_config)
        except:
            return {}

    async def _crawl_api(self) -> Dict:
        """API 接口抓取"""
        import httpx

        url = self.rule.source_url
        if not url:
            raise ValueError("No API URL provided")

        self._log("info", f"Fetching API: {url}")

        try:
            # 获取请求配置
            headers = {}
            if self.rule.headers_config:
                try:
                    headers = json.loads(self.rule.headers_config)
                except:
                    pass
            if self.rule.user_agent:
                headers["User-Agent"] = self.rule.user_agent

            # 处理动态日期参数
            from datetime import timedelta
            if "{{days_ago}}" in url:
                match_days = 7
                import re
                m = re.search(r'created:>(\d+)', url)
                if m:
                    match_days = int(m.group(1))
                date = (datetime.now() - timedelta(days=match_days)).strftime("%Y-%m-%d")
                url = url.replace("{{days_ago}}", date)
                self._log("info", f"Using date: {date} for API query")

            response = httpx.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            # 获取字段映射
            field_mapping = self._get_field_mapping()

            # 处理返回数据（支持数组或对象中的 items）
            items = data
            if isinstance(data, dict):
                items = data.get("items", data.get("data", [data]))

            if not isinstance(items, list):
                items = [items]

            success_count = 0
            failed_count = 0

            for item in items:
                try:
                    article = self._extract_api_item(item, field_mapping)
                    if article:
                        success_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    self._log("error", f"Failed to extract API item: {e}")
                    failed_count += 1

            self.job.articles_count = len(items)
            self.job.success_count = success_count
            self.job.failed_count = failed_count

            return {"total": len(items), "success": success_count, "failed": failed_count}

        except Exception as e:
            raise ValueError(f"API crawl failed: {e}")

    def _extract_api_item(self, item: Dict, field_mapping: Dict) -> Optional[Article]:
        """从 API 响应中提取文章"""
        # 获取字段映射
        title_field = field_mapping.get("title", "title")
        url_field = field_mapping.get("url", "url") or field_mapping.get("link", "link") or field_mapping.get("html_url", "html_url")
        content_field = field_mapping.get("content", "content") or field_mapping.get("body", "body") or field_mapping.get("description", "description")
        author_field = field_mapping.get("author", "author") or field_mapping.get("owner", "owner")
        date_field = field_mapping.get("date", "date") or field_mapping.get("created_at", "created_at") or field_mapping.get("published", "published")
        image_field = field_mapping.get("image", "image") or field_mapping.get("avatar_url", "avatar_url")

        # 提取字段
        title = self._get_nested_field(item, title_field)
        url = self._get_nested_field(item, url_field)
        content = self._get_nested_field(item, content_field)
        author = self._get_nested_field(item, author_field)
        date_str = self._get_nested_field(item, date_field)
        image = self._get_nested_field(item, image_field)

        if not url:
            return None

        # 检查是否已存在
        existing = self.db.query(Article).filter(Article.url == url).first()
        if existing:
            self._log("info", f"Article already exists: {url}")
            return existing

        # 生成 markdown
        markdown_content = self._generate_markdown({
            "title": title,
            "text": content or "",
            "author": author,
            "date": date_str,
            "image": image,
        }, url)
        markdown_file = self._save_markdown(markdown_content, url)

        # 创建文章记录
        article = Article(
            rule_id=self.rule.id,
            url=url,
            title=title,
            summary=content[:500] if content else None,
            author=author,
            publish_time=self._parse_date(date_str),
            cover_image=image,
            markdown_file=markdown_file,
            status="success",
        )

        self.db.add(article)
        self.db.commit()

        self._log("info", f"Extracted API article: {title}")
        return article

    def _get_nested_field(self, data: Dict, field: str) -> Optional[str]:
        """获取嵌套字段，支持点号分隔的路径"""
        if not field or not data:
            return None

        # 支持嵌套如 "owner.login"
        parts = field.split(".")
        current = data

        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None

        return str(current) if current is not None else None

    async def _crawl_playwright(self) -> Dict:
        """Playwright + Trafilatura 抓取"""
        # 检查是否有新的 extract_config 配置
        extract_config = self._get_extract_config()
        if extract_config:
            return await self._crawl_with_config(extract_config)

        # 旧逻辑：检查是否有层级配置
        if self.rule.levels:
            return await self._crawl_with_levels()
        else:
            return await self._crawl_simple_playwright()

    async def _crawl_with_config(self, config: Dict) -> Dict:
        """使用新的统一配置抓取 - 两阶段：列表→详情"""
        list_config = config.get("list", {})
        detail_config = config.get("detail", {})
        wait_config = config.get("wait", {})

        # 获取列表页 URL
        list_url = list_config.get("url")
        if not list_url:
            list_url = self.rule.source_url

        if not list_url:
            raise ValueError("No list page URL provided")

        self._log("info", f"Crawling with unified config, list URL: {list_url}")

        async with PlaywrightCrawler(
            user_agent=self.rule.user_agent,
            delay_min=self.rule.delay_min,
            delay_max=self.rule.delay_max,
        ) as crawler:
            # 检查是否配置了分页
            pagination = list_config.get("pagination", {})

            if pagination:
                # 分页抓取
                all_items = await self._crawl_with_pagination(list_url, list_config, crawler)
            else:
                # 单页抓取
                html = await crawler.fetch(list_url)
                if not html:
                    raise ValueError(f"Failed to fetch list page: {list_url}")

                # 检查是否配置了列表字段提取（item_fields）
                item_fields = list_config.get("item_fields", {})
                if item_fields:
                    all_items = self._extract_list_items_with_config(html, list_config, list_url)
                else:
                    # 没有配置 item_fields，使用原来的方式
                    article_urls = self._extract_links_with_config(html, list_config, list_url)
                    all_items = [{'url': url} for url in article_urls]

            self._log("info", f"Extracted {len(all_items)} items from list pages")

            # 过滤链接
            list_items = self._filter_list_items(all_items)

            # 保存到数据库（状态为 pending）
            saved_count = self._save_list_items(list_items)
            self._log("info", f"Saved {saved_count} new pending articles from list")

            # 阶段2：抓取详情页（只抓新保存的）
            return await self._extract_pending_articles(detail_config, crawler)

    async def _crawl_with_pagination(self, start_url: str, list_config: Dict, crawler) -> List[Dict]:
        """分页抓取列表"""
        pagination = list_config.get("pagination", {})
        pagination_type = pagination.get("type", "button")  # button, scroll, param
        max_pages = pagination.get("max_pages", 5)
        item_fields = list_config.get("item_fields", {})

        all_items = []
        current_url = start_url

        for page in range(1, max_pages + 1):
            self._log("info", f"Fetching list page {page}: {current_url}")

            # 获取页面
            html = await crawler.fetch(current_url)
            if not html:
                self._log("warning", f"Failed to fetch page {page}")
                break

            # 提取内容
            if item_fields:
                items = self._extract_list_items_with_config(html, list_config, current_url)
            else:
                urls = self._extract_links_with_config(html, list_config, current_url)
                items = [{'url': url} for url in urls]

            if not items:
                self._log("info", f"No more items found on page {page}")
                break

            all_items.extend(items)
            self._log("info", f"Page {page}: extracted {len(items)} items, total: {len(all_items)}")

            # 处理分页
            if page >= max_pages:
                break

            if pagination_type == "button":
                # 点击"加载更多"按钮
                button_selector = pagination.get("selector", ".load-more, .more, button:has-text('更多')")
                html = await crawler.click_and_wait(current_url, button_selector)
                if not html:
                    self._log("info", "No more button found, stopping pagination")
                    break
                # 继续用相同 URL 提取（页面已更新）
                continue
            elif pagination_type == "scroll":
                # 滚动加载 - 使用 scroll_load 方法
                scroll_times = pagination.get("scroll_times", 3)
                html = await crawler.scroll_load(current_url, "", scroll_times)
                if not html:
                    self._log("info", "Scroll failed, stopping pagination")
                    break
                # 提取滚动后的内容
                if item_fields:
                    new_items = self._extract_list_items_with_config(html, list_config, current_url)
                else:
                    urls = self._extract_links_with_config(html, list_config, current_url)
                    new_items = [{'url': url} for url in urls]
                # 如果没有新内容，停止
                if not new_items or len(new_items) <= len(items):
                    self._log("info", "No more content after scroll")
                    break
                continue
            elif pagination_type == "param":
                # URL参数分页
                param_name = pagination.get("param", "page")
                # 解析当前URL，添加/替换分页参数
                from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
                parsed = urlparse(current_url)
                params = parse_qs(parsed.query)
                params[param_name] = [str(page + 1)]
                new_query = urlencode(params, doseq=True)
                current_url = urlunparse((
                    parsed.scheme, parsed.netloc, parsed.path,
                    parsed.params, new_query, parsed.fragment
                ))
            else:
                break

        return all_items

    def _filter_list_items(self, items: List[Dict]) -> List[Dict]:
        """过滤列表项 - 排除模式和增量更新"""
        import re

        filtered = []
        exclude_patterns = []
        if self.rule.exclude_patterns:
            try:
                exclude_patterns = json.loads(self.rule.exclude_patterns)
            except:
                pass

        detail_url_pattern = self.rule.detail_url_pattern

        for item in items:
            url = item.get('url', '')
            if not url:
                continue

            # URL 模式过滤
            if detail_url_pattern:
                try:
                    if not re.match(detail_url_pattern, url):
                        continue
                except re.error:
                    pass

            # 排除模式过滤
            skip = False
            for pattern in exclude_patterns:
                if pattern.replace("*", "") in url:
                    skip = True
                    break
            if skip:
                continue

            filtered.append(item)

        return filtered

    def _is_duplicate_article(self, url: str) -> bool:
        """检查是否为已存在的文章（增量更新）"""
        from app.models import Article

        # 检查是否已存在
        existing = self.db.query(Article).filter(Article.url == url).first()
        if existing:
            # 如果已存在且状态为 success，说明已抓取过，跳过
            if existing.status == "success":
                return True
            # 如果是 pending 或 failed，则重新抓取
        return False

    def _save_list_items(self, items: List[Dict]) -> int:
        """保存列表项到数据库（增量更新：跳过已存在的success文章）"""
        from app.models import Article

        count = 0
        for item in items:
            url = item.get('url')
            if not url:
                continue

            # 增量更新：检查是否已存在
            existing = self.db.query(Article).filter(Article.url == url).first()
            if existing:
                # 如果已存在且状态为 success，说明已抓取过，跳过
                if existing.status == "success":
                    continue
                # 如果是 pending 或 failed，则更新基本信息后重新抓取
                if not existing.title and item.get('title'):
                    existing.title = item.get('title')
                if not existing.summary and item.get('summary'):
                    existing.summary = item.get('summary')[:500]
                if not existing.cover_image and item.get('image'):
                    existing.cover_image = item.get('image')
                if not existing.author and item.get('author'):
                    existing.author = item.get('author')
                if not existing.publish_time and item.get('date'):
                    existing.publish_time = self._parse_date(item.get('date'))
                existing.updated_at = datetime.utcnow()
                existing.status = "pending"  # 标记为待抓取
                self.db.commit()
                continue

            # 创建新记录（状态为 pending，表示待抓取详情）
            article = Article(
                rule_id=self.rule.id,
                url=url,
                title=item.get('title'),
                summary=item.get('summary', '').strip()[:500] if item.get('summary') else None,
                author=item.get('author'),
                publish_time=self._parse_date(item.get('date')) if item.get('date') else None,
                cover_image=item.get('image'),
                status="pending",  # 待抓取详情
            )
            self.db.add(article)
            count += 1

        if count > 0:
            self.db.commit()

        return count

    async def _extract_pending_articles(self, detail_config: Dict, crawler) -> Dict:
        """抓取 pending 状态的详情页内容"""
        from app.models import Article

        # 获取所有 pending 的文章
        pending_articles = self.db.query(Article).filter(
            Article.rule_id == self.rule.id,
            Article.status == "pending"
        ).all()

        if not pending_articles:
            self._log("info", "No pending articles to fetch")
            return {"total": 0, "success": 0, "failed": 0}

        self._log("info", f"Fetching details for {len(pending_articles)} pending articles")

        success_count = 0
        failed_count = 0

        for article in pending_articles:
            try:
                url = article.url

                # 获取详情页内容
                html = await crawler.fetch(url)
                if not html:
                    # 降级使用 httpx
                    import httpx
                    headers = {"User-Agent": self.rule.user_agent} if self.rule.user_agent else {}
                    try:
                        response = httpx.get(url, headers=headers, timeout=30)
                        html = response.text
                    except Exception as e:
                        self._log("error", f"Failed to fetch {url}: {e}")
                        article.status = "failed"
                        article.error_message = str(e)
                        failed_count += 1
                        continue

                if not html:
                    article.status = "failed"
                    article.error_message = "Empty response"
                    failed_count += 1
                    continue

                # 提取内容
                if detail_config:
                    content = await self._extract_with_config(html, detail_config)
                else:
                    content = TrafilaturaExtractor.extract_with_fallback(html)

                # 更新基本信息（如果之前没有）
                if not article.title and content.get("title"):
                    article.title = content.get("title")
                if not article.summary and content.get("text"):
                    article.summary = content.get("text")[:500]
                if not article.author and content.get("author"):
                    article.author = content.get("author")
                if not article.publish_time and content.get("date"):
                    article.publish_time = self._parse_date(content.get("date"))
                if not article.cover_image and content.get("image"):
                    article.cover_image = content.get("image")

                # 生成 markdown 并保存
                markdown_content = self._generate_markdown(content, url)
                markdown_file = self._save_markdown(markdown_content, url)

                article.markdown_file = markdown_file
                article.status = "success"
                self.db.commit()

                success_count += 1
                self._log("info", f"Extracted article: {article.title}")

            except Exception as e:
                self._log("error", f"Failed to process {article.url}: {e}")
                article.status = "failed"
                article.error_message = str(e)
                self.db.commit()
                failed_count += 1

        self.job.articles_count = len(pending_articles)
        self.job.success_count = success_count
        self.job.failed_count = failed_count

        return {
            "total": len(pending_articles),
            "success": success_count,
            "failed": failed_count,
        }

    async def _extract_articles_with_config(self, urls: List[str], detail_config: Dict, crawler) -> Dict:
        """使用配置提取文章内容"""
        success_count = 0
        failed_count = 0

        for url in urls:
            try:
                article = await self._extract_single_article_with_config(url, detail_config, crawler)
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

    async def _extract_single_article_with_config(self, url: str, detail_config: Dict, crawler) -> Optional[Article]:
        """使用配置提取单篇文章"""
        # 检查是否已存在
        existing = self.db.query(Article).filter(Article.url == url).first()
        if existing:
            self._log("info", f"Article already exists: {url}")
            return existing

        # 获取页面内容
        html = await crawler.fetch(url)
        if not html:
            # 降级使用 httpx
            import httpx
            headers = {"User-Agent": self.rule.user_agent} if self.rule.user_agent else {}
            try:
                response = httpx.get(url, headers=headers, timeout=30)
                html = response.text
            except Exception as e:
                self._log("error", f"Failed to fetch {url}: {e}")
                return None

        if not html:
            return None

        # 提取内容
        if detail_config:
            content = await self._extract_with_config(html, detail_config)
        else:
            # 使用 trafilatura 作为默认
            content = TrafilaturaExtractor.extract_with_fallback(html)

        # 如果没有提取到标题，使用 URL 作为标题
        if not content.get("title"):
            content["title"] = url.split("/")[-1] or url

        # 生成 markdown
        markdown_content = self._generate_markdown(content, url)
        markdown_file = self._save_markdown(markdown_content, url)

        # 创建文章记录
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

    async def _crawl_with_levels(self) -> Dict:
        """Crawl using level configuration"""
        levels = self.db.query(RuleLevel).filter(
            RuleLevel.rule_id == self.rule.id
        ).order_by(RuleLevel.level).all()

        if not levels:
            return await self._crawl_simple_playwright()

        # Start with first level URLs
        current_urls = [levels[0].url] if levels[0].url else []

        for level in levels:
            if level.is_final:
                if level.link_selector:
                    final_urls = await self._extract_links(current_urls, level)
                    self._log("info", f"Final level extracted {len(final_urls)} links")
                    return await self._extract_articles(final_urls)
                else:
                    return await self._extract_articles(current_urls)
            else:
                current_urls = await self._extract_links(current_urls, level)

        return {"urls": current_urls}

    async def _crawl_simple_playwright(self) -> Dict:
        """Simple single-level crawl for Playwright"""
        url = self.rule.source_url
        if not url:
            raise ValueError("No URL to crawl")

        # Extract links
        links = await self._extract_links([url], None)

        # Extract content from links
        return await self._extract_articles(links)

    async def _extract_links(self, urls: List[str], level: Optional[RuleLevel]) -> List[str]:
        """Extract links from pages"""
        all_links = []

        # Use Playwright for link extraction if source_type is playwright
        if self.rule.source_type == "playwright":
            async with PlaywrightCrawler(
                user_agent=self.rule.user_agent,
                delay_min=self.rule.delay_min,
                delay_max=self.rule.delay_max,
            ) as crawler:
                html = await self._fetch_with_method(urls[0], crawler)
                if html:
                    all_links = self._extract_links_from_html(html, urls[0], level)
        elif self.rule.source_type == "api":
            # API mode - skip link extraction, handled in _crawl_api
            pass
        else:
            # Use httpx for RSS mode
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

        # Fetch based on source_type (only playwright is used here)
        html = None
        async with PlaywrightCrawler(
            user_agent=self.rule.user_agent,
            delay_min=self.rule.delay_min,
            delay_max=self.rule.delay_max,
        ) as crawler:
            html = await crawler.fetch(url)

        # Fallback to httpx if playwright fails
        if not html:
            import httpx
            headers = {"User-Agent": self.rule.user_agent} if self.rule.user_agent else {}
            response = httpx.get(url, headers=headers, timeout=30)
            html = response.text

        if not html:
            raise ValueError(f"Failed to fetch: {url}")

        # Extract content - use trafilatura if no custom selectors configured
        if self.rule.title_selector is None:
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
        """Extract using custom selectors (legacy format)"""
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

    async def _extract_with_config(self, html: str, detail_config: Dict) -> Dict:
        """Extract using new unified extract_config format"""
        result = {}

        for field_name, field_config in detail_config.items():
            if not field_config:
                continue

            selector = field_config.get("selector")
            extract_type = field_config.get("type", "text")  # text, html, attribute
            attr = field_config.get("attr", "src")  # for attribute type

            if not selector:
                continue

            try:
                if extract_type == "text":
                    result[field_name] = SelectorParser.extract_text_css(html, selector)
                elif extract_type == "html":
                    result[field_name] = SelectorParser.extract_html_css(html, selector)
                elif extract_type == "attribute":
                    result[field_name] = SelectorParser.extract_attribute_css(html, selector, attr)
            except Exception as e:
                self._log("warning", f"Failed to extract {field_name}: {e}")
                result[field_name] = None

        return result

    def _extract_links_with_config(self, html: str, list_config: Dict, base_url: str) -> List[str]:
        """Extract article links using new unified config format"""
        selector = list_config.get("selector", "a")
        link_attr = list_config.get("link_attr", "href")

        # Use CSS selector to extract links
        links = SelectorParser.extract_links_css(html, selector, base_url)

        # If link_attr is not href, we need to handle it differently
        if link_attr != "href":
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'lxml')
            links = []
            for element in soup.select(selector):
                attr_value = element.get(link_attr)
                if attr_value:
                    # Handle relative URLs
                    from urllib.parse import urljoin
                    full_url = urljoin(base_url, attr_value)
                    links.append(full_url)

        return list(set(links))

    def _extract_list_items_with_config(self, html: str, list_config: Dict, base_url: str) -> List[Dict]:
        """Extract list items with basic info (title, summary, etc.)"""
        from bs4 import BeautifulSoup

        selector = list_config.get("selector", "a")
        item_fields = list_config.get("item_fields", {})  # 列表中每个item的字段提取配置

        soup = BeautifulSoup(html, 'lxml')
        elements = soup.select(selector)

        items = []
        for el in elements:
            item = {}

            # 提取链接
            link = el.get('href') or el.get('data-url')
            if link:
                from urllib.parse import urljoin
                item['url'] = urljoin(base_url, link)
            else:
                # 尝试从父元素获取链接
                parent = el.find_parent('a')
                if parent:
                    item['url'] = parent.get('href')
                    if item['url']:
                        from urllib.parse import urljoin
                        item['url'] = urljoin(base_url, item['url'])

            # 提取配置的字段
            for field_name, field_config in item_fields.items():
                if not field_config:
                    continue

                selector = field_config.get("selector")  # 可以是 CSS 选择器或相对路径
                extract_type = field_config.get("type", "text")

                if not selector:
                    continue

                try:
                    if extract_type == "text":
                        # 尝试在当前元素内查找
                        target = el.select_one(selector) if ',' not in selector else el
                        if target:
                            item[field_name] = target.get_text(strip=True)
                    elif extract_type == "attribute":
                        attr = field_config.get("attr", "src")
                        target = el.select_one(selector) if ',' not in selector else el
                        if target:
                            item[field_name] = target.get(attr)
                    elif extract_type == "html":
                        target = el.select_one(selector) if ',' not in selector else el
                        if target:
                            item[field_name] = str(target)
                except Exception as e:
                    pass

            if item.get('url'):
                items.append(item)

        return items

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
