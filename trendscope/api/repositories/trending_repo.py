"""热榜数据访问层"""
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from trendscope.api.models.database import TrendingTopic, Platform, CrawlLog


class TrendingRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_platforms(self) -> list[Platform]:
        """获取所有激活的平台"""
        stmt = select(Platform).where(Platform.is_active == True).order_by(Platform.id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_platform_by_code(self, code: str) -> Platform | None:
        """根据代码获取平台"""
        stmt = select(Platform).where(Platform.code == code)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_latest_snapshot_time(self, platform_id: int) -> datetime | None:
        """获取某平台最新快照时间"""
        stmt = (
            select(func.max(TrendingTopic.snapshot_at))
            .where(TrendingTopic.platform_id == platform_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar()

    async def get_aggregated_trending(
        self, platform_ids: list[int] = None, category: str = "all",
        page: int = 1, page_size: int = 20
    ) -> tuple[list[TrendingTopic], int]:
        """获取聚合热榜（最新快照，跨平台）"""
        # 子查询：每个平台最新快照时间
        latest_snapshot = (
            select(
                TrendingTopic.platform_id,
                func.max(TrendingTopic.snapshot_at).label("max_snapshot")
            )
            .group_by(TrendingTopic.platform_id)
        )

        if platform_ids:
            latest_snapshot = latest_snapshot.where(
                TrendingTopic.platform_id.in_(platform_ids)
            )
        latest_snapshot = latest_snapshot.subquery()

        # 主查询：关联最新快照
        base = (
            select(TrendingTopic)
            .join(
                latest_snapshot,
                and_(
                    TrendingTopic.platform_id == latest_snapshot.c.platform_id,
                    TrendingTopic.snapshot_at == latest_snapshot.c.max_snapshot,
                )
            )
        )

        # 分类过滤
        if category != "all":
            base = base.where(TrendingTopic.category == category)

        # 计数
        count_stmt = select(func.count()).select_from(base.subquery())
        result = await self.db.execute(count_stmt)
        total = result.scalar() or 0

        # 分页 + 排序
        stmt = base.order_by(desc(TrendingTopic.hot_value_norm))
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    async def get_platform_trending(
        self, platform_code: str, page: int = 1, page_size: int = 50
    ) -> tuple[list[TrendingTopic], int]:
        """获取单平台热榜（最新快照）"""
        platform = await self.get_platform_by_code(platform_code)
        if not platform:
            return [], 0

        latest_time = await self.get_latest_snapshot_time(platform.id)
        if not latest_time:
            return [], 0

        base = (
            select(TrendingTopic)
            .where(
                and_(
                    TrendingTopic.platform_id == platform.id,
                    TrendingTopic.snapshot_at >= latest_time - timedelta(seconds=5),
                )
            )
        )

        count_stmt = select(func.count()).select_from(base.subquery())
        result = await self.db.execute(count_stmt)
        total = result.scalar() or 0

        stmt = base.order_by(TrendingTopic.rank).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    async def get_trending_history(
        self, topic_id: int, time_range: str = "24h"
    ) -> list[TrendingTopic]:
        """获取话题历史趋势"""
        # 解析时间范围
        hours = {"24h": 24, "3d": 72, "7d": 168}.get(time_range, 24)
        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        # 先获取当前话题
        topic = await self.db.get(TrendingTopic, topic_id)
        if not topic:
            return []

        # 查询同名话题的历史快照
        stmt = (
            select(TrendingTopic)
            .where(
                and_(
                    TrendingTopic.title == topic.title,
                    TrendingTopic.platform_id == topic.platform_id,
                    TrendingTopic.snapshot_at >= since,
                )
            )
            .order_by(TrendingTopic.snapshot_at)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def upsert_topics(self, topics: list[dict]) -> int:
        """批量 UPSERT 话题数据，返回写入条数"""
        count = 0
        for item in topics:
            # 查找是否存在（同平台+同标题+相近时间）
            stmt = (
                select(TrendingTopic)
                .where(
                    and_(
                        TrendingTopic.platform_id == item.get("platform_id"),
                        TrendingTopic.title == item.get("title"),
                    )
                )
                .order_by(desc(TrendingTopic.snapshot_at))
                .limit(1)
            )
            result = await self.db.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                # 更新排名和热度
                existing.rank = item.get("rank", existing.rank)
                existing.hot_value = item.get("hot_value", existing.hot_value)
                existing.hot_value_norm = item.get("hot_value_norm", existing.hot_value_norm)
                existing.snapshot_at = item.get("snapshot_at", existing.snapshot_at)
            else:
                topic = TrendingTopic(**item)
                self.db.add(topic)
                count += 1

        await self.db.flush()
        return count

    async def log_crawl(self, platform_id: int, status: str,
                        items_count: int = 0, error: str = None,
                        duration_ms: int = None) -> CrawlLog:
        """记录采集日志"""
        log_entry = CrawlLog(
            platform_id=platform_id,
            status=status,
            items_count=items_count,
            error_message=error,
            duration_ms=duration_ms,
        )
        self.db.add(log_entry)
        await self.db.flush()
        return log_entry
