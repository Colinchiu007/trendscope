"""知乎热榜爬虫

数据来源: https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=50
返回 JSON:
  {"data": [{"target": {"id": ..., "title": "...", "excerpt": "...",
     "detail_text": "1000 万热度", "metrics_area": {"text": "..."}}}]}
"""
from datetime import datetime, timezone

from spiders.base import BaseSpider


class ZhihuSpider(BaseSpider):
    platform_code = "zhihu"
    platform_name = "知乎"
    base_url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total"

    def fetch_trending_list(self) -> list[dict]:
        response = self._make_request(
            self.base_url,
            params={"limit": 50, "desktop": "true"},
        )
        data = response.json()
        now = datetime.now(timezone.utc)

        items = []
        for idx, item in enumerate(data.get("data", []), 1):
            target = item.get("target", {})
            title = target.get("title", "").strip()
            if not title:
                continue

            # 热度值
            detail_text = target.get("detail_text", "")
            metrics = target.get("metrics_area", {})
            hot_value = detail_text or metrics.get("text", "")

            items.append({
                "rank": idx,
                "title": title,
                "hot_value": hot_value,
                "topic_url": f"https://www.zhihu.com/question/{target.get('id', '')}",
                "snapshot_at": now.isoformat(),
                "category": "general",
            })

        return items[:50]
