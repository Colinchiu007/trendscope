"""小红书热榜爬虫 - Playwright 方案

数据来源: https://www.xiaohongshu.com/explore
小红书有强反爬机制（X-s/X-t 签名参数），优先使用 Playwright 渲染方案。

备用 API（签名破解难度高）:
  POST https://edith.xiaohongshu.com/api/sns/web/v1/search/notes
  Headers: X-s, X-t (需要逆向 App 获取签名算法)
"""
import asyncio
import json
import time
from datetime import datetime, timezone

from spiders.base import BaseSpider


class XiaohongshuSpider(BaseSpider):
    platform_code = "xiaohongshu"
    platform_name = "小红书"
    base_url = "https://www.xiaohongshu.com/explore"
    use_playwright = True

    def fetch_trending_list(self) -> list[dict]:
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

            # 注入 stealth 脚本（消除 webdriver 痕迹）
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh', 'en']});
                window.chrome = {runtime: {}};
            """)

            page = await context.new_page()

            # 捕获 XHR 响应
            api_responses = []
            async def capture(response):
                if "api/sns/web/v1" in response.url or "homefeed" in response.url:
                    try:
                        body = await response.json()
                        api_responses.append({"url": response.url, "data": body})
                    except Exception:
                        pass

            page.on("response", capture)

            try:
                await page.goto(self.base_url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(5)

                # 模拟滚动触发懒加载
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(2)

                # 尝试从 API 响应提取
                items = self._parse_api_responses(api_responses)
                if not items:
                    items = await self._parse_dom(page)

            finally:
                await browser.close()

        return items[:50]

    def _parse_api_responses(self, responses: list[dict]) -> list[dict]:
        """从捕获的 API 响应提取数据"""
        now = datetime.now(timezone.utc).isoformat()
        items = []

        for resp in responses:
            data = resp.get("data", resp)
            if not isinstance(data, dict):
                continue

            # 小红书 API 常见结构: data.items[] 或 data.notes[]
            note_list = (
                data.get("data", {}).get("items", [])
                or data.get("items", [])
                or data.get("data", {}).get("notes", [])
                or data.get("notes", [])
            )
            if not note_list:
                continue

            for idx, note in enumerate(note_list, 1):
                if not isinstance(note, dict):
                    continue
                note_card = note.get("note_card", note)
                display = note_card.get("display_title", note_card.get("title", ""))
                if not display:
                    continue

                user = note_card.get("user", {})
                interact = note_card.get("interact_info", {})

                items.append({
                    "rank": idx,
                    "title": display,
                    "hot_value": str(interact.get("liked_count", interact.get("share_count", 0))),
                    "topic_url": f"https://www.xiaohongshu.com/explore/{note_card.get('note_id', note.get('id', ''))}",
                    "snapshot_at": now,
                    "category": _classify_xhs(display),
                    "_article": {
                        "title": display,
                        "summary": note_card.get("desc", ""),
                        "images": [{"url": note_card.get("cover", {}).get("url", "")}] if note_card.get("cover") else [],
                        "author_name": user.get("nickname", ""),
                        "author_avatar": user.get("avatar", ""),
                        "source_url": f"https://www.xiaohongshu.com/explore/{note_card.get('note_id', note.get('id', ''))}",
                        "like_count": interact.get("liked_count", 0),
                        "comment_count": interact.get("comment_count", 0),
                        "share_count": interact.get("share_count", 0),
                    },
                })

            if items:
                break

        return items

    async def _parse_dom(self, page) -> list[dict]:
        """从 DOM 提取（降级方案）"""
        now = datetime.now(timezone.utc).isoformat()
        items = []

        js_code = """
        () => {
            const items = [];
            const cards = document.querySelectorAll('.note-item, .feeds-page .note-item, [class*="note"]');
            cards.forEach((card, idx) => {
                const titleEl = card.querySelector('.title, .note-title, [class*="title"]');
                const authorEl = card.querySelector('.author .name, .nickname, [class*="name"]');
                const likesEl = card.querySelector('.like-wrapper .count, .like-count, [class*="like"] span');
                if (titleEl) {
                    items.push({
                        rank: idx + 1,
                        title: titleEl.textContent.trim(),
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
            for item in dom_items:
                items.append({
                    "rank": item.get("rank", 0),
                    "title": item.get("title", "").strip(),
                    "hot_value": str(item.get("likes", "0")),
                    "topic_url": "",
                    "snapshot_at": now,
                    "category": _classify_xhs(item.get("title", "")),
                })
        except Exception:
            pass

        return items


def _classify_xhs(title: str) -> str:
    keywords = {
        "tech": ["数码", "科技", "AI", "手机", "电脑"],
        "entertainment": ["美食", "旅游", "穿搭", "美妆", "护肤", "健身"],
        "social": ["教育", "职场", "情感", "亲子"],
    }
    for cat, words in keywords.items():
        for w in words:
            if w in title:
                return cat
    return "lifestyle"
