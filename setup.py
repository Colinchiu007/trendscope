"""TrendScope - 多平台热榜聚合引擎"""
from setuptools import setup, find_packages

setup(
    name="trendscope",
    version="0.1.0",
    description="多平台热榜聚合引擎",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "fastapi>=0.115.0",
        "uvicorn[standard]>=0.30.0",
        "sqlalchemy[asyncio]>=2.0.31",
        "psycopg2-binary>=2.9.9",
        "asyncpg>=0.29.0",
        "redis>=5.0.7",
        "httpx>=0.27.0",
        "python-jose[cryptography]>=3.3.0",
        "passlib[bcrypt]>=1.7.4",
        "pydantic>=2.7.0",
        "celery[redis]>=5.4.0",
        "loguru>=0.7.2",
        "rpa-common",
    ],
    extras_require={
        "crawler": [
            "beautifulsoup4>=4.12.3",
            "lxml>=5.2.2",
            "playwright>=1.45.0",
            "fake-useragent>=1.5.1",
            "tenacity>=8.5.0",
        ],
    },
)
