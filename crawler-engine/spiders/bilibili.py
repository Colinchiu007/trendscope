"""B站热门爬虫

数据来源: https://api.bilibili.com/x/web-interface/popular?pn=1&ps=50
返回 JSON:
  {"code": 0, "data": {"list": [{"bvid": "...", "title": "...",
     "owner": {"name": "...", "face": "..."}, "stat": {"view": ..., "danmaku": ..., "reply": ..., "favorite": ..., "like": ...}}]}}
"""
from datetime import datetime, timezone

from spiders.base import BaseSpider


class BilibiliSpider(BaseSpider):
    platform_code = "bilibili"
    platform_name = "B站"
    base_url = "https://api.bilibili.com/x/web-interface/popular"

    def fetch_trending_list(self) -> list[dict]:
        response = self._make_request(
            self.base_url,
            params={"pn": 1, "ps": 50},
        )
        data = response.json()
        now = datetime.now(timezone.utc)

        if data.get("code") != 0:
            return []

        items = []
        for idx, video in enumerate(data.get("data", {}).get("list", []), 1):
            title = video.get("title", "").strip()
            if not title:
                continue

            bvid = video.get("bvid", "")
            stat = video.get("stat", {})
            owner = video.get("owner", {})

            items.append({
                "rank": idx,
                "title": title,
                "hot_value": str(stat.get("view", 0)),
                "topic_url": f"https://www.bilibili.com/video/{bvid}",
                "snapshot_at": now.isoformat(),
                "category": "video",
                # 额外信息用于文章表
                "_article": {
                    "title": title,
                    "summary": video.get("desc", ""),
                    "images": [{"url": video.get("pic", "")}] if video.get("pic") else [],
                    "author_name": owner.get("name", ""),
                    "author_avatar": owner.get("face", ""),
                    "source_url": f"https://www.bilibili.com/video/{bvid}",
                    "read_count": stat.get("view", 0),
                    "like_count": stat.get("like", 0),
                    "comment_count": stat.get("reply", 0),
                    "share_count": stat.get("share", 0),
                    "publish_at": datetime.fromtimestamp(
                        video.get("pubdate", 0), tz=timezone.utc
                    ).isoformat() if video.get("pubdate") else None,
                },
            })

        return items[:50]
