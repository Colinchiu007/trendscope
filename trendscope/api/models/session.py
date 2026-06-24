"""数据库连接管理 — 延迟初始化，启动时不强制连接 PostgreSQL。"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from loguru import logger

from trendscope.api.config import settings

# 懒加载 — 模块导入时不创建引擎，避免 PostgreSQL 离线时无法启动
_engine = None
_async_session_factory = None


def _get_engine():
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.DEBUG,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
        )
    return _engine


def _get_session_factory():
    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            _get_engine(), class_=AsyncSession, expire_on_commit=False
        )
    return _async_session_factory


async def get_db() -> AsyncSession:
    """依赖注入：获取数据库会话"""
    async with _get_session_factory()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """初始化数据库表"""
    from trendscope.api.models.database import Base
    async with _get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("数据库表初始化完成")


async def close_db():
    """关闭数据库连接"""
    if _engine is not None:
        await _engine.dispose()
        logger.info("数据库连接已关闭")
