"""Redis 缓存层 - 热榜数据缓存"""
import json
from datetime import timedelta

import redis.asyncio as aioredis
from loguru import logger

# 缓存 Key 前缀
KEY_PREFIX = "trendscope"

# TTL 配置
TTL_TRENDING_AGG = 60        # 聚合热榜 60s
TTL_TRENDING_PLAT = 120      # 单平台热榜 120s
TTL_ARTICLE_DETAIL = 600     # 文章详情 10min
TTL_PLATFORM_LIST = 3600     # 平台列表 1h
TTL_SEARCH_RESULT = 120      # 搜索结果 120s


class TrendingCache:
    """热榜数据缓存"""

    def __init__(self, redis_client: aioredis.Redis = None):
        self.rdb = redis_client

    async def _get(self, key: str) -> dict | list | None:
        if not self.rdb:
            return None
        try:
            data = await self.rdb.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.warning(f"[Cache] 读取失败: {key}, {e}")
        return None

    async def _set(self, key: str, data: any, ttl: int) -> None:
        if not self.rdb:
            return
        try:
            await self.rdb.setex(key, ttl, json.dumps(data, default=str, ensure_ascii=False))
        except Exception as e:
            logger.warning(f"[Cache] 写入失败: {key}, {e}")

    # ─── 聚合热榜 ───

    def _agg_key(self, category: str, page: int, page_size: int) -> str:
        return f"{KEY_PREFIX}:trending:agg:{category}:{page}:{page_size}"

    async def get_aggregated(self, category: str, page: int, page_size: int) -> dict | None:
        return await self._get(self._agg_key(category, page, page_size))

    async def set_aggregated(self, category: str, page: int, page_size: int, data: dict) -> None:
        await self._set(self._agg_key(category, page, page_size), data, TTL_TRENDING_AGG)

    # ─── 单平台热榜 ───

    def _plat_key(self, platform: str, page: int, page_size: int) -> str:
        return f"{KEY_PREFIX}:trending:plat:{platform}:{page}:{page_size}"

    async def get_platform_trending(self, platform: str, page: int, page_size: int) -> dict | None:
        return await self._get(self._plat_key(platform, page, page_size))

    async def set_platform_trending(self, platform: str, page: int, page_size: int, data: dict) -> None:
        await self._set(self._plat_key(platform, page, page_size), data, TTL_TRENDING_PLAT)

    # ─── 文章 ───

    def _article_key(self, article_id: int) -> str:
        return f"{KEY_PREFIX}:article:{article_id}"

    async def get_article(self, article_id: int) -> dict | None:
        return await self._get(self._article_key(article_id))

    async def set_article(self, article_id: int, data: dict) -> None:
        await self._set(self._article_key(article_id), data, TTL_ARTICLE_DETAIL)

    # ─── 平台列表 ───

    def _platforms_key(self) -> str:
        return f"{KEY_PREFIX}:platforms"

    async def get_platforms(self) -> list | None:
        return await self._get(self._platforms_key())

    async def set_platforms(self, data: list) -> None:
        await self._set(self._platforms_key(), data, TTL_PLATFORM_LIST)

    # ─── 失效 ───

    async def invalidate(self, platform: str = None) -> int:
        """失效热榜缓存（采集入库后调用）"""
        if not self.rdb:
            return 0

        pattern = f"{KEY_PREFIX}:trending:*"
        if platform:
            pattern = f"{KEY_PREFIX}:trending:plat:{platform}:*"

        count = 0
        try:
            cursor = 0
            while True:
                cursor, keys = await self.rdb.scan(cursor, match=pattern, count=100)
                if keys:
                    await self.rdb.delete(*keys)
                    count += len(keys)
                if cursor == 0:
                    break
        except Exception as e:
            logger.warning(f"[Cache] 失效失败: {pattern}, {e}")

        if count > 0:
            logger.debug(f"[Cache] 失效 {count} 个 key: {pattern}")
        return count
