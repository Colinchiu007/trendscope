"""今日头条热榜爬虫 - Playwright sync_api 方案

数据来源: https://www.toutiao.com/hot-event/hot-board/
使用 Playwright sync_api 避免 asyncio 嵌套问题。
"""
import json
import re
from datetime import datetime, timezone

from spiders.base import BaseSpider


class ToutiaoSpider(BaseSpider):
    platform_code = "toutiao"
    platform_name = "今日头条"
    base_url = "https://www.toutiao.com/hot-event/hot-board/"
    use_playwright = True

    def fetch_trending_list(self) -> list[dict]:
        return self._fetch_sync()

    def _fetch_sync(self) -> list[dict]:
        from playwright.sync_api import sync_playwright
        from anti_anti_spider.fingerprint import FingerprintManager

        items = []
        with sync_playwright() as p:
            launch_kwargs = FingerprintManager.get_playwright_launch_kwargs()
            browser = p.chromium.launch(**launch_kwargs)
            context = browser.new_context(
                viewport=FingerprintManager.get_random_viewport(),
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                locale="zh-CN",
            )
            page = context.new_page()

            try:
                page.goto(self.base_url, wait_until="load", timeout=30000)
                page.wait_for_timeout(3000)

                html = page.content()
                items = self._parse_render_data(html)
                if not items:
                    items = self._extract_from_dom(page)
            except Exception:
                pass
            finally:
                browser.close()

        return items[:50]

    def _parse_render_data(self, html: str) -> list[dict]:
        match = re.search(
            r'<script[^>]*id="RENDER_DATA"[^>]*>(.*?)</script>',
            html, re.DOTALL
        )
        if not match:
            return []

        now = datetime.now(timezone.utc).isoformat()
        items = []

        try:
            data_str = match.group(1)
            decoded = json.loads(json.loads(f'"{data_str}"'))
            hot_board = self._extract_hot_board(decoded)
            for idx, item in enumerate(hot_board[:50], 1):
                title = item.get("Title", item.get("title", "")).strip()
                if not title:
                    continue
                items.append({
                    "rank": idx,
                    "title": title,
                    "hot_value": str(item.get("HotValue", item.get("hot_value", 0))),
                    "topic_url": item.get("Url", item.get("url", "")),
                    "snapshot_at": now,
                    "category": item.get("Tag", item.get("tag", "general")),
                })
        except (json.JSONDecodeError, KeyError, Exception):
            pass

        return items

    def _extract_hot_board(self, data) -> list[dict]:
        if isinstance(data, list):
            for item in data:
                result = self._extract_hot_board(item)
                if result:
                    return result
        elif isinstance(data, dict):
            if "hotBoard" in data:
                return data["hotBoard"]
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    result = self._extract_hot_board(value)
                    if result:
                        return result
        return []

    def _extract_from_dom(self, page) -> list[dict]:
        now = datetime.now(timezone.utc).isoformat()

        js_code = """
        () => {
            const items = [];
            const cards = document.querySelectorAll(
                '.hot-list-item, .trending-item, [class*="hot"] a, .feed-card'
            );
            cards.forEach((card, idx) => {
                const titleEl = card.querySelector('a, .title, [class*="title"]');
                const hotEl = card.querySelector('.hot-value, .score, [class*="hot"], [class*="num"]');
                if (titleEl) {
                    items.push({
                        rank: idx + 1,
                        title: titleEl.textContent.trim(),
                        hot_value: hotEl ? hotEl.textContent.trim() : '0',
                        url: titleEl.href || ''
                    });
                }
            });
            return items;
        }
        """
        try:
            dom_items = page.evaluate(js_code)
            items = []
            for item in dom_items:
                title = item.get("title", "").strip()
                if not title or len(title) < 2:
                    continue
                items.append({
                    "rank": item.get("rank", 0),
                    "title": title,
                    "hot_value": str(item.get("hot_value", "0")),
                    "topic_url": item.get("url", ""),
                    "snapshot_at": now,
                    "category": "general",
                })
            return items
        except Exception:
            return []
