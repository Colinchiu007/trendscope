"""小红书热榜爬虫 - Playwright sync_api 方案

数据来源: https://www.xiaohongshu.com/explore
使用 Playwright sync_api 避免 asyncio 嵌套问题。
"""
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
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh', 'en']});
                window.chrome = {runtime: {}};
            """)

            page = context.new_page()

            api_responses = []
            def capture(response):
                if "api/sns/web/v1" in response.url or "homefeed" in response.url:
                    try:
                        body = response.json()
                        api_responses.append({"url": response.url, "data": body})
                    except Exception:
                        pass

            page.on("response", capture)

            try:
                page.goto(self.base_url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(5000)

                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(2000)

                items = self._parse_api_responses(api_responses)
                if not items:
                    items = self._parse_dom(page)
            finally:
                browser.close()

        return items[:50]

    def _parse_api_responses(self, responses: list[dict]) -> list[dict]:
        now = datetime.now(timezone.utc).isoformat()
        items = []

        for resp in responses:
            data = resp.get("data", resp)
            if not isinstance(data, dict):
                if isinstance(data, list):
                    note_list = data
                else:
                    continue
            else:
                note_list = (
                    data.get("items", [])
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

    def _parse_dom(self, page) -> list[dict]:
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
            dom_items = page.evaluate(js_code)
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
