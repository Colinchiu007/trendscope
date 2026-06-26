"""文章数据访问层"""
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func, and_, or_, desc, text
from sqlalchemy.ext.asyncio import AsyncSession

from trendscope.api.models.database import HotArticle, Platform


class ArticleRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_articles(
        self, platform_ids: list[int] = None, time_range: str = "24h",
        status: str = "approved", page: int = 1, page_size: int = 20
    ) -> tuple[list[HotArticle], int]:
        """获取热门文章列表"""
        # 时间范围
        hours = {"1h": 1, "6h": 6, "24h": 24, "7d": 168}.get(time_range, 24)
        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        base = (
            select(HotArticle)
            .where(
                and_(
                    HotArticle.snapshot_at >= since,
                    HotArticle.status == status,
                )
            )
        )

        if platform_ids:
            base = base.where(HotArticle.platform_id.in_(platform_ids))

        # 计数
        count_stmt = select(func.count()).select_from(base.subquery())
        result = await self.db.execute(count_stmt)
        total = result.scalar() or 0

        # 分页
        stmt = (
            base.order_by(desc(HotArticle.read_count))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    async def get_article(self, article_id: int) -> HotArticle | None:
        """获取文章详情"""
        stmt = select(HotArticle).where(HotArticle.id == article_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def search_articles(
        self, q: str, platform_ids: list[int] = None,
        page: int = 1, page_size: int = 20
    ) -> tuple[list[HotArticle], int]:
        """全文搜索（PostgreSQL 内置）"""
        # 使用 PostgreSQL ts_query 全文检索
        ts_query = func.plainto_tsquery("simple", q)

        base = (
            select(HotArticle)
            .where(
                or_(
                    func.to_tsvector("simple", HotArticle.title).match(ts_query),
                    func.to_tsvector("simple", HotArticle.content_text).match(ts_query),
                )
            )
        )

        if platform_ids:
            base = base.where(HotArticle.platform_id.in_(platform_ids))

        base = base.where(HotArticle.status == "approved")

        # 计数
        count_stmt = select(func.count()).select_from(base.subquery())
        result = await self.db.execute(count_stmt)
        total = result.scalar() or 0

        # 按相关度 + 热度排序
        stmt = (
            base.order_by(desc(HotArticle.read_count))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    async def upsert_articles(self, articles: list[dict]) -> int:
        """批量 UPSERT 文章数据"""
        count = 0
        for item in articles:
            # 按 source_url 去重
            stmt = (
                select(HotArticle)
                .where(HotArticle.source_url == item.get("source_url"))
                .limit(1)
            )
            result = await self.db.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                # 更新互动数据
                existing.read_count = item.get("read_count", existing.read_count)
                existing.like_count = item.get("like_count", existing.like_count)
                existing.comment_count = item.get("comment_count", existing.comment_count)
                existing.snapshot_at = item.get("snapshot_at", existing.snapshot_at)
            else:
                article = HotArticle(**item)
                self.db.add(article)
                count += 1

        await self.db.flush()
        return count

    async def update_status(self, article_id: int, status: str) -> bool:
        """更新文章审核状态"""
        article = await self.get_article(article_id)
        if not article:
            return False
        article.status = status
        await self.db.flush()
        return True
