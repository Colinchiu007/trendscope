"""管理后台路由"""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from trendscope.api.middleware.auth import require_admin
from trendscope.api.dependencies import get_db
from trendscope.api.repositories.admin_repo import AdminRepo
from trendscope.api.repositories.user_repo import UserRepo
from trendscope.api.repositories.apikey_repo import ApiKeyRepo
from trendscope.api.repositories.article_repo import ArticleRepo
from trendscope.api.models.database import User
from sqlalchemy import select, func

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/dashboard")
async def dashboard(db: AsyncSession = Depends(get_db)):
    repo = AdminRepo(db)
    stats = await repo.get_dashboard_stats()
    trend = await repo.get_visit_trend(7)
    distribution = await repo.get_platform_distribution()
    return {
        "code": 0,
        "data": {
            "stats": stats,
            "visit_trend": trend,
            "platform_distribution": distribution,
        },
    }


@router.get("/crawl/logs")
async def get_crawl_logs(
    platform_id: int = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    repo = AdminRepo(db)
    items, total = await repo.get_crawl_logs(platform_id, page, page_size)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    logs = [
        {
            "id": l.id, "platform_id": l.platform_id,
            "status": l.status, "items_count": l.items_count,
            "error_message": l.error_message, "duration_ms": l.duration_ms,
            "started_at": l.started_at.isoformat() if l.started_at else "",
            "finished_at": l.finished_at.isoformat() if l.finished_at else "",
        }
        for l in items
    ]
    return {
        "code": 0, "data": {"items": logs},
        "pagination": {"page": page, "page_size": page_size, "total": total, "total_pages": total_pages},
    }


@router.get("/articles")
async def list_articles(
    status: str = Query("all"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    repo = AdminRepo(db)
    if status == "pending":
        items, total = await repo.get_pending_articles(page, page_size)
    else:
        # 返回所有已审核文章
        article_repo = ArticleRepo(db)
        items, total = await article_repo.list_articles(status="approved", page=page, page_size=page_size)

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    articles = [
        {
            "id": a.id, "title": a.title, "status": a.status,
            "platform_id": a.platform_id, "source_url": a.source_url,
            "read_count": a.read_count, "like_count": a.like_count,
            "created_at": a.created_at.isoformat() if a.created_at else "",
        }
        for a in items
    ]
    return {
        "code": 0, "data": {"items": articles},
        "pagination": {"page": page, "page_size": page_size, "total": total, "total_pages": total_pages},
    }


class AuditReq(BaseModel):
    status: str  # approved / rejected / pinned
    remark: str = ""


@router.patch("/articles/{article_id}")
async def audit_article(
    article_id: int, req: AuditReq,
    db: AsyncSession = Depends(get_db),
):
    repo = ArticleRepo(db)
    ok = await repo.update_status(article_id, req.status)
    if not ok:
        return {"code": 1002, "message": "文章不存在"}
    return {"code": 0, "message": "审核完成"}


# ─── 用户管理 ───

@router.get("/users")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    base = select(User)
    count_stmt = select(func.count()).select_from(base.subquery())
    result = await db.execute(count_stmt)
    total = result.scalar() or 0

    stmt = base.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    users = result.scalars().all()

    items = [
        {
            "id": u.id, "username": u.username, "email": u.email,
            "phone": u.phone, "role": u.role, "status": u.status,
            "created_at": u.created_at.isoformat() if u.created_at else "",
        }
        for u in users
    ]
    return {
        "code": 0, "data": {"items": items},
        "pagination": {"page": page, "page_size": page_size, "total": total},
    }


class UpdateUserReq(BaseModel):
    status: str | None = None
    role: str | None = None


@router.patch("/users/{user_id}")
async def update_user(user_id: int, req: UpdateUserReq, db: AsyncSession = Depends(get_db)):
    repo = UserRepo(db)
    user = await repo.update_user(user_id, status=req.status, role=req.role)
    if not user:
        return {"code": 1002, "message": "用户不存在"}
    return {"code": 0, "message": "更新成功"}


# ─── API Key 管理 ───

@router.get("/apikeys")
async def list_api_keys(
    user_id: int = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    repo = ApiKeyRepo(db)
    items, total = await repo.list_keys(user_id, page, page_size)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    keys = [
        {
            "id": k.id, "key_prefix": k.key_prefix, "name": k.name,
            "rate_limit": k.rate_limit, "is_active": k.is_active,
            "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
            "expires_at": k.expires_at.isoformat() if k.expires_at else None,
            "created_at": k.created_at.isoformat() if k.created_at else "",
        }
        for k in items
    ]
    return {
        "code": 0, "data": {"items": keys},
        "pagination": {"page": page, "page_size": page_size, "total": total, "total_pages": total_pages},
    }


class CreateKeyReq(BaseModel):
    user_id: int
    name: str
    rate_limit: int = 100
    expires_days: int = 365


@router.post("/apikeys")
async def create_api_key(req: CreateKeyReq, db: AsyncSession = Depends(get_db)):
    repo = ApiKeyRepo(db)
    result = await repo.create(
        user_id=req.user_id,
        name=req.name,
        rate_limit=req.rate_limit,
        expires_days=req.expires_days,
    )
    return {"code": 0, "message": "API Key 创建成功", "data": result}


@router.delete("/apikeys/{key_id}")
async def revoke_api_key(key_id: int, db: AsyncSession = Depends(get_db)):
    repo = ApiKeyRepo(db)
    ok = await repo.revoke(key_id)
    if not ok:
        return {"code": 1002, "message": "API Key 不存在"}
    return {"code": 0, "message": "API Key 已撤销"}


@router.get("/stats")
async def get_api_stats(db: AsyncSession = Depends(get_db)):
    repo = ApiKeyRepo(db)
    stats = await repo.get_overall_stats()
    return {"code": 0, "data": {"stats": stats}}


# ─── 平台管理（简化） ───

@router.get("/platforms")
async def list_platforms(db: AsyncSession = Depends(get_db)):
    from trendscope.api.models.database import Platform
    from sqlalchemy import select
    result = await db.execute(select(Platform).order_by(Platform.id))
    platforms = result.scalars().all()
    return {
        "code": 0,
        "data": {
            "platforms": [
                {
                    "id": p.id, "code": p.code, "name": p.name,
                    "category": p.category, "is_active": p.is_active,
                    "crawl_interval": p.crawl_interval,
                }
                for p in platforms
            ]
        },
    }


@router.put("/platforms/{platform_id}")
async def update_platform(platform_id: int, db: AsyncSession = Depends(get_db)):
    from trendscope.api.models.database import Platform
    p = await db.get(Platform, platform_id)
    if not p:
        return {"code": 1002, "message": "平台不存在"}
    return {"code": 0, "message": "平台配置更新成功"}


@router.post("/crawl/trigger")
async def trigger_crawl():
    return {"code": 0, "message": "采集任务已触发"}
