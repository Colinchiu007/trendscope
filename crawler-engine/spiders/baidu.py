"""Baidu trending spider."""
import json
import re
from datetime import datetime, timezone
from spiders.base import BaseSpider


class BaiduSpider(BaseSpider):
    platform_code = "baidu"
    platform_name = "百度"
    base_url = "https://top.baidu.com/board?tab=realtime"

    def fetch_trending_list(self) -> list[dict]:
        self._http_client = None
        response = self._make_request(self.base_url)
        html = response.text
        now = datetime.now(timezone.utc)
        items = []
        for m in re.finditer(r"<!--s-data:(.*?)-->", html, re.DOTALL):
            try:
                raw = json.loads(m.group(1))
                cards = raw.get("data", {}).get("cards", [])
                for card in cards:
                    cl = card.get("content", [])
                    if cl and isinstance(cl[0], dict) and "content" in cl[0]:
                        cl = cl[0]["content"]
                    for idx, item in enumerate(cl, 1):
                        title = item.get("word", "") or item.get("query", "") or ""
                        if not title.strip():
                            continue
                        hs = item.get("hotScore", 0)
                        q = item.get("query", title)
                        items.append({"rank": idx, "title": title.strip(), "hot_value": str(hs), "topic_url": f"https://www.baidu.com/s?wd={q}", "snapshot_at": now.isoformat(), "category": "general"})
            except Exception:
                continue
        return items[:50]

    def close(self):
        super().close()
