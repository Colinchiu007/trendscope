"""百度热搜爬虫

数据来源: https://top.baidu.com/board?tab=realtime
页面通过 XHR 请求获取数据:
  https://top.baidu.com/board?tab=realtime&sa=topic&ajax=1&page_size=50

返回 JSON 格式:
  {"data": {"cards": [{"content": [{"word": "标题", "hotScore": 123456, "url": "..."}]}]}}
"""
from datetime import datetime, timezone
from typing import Optional

import httpx
from spiders.base import BaseSpider


class BaiduSpider(BaseSpider):
    platform_code = "baidu"
    platform_name = "百度"
    base_url = "https://top.baidu.com/board"
    api_url = "https://top.baidu.com/board?tab=realtime&sa=topic&ajax=1&page_size=50"

    def __init__(self):
        super().__init__()
        self._api_client: Optional[httpx.Client] = None

    @property
    def api_client(self) -> httpx.Client:
        if self._api_client is None:
            self._api_client = httpx.Client(
                timeout=self.request_timeout,
                headers={
                    **self._build_headers(),
                    "Accept": "application/json",
                    "Referer": "https://top.baidu.com/board?tab=realtime",
                    "X-Requested-With": "XMLHttpRequest",
                },
                follow_redirects=True,
            )
        return self._api_client

    def fetch_trending_list(self) -> list[dict]:
        response = self.api_client.get(self.api_url)
        data = response.json()
        now = datetime.now(timezone.utc)

        items = []
        cards = data.get("data", {}).get("cards", [])

        for card in cards:
            for idx, item in enumerate(card.get("content", []), 1):
                word = item.get("word", "").strip()
                if not word:
                    continue

                hot_score = item.get("hotScore", 0)
                items.append({
                    "rank": item.get("index", idx),
                    "title": word,
                    "hot_value": str(hot_score),
                    "topic_url": item.get("url", ""),
                    "snapshot_at": now.isoformat(),
                    "category": "general",
                })

        return items[:50]

    def close(self):
        if self._api_client:
            self._api_client.close()
            self._api_client = None
        super().close()
