"""Trending service and serializers."""
from datetime import datetime

from loguru import logger

from trendscope.api.repositories.trending_repo import TrendingRepo
from trendscope.api.cache.trending_cache import TrendingCache


_FALLBACK_PLATFORMS = [
    {"id": 6, "code": "douyin", "name": "\u6296\u97f3", "icon_url": "", "category": "entertainment", "is_active": True},
    {"id": 7, "code": "xiaohongshu", "name": "\u5c0f\u7ea2\u4e66", "icon_url": "", "category": "lifestyle", "is_active": True},
    {"id": 11, "code": "kuaishou", "name": "\u5feb\u624b", "icon_url": "", "category": "entertainment", "is_active": True},
    {"id": 4, "code": "bilibili", "name": "B\u7ad9", "icon_url": "", "category": "entertainment", "is_active": True},
    {"id": 1, "code": "weibo", "name": "\u5fae\u535a", "icon_url": "", "category": "social", "is_active": True},
    {"id": 10, "code": "weixin_article", "name": "\u516c\u4f17\u53f7", "icon_url": "", "category": "news", "is_active": True},
    {"id": 2, "code": "baidu", "name": "\u767e\u5ea6", "icon_url": "", "category": "general", "is_active": True},
    {"id": 13, "code": "netease", "name": "\u7f51\u6613\u65b0\u95fb", "icon_url": "", "category": "news", "is_active": True},
    {"id": 3, "code": "zhihu", "name": "\u77e5\u4e4e", "icon_url": "", "category": "social", "is_active": True},
    {"id": 8, "code": "youtube", "name": "YouTube", "icon_url": "", "category": "video", "is_active": True},
    {"id": 12, "code": "tiktok", "name": "TikTok", "icon_url": "", "category": "entertainment", "is_active": True},
    {"id": 9, "code": "x_twitter", "name": "X/Twitter", "icon_url": "", "category": "social", "is_active": True},
]


_PLATFORM_DISPLAY_ORDER = [
    "douyin", "xiaohongshu", "kuaishou", "bilibili",
    "weibo", "weixin_article", "baidu", "netease",
    "zhihu", "youtube", "tiktok", "x_twitter",
]


class TrendingService:

    def __init__(self, repo: TrendingRepo, cache: TrendingCache):
        self.repo = repo
        self.cache = cache

    @staticmethod
    def _sort_platforms(platforms: list[dict]) -> list[dict]:
        """\u6309\u5e73\u53f0\u987a\u5e8f\u6392\u5e8f"""
        order = {code: i for i, code in enumerate(_PLATFORM_DISPLAY_ORDER)}
        return sorted(platforms, key=lambda p: order.get(p["code"], 999))

    async def get_aggregated(self, platforms: str = None, category: str = "all",
                             page: int = 1, page_size: int = 20) -> tuple[list[dict], int]:
        try:
            if page == 1:
                cached = await self.cache.get_aggregated(category, page, page_size)
                if cached:
                    return cached.get("items", []), cached.get("total", 0)
            platform_ids = None
            if platforms:
                platform_ids = [int(p) for p in platforms.split(",") if p.strip().isdigit()]
            items, total = await self.repo.get_aggregated_trending(
                platform_ids=platform_ids, category=category,
                page=page, page_size=page_size,
            )
            result = [_serialize_topic(item) for item in items]
            if page == 1:
                await self.cache.set_aggregated(category, page, page_size, {"items": result, "total": total})
            return result, total
        except Exception as e:
            logger.warning(f"[Service] get_aggregated failed: {e}")
            return [], 0

    async def get_platform_trending(self, platform: str, page: int = 1, page_size: int = 50) -> tuple[list[dict], int]:
        try:
            if page == 1:
                cached = await self.cache.get_platform_trending(platform, page, page_size)
                if cached:
                    return cached.get("items", []), cached.get("total", 0)
            items, total = await self.repo.get_platform_trending(platform, page, page_size)
            result_items = [_serialize_topic(item) for item in items]
            if page == 1:
                await self.cache.set_platform_trending(platform, page, page_size, {"items": result_items, "total": total})
            return result_items, total
        except Exception as e:
            logger.warning(f"[Service] get_platform_trending({platform}) failed: {e}")
            return [], 0

    async def get_history(self, topic_id: int, time_range: str = "24h") -> dict:
        try:
            items = await self.repo.get_trending_history(topic_id, time_range)
            if not items:
                return {}
            history = [{
                "snapshot_at": item.snapshot_at.isoformat() if item.snapshot_at else "",
                "rank": item.rank,
                "hot_value": item.hot_value,
                "hot_value_norm": float(item.hot_value_norm or 0),
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
            result = self._sort_platforms(result)
            await self.cache.set_platforms(result)
            return result
        except Exception as e:
            logger.warning(f"[Service] get_platforms failed: {e}, using fallback")
            return _FALLBACK_PLATFORMS


def _serialize_topic_compact(item) -> dict:
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
