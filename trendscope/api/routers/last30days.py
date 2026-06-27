"""last30days 多源搜索路由"""
from fastapi import APIRouter, Query

from trendscope.api.services.last30days_search import (
    DEFAULT_SOURCES,
    SOURCE_LABELS,
    search_multi_source,
)

router = APIRouter()


@router.get("/last30days")
async def search_last30days(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    sources: str = Query(None, description="逗号分隔的源列表，默认全部"),
    per_source: int = Query(12, ge=3, le=30, description="每源最大结果数"),
    total_max: int = Query(30, ge=1, le=100, description="总结果上限"),
):
    """跨源搜索（last30days 模式）。

    并行搜索 Reddit / Hacker News / GitHub / Polymarket，
    log10 归一化互动数据后按 RRF 融合排序返回。

    sources 示例: "reddit,github" 只搜 Reddit 和 GitHub。
    """
    source_list = sources.split(",") if sources else None
    result = await search_multi_source(
        query=q,
        sources=source_list,
        per_source=per_source,
        total_max=total_max,
    )
    return {
        "code": 0,
        "data": result,
    }


@router.get("/last30days/sources")
async def list_available_sources():
    """列出可用的搜索源信息。"""
    return {
        "code": 0,
        "data": {
            "default_sources": DEFAULT_SOURCES,
            "sources": {
                k: {"label": v, "name": k}
                for k, v in SOURCE_LABELS.items()
            },
        },
    }
