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


    # ─── 采集实时状态（Task 17）───

    async def get_crawl_status(self) -> list[dict]:
        """获取当前所有平台的采集状态（最近一次采集记录）"""
        from sqlalchemy import text
        stmt = text("""
            SELECT DISTINCT ON (cl.platform_id)
                cl.platform_id,
                p.code as platform_code,
                p.name as platform_name,
                cl.status,
                cl.items_count,
                cl.error_message,
                cl.started_at,
                cl.finished_at
            FROM crawl_logs cl
            JOIN platforms p ON cl.platform_id = p.id
            ORDER BY cl.platform_id, cl.created_at DESC
        """)
        result = await self.db.execute(stmt)
        rows = result.all()
        return [
            {
                "platform_id": r[0],
                "platform_code": r[1],
                "platform_name": r[2],
                "status": r[3],
                "items_count": r[4],
                "error_message": r[5],
                "started_at": r[6].isoformat() if r[6] else "",
                "finished_at": r[7].isoformat() if r[7] else "",
            }
            for r in rows
        ]

    # ─── 批量审核（Task 18）───

    async def batch_audit_articles(self, article_ids: list[int], status: str) -> int:
        """批量审核文章"""
        from sqlalchemy import update
        from trendscope.api.models.database import HotArticle
        stmt = (
            update(HotArticle)
            .where(HotArticle.id.in_(article_ids))
            .values(status=status)
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount

    # ─── 用户详情统计（Task 19）───

    async def get_user_stats(self, user_id: int) -> dict:
        """获取用户统计数据"""
        from sqlalchemy import select, func
        from trendscope.api.models.database import UserFavorite, UserSubscription

        # 收藏数
        result = await self.db.execute(
            select(func.count()).where(UserFavorite.user_id == user_id)
        )
        favorites_count = result.scalar() or 0

        # 订阅数
        result = await self.db.execute(
            select(func.count()).where(
                UserSubscription.user_id == user_id,
                UserSubscription.is_active == True,
            )
        )
        subscriptions_count = result.scalar() or 0

        return {
            "user_id": user_id,
            "favorites_count": favorites_count,
            "subscriptions_count": subscriptions_count,
        }
