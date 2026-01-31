"""Base crawler class with User-Agent rotation, rate limiting, and retry logic."""
import asyncio
import logging
import random
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Callable, Awaitable

from playwright.async_api import async_playwright, Browser, Page, BrowserContext

from app.config import settings

logger = logging.getLogger(__name__)

# Common User-Agent strings for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]


class RateLimiter:
    """Simple rate limiter for requests."""

    def __init__(self, requests_per_second: float = 1.0):
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time: float = 0

    async def wait(self):
        """Wait until the next request is allowed."""
        now = asyncio.get_event_loop().time()
        elapsed = now - self.last_request_time
        if elapsed < self.min_interval:
            await asyncio.sleep(self.min_interval - elapsed)
        self.last_request_time = asyncio.get_event_loop().time()


class BaseCrawler(ABC):
    """Base class for all crawlers with enhanced features."""

    def __init__(self, config: dict):
        self.config = config
        self.city_id = config.get("city_id")
        self.data_source_id = config.get("data_source_id")
        self.keyword_id = config.get("keyword_id")
        self.playwright = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None
        self.rate_limiter = RateLimiter(settings.CRAWLER_RATE_LIMIT)
        self.user_agent = random.choice(USER_AGENTS)

    async def setup(self):
        """Initialize browser with random User-Agent."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ],
        )

        # Create context with random User-Agent
        self.context = await self.browser.new_context(
            user_agent=self.user_agent,
            viewport={"width": 1920, "height": 1080},
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
        )

        # Add stealth scripts to avoid detection
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh', 'en']});
        """)

        self.page = await self.context.new_page()

        # Set extra headers
        await self.page.set_extra_http_headers({
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        })

        logger.info(f"Browser initialized with User-Agent: {self.user_agent[:50]}...")

    async def teardown(self):
        """Close browser and cleanup resources."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def run(
        self,
        on_progress: Callable[[int, int], Awaitable[None]] | None = None,
    ) -> dict:
        """Run the crawler with error handling.

        Args:
            on_progress: Callback for progress updates (progress%, record_count)

        Returns:
            dict with crawl results
        """
        try:
            await self.setup()
            result = await self.crawl(on_progress)
            return result
        except Exception as e:
            logger.exception(f"Crawler failed: {e}")
            raise
        finally:
            await self.teardown()

    @abstractmethod
    async def crawl(
        self,
        on_progress: Callable[[int, int], Awaitable[None]] | None = None,
    ) -> dict:
        """Implement actual crawling logic in subclasses."""
        pass

    async def goto_with_retry(
        self,
        url: str,
        max_retries: int | None = None,
        wait_until: str = "domcontentloaded",
    ) -> bool:
        """Navigate to URL with rate limiting and retry logic.

        Args:
            url: URL to navigate to
            max_retries: Maximum retry attempts (default from settings)
            wait_until: Wait condition ('load', 'domcontentloaded', 'networkidle')

        Returns:
            True if navigation successful, False otherwise
        """
        if max_retries is None:
            max_retries = settings.CRAWLER_RETRY_MAX

        for attempt in range(max_retries + 1):
            try:
                # Rate limiting
                await self.rate_limiter.wait()

                # Add random delay to appear more human
                await self.wait_random(0.3, 1.0)

                # Navigate
                response = await self.page.goto(
                    url,
                    timeout=settings.CRAWLER_TIMEOUT * 1000,
                    wait_until=wait_until,
                )

                if response and response.ok:
                    logger.debug(f"Successfully loaded: {url}")
                    return True
                else:
                    status = response.status if response else "No response"
                    logger.warning(f"Page returned status {status}: {url}")

            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}/{max_retries + 1} failed for {url}: {e}")
                if attempt < max_retries:
                    # Exponential backoff
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.info(f"Waiting {wait_time:.1f}s before retry...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"All retries exhausted for {url}")
                    return False

        return False

    async def wait_random(self, min_sec: float = 0.5, max_sec: float = 2.0):
        """Wait a random amount of time to avoid detection."""
        delay = random.uniform(min_sec, max_sec)
        await asyncio.sleep(delay)

    async def scroll_page(self, scroll_count: int = 3, delay: float = 0.5):
        """Scroll down the page to load lazy content."""
        for _ in range(scroll_count):
            await self.page.evaluate("window.scrollBy(0, window.innerHeight)")
            await asyncio.sleep(delay)

    async def safe_get_text(self, selector: str, default: str = "") -> str:
        """Safely get text content from an element."""
        try:
            element = await self.page.query_selector(selector)
            if element:
                text = await element.text_content()
                return text.strip() if text else default
        except Exception:
            pass
        return default

    async def safe_get_attribute(
        self, selector: str, attribute: str, default: str = ""
    ) -> str:
        """Safely get an attribute from an element."""
        try:
            element = await self.page.query_selector(selector)
            if element:
                value = await element.get_attribute(attribute)
                return value.strip() if value else default
        except Exception:
            pass
        return default

    async def wait_for_selector_safe(
        self, selector: str, timeout: int = 10000
    ) -> bool:
        """Wait for a selector with error handling."""
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception:
            return False
