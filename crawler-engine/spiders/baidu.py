"""Baidu trending spider. Parses <!--s-data:{}--> from SSR HTML."""
import json
import re
from datetime import datetime, timezone

from spiders.base import BaseSpider


class BaiduSpider(BaseSpider):
    platform_code = "baidu"
    platform_name = "百度"
    base_url = "https://top.baidu.com/board?tab=realtime"

    def fetch_trending_list(self) -> list[dict]:
        response = self._make_request(self.base_url)
        html = response.text
        now = datetime.now(timezone.utc)
        items = []
        for match in re.finditer(r"<!--s-data:(.*?)-->", html, re.DOTALL):
            try:
                raw_data = json.loads(match.group(1))
                cards = raw_data.get("data", {}).get("cards", []) or raw_data.get("cards", [])
                for card in cards:
                    content_list = card.get("content", [])
                    if content_list and isinstance(content_list[0], dict) and "content" in content_list[0]:
                        content_list = content_list[0]["content"]
                    for idx, item in enumerate(content_list, 1):
                        title = item.get("word", "") or item.get("query", "") or ""
                        if not title.strip():
                            continue
                        hot_score = item.get("hotScore", 0)
                        query = item.get("query", title)
                        items.append({
                            "rank": idx,
                            "title": title.strip(),
                            "hot_value": str(hot_score),
                            "topic_url": f"https://www.baidu.com/s?wd={query}",
                            "snapshot_at": now.isoformat(),
                            "category": "general",
                        })
            except (json.JSONDecodeError, KeyError, TypeError):
                continue
        return items[:50]

    def close(self):
        super().close()
