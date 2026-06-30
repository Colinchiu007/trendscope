"""FastAPI 依赖注入配置"""
from functools import lru_cache

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from trendscope.api.config import settings
from trendscope.api.models.session import get_db
from trendscope.api.cache.trending_cache import TrendingCache
from trendscope.api.repositories.trending_repo import TrendingRepo
from trendscope.api.repositories.article_repo import ArticleRepo
from trendscope.api.services.trending_service import TrendingService
from trendscope.api.services.article_service import ArticleService
from trendscope.api.services.user_service import UserService


# ─── Redis（可选 — 不可用时传 None，cache 层自动降级）───

try:
    import redis.asyncio as aioredis

    @lru_cache()
    def _get_redis_pool() -> aioredis.ConnectionPool | None:
        try:
            return aioredis.ConnectionPool(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                max_connections=20,
                decode_responses=True,
            )
        except Exception:
            return None

    async def get_redis() -> aioredis.Redis | None:
        pool = _get_redis_pool()
        if pool is None:
            return None
        return aioredis.Redis(connection_pool=pool)

except ImportError:
    aioredis = None

    async def get_redis() -> None:
        return None


# ─── 热榜依赖链 ───

def get_trending_service(
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> TrendingService:
    cache = TrendingCache(redis)
    repo = TrendingRepo(db)
    return TrendingService(repo, cache)


# ─── 文章依赖链 ───

def get_article_service(
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> ArticleService:
    cache = TrendingCache(redis)
    repo = ArticleRepo(db)
    return ArticleService(repo, cache)


# ─── 用户依赖链 ───

def get_user_service(
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> UserService:
    from trendscope.api.cache.sms_cache import SmsCache
    sms_cache = SmsCache(redis_client=redis)
    return UserService(db, sms_cache=sms_cache)
