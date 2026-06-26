"""Trending routes."""
from fastapi import APIRouter, Depends, Query
from trendscope.api.services.trending_service import TrendingService
from trendscope.api.dependencies import get_trending_service

router = APIRouter()


@router.get("/summary")
async def get_platform_summary(svc: TrendingService = Depends(get_trending_service)):
    data = await svc.get_platform_summary()
    return {"code": 0, "data": {"platforms": data}}


@router.get("/platforms")
async def get_platforms(svc: TrendingService = Depends(get_trending_service)):
    platforms = await svc.get_platforms()
    return {"code": 0, "data": {"platforms": platforms}}


@router.get("/history")
async def get_trending_history(
    topic_id: int = Query(..., gt=0),
    range: str = Query("24h"),
    svc: TrendingService = Depends(get_trending_service),
):
    data = await svc.get_history(topic_id, range)
    return {"code": 0, "data": data}


@router.get("")
async def get_aggregated_trending(
    platforms: str = Query(None),
    category: str = Query("all"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    limit: int = Query(None, ge=1, le=200, description="limit response items"),
    svc: TrendingService = Depends(get_trending_service),
):
    items, total = await svc.get_aggregated(platforms, category, page, page_size)
    if limit:
        items = items[:limit]
        total = min(total, limit)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return {
        "code": 0, "message": "success",
        "data": {"items": items},
        "pagination": {"page": page, "page_size": page_size,
                       "total": total, "total_pages": total_pages},
    }


@router.get("/{platform}")
async def get_platform_trending(
    platform: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    limit: int = Query(None, ge=1, le=200, description="limit response items"),
    svc: TrendingService = Depends(get_trending_service),
):
    items, total = await svc.get_platform_trending(platform, page, page_size)
    if limit:
        items = items[:limit]
        total = min(total, limit)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return {
        "code": 0, "message": "success",
        "data": {"items": items},
        "pagination": {"page": page, "page_size": page_size,
                       "total": total, "total_pages": total_pages},
    }
