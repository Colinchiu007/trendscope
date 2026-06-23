"""微博热搜爬虫

数据来源: https://weibo.com/ajax/side/hotSearch
接口返回 JSON 格式，包含 realtime 热搜、hotband 热bands 等分类。

返回格式:
    {"data": {"realtime": [{"word": "...", "rank": 1, "num": 123456, "raw_hot": 123456}]}}
"""
from datetime import datetime, timezone

from spiders.base import BaseSpider


class WeiboSpider(BaseSpider):
    platform_code = "weibo"
    platform_name = "微博"
    base_url = "https://weibo.com/ajax/side/hotSearch"

    def fetch_trending_list(self) -> list[dict]:
        response = self._make_request(self.base_url)
        data = response.json()
        now = datetime.now(timezone.utc)

        items = []
        realtime = data.get("data", {}).get("realtime", [])

        for item in realtime[:50]:
            rank = item.get("rank", 0)
            if rank == 0:
                continue

            word = item.get("word", "").strip()
            if not word:
                continue

            raw_hot = item.get("raw_hot", item.get("num", 0))
            if isinstance(raw_hot, (int, float)):
                hot_value = f"{raw_hot}"
            else:
                hot_value = str(raw_hot)

            items.append({
                "rank": rank,
                "title": word,
                "hot_value": hot_value,
                "topic_url": f"https://s.weibo.com/weibo?q=%23{word}%23",
                "snapshot_at": now.isoformat(),
                "category": _classify(word),
            })

        return items


def _classify(title: str) -> str:
    """简单关键词分类"""
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
