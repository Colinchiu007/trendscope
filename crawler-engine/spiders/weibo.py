"""微博热搜爬虫 - Playwright sync_api 方案

数据来源: https://s.weibo.com/top/summary?cate=realtimehot
使用 Playwright sync_api 避免 asyncio 嵌套问题。
"""
from datetime import datetime, timezone

from spiders.base import BaseSpider


class WeiboSpider(BaseSpider):
    platform_code = "weibo"
    platform_name = "微博"
    base_url = "https://s.weibo.com/top/summary?cate=realtimehot"
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
            )
            page = context.new_page()

            try:
                page.goto(self.base_url, wait_until="load", timeout=30000)
                page.wait_for_timeout(2000)
                items = self._extract_from_dom(page)
            except Exception:
                pass
            finally:
                browser.close()

        return items[:50]

    def _extract_from_dom(self, page) -> list[dict]:
        now = datetime.now(timezone.utc).isoformat()
        items = []

        js_code = """
        () => {
            const items = [];
            const rows = document.querySelectorAll('#pl_top_realtimehot table tbody tr');
            rows.forEach((row) => {
                const rankEl = row.querySelector('.td-01');
                const linkEl = row.querySelector('.td-02 a');
                const hotEl = row.querySelector('.td-02 span');
                if (rankEl && linkEl) {
                    let rank = 0;
                    const rankText = rankEl.textContent.trim();
                    if (rankText) {
                        rank = parseInt(rankText) || 0;
                    }
                    const title = linkEl.textContent.trim();
                    if (!title) return;
                    let hot_value = hotEl ? hotEl.textContent.trim() : '';
                    hot_value = hot_value.replace(/\\s+/g, '');
                    const href = linkEl.getAttribute('href') || '';
                    const url = href.startsWith('http') ? href : 'https://s.weibo.com' + href;
                    items.push({
                        rank: rank,
                        title: title,
                        hot_value: hot_value || '0',
                        url: url
                    });
                }
            });
            return items;
        }
        """
        try:
            dom_items = page.evaluate(js_code)
            for item in dom_items:
                title = item.get("title", "").strip()
                if not title:
                    continue
                items.append({
                    "rank": item.get("rank", 0),
                    "title": title,
                    "hot_value": item.get("hot_value", "0"),
                    "topic_url": item.get("url", ""),
                    "snapshot_at": now,
                    "category": _classify(title),
                })
        except Exception:
            pass

        return items


def _classify(title: str) -> str:
    keywords = {
        "tech": ["AI", "人工智能", "芯片", "5G", "科技", "苹果", "华为", "特斯拉"],
        "entertainment": ["电影", "综艺", "明星", "演唱会", "音乐", "游戏"],
        "social": ["政策", "民生", "房价", "教育", "高考", "考研"],
        "finance": ["股市", "A股", "基金", "经济", "央行"],
        "sports": ["NBA", "足球", "世界杯", "冠军", "比赛"],
    }
    for cat, words in keywords.items():
        for w in words:
            if w.lower() in title.lower():
                return cat
    return "general"