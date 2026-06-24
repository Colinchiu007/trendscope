"""Trending service and serializers."""
from datetime import datetime

from loguru import logger

from trendscope.api.repositories.trending_repo import TrendingRepo
from trendscope.api.cache.trending_cache import TrendingCache


_FALLBACK_PLATFORMS = [
    {"id": 1, "code": "weibo", "name": "微博", "icon_url": "", "category": "social", "is_active": True},
    {"id": 2, "code": "baidu", "name": "百度", "icon_url": "", "category": "general", "is_active": True},
    {"id": 3, "code": "zhihu", "name": "知乎", "icon_url": "", "category": "social", "is_active": True},
    {"id": 4, "code": "bilibili", "name": "B站", "icon_url": "", "category": "entertainment", "is_active": True},
    {"id": 5, "code": "toutiao", "name": "今日头条", "icon_url": "", "category": "news", "is_active": True},
    {"id": 6, "code": "douyin", "name": "抖音", "icon_url": "", "category": "entertainment", "is_active": True},
    {"id": 7, "code": "xiaohongshu", "name": "小红书", "icon_url": "", "category": "lifestyle", "is_active": True},
    {"id": 8, "code": "youtube", "name": "YouTube", "icon_url": "", "category": "video", "is_active": True},
    {"id": 9, "code": "x_twitter", "name": "X/Twitter", "icon_url": "", "category": "social", "is_active": True},
    {"id": 10, "code": "weixin_article", "name": "微信公众号", "icon_url": "", "category": "news", "is_active": True},
    {"id": 11, "code": "shipinhao", "name": "视频号", "icon_url": "", "category": "video", "is_active": True},
    {"id": 12, "code": "tiktok", "name": "TikTok", "icon_url": "", "category": "entertainment", "is_active": True},
]


class TrendingService:

    def __init__(self, repo: TrendingRepo, cache: TrendingCache):
        self.repo = repo
        self.cache = cache

    async def get_aggregated(self, platforms: str = None, category: str = "all",
                             page: int = 1, page_size: int = 20) -> tuple[list[dict], int]:
        """Tier 1: Aggregated trending feed - compact fields, cross-platform."""
        try:
            if page == 1:
                cached = await self.cache.get_aggregated(category, page, page_size)
                if cached:
                    return cached.get("items", []), cached.get("total", 0)
            platform_ids = None
            if platforms:
                codes = [c.strip() for c in platforms.split(",") if c.strip()]
                if codes:
                    platform_ids = []
                    for code in codes:
                        p = await self.repo.get_platform_by_code(code)
                        if p:
                            platform_ids.append(p.id)
            items, total = await self.repo.get_aggregated_trending(
                platform_ids, category, page, page_size
            )
            result_items = [_serialize_topic_compact(item) for item in items]
            if page == 1:
                await self.cache.set_aggregated(category, page, page_size, {
                    "items": result_items, "total": total
                })
            return result_items, total
        except Exception as e:
            logger.warning(f"[Service] get_aggregated failed: {e}")
            return [], 0

    async def get_platform_summary(self) -> list[dict]:
        """Tier 1: Platform list with top-3 preview for each platform."""
        try:
            platforms = await self.repo.get_platforms()
            result = []
            for p in platforms:
                items, _ = await self.repo.get_platform_trending(p.code, page=1, page_size=3)
                top3 = [_serialize_topic_compact(item) for item in items]
                latest = items[0].snapshot_at.isoformat() if items else None
                result.append({
                    "code": p.code, "name": p.name,
                    "icon_url": p.icon_url or "", "category": p.category,
                    "top3": top3, "snapshot_at": latest,
                })
            return result
        except Exception as e:
            logger.warning(f"[Service] get_platform_summary failed: {e}")
            return []

    async def get_platform_trending(self, platform: str, page: int = 1,
                                    page_size: int = 50) -> tuple[list[dict], int]:
        """Tier 2: Single platform full trending list."""
        try:
            if page == 1:
                cached = await self.cache.get_platform_trending(platform, page, page_size)
                if cached:
                    return cached.get("items", []), cached.get("total", 0)
            items, total = await self.repo.get_platform_trending(platform, page, page_size)
            result_items = [_serialize_topic(item) for item in items]
            if page == 1:
                await self.cache.set_platform_trending(platform, page, page_size, {
                    "items": result_items, "total": total
                })
            return result_items, total
        except Exception as e:
            logger.warning(f"[Service] get_platform_trending({platform}) failed: {e}")
            return [], 0

    async def get_history(self, topic_id: int, time_range: str = "24h") -> dict:
        """Tier 3: Topic heat trend history."""
        try:
            items = await self.repo.get_trending_history(topic_id, time_range)
            if not items:
                return {}
            history = [{
                "timestamp": item.snapshot_at.isoformat(),
                "hot_value": float(item.hot_value_norm or 0),
                "rank": item.rank,
            } for item in items]
            return {
                "topic_id": topic_id,
                "title": items[0].title,
                "platform": items[0].platform.code if items[0].platform else "",
                "history": history,
            }
        except Exception as e:
            logger.warning(f"[Service] get_history failed: {e}")
            return {}

    async def get_platforms(self) -> list[dict]:
        """Get platform list (cache first, fallback to hardcoded list)."""
        cached = await self.cache.get_platforms()
        if cached:
            return cached
        try:
            platforms = await self.repo.get_platforms()
            result = [{
                "id": p.id, "code": p.code, "name": p.name,
                "icon_url": p.icon_url or "", "category": p.category,
                "is_active": p.is_active,
            } for p in platforms]
            await self.cache.set_platforms(result)
            return result
        except Exception as e:
            logger.warning(f"[Service] get_platforms failed: {e}, using fallback")
            return _FALLBACK_PLATFORMS


def _serialize_topic_compact(item) -> dict:
    """Compact serialization - tier 1 aggregated feed."""
    return {
        "id": item.id,
        "platform_code": item.platform.code if item.platform else "",
        "platform_name": item.platform.name if item.platform else "",
        "rank": item.rank,
        "title": item.title,
        "hot_value": item.hot_value,
        "hot_value_norm": float(item.hot_value_norm or 0),
        "topic_url": item.topic_url or "",
        "category": item.category or "general",
        "snapshot_at": item.snapshot_at.isoformat() if item.snapshot_at else "",
    }


def _serialize_topic(item) -> dict:
    """Full serialization - tier 2 single platform detail."""
    return {
        "id": item.id,
        "platform": {
            "code": item.platform.code if item.platform else "",
            "name": item.platform.name if item.platform else "",
            "icon_url": item.platform.icon_url if item.platform else "",
        },
        "rank": item.rank,
        "title": item.title,
        "hot_value": item.hot_value,
        "hot_value_norm": float(item.hot_value_norm or 0),
        "topic_url": item.topic_url or "",
        "category": item.category or "general",
        "snapshot_at": item.snapshot_at.isoformat() if item.snapshot_at else "",
    }
