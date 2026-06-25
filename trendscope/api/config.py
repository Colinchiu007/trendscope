"""应用配置 — 从环境变量和 feature_gates.yaml 加载"""
import os
from functools import lru_cache


class Settings:
    # 服务器
    API_PORT: int = int(os.getenv("TS_API_PORT", "8001"))
    DEBUG: bool = os.getenv("TS_DEBUG", "true").lower() == "true"

    # 数据库（共享已有）
    DB_HOST: str = os.getenv("TS_DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("TS_DB_PORT", "5432"))
    DB_USER: str = os.getenv("TS_DB_USER", "trendscope")
    DB_PASSWORD: str = os.getenv("TS_DB_PASSWORD", "trendscope_dev")
    DB_NAME: str = os.getenv("TS_DB_NAME", "trendscope")

    # Redis（共享已有）
    REDIS_HOST: str = os.getenv("TS_REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("TS_REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("TS_REDIS_DB", "3"))

    # JWT（与已有平台共享密钥）
    JWT_SECRET: str = os.getenv("PO_SECRET_KEY", "")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE: int = 7200

    # Celery
    CELERY_BROKER: str = os.getenv("TS_CELERY_BROKER", "redis://localhost:6379/4")
    CELERY_BACKEND: str = os.getenv("TS_CELERY_BACKEND", "redis://localhost:6379/5")

    # 功能开关
    FEATURE_GATES_PATH: str = os.getenv(
        "FEATURE_GATES_PATH", "/srv/projects/feature_gates.yaml"
    )

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def database_url_sync(self) -> str:
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


# ── 启动验证