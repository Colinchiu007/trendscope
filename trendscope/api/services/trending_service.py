"""Trending service and serializers."""
from datetime import datetime

from loguru import logger

from trendscope.api.repositories.trending_repo import TrendingRepo
from trendscope.api.cache.trending_cache import TrendingCache


_FALLBACK_PLATFORMS = [
    {"id": 6, "code": "douyin", "name": "抖音", "icon_url": "", "category": "entertainment", "is_active": True},
    {"id": 7, "code": "xiaohongshu", "name": "小红书", "icon_url": "", "category": "lifestyle", "is_active": True},
    {"id": 11, "code": "kuaishou", "name": "快手", "icon_url": "", "category": "entertainment", "is_active": True},
    {"id": 4, "code": "bilibili", "name": "B站", "icon_url": "", "category": "entertainment", "is_active": True},
    {"id": 1, "code": "weibo", "name": "微博", "icon_url": "", "category": "social", "is_active": True},
    {"id": 10, "code": "weixin_article", "name": "公众号", "icon_url": "", "category": "news", "is_active": True},
    {"id": 2, "code": "baidu", "name": "百度", "icon_url": "", "category": "general", "is_active": True},
    {"id": 13, "code": "netease", "name": "网易新闻", "icon_url": "", "category": "news", "is_active": True},
    {"id": 3, "code": "zhihu", "name": "知乎", "icon_url": "", "category": "social", "is_active": True},
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
        """按平台顺序排序"""
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

            # 计算 rank_change
            rank_changes = await self._compute_rank_changes(items)

            result_items = [_serialize_topic(item, rank_change=rank_changes.get(item.id)) for item in items]

            if page == 1:
                await self.cache.set_platform_trending(platform, page, page_size, {"items": result_items, "total": total})
            return result_items, total
        except Exception as e:
            logger.warning(f"[Service] get_platform_trending({platform}) failed: {e}")
            return [], 0

    async def _compute_rank_changes(self, items: list) -> dict[int, int | None]:
        """计算当前话题列表中每个话题的排名变化。

        返回 {topic_id: rank_change}:
        - 正数 = 上升（名次减小）
        - 负数 = 下降（名次增大）
        - 0    = 持平
        - None = 新进（上次快照无此话题）
        """
        if not items:
            return {}

        changes: dict[int, int | None] = {}
        # 按 platform_id 分组计算
        from collections import defaultdict
        by_platform = defaultdict(list)
        for item in items:
            by_platform[item.platform_id].append(item)

        for pid, platform_items in by_platform.items():
            # 取这批话题共同的 snapshot_at（应都相同）
            snapshot_time = platform_items[0].snapshot_at
            prev_ranks = await self.repo.get_previous_snapshot_ranks(pid, snapshot_time)

            for item in platform_items:
                if item.title in prev_ranks:
                    changes[item.id] = prev_ranks[item.title] - item.rank
                else:
                    changes[item.id] = None  # 新进

        return changes

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


def _serialize_topic_compact(item, rank_change: int | None = None) -> dict:
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
        "rank_change": rank_change,
    }


def _serialize_topic(item, rank_change: int | None = None) -> dict:
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
        "rank_change": rank_change,
    }


    async def get_related_topics(self, topic_id: int, limit: int = 10) -> list:
        """获取关联话题推荐（基于同平台/同分类的热门话题）"""
        return await self.repo.get_related_topics(topic_id, limit)
