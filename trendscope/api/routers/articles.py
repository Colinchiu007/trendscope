"""文章相关路由"""
from fastapi import APIRouter, Depends, Query

from trendscope.api.services.article_service import ArticleService
from trendscope.api.dependencies import get_article_service

router = APIRouter()


@router.get("")
async def list_articles(
    platforms: str = Query(None),
    time_range: str = Query("24h"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    svc: ArticleService = Depends(get_article_service),
):
    items, total = await svc.list_articles(platforms, time_range, page, page_size)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return {
        "code": 0,
        "data": {"items": items},
        "pagination": {
            "page": page, "page_size": page_size,
            "total": total, "total_pages": total_pages,
        },
    }


@router.get("/search")
async def search_articles(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    platforms: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    svc: ArticleService = Depends(get_article_service),
):
    items, total = await svc.search(q, platforms, page, page_size)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return {
        "code": 0,
        "data": {"items": items, "q": q},
        "pagination": {
            "page": page, "page_size": page_size,
            "total": total, "total_pages": total_pages,
        },
    }


@router.get("/{article_id}")
async def get_article(
    article_id: int,
    svc: ArticleService = Depends(get_article_service),
):
    data = await svc.get_article(article_id)
    if not data:
        return {"code": 1002, "message": "文章不存在"}
    return {"code": 0, "data": data}
