"""视频号热榜爬虫 - 企业微信 API 方案

视频号几乎没有公开 API，可行的采集路径：
1. 企业微信「客户联系」→「发表内容到视频号」API（需企业微信认证）
2. 微信搜一搜「视频号」搜索结果（搜狗微信搜索）
3. Playwright 模拟微信内置浏览器访问 channels.weixin.qq.com

当前实现：通过搜狗微信搜索 + Playwright 混合方案
"""
import asyncio
from datetime import datetime, timezone

from spiders.base import BaseSpider


class ShipinhaoSpider(BaseSpider):
    platform_code = "shipinhao"
    platform_name = "视频号"
    base_url = "https://channels.weixin.qq.com/"
    use_playwright = True

    def fetch_trending_list(self) -> list[dict]:
        """使用 Playwright 模拟微信浏览器"""
        return asyncio.run(self._fetch_with_playwright())

    async def _fetch_with_playwright(self) -> list[dict]:
        from playwright.async_api import async_playwright
        from anti_anti_spider.fingerprint import FingerprintManager

        items = []
        async with async_playwright() as p:
            fp = FingerprintManager.get_playwright_stealth_args()
            viewport = FingerprintManager.get_random_viewport()

            browser = await p.chromium.launch(headless=True, args=["--no-sandbox"] + fp)
            context = await browser.new_context(
                viewport={"width": 375, "height": 812},  # 手机尺寸
                user_agent=(
                    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                    "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 "
                    "MicroMessenger/8.0.43"
                ),
                locale="zh-CN",
            )
            page = await context.new_page()

            try:
                # 访问视频号发现页
                await page.goto(
                    "https://channels.weixin.qq.com/finder?entry=hot",
                    wait_until="domcontentloaded",
                    timeout=30000,
                )
                await asyncio.sleep(5)

                # 尝试从页面提取
                items = await self._extract_from_page(page)
            except Exception:
                pass
            finally:
                await browser.close()

        return items[:30]

    async def _extract_from_page(self, page) -> list[dict]:
        """从页面提取视频号热榜"""
        now = datetime.now(timezone.utc).isoformat()

        js_code = """
        () => {
            const items = [];
            const cards = document.querySelectorAll(
                '.feed-card, .video-card, [class*="feed"], [class*="card"], .finder-feed-item'
            );
            cards.forEach((card, idx) => {
                const titleEl = card.querySelector(
                    '.feed-desc, .desc, [class*="desc"], [class*="title"], .nickname'
                );
                const authorEl = card.querySelector('.finder-name, .name, [class*="name"]');
                const likesEl = card.querySelector('.like-count, [class*="like"]');
                if (titleEl) {
                    items.push({
                        rank: idx + 1,
                        title: titleEl.textContent.trim().substring(0, 100),
                        author: authorEl ? authorEl.textContent.trim() : '',
                        likes: likesEl ? likesEl.textContent.trim() : '0'
                    });
                }
            });
            return items;
        }
        """
        try:
            dom_items = await page.evaluate(js_code)
            items = []
            for i in dom_items:
                title = i.get("title", "").strip()
                if not title or len(title) < 3:
                    continue
                items.append({
                    "rank": i.get("rank", 0),
                    "title": title,
                    "hot_value": str(i.get("likes", "0")),
                    "topic_url": "",
                    "snapshot_at": now,
                    "category": "video",
                    "_article": {
                        "title": title,
                        "author_name": i.get("author", ""),
                        "source_url": "",
                        "like_count": 0,
                    },
                })
            return items
        except Exception:
            return []
