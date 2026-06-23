"""FastAPI 依赖注入配置"""
from functools import lru_cache
from typing import AsyncGenerator

import redis.asyncio as aioredis
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from trendscope.api.config import settings
from trendscope.api.models.session import async_session
from trendscope.api.cache.trending_cache import TrendingCache
from trendscope.api.repositories.trending_repo import TrendingRepo
from trendscope.api.repositories.article_repo import ArticleRepo
from trendscope.api.services.trending_service import TrendingService
from trendscope.api.services.article_service import ArticleService
from trendscope.api.services.user_service import UserService


# ─── 数据库会话 ───

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话（FastAPI Depends）"""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ─── Redis ───

@lru_cache()
def _get_redis_pool() -> aioredis.ConnectionPool:
    return aioredis.ConnectionPool(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        max_connections=20,
        decode_responses=True,
    )


async def get_redis() -> aioredis.Redis:
    pool = _get_redis_pool()
    return aioredis.Redis(connection_pool=pool)


# ─── 热榜依赖链 ───

def get_trending_service(
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> TrendingService:
    cache = TrendingCache(redis)
    repo = TrendingRepo(db)
    return TrendingService(repo, cache)


# ─── 文章依赖链 ───

def get_article_service(
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> ArticleService:
    cache = TrendingCache(redis)
    repo = ArticleRepo(db)
    return ArticleService(repo, cache)


# ─── 用户依赖链 ───

def get_user_service(
    db: AsyncSession = Depends(get_db),
) -> UserService:
    return UserService(db)
