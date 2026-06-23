"""X(Twitter) 热门话题爬虫

数据来源: Twitter API v2
端点: https://api.twitter.com/2/tweets/search/recent?query=
需要 Bearer Token（从环境变量 TWITTER_BEARER_TOKEN 获取）

Twitter API v2 的 trends 端点需要 Pro tier ($100/月)，Basic tier 不支持。
当前使用 search/recent 端点作为替代方案，获取热门话题相关推文。
"""
import os
from datetime import datetime, timezone

from spiders.base import BaseSpider


class XTwitterSpider(BaseSpider):
    platform_code = "x_twitter"
    platform_name = "X"
    base_url = "https://api.twitter.com/2"

    def __init__(self):
        super().__init__()
        self.bearer_token = os.getenv("TWITTER_BEARER_TOKEN", "")

    def fetch_trending_list(self) -> list[dict]:
        now = datetime.now(timezone.utc)
        items = []

        if not self.bearer_token:
            return self._mock_data()

        # 使用 search/recent 获取热门推文
        # 注：trends 端点需要 Pro tier，Basic tier 仅支持 search
        url = f"{self.base_url}/tweets/search/recent"
        headers = {
            **self._build_headers(),
            "Authorization": f"Bearer {self.bearer_token}",
        }
        params = {
            "query": "trending OR hot OR viral -is:retweet lang:en",
            "max_results": 50,
            "tweet.fields": "public_metrics,created_at,author_id",
            "expansions": "author_id",
            "user.fields": "username,name,profile_image_url",
        }

        try:
            response = self._make_request(url, headers=headers, params=params)
            data = response.json()
        except Exception:
            return self._mock_data()

        users = {}
        for user in data.get("includes", {}).get("users", []):
            users[user["id"]] = user

        for idx, tweet in enumerate(data.get("data", []), 1):
            metrics = tweet.get("public_metrics", {})
            author = users.get(tweet.get("author_id", ""), {})

            items.append({
                "rank": idx,
                "title": tweet.get("text", "")[:120],
                "hot_value": str(metrics.get("like_count", 0)),
                "topic_url": f"https://x.com/{author.get('username', 'i')}/status/{tweet.get('id', '')}",
                "snapshot_at": now.isoformat(),
                "category": "general",
                "_article": {
                    "title": tweet.get("text", "")[:120],
                    "summary": tweet.get("text", ""),
                    "author_name": author.get("name", ""),
                    "author_avatar": author.get("profile_image_url", ""),
                    "source_url": f"https://x.com/{author.get('username', 'i')}/status/{tweet.get('id', '')}",
                    "like_count": metrics.get("like_count", 0),
                    "comment_count": metrics.get("reply_count", 0),
                    "share_count": metrics.get("retweet_count", 0),
                    "read_count": metrics.get("impression_count", 0),
                },
            })

        return items[:50]

    def _mock_data(self) -> list[dict]:
        return []
