"""API Key 数据访问层"""
import hashlib
import secrets
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from trendscope.api.models.database import ApiKey, ApiUsageLog


class ApiKeyRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ─── CRUD ───

    async def find_by_hash(self, key_hash: str) -> ApiKey | None:
        stmt = select(ApiKey).where(
            and_(ApiKey.key_hash == key_hash, ApiKey.is_active == True)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_prefix(self, prefix: str) -> ApiKey | None:
        stmt = select(ApiKey).where(ApiKey.key_prefix == prefix)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_keys(self, user_id: int = None,
                        page: int = 1, page_size: int = 20) -> tuple[list[ApiKey], int]:
        base = select(ApiKey)
        if user_id:
            base = base.where(ApiKey.user_id == user_id)

        count_stmt = select(func.count()).select_from(base.subquery())
        result = await self.db.execute(count_stmt)
        total = result.scalar() or 0

        stmt = base.order_by(ApiKey.created_at.desc()) \
            .offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def create(self, user_id: int, name: str,
                     rate_limit: int = 100, expires_days: int = 365) -> dict:
        # 生成原始 Key
        raw_key = f"ts_live_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key_prefix = raw_key[:16]

        api_key = ApiKey(
            user_id=user_id,
            key_hash=key_hash,
            key_prefix=key_prefix,
            name=name,
            rate_limit=rate_limit,
            expires_at=datetime.now(timezone.utc) + timedelta(days=expires_days) if expires_days else None,
        )
        self.db.add(api_key)
        await self.db.flush()

        return {
            "id": api_key.id,
            "key": raw_key,
            "key_prefix": key_prefix,
            "name": name,
            "rate_limit": rate_limit,
            "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
        }

    async def revoke(self, key_id: int) -> bool:
        key = await self.db.get(ApiKey, key_id)
        if not key:
            return False
        key.is_active = False
        await self.db.flush()
        return True

    # ─── 验证 ───

    async def validate(self, key_hash: str) -> dict | None:
        """验证 API Key，返回 payload 或 None"""
        api_key = await self.find_by_hash(key_hash)
        if not api_key:
            return None

        # 检查过期
        if api_key.expires_at and api_key.expires_at < datetime.now(timezone.utc):
            return None

        # 更新最后使用时间
        api_key.last_used_at = datetime.now(timezone.utc)
        await self.db.flush()

        return {
            "key_id": api_key.id,
            "user_id": api_key.user_id,
            "rate_limit": api_key.rate_limit,
            "key_prefix": api_key.key_prefix,
        }

    # ─── 用量记录 ───

    async def log_usage(self, api_key_id: int, endpoint: str,
                        method: str, status_code: int, ip: str = ""):
        log = ApiUsageLog(
            api_key_id=api_key_id,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            ip_address=ip,
        )
        self.db.add(log)
        await self.db.flush()

    async def get_usage_stats(self, api_key_id: int, days: int = 30) -> dict:
        """获取指定 Key 的用量统计"""
        since = datetime.now(timezone.utc) - timedelta(days=days)

        today_count_stmt = select(func.count()).where(
            and_(
                ApiUsageLog.api_key_id == api_key_id,
                ApiUsageLog.created_at >= datetime.now(timezone.utc).replace(hour=0, minute=0, second=0),
            )
        )
        result = await self.db.execute(today_count_stmt)
        today_calls = result.scalar() or 0

        monthly_count_stmt = select(func.count()).where(
            and_(ApiUsageLog.api_key_id == api_key_id, ApiUsageLog.created_at >= since)
        )
        result = await self.db.execute(monthly_count_stmt)
        monthly_calls = result.scalar() or 0

        return {
            "today_calls": today_calls,
            "monthly_calls": monthly_calls,
            "period_days": days,
        }

    async def get_overall_stats(self) -> dict:
        """获取全局 API 调用统计"""
        today_count_stmt = select(func.count()).where(
            ApiUsageLog.created_at >= datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
        )
        result = await self.db.execute(today_count_stmt)
        today_total = result.scalar() or 0

        # 热门端点 Top 10
        top_endpoints_stmt = (
            select(ApiUsageLog.endpoint, func.count().label("calls"))
            .group_by(ApiUsageLog.endpoint)
            .order_by(func.count().desc())
            .limit(10)
        )
        result = await self.db.execute(top_endpoints_stmt)
        top_endpoints = [{"endpoint": row[0], "calls": row[1]} for row in result.all()]

        return {
            "today_total_calls": today_total,
            "top_endpoints": top_endpoints,
        }
