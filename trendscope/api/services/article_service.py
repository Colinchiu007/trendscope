"""文章业务逻辑"""
from loguru import logger

from trendscope.api.repositories.article_repo import ArticleRepo
from trendscope.api.cache.trending_cache import TrendingCache


class ArticleService:
    def __init__(self, repo: ArticleRepo, cache: TrendingCache):
        self.repo = repo
        self.cache = cache

    async def list_articles(self, platforms: str = None, time_range: str = "24h",
                            page: int = 1, page_size: int = 20) -> tuple[list[dict], int]:
        """热门文章列表"""
        platform_ids = await _resolve_platforms(self.repo, platforms)
        items, total = await self.repo.list_articles(
            platform_ids, time_range, page=page, page_size=page_size
        )
        result_items = [_serialize_article(item) for item in items]
        return result_items, total

    async def get_article(self, article_id: int) -> dict | None:
        """文章详情（缓存优先）"""
        cached = await self.cache.get_article(article_id)
        if cached:
            return cached

        article = await self.repo.get_article(article_id)
        if not article:
            return None

        result = _serialize_article(article, include_content=True)
        await self.cache.set_article(article_id, result)
        return result

    async def search(self, q: str, platforms: str = None,
                     page: int = 1, page_size: int = 20) -> tuple[list[dict], int]:
        """全文搜索"""
        platform_ids = await _resolve_platforms(self.repo, platforms)
        items, total = await self.repo.search_articles(
            q, platform_ids, page=page, page_size=page_size
        )
        result_items = [_serialize_article(item) for item in items]
        return result_items, total


async def _resolve_platforms(repo, platforms: str = None) -> list[int] | None:
    """解析平台代码为 ID 列表"""
    if not platforms:
        return None
    from sqlalchemy import select
    from trendscope.api.models.database import Platform

    ids = []
    for code in platforms.split(","):
        code = code.strip()
        if not code:
            continue
        result = await repo.db.execute(select(Platform.id).where(Platform.code == code))
        pid = result.scalar()
        if pid:
            ids.append(pid)
    return ids or None


def _serialize_article(item, include_content: bool = False) -> dict:
    result = {
        "id": item.id,
        "platform": {
            "code": item.platform.code if item.platform else "",
            "name": item.platform.name if item.platform else "",
            "icon_url": item.platform.icon_url if item.platform else "",
        },
        "title": item.title,
        "summary": item.summary or "",
        "images": item.images or [],
        "video_url": item.video_url or "",
        "author_name": item.author_name or "",
        "author_avatar": item.author_avatar or "",
        "source_url": item.source_url,
        "read_count": item.read_count or 0,
        "like_count": item.like_count or 0,
        "comment_count": item.comment_count or 0,
        "share_count": item.share_count or 0,
        "publish_at": item.publish_at.isoformat() if item.publish_at else "",
        "snapshot_at": item.snapshot_at.isoformat() if item.snapshot_at else "",
    }
    if include_content:
        result["content_text"] = item.content_text or ""
    return result
