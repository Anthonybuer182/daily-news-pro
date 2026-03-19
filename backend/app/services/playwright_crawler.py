import asyncio
import random
from typing import Optional, Dict, List
from playwright.async_api import async_playwright, Browser, Page, Playwright, Response
from app.services.selector import SelectorParser

# HTTP fallback imports
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


def build_stealth_script() -> str:
    """构建反检测脚本，模拟真实浏览器环境"""
    return """
    // 移除 webdriver 属性
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined,
        configurable: true
    });

    // 模拟 Chrome 对象
    window.chrome = {
        runtime: {},
        loadTimes: function() {},
        csi: function() {}
    };

    // 模拟 plugins
    Object.defineProperty(navigator, 'plugins', {
        get: () => {
            const plugins = [
                { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
                { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
                { name: 'Native Client', filename: 'internal-nacl-plugin' }
            ];
            return plugins;
        }
    });

    // 模拟 languages
    Object.defineProperty(navigator, 'languages', {
        get: () => ['en-US', 'en', 'zh-CN', 'zh']
    });

    // 移除自动化相关属性
    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
    delete window.__webdriver_evaluate;
    delete window.__selenium_evaluate;
    delete window.__webdriver_script_function;
    delete window.__webdriver_script_func;
    delete window.__webdriver_script_fn;
    delete window.__fxdriver_evaluate;
    delete window.__driver_unwrapped;
    delete window.__webdriver_unwrapped;
    delete window.__driver_evaluate;
    delete window.__selenium_unwrapped;
    delete window.__fxdriver_unwrapped;

    // 模拟 permissions
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) => (
        parameters.name === 'notifications' ?
            Promise.resolve({ state: Notification.permission }) :
            originalQuery(parameters)
    );
    """


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
        default_ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/115.0"

        # 先尝试Firefox（更稳定）
        try:
            launch_options_ff = {
                "headless": True,
                "args": [
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-extensions",
                    "--disable-plugins",
                    "--disable-background-networking",
                    "--disable-sync",
                    "--metrics-recording-only",
                    "--mute-audio",
                    "--no-first-run",
                ],
            }
            browser_type = self.playwright.firefox
            self.browser = await browser_type.launch(**launch_options_ff)

            # 创建 context 并添加反检测设置
            self.context = await self.browser.new_context(
                user_agent=self.user_agent or default_ua,
                viewport={'width': 1920, 'height': 1080},
                locale='en-US',
                timezone_id='America/New_York',
                extra_http_headers={
                    'Accept-Language': 'en-US,en;q=0.9',
                }
            )

            # 为 Firefox 添加反检测脚本
            ff_page = await self.context.new_page()
            await ff_page.add_init_script(build_stealth_script())
            await ff_page.close()

        except Exception as e:
            # Firefox失败，尝试Chromium
            try:
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
                if self.user_agent:
                    launch_options["user_agent"] = self.user_agent
                if self.proxy:
                    launch_options["proxy"] = {"server": self.proxy}

                browser_type = self.playwright.chromium
                self.browser = await browser_type.launch(**launch_options)

                # 创建 context
                self.context = await self.browser.new_context(
                    user_agent=self.user_agent or default_ua,
                    viewport={'width': 1920, 'height': 1080},
                )

                # 添加反检测脚本
                page = await self.context.new_page()
                await page.add_init_script(build_stealth_script())
                await page.close()

            except Exception as e2:
                # 都失败，抛出异常
                if self.playwright:
                    await self.playwright.stop()
                raise RuntimeError(f"Failed to launch browsers: {e}, {e2}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def fetch(self, url: str) -> Optional[str]:
        """Fetch page HTML - tries Playwright first, falls back to HTTP"""
        # 尝试使用 Playwright
        if self.browser:
            try:
                return await self._fetch_with_playwright(url)
            except Exception as e:
                print(f"Playwright fetch failed for {url}: {e}")

        # Fallback to HTTP if Playwright fails
        if HTTPX_AVAILABLE:
            print(f"Falling back to HTTP for {url}")
            return await self._fetch_with_http(url)

        return None

    async def _fetch_with_playwright(self, url: str) -> Optional[str]:
        """Fetch using Playwright browser"""
        # 每次都创建新的 context，避免状态污染
        # 注意：这会有性能开销，但如果网站有反爬机制更稳定
        created_context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=self.user_agent or "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/115.0",
            locale="en-US",
            timezone_id="America/New_York",
        )
        page = await created_context.new_page()

        # 添加反检测脚本到当前页面
        await page.add_init_script(build_stealth_script())

        try:
            # 使用 commit 等待策略 - 只要收到第一个响应就继续
            # 这避免了等待所有资源加载（可能被阻塞）
            response = await page.goto(url, wait_until="commit", timeout=30000)

            # 直接从 response 获取完整的 HTML body
            # page.content() 可能会被 JS 修改导致内容不完整
            if response:
                html_bytes = await response.body()
                html = html_bytes.decode('utf-8', errors='replace')
                return html

            # 如果 response 为 None，尝试 page.content() 作为后备
            await asyncio.sleep(1)
            html = await page.content()
            return html
        except Exception as e:
            raise e  # Re-raise to be caught by fetch()
        finally:
            await created_context.close()

    async def _fetch_with_http(self, url: str) -> Optional[str]:
        """Fallback fetch using httpx"""
        if not HTTPX_AVAILABLE:
            return None

        headers = {
            'User-Agent': self.user_agent or 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Connection': 'keep-alive',
        }

        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    return response.text
                else:
                    print(f"HTTP fetch failed with status {response.status_code}")
                    return None
        except Exception as e:
            print(f"HTTP fetch error: {e}")
            return None

    async def click_and_wait(self, url: str, click_selector: str, wait_selector: str = None) -> Optional[str]:
        """Click element and wait for new content"""
        if not self.browser:
            raise RuntimeError("Browser not initialized")

        # 使用共享 context 或创建新的
        created_context = None
        if hasattr(self, 'context') and self.context:
            page = await self.context.new_page()
        else:
            created_context = await self.browser.new_context()
            page = await created_context.new_page()

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
            if created_context:
                await created_context.close()
            else:
                await page.close()

    async def scroll_load(self, url: str, scroll_selector: str = None, times: int = 3) -> Optional[str]:
        """Scroll to load more content"""
        if not self.browser:
            raise RuntimeError("Browser not initialized")

        # 使用共享 context 或创建新的
        created_context = None
        if hasattr(self, 'context') and self.context:
            page = await self.context.new_page()
        else:
            created_context = await self.browser.new_context()
            page = await created_context.new_page()

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
            if created_context:
                await created_context.close()
            else:
                await page.close()

    async def scroll_and_wait(self, scroll_selector: str = "", wait_ms: int = 2000) -> bool:
        """Scroll down and wait for more content to load"""
        # Note: This method needs to be called on an existing page
        # For pagination, we'll use a different approach in the crawler
        await asyncio.sleep(wait_ms / 1000)
        return True

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
