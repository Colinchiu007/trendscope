"""TrendScope FastAPI 应用入口"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from trendscope.api.config import settings
from trendscope.api.middleware.security import (
    SecurityHeadersMiddleware,
    RequestSizeLimitMiddleware,
)
from trendscope.api.routers import trending, articles, user, admin, partner

app = FastAPI(
    title="TrendScope API",
    description="多平台热榜聚合引擎 API",
    version="0.1.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url=None,
)

# 安全中间件（从内到外：size → security → cors）
app.add_middleware(RequestSizeLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由 — 使用 prefix 直接挂载
app.include_router(trending.router, prefix="/api/v1/trending", tags=["热榜"])
# 注意: /platforms 路由需要在前，否则会被 /{platform} 捕获
app.include_router(articles.router, prefix="/api/v1/articles", tags=["文章"])
app.include_router(user.router, prefix="/api/v1/user", tags=["用户"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["管理后台"])
app.include_router(partner.router, prefix="/api/v1/partner", tags=["第三方API"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "trendscope", "version": "0.1.0"}
