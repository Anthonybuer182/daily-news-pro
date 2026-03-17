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

        # 增强反检测配置
        default_ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

        # 先尝试Chromium - 增强反检测
        launch_options = {
            "headless": True,
            "args": [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-web-security",
                "--disable-blink-features=AutomationControlled",
                "--disable-features=IsolateOrigins,site-per-process",
                "--window-size=1920,1080",
                "--start-maximized",
                # 模拟真实浏览器
                "--disable-extensions",
                "--disable-plugins",
                "--disable-default-apps",
                "--disable-background-networking",
                "--disable-default-fonts",
                "--disable-sync",
                "--metrics-recording-only",
                "--mute-audio",
                "--no-first-run",
            ],
            "ignore_default_args": ["--enable-automation", "--headless"],
        }
        # 使用默认User-Agent避免被检测
        launch_options["user_agent"] = self.user_agent or default_ua

        if self.proxy:
            launch_options["proxy"] = {"server": self.proxy}

        try:
            browser_type = self.playwright.chromium
            self.browser = await browser_type.launch(**launch_options)
        except Exception as e:
            # 如果启动失败，尝试使用Firefox（不使用user_agent参数）
            try:
                launch_options_ff = {
                    "headless": True,
                    "args": [
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                    ],
                }
                browser_type = self.playwright.firefox
                self.browser = await browser_type.launch(**launch_options_ff)
            except:
                # 如果Firefox也失败，抛出异常让调用方处理
                if self.playwright:
                    await self.playwright.stop()
                raise RuntimeError(f"Failed to launch browser: {e}")
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

        # 设置视口和上下文
        context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=self.user_agent or "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
        )
        page = await context.new_page()

        # 添加反检测脚本
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            window.navigator.chrome = {
                runtime: {}
            };
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en']
            });
        """)

        try:
            # 增加超时时间到60秒，使用 wait_until: "domcontentloaded" 更快
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            # 等待页面稳定
            await page.wait_for_load_state("networkidle", timeout=30000)
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
