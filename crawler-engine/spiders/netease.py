"""网易新闻热榜爬虫 - Playwright DOM 提取方案

数据来源: https://news.163.com/
从网易新闻首页的"热点排行"栏目提取热榜数据（SSR 渲染，10条）。
补充从首页新闻列表提取更多热门新闻标题。
"""
from datetime import datetime, timezone

from spiders.base import BaseSpider


class NeteaseSpider(BaseSpider):
    platform_code = "netease"
    platform_name = "网易新闻"
    base_url = "https://news.163.com/"
    use_playwright = True

    def fetch_trending_list(self) -> list[dict]:
        return self._fetch_sync()

    DESKTOP_UA = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    )

    def _fetch_sync(self) -> list[dict]:
        from playwright.sync_api import sync_playwright
        from anti_anti_spider.fingerprint import FingerprintManager

        items = []
        with sync_playwright() as p:
            launch_kwargs = FingerprintManager.get_playwright_launch_kwargs()
            browser = p.chromium.launch(**launch_kwargs)
            context = browser.new_context(
                viewport=FingerprintManager.get_random_viewport(),
                user_agent=self.DESKTOP_UA,
                locale="zh-CN",
            )
            page = context.new_page()

            try:
                page.goto(self.base_url, wait_until="load", timeout=30000)
                page.wait_for_timeout(3000)

                items = self._extract_from_dom(page)
            finally:
                browser.close()

        return items[:50]

    def _extract_from_dom(self, page) -> list[dict]:
        """从 DOM 提取热点排行 + 新闻列表"""
        now = datetime.now(timezone.utc).isoformat()
        items = []

        js_code = """
        () => {
            const items = [];
            const seen = new Set();

            // 1. 提取"热点排行"列表（有热度值）
            const rankList = document.querySelector(".mod_hot_rank ul");
            if (rankList) {
                const liItems = rankList.querySelectorAll("li");
                liItems.forEach(li => {
                    const em = li.querySelector("em");
                    const a = li.querySelector("a");
                    const span = li.querySelector("span");
                    if (a && a.textContent.trim()) {
                        const title = a.textContent.trim();
                        if (!seen.has(title)) {
                            seen.add(title);
                            items.push({
                                rank: em ? parseInt(em.textContent) || (items.length + 1) : (items.length + 1),
                                title: title,
                                hot_value: span ? span.textContent.trim() : "0",
                                url: a.href || ""
                            });
                        }
                    }
                });
            }

            // 2. 从首页新闻列表补充更多热门新闻标题
            const newsLinks = document.querySelectorAll(
                "a[href*=\'163.com\'], .news_title a, .news-item a, " +
                "[class*=\'title\'] a, .ndi_main a, .mod_article a"
            );
            newsLinks.forEach(a => {
                const title = a.textContent.trim();
                if (title && title.length > 8 && !seen.has(title)) {
                    seen.add(title);
                    const parent = a.closest("li, div, .ndi_main");
                    const hotEl = parent ? parent.querySelector("em, .hot, .num, [class*=click]") : null;
                    items.push({
                        rank: items.length + 1,
                        title: title,
                        hot_value: hotEl ? hotEl.textContent.trim() : "0",
                        url: a.href || ""
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
                if not title or len(title) < 5:
                    continue
                items.append({
                    "rank": item.get("rank", 0),
                    "title": title,
                    "hot_value": item.get("hot_value", "0"),
                    "topic_url": item.get("url", ""),
                    "snapshot_at": now,
                    "category": _classify_163(title),
                })
        except Exception:
            pass

        return items


def _classify_163(title: str) -> str:
    keywords = {
        "tech": ["AI", "人工智能", "芯片", "手机", "数码", "科技", "苹果", "华为", "特斯拉", "互联网", "软件"],
        "entertainment": ["电影", "综艺", "明星", "演唱会", "音乐", "游戏", "视频", "娱乐"],
        "social": ["政策", "民生", "房价", "教育", "高考", "考研", "社会", "调查"],
        "finance": ["股市", "A股", "基金", "经济", "央行", "房地产", "房价", "财经"],
        "sports": ["NBA", "足球", "世界杯", "冠军", "比赛", "奥运"],
        "international": ["美国", "日本", "英国", "俄", "乌克兰", "巴以", "国际", "外交"],
    }
    for cat, words in keywords.items():
        for w in words:
            if w.lower() in title.lower():
                return cat
    return "general"
