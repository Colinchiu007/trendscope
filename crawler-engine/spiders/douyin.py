"""抖音热榜爬虫 - Playwright 方案

数据来源: https://www.douyin.com/hot
页面为 SPA 渲染，需要通过 Playwright 等待数据加载后提取。
"""
import asyncio
import json
from datetime import datetime, timezone

from spiders.base import BaseSpider


class DouyinSpider(BaseSpider):
    platform_code = "douyin"
    platform_name = "抖音"
    base_url = "https://www.douyin.com/hot"
    use_playwright = True

    def fetch_trending_list(self) -> list[dict]:
        """Playwright 渲染方案获取抖音热榜"""
        return asyncio.run(self._fetch_with_playwright())

    async def _fetch_with_playwright(self) -> list[dict]:
        from playwright.async_api import async_playwright
        from anti_anti_spider.fingerprint import FingerprintManager

        items = []
        async with async_playwright() as p:
            fp = FingerprintManager.get_playwright_stealth_args()
            viewport = FingerprintManager.get_random_viewport()

            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox"] + fp,
            )
            context = await browser.new_context(
                viewport=viewport,
                user_agent=self.ua.random,
                locale="zh-CN",
            )
            page = await context.new_page()

            # 拦截网络请求，捕获热榜 XHR 数据
            captured_data = []
            async def intercept_response(response):
                if "hot-board" in response.url or "trending" in response.url:
                    try:
                        body = await response.json()
                        captured_data.append(body)
                    except Exception:
                        pass

            page.on("response", intercept_response)

            try:
                await page.goto(self.base_url, wait_until="networkidle", timeout=30000)
                # 等待榜单渲染
                try:
                    await page.wait_for_selector(
                        '[data-e2e="hot-list"] li, .hot-list-item, .trending-item',
                        timeout=15000,
                    )
                except Exception:
                    pass
                await asyncio.sleep(3)

                # 尝试从捕获的 XHR 数据中提取
                rankings = self._extract_from_captured(captured_data)
                if rankings:
                    items = rankings
                else:
                    # 降级：从 DOM 提取
                    items = await self._extract_from_dom(page)
            finally:
                await browser.close()

        return items

    def _extract_from_captured(self, data: list) -> list[dict]:
        """从捕获的 XHR JSON 中提取"""
        now = datetime.now(timezone.utc).isoformat()
        items = []

        for chunk in data:
            word_list = None
            if isinstance(chunk, dict):
                word_list = chunk.get("data", {}).get("word_list") or chunk.get("word_list") or chunk.get("data", {}).get("list")
            if not word_list:
                continue

            for idx, item in enumerate(word_list):
                if isinstance(item, dict):
                    title = item.get("word", "") or item.get("title", "")
                    if not title:
                        continue
                    items.append({
                        "rank": item.get("position", idx + 1),
                        "title": title,
                        "hot_value": str(item.get("hot_value", item.get("score", 0))),
                        "topic_url": f"https://www.douyin.com/search/{title}",
                        "snapshot_at": now,
                        "category": "general",
                    })

            if items:
                break

        return items[:50]

    async def _extract_from_dom(self, page) -> list[dict]:
        """从 DOM 提取（降级方案）"""
        now = datetime.now(timezone.utc).isoformat()
        items = []

        js_code = """
        () => {
            const items = [];
            const listItems = document.querySelectorAll('li[data-e2e="hot-list-item"], .hot-item');
            listItems.forEach((li, idx) => {
                const titleEl = li.querySelector('[data-e2e="hot-list-item-title"], .title, .word');
                const hotEl = li.querySelector('[data-e2e="hot-list-item-hot-score"], .hot-score, .num');
                if (titleEl) {
                    items.push({
                        rank: idx + 1,
                        title: titleEl.textContent.trim(),
                        hot_value: hotEl ? hotEl.textContent.trim() : '0'
                    });
                }
            });
            return items;
        }
        """
        try:
            dom_items = await page.evaluate(js_code)
            for item in dom_items:
                items.append({
                    "rank": item.get("rank", 0),
                    "title": item.get("title", "").strip(),
                    "hot_value": str(item.get("hot_value", "0")),
                    "topic_url": f"https://www.douyin.com/search/{item.get('title', '')}",
                    "snapshot_at": now,
                    "category": "general",
                })
        except Exception:
            pass

        return items[:50]
