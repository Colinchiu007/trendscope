"""第三方 API 路由 (X-API-Key 认证)"""
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from trendscope.api.dependencies import get_db, get_redis, get_trending_service, get_article_service
from trendscope.api.middleware.auth import verify_api_key as middleware_verify_api_key
from trendscope.api.middleware.ratelimit import RedisTokenBucket
from trendscope.api.repositories.apikey_repo import ApiKeyRepo
from trendscope.api.services.trending_service import TrendingService
from trendscope.api.services.article_service import ArticleService

router = APIRouter()


async def verify_api_key(
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
    x_api_key: str = Header(None, alias="X-API-Key"),
) -> dict:
    """验证 API Key 并记录用量（委托 middleware.auth.verify_api_key 做数据库校验）"""
    payload = await middleware_verify_api_key(x_api_key, db)
    if not payload:
        raise HTTPException(status_code=401, detail={"code": 1003, "message": "API Key 无效或已过期"})

    # 分布式限流（Redis 滑动窗口，Redis 不可用时降级到本地令牌桶）
    rate_limit = payload.get("rate_limit", 60)
    limiter = RedisTokenBucket(redis, prefix="trendscope:partner:ratelimit")
    allowed = await limiter.consume(payload.get("key_prefix", "unknown"), rate=rate_limit)
    if not allowed:
        raise HTTPException(status_code=429, detail={"code": 1005, "message": "API 请求超限，请稍后再试"})

    # 记录用量
    repo = ApiKeyRepo(db)
    await repo.log_usage(
        api_key_id=payload["key_id"],
        endpoint=request.url.path,
        method=request.method,
        status_code=200,
        ip=request.client.host if request.client else "",
    )
    return payload


# ─── 热榜接口 ───

@router.get("/trending")
async def partner_trending(
    key: dict = Depends(verify_api_key),
    svc: TrendingService = Depends(get_trending_service),
    platforms: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    items, total = await svc.get_aggregated(platforms, "all", page, page_size)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return {
        "code": 0,
        "data": {"items": items},
        "pagination": {"page": page, "page_size": page_size, "total": total, "total_pages": total_pages},
        "key_prefix": key["key_prefix"],
    }


@router.get("/trending/{platform}")
async def partner_platform_trending(
    platform: str,
    key: dict = Depends(verify_api_key),
    svc: TrendingService = Depends(get_trending_service),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    items, total = await svc.get_platform_trending(platform, page, page_size)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return {
        "code": 0,
        "data": {"items": items},
        "pagination": {"page": page, "page_size": page_size, "total": total, "total_pages": total_pages},
        "key_prefix": key["key_prefix"],
    }


# ─── 文章接口 ───

@router.get("/articles")
async def partner_articles(
    key: dict = Depends(verify_api_key),
    svc: ArticleService = Depends(get_article_service),
    platforms: str = Query(None),
    time_range: str = Query("24h"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    items, total = await svc.list_articles(platforms, time_range, page, page_size)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return {
        "code": 0,
        "data": {"items": items},
        "pagination": {"page": page, "page_size": page_size, "total": total, "total_pages": total_pages},
        "key_prefix": key["key_prefix"],
    }


@router.get("/articles/{article_id}")
async def partner_article(
    article_id: int,
    key: dict = Depends(verify_api_key),
    svc: ArticleService = Depends(get_article_service),
):
    data = await svc.get_article(article_id)
    if not data:
        return {"code": 1002, "message": "文章不存在"}
    return {"code": 0, "data": data, "key_prefix": key["key_prefix"]}


# ─── 用量查询 ───

@router.get("/usage")
async def partner_usage(
    key: dict = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
):
    repo = ApiKeyRepo(db)
    stats = await repo.get_usage_stats(key["key_id"])
    return {
        "code": 0,
        "data": {
            **stats,
            "rate_limit_rpm": key["rate_limit"],
            "key_prefix": key["key_prefix"],
        },
    }
