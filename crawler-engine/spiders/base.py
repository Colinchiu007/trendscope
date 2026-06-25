"""Base spider class used by all platform spiders."""
from abc import ABC, abstractmethod
from typing import Optional

import httpx
from fake_useragent import UserAgent
from loguru import logger

try:
    from rpa_common import ProxyManager, CookieManager, RequestThrottle, FingerprintManager
    logger.info("[base] Using rpa-common shared module")
except ImportError:
    from anti_anti_spider.proxy_pool import ProxyPool as ProxyManager
    from anti_anti_spider.cookie_manager import CookieManager
    from anti_anti_spider.request_throttle import RequestThrottle
    from anti_anti_spider.fingerprint import FingerprintManager
    logger.warning("[base] rpa-common not installed, using local anti_anti_spider")


class BaseSpider(ABC):

    platform_code: str = ""
    platform_name: str = ""
    base_url: str = ""
    request_timeout: int = 30
    use_proxy: bool = True
    use_playwright: bool = False

    def __init__(self):
        self.ua = UserAgent()
        self.proxy = ProxyManager() if self.use_proxy else None
        self.cookie = CookieManager()
        self.throttle = RequestThrottle()
        self._http_client: Optional[httpx.Client] = None
        self.logger = logger.bind(platform=self.platform_code)

    @property
    def http_client(self) -> httpx.Client:
        if self._http_client is None:
            headers = self._build_headers()
            # 不接受 br 编码，httpx 0.28 的 br 解码有问题
            headers["Accept-Encoding"] = "gzip, deflate"
            kwargs = dict(
                timeout=self.request_timeout,
                headers=headers,
                follow_redirects=True,
            )
            proxy_val = self.proxy.get() if self.proxy else None
            if proxy_val:
                kwargs["proxy"] = proxy_val
            self._http_client = httpx.Client(**kwargs)
        return self._http_client

    def _build_headers(self) -> dict:
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Cache-Control": "no-cache",
        }

    @abstractmethod
    def fetch_trending_list(self) -> list[dict]:
        ...

    def _make_request(self, url: str, method: str = "GET", follow_redirects: bool = None, **kwargs) -> httpx.Response:
        self.throttle.wait(self.platform_code)
        try:
            if follow_redirects is not None:
                kwargs["follow_redirects"] = follow_redirects
            response = self.http_client.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as e:
            logger.error(f"[{self.platform_code}] HTTP {e.response.status_code}")
            if self.proxy:
                self.proxy.report_failure(self.proxy._current)
            raise
        except httpx.RequestError as e:
            logger.error(f"[{self.platform_code}] Request error: {e}")
            if self.proxy:
                self.proxy.report_failure(self.proxy._current)
            raise

    def safe_run(self) -> list[dict]:
        try:
            return self.fetch_trending_list()
        except Exception as e:
            logger.error(f"[{self.platform_code}] Crawl failed: {e}")
            if not self.use_playwright:
                logger.warning(f"[{self.platform_code}] Falling back to Playwright")
                self.use_playwright = True
                try:
                    return self.fetch_trending_list()
                except Exception as ee:
                    logger.error(f"[{self.platform_code}] Playwright fallback also failed: {ee}")
            raise

    def close(self):
        if self._http_client:
            self._http_client.close()
            self._http_client = None
        if self.proxy:
            self.proxy._current = None
