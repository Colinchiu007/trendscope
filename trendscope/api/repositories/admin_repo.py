"""管理后台数据访问"""
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, func, and_, desc, text
from sqlalchemy.ext.asyncio import AsyncSession

from trendscope.api.models.database import (
    TrendingTopic, HotArticle, User, CrawlLog, Platform, ApiUsageLog
)


class AdminRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_dashboard_stats(self) -> dict:
        """获取仪表盘统计数据"""
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)

        # 活跃平台数
        result = await self.db.execute(
            select(func.count()).where(Platform.is_active == True)
        )
        active_platforms = result.scalar() or 0

        # 活跃用户数
        result = await self.db.execute(
            select(func.count()).where(User.status == "active")
        )
        active_users = result.scalar() or 0

        # 今日采集文章数
        result = await self.db.execute(
            select(func.count()).where(HotArticle.snapshot_at >= today_start)
        )
        today_articles = result.scalar() or 0

        # 今日话题数
        result = await self.db.execute(
            select(func.count()).where(TrendingTopic.snapshot_at >= today_start)
        )
        today_topics = result.scalar() or 0

        # 今日 API 调用量
        result = await self.db.execute(
            select(func.count()).where(ApiUsageLog.created_at >= today_start)
        )
        today_api_calls = result.scalar() or 0

        # 采集成功率（最近 24h）
        since = datetime.now(timezone.utc) - timedelta(hours=24)
        result = await self.db.execute(
            select(func.count()).where(
                and_(CrawlLog.status == "success", CrawlLog.created_at >= since)
            )
        )
        success_count = result.scalar() or 0
        result = await self.db.execute(
            select(func.count()).where(CrawlLog.created_at >= since)
        )
        total_crawls = result.scalar() or 1
        success_rate = round(success_count / total_crawls * 100, 1)

        return {
            "active_platforms": active_platforms,
            "active_users": active_users,
            "today_articles": today_articles,
            "today_topics": today_topics,
            "today_api_calls": today_api_calls,
            "crawl_success_rate": success_rate,
            "total_articles": await self._count(HotArticle),
            "total_topics": await self._count(TrendingTopic),
        }

    async def get_visit_trend(self, days: int = 7) -> list[dict]:
        """获取访问趋势"""
        since = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = (
            select(
                func.date(ApiUsageLog.created_at).label("date"),
                func.count().label("count"),
            )
            .where(ApiUsageLog.created_at >= since)
            .group_by(text("date"))
            .order_by(text("date"))
        )
        result = await self.db.execute(stmt)
        return [{"date": str(row[0]), "count": row[1]} for row in result.all()]

    async def get_platform_distribution(self) -> list[dict]:
        """获取平台话题分布"""
        # 最新快照时间
        latest = select(func.max(TrendingTopic.snapshot_at)).scalar_subquery()
        stmt = (
            select(
                TrendingTopic.platform_id,
                Platform.name,
                func.count().label("count"),
            )
            .join(Platform, TrendingTopic.platform_id == Platform.id)
            .where(TrendingTopic.snapshot_at >= latest)
            .group_by(TrendingTopic.platform_id, Platform.name)
            .order_by(desc(text("count")))
        )
        result = await self.db.execute(stmt)
        return [{"platform_id": row[0], "name": row[1], "count": row[2]} for row in result.all()]

    async def get_crawl_logs(self, platform_id: int = None,
                             page: int = 1, page_size: int = 20) -> tuple[list[CrawlLog], int]:
        base = select(CrawlLog)
        if platform_id:
            base = base.where(CrawlLog.platform_id == platform_id)

        count_stmt = select(func.count()).select_from(base.subquery())
        result = await self.db.execute(count_stmt)
        total = result.scalar() or 0

        stmt = base.order_by(desc(CrawlLog.created_at)) \
            .offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def get_pending_articles(self, page: int = 1,
                                   page_size: int = 20) -> tuple[list[HotArticle], int]:
        base = select(HotArticle).where(HotArticle.status == "pending")
        count_stmt = select(func.count()).select_from(base.subquery())
        result = await self.db.execute(count_stmt)
        total = result.scalar() or 0

        stmt = base.order_by(desc(HotArticle.created_at)) \
            .offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def _count(self, model) -> int:
        result = await self.db.execute(select(func.count()).select_from(model))
        return result.scalar() or 0
