"""抖音热榜爬虫 - Playwright sync_api 方案

数据来源: https://www.douyin.com/hot
使用 page.evaluate(fetch) 在浏览器上下文中获取 API 数据，
避免 response.json() 在 sync_api 中无法读取的问题。
"""
import json
from datetime import datetime, timezone

from spiders.base import BaseSpider


class DouyinSpider(BaseSpider):
    platform_code = "douyin"
    platform_name = "抖音"
    base_url = "https://www.douyin.com/hot"
    use_playwright = True

    # 抖音热榜 API 路径
    _API_PATH = (
        "/aweme/v1/web/hot/search/list/"
        "?device_platform=webapp&aid=6383"
        "&channel=channel_pc_web&detail_list=1"
        "&source=6&pc_client_type=1&version_code=170400"
        "&version_name=17.4.0&cookie_enabled=true"
        "&screen_width=1920&screen_height=1080"
        "&browser_language=zh-CN&browser_platform=Win32"
        "&browser_name=Chrome&browser_version=120.0.0.0"
        "&browser_online=true"
    )

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
                user_agent=self.ua.random,
                locale="zh-CN",
            )
            page = context.new_page()

            try:
                page.goto(self.base_url, wait_until="load", timeout=30000)
                page.wait_for_timeout(5000)

                # 在浏览器上下文中 fetch API 数据（此时页面存活，能正常读取）
                api_data = page.evaluate("""async (apiPath) => {
                    try {
                        const r = await fetch(apiPath);
                        return await r.json();
                    } catch(e) {
                        return {error: e.message};
                    }
                }""", self._API_PATH)

                rankings = self._extract_from_api(api_data)
                if rankings:
                    items = rankings
                else:
                    items = self._extract_from_dom(page)
            finally:
                browser.close()

        return items

    def _extract_from_api(self, api_data: dict) -> list[dict]:
        """从 API JSON 响应提取热榜条目"""
        if not isinstance(api_data, dict) or "error" in api_data:
            return []

        now = datetime.now(timezone.utc).isoformat()
        items = []

        chunk_data = api_data.get("data", {})
        if not isinstance(chunk_data, dict):
            return []

        word_list = chunk_data.get("word_list", [])
        if not word_list:
            return []

        for item in word_list:
            if not isinstance(item, dict):
                continue
            title = item.get("word", "") or item.get("title", "")
            if not title:
                continue

            items.append({
                "rank": item.get("position", item.get("rank", 0)),
                "title": title,
                "hot_value": str(item.get("hot_value", item.get("score", 0))),
                "topic_url": f"https://www.douyin.com/search/{title}",
                "snapshot_at": now,
                "category": "general",
            })

        return items[:50]

    def _extract_from_dom(self, page) -> list[dict]:
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
            dom_items = page.evaluate(js_code)
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