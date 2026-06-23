"""爬虫基类 — 基于 rpa-common 共享模块

每个平台的爬虫继承此基类，复用统一的代理、指纹、Cookie 管理。
"""
from abc import ABC, abstractmethod
from typing import Optional

import httpx
from fake_useragent import UserAgent
from loguru import logger

# 优先使用 rpa-common（共享模块），否则降级到本地的 anti_anti_spider
try:
    from rpa_common import ProxyManager, CookieManager, RequestThrottle, FingerprintManager
    logger.info("[base] 使用 rpa-common 共享模块")
except ImportError:
    from anti_anti_spider.proxy_pool import ProxyPool as ProxyManager
    from anti_anti_spider.cookie_manager import CookieManager
    from anti_anti_spider.request_throttle import RequestThrottle
    from anti_anti_spider.fingerprint import FingerprintManager
    logger.warning("[base] rpa-common 未安装，使用本地 anti_anti_spider")


class BaseSpider(ABC):
    """爬虫抽象基类"""

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

    @property
    def http_client(self) -> httpx.Client:
        if self._http_client is None:
            self._http_client = httpx.Client(
                timeout=self.request_timeout,
                headers=self._build_headers(),
                follow_redirects=True,
            )
        return self._http_client

    def _build_headers(self) -> dict:
        return {
            "User-Agent": self.ua.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache",
        }

    @abstractmethod
    def fetch_trending_list(self) -> list[dict]:
        """获取热榜列表

        Returns:
            list[dict]: 标准化数据，每个包含:
                - rank: int, 排名
                - title: str, 标题
                - hot_value: str, 原始热度值
                - topic_url: str, 平台链接
                - snapshot_at: str, ISO 时间戳
        """
        ...

    def _make_request(self, url: str, method: str = "GET", **kwargs) -> httpx.Response:
        self.throttle.wait(self.platform_code)
        try:
            response = self.http_client.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as e:
            logger.error(f"[{self.platform_code}] HTTP {e.response.status_code}")
            raise
        except httpx.RequestError as e:
            logger.error(f"[{self.platform_code}] 请求异常: {e}")
            raise

    def safe_run(self) -> list[dict]:
        """安全执行框架（多层降级）"""
        try:
            return self.fetch_trending_list()
        except Exception as e:
            logger.error(f"[{self.platform_code}] 采集失败: {e}")
            if not self.use_playwright:
                logger.warning(f"[{self.platform_code}] 降级到 Playwright")
                self.use_playwright = True
                try:
                    return self.fetch_trending_list()
                except Exception as ee:
                    logger.error(f"[{self.platform_code}] Playwright 降级也失败: {ee}")
            raise

    def close(self):
        if self._http_client:
            self._http_client.close()
            self._http_client = None
