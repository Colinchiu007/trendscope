"""快手热榜爬虫 - API 拦截提取

数据来源: https://www.kuaishou.com/hot
快手热榜页面已重定向为短视频信息流 (new-reco)。
通过 Playwright 加载页面后拦截 /rest/v/feed/hot API 响应的数据。
"""
import re
from datetime import datetime, timezone

from spiders.base import BaseSpider


class KuaishouSpider(BaseSpider):
    platform_code = "kuaishou"
    platform_name = "快手"
    base_url = "https://www.kuaishou.com/hot"
    use_playwright = True

    DESKTOP_UA = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
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
                user_agent=self.DESKTOP_UA,
                locale="zh-CN",
            )
            page = context.new_page()

            try:
                api_data = {}

                def on_response(response):
                    url = response.url
                    if "/rest/v/feed/hot" in url:
                        try:
                            api_data["hot"] = response.json()
                        except Exception:
                            pass

                page.on("response", on_response)

                page.goto(self.base_url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(8000)

                if api_data.get("hot"):
                    items = self._extract_from_api(api_data["hot"])
            except Exception:
                pass
            finally:
                browser.close()

        return items[:50]

    def _extract_from_api(self, data: dict) -> list[dict]:
        now = datetime.now(timezone.utc).isoformat()
        items = []

        try:
            feeds = data.get("feeds", [])
            if not feeds:
                return items

            seen_titles = set()
            for i, feed in enumerate(feeds):
                if not isinstance(feed, dict):
                    continue

                photo = feed.get("photo", {})

                caption = photo.get("caption", "") or feed.get("caption", "") or ""
                title = _clean_caption(caption)

                if not title or len(title) < 2 or title in seen_titles:
                    continue
                seen_titles.add(title)

                tags = [
                    t.get("name", "")
                    for t in feed.get("tags", [])
                    if isinstance(t, dict)
                ]
                tag_text = " ".join(tags)

                hot_value = photo.get("viewCount", photo.get("likeCount", 0))
                if isinstance(hot_value, bool):
                    hot_value = 0

                items.append({
                    "rank": i + 1,
                    "title": title,
                    "hot_value": str(int(hot_value)),
                    "hot_value_norm": float(hot_value),
                    "topic_url": "",
                    "snapshot_at": now,
                    "category": _classify(title + " " + tag_text),
                })
        except Exception:
            pass

        return items


def _clean_caption(caption: str) -> str:
    text = re.sub(r"@\S+(?:\([^)]*\))?", "", caption)
    text = re.sub(r"#\S+", "", text)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = text.strip("，。,．.!！？?；;、")
    return text.strip()


def _classify(title: str) -> str:
    keywords = {
        "entertainment": ["明星", "综艺", "电影", "音乐", "游戏", "搞笑", "段子", "网红",
                          "短剧", "拍摄", "舞蹈", "唱歌", "才艺", "表演"],
        "social": ["社会", "民生", "政策", "教育", "热点", "新闻", "现场", "感人",
                   "正能量", "致敬", "英雄", "暖心", "互助"],
        "tech": ["手机", "数码", "科技", "汽车", "互联网", "AI", "智能"],
        "sports": ["体育", "NBA", "CBA", "足球", "冠军", "比赛", "健身", "运动",
                   "篮球", "冬奥"],
        "life": ["美食", "旅游", "健身", "穿搭", "美妆", "宠物", "乡村", "三农",
                 "农村", "养殖", "种植", "手工", "创意", "生活"],
    }
    for cat, words in keywords.items():
        for w in words:
            if w in title:
                return cat
    return "general"
