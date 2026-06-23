"""第三方 API 路由 (X-API-Key 认证)"""
import hashlib

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from trendscope.api.dependencies import get_db, get_trending_service, get_article_service
from trendscope.api.repositories.apikey_repo import ApiKeyRepo
from trendscope.api.services.trending_service import TrendingService
from trendscope.api.services.article_service import ArticleService

router = APIRouter()


async def verify_api_key(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_api_key: str = Header(None, alias="X-API-Key"),
) -> dict:
    """验证 API Key 并记录用量"""
    if not x_api_key:
        raise HTTPException(status_code=401, detail={"code": 1003, "message": "缺少 API Key"})

    repo = ApiKeyRepo(db)
    key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
    payload = await repo.validate(key_hash)

    if not payload:
        raise HTTPException(status_code=401, detail={"code": 1003, "message": "API Key 无效或已过期"})

    # 简单限流检查（TODO: 分布式 Redis 滑动窗口）
    # 记录用量
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
