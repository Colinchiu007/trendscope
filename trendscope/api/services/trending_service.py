"""热榜业务逻辑"""
from datetime import datetime

from loguru import logger

from trendscope.api.repositories.trending_repo import TrendingRepo
from trendscope.api.cache.trending_cache import TrendingCache


# 12 个平台的硬编码降级列表（数据库不可用时返回）
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
        """获取聚合热榜（缓存优先，数据库不可用时返回空列表）"""
        try:
            # 1. 尝试缓存
            if page == 1:
                cached = await self.cache.get_aggregated(category, page, page_size)
                if cached:
                    logger.debug("[Service] 聚合热榜命中缓存")
                    return cached.get("items", []), cached.get("total", 0)

            # 2. 解析平台过滤
            platform_ids = None
            if platforms:
                codes = [c.strip() for c in platforms.split(",") if c.strip()]
                if codes:
                    platform_ids = []
                    for code in codes:
                        p = await self.repo.get_platform_by_code(code)
                        if p:
                            platform_ids.append(p.id)

            # 3. 查询数据库
            items, total = await self.repo.get_aggregated_trending(
                platform_ids, category, page, page_size
            )

            # 4. 序列化
            result_items = [_serialize_topic(item) for item in items]

            # 5. 写缓存
            if page == 1:
                await self.cache.set_aggregated(category, page, page_size, {
                    "items": result_items, "total": total
                })

            return result_items, total
        except Exception as e:
            logger.warning(f"[Service] 聚合热榜查询失败: {e}，返回空列表")
            return [], 0

    async def get_platform_trending(self, platform: str, page: int = 1,
                                    page_size: int = 50) -> tuple[list[dict], int]:
        """获取单平台热榜"""
        try:
            # 1. 缓存
            if page == 1:
                cached = await self.cache.get_platform_trending(platform, page, page_size)
                if cached:
                    return cached.get("items", []), cached.get("total", 0)

            # 2. 查询
            items, total = await self.repo.get_platform_trending(platform, page, page_size)
            result_items = [_serialize_topic(item) for item in items]

            # 3. 缓存
            if page == 1:
                await self.cache.set_platform_trending(platform, page, page_size, {
                    "items": result_items, "total": total
                })

            return result_items, total
        except Exception as e:
            logger.warning(f"[Service] 单平台热榜查询失败({platform}): {e}，返回空列表")
            return [], 0

    async def get_history(self, topic_id: int, time_range: str = "24h") -> dict:
        """获取热度趋势"""
        try:
            items = await self.repo.get_trending_history(topic_id, time_range)
            if not items:
                return {}

            history = [
                {
                    "timestamp": item.snapshot_at.isoformat(),
                    "hot_value": float(item.hot_value_norm or 0),
                    "rank": item.rank,
                }
                for item in items
            ]

            return {
                "topic_id": topic_id,
                "title": items[0].title,
                "platform": items[0].platform.code if items[0].platform else "",
                "history": history,
            }
        except Exception as e:
            logger.warning(f"[Service] 历史趋势查询失败: {e}")
            return {}

    async def get_platforms(self) -> list[dict]:
        """获取平台列表（缓存优先，数据库不可用时返回硬编码降级列表）"""
        cached = await self.cache.get_platforms()
        if cached:
            return cached

        try:
            platforms = await self.repo.get_platforms()
            result = [
                {
                    "id": p.id,
                    "code": p.code,
                    "name": p.name,
                    "icon_url": p.icon_url or "",
                    "category": p.category,
                    "is_active": p.is_active,
                }
                for p in platforms
            ]

            await self.cache.set_platforms(result)
            return result
        except Exception as e:
            logger.warning(f"[Service] 获取平台列表失败（DB不可用？）: {e}，返回降级列表")
            return _FALLBACK_PLATFORMS


def _serialize_topic(item) -> dict:
    """序列化 TrendingTopic 为 JSON"""
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
