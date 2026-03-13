import asyncio
import random
from typing import Optional, Dict, List
from playwright.async_api import async_playwright, Browser, Page, Playwright
from app.services.selector import SelectorParser


class PlaywrightCrawler:
    """Playwright-based web crawler"""

    def __init__(
        self,
        user_agent: str = None,
        proxy: str = None,
        delay_min: int = 1,
        delay_max: int = 3,
    ):
        self.user_agent = user_agent
        self.proxy = proxy
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.browser: Optional[Browser] = None
        self.playwright: Optional[Playwright] = None

    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        browser_type = self.playwright.chromium
        launch_options = {
            "headless": True,
        }
        if self.user_agent:
            launch_options["user_agent"] = self.user_agent
        if self.proxy:
            launch_options["proxy"] = {"server": self.proxy}

        self.browser = await browser_type.launch(**launch_options)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def fetch(self, url: str) -> Optional[str]:
        """Fetch page HTML"""
        if not self.browser:
            raise RuntimeError("Browser not initialized")

        context = await self.browser.new_context()
        page = await context.new_page()

        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await self._random_delay()
            html = await page.content()
            return html
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
        finally:
            await context.close()

    async def click_and_wait(self, url: str, click_selector: str, wait_selector: str = None) -> Optional[str]:
        """Click element and wait for new content"""
        if not self.browser:
            raise RuntimeError("Browser not initialized")

        context = await self.browser.new_context()
        page = await context.new_page()

        try:
            await page.goto(url, wait_until="networkidle")
            await self._random_delay()

            await page.click(click_selector)
            if wait_selector:
                await page.wait_for_selector(wait_selector, timeout=10000)

            await self._random_delay()
            html = await page.content()
            return html
        except Exception as e:
            print(f"Error clicking {click_selector}: {e}")
            return None
        finally:
            await context.close()

    async def scroll_load(self, url: str, scroll_selector: str = None, times: int = 3) -> Optional[str]:
        """Scroll to load more content"""
        if not self.browser:
            raise RuntimeError("Browser not initialized")

        context = await self.browser.new_context()
        page = await context.new_page()

        try:
            await page.goto(url, wait_until="networkidle")
            await self._random_delay()

            for _ in range(times):
                if scroll_selector:
                    await page.evaluate(f"""
                        document.querySelector('{scroll_selector}').scrollIntoView();
                    """)
                else:
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(2)

            html = await page.content()
            return html
        except Exception as e:
            print(f"Error scrolling: {e}")
            return None
        finally:
            await context.close()

    async def extract_links(
        self,
        url: str,
        selector: str,
        selector_type: str = "css",
        base_url: str = ""
    ) -> List[str]:
        """Extract links from page"""
        html = await self.fetch(url)
        if not html:
            return []

        if selector_type == "css":
            return SelectorParser.extract_links_css(html, selector, base_url)
        elif selector_type == "xpath":
            return SelectorParser.extract_links_xpath(html, selector, base_url)
        else:
            return []

    async def extract_content(
        self,
        url: str,
        selectors: Dict[str, str],
        selector_type: str = "css"
    ) -> Dict[str, Optional[str]]:
        """Extract content from page"""
        html = await self.fetch(url)
        if not html:
            return {}

        result = {}
        for field, selector in selectors.items():
            if selector_type == "css":
                text = SelectorParser.extract_text_css(html, selector)
                result[field] = text
            elif selector_type == "xpath":
                text = SelectorParser.extract_text_xpath(html, selector)
                result[field] = text

        return result

    async def _random_delay(self):
        """Random delay between requests"""
        delay = random.uniform(self.delay_min, self.delay_max)
        await asyncio.sleep(delay)
