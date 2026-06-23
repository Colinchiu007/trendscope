"""YouTube 热门视频爬虫

数据来源: YouTube Data API v3
端点: https://www.googleapis.com/youtube/v3/videos
参数: part=snippet,statistics&chart=mostPopular&regionCode=CN&maxResults=50
需要 API Key（从环境变量 YOUTUBE_API_KEY 获取）
"""
import os
from datetime import datetime, timezone

from spiders.base import BaseSpider


class YouTubeSpider(BaseSpider):
    platform_code = "youtube"
    platform_name = "YouTube"
    base_url = "https://www.googleapis.com/youtube/v3/videos"

    def __init__(self):
        super().__init__()
        self.api_key = os.getenv("YOUTUBE_API_KEY", "")

    def fetch_trending_list(self) -> list[dict]:
        now = datetime.now(timezone.utc)
        items = []

        if not self.api_key:
            return self._mock_data()

        params = {
            "part": "snippet,statistics",
            "chart": "mostPopular",
            "regionCode": "CN",
            "maxResults": 50,
            "key": self.api_key,
        }

        try:
            response = self._make_request(self.base_url, params=params)
            data = response.json()
        except Exception:
            return self._mock_data()

        for idx, video in enumerate(data.get("items", []), 1):
            snippet = video.get("snippet", {})
            stats = video.get("statistics", {})
            video_id = video.get("id", "")

            if not video_id:
                continue

            items.append({
                "rank": idx,
                "title": snippet.get("title", ""),
                "hot_value": str(stats.get("viewCount", 0)),
                "topic_url": f"https://www.youtube.com/watch?v={video_id}",
                "snapshot_at": now.isoformat(),
                "category": "video",
                "_article": {
                    "title": snippet.get("title", ""),
                    "summary": snippet.get("description", ""),
                    "images": [{"url": snippet.get("thumbnails", {}).get("high", {}).get("url", "")}]
                    if snippet.get("thumbnails") else [],
                    "author_name": snippet.get("channelTitle", ""),
                    "source_url": f"https://www.youtube.com/watch?v={video_id}",
                    "read_count": int(stats.get("viewCount", 0)),
                    "like_count": int(stats.get("likeCount", 0)),
                    "comment_count": int(stats.get("commentCount", 0)),
                    "publish_at": snippet.get("publishedAt", ""),
                },
            })

        return items[:50]

    def _mock_data(self) -> list[dict]:
        """无 API Key 时返回示例数据（开发调试用）"""
        return []
