"""管理后台路由"""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from trendscope.api.middleware.auth import require_admin
from trendscope.api.dependencies import get_db
from trendscope.api.repositories.admin_repo import AdminRepo
from trendscope.api.repositories.user_repo import UserRepo
from trendscope.api.repositories.apikey_repo import ApiKeyRepo
from trendscope.api.repositories.article_repo import ArticleRepo
from trendscope.api.models.database import User
from sqlalchemy import select, func
import os
import json

router = APIRouter(dependencies=[Depends(require_admin)])

# 公开路由器（不需要登录即可访问）
public_router = APIRouter()


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


# ─── 平台凭证管理 ───

_CREDENTIAL_FIELDS: dict[str, list[dict]] = {
    "zhihu": [
        {"key": "cookie", "label": "Cookie", "env_var": "ZHIHU_COOKIE", "type": "textarea"},
    ],
    "youtube": [
        {"key": "api_key", "label": "API Key", "env_var": "YOUTUBE_API_KEY", "type": "password"},
    ],
    "tiktok": [
        {"key": "proxy_url", "label": "代理地址 (Proxy URL)", "env_var": "TIKTOK_PROXY_URL", "type": "password"},
    ],
    "x_twitter": [
        {"key": "bearer_token", "label": "Bearer Token", "env_var": "TWITTER_BEARER_TOKEN", "type": "password"},
    ],
}


class PlatformCredentials(BaseModel):
    """单平台凭据更新请求"""
    config: dict


@public_router.get("/platforms/credential-fields")
async def get_credential_fields():
    """返回各平台需要的凭证字段定义（前端表单渲染用）"""
    return {"code": 0, "data": _CREDENTIAL_FIELDS}


@router.get("/platforms/{code}/credentials")
async def get_platform_credentials(
    code: str,
    db: AsyncSession = Depends(get_db),
):
    """获取指定平台的凭证配置（值掩码处理）"""
    from trendscope.api.models.database import Platform
    from sqlalchemy import select
    result = await db.execute(select(Platform).where(Platform.code == code))
    platform = result.scalar_one_or_none()
    if not platform:
        return {"code": 1002, "message": "平台不存在"}

    config = platform.crawl_config or {}
    fields = _CREDENTIAL_FIELDS.get(code, [])

    # 掩码处理：只返回前4位+后4位，中间用****代替
    masked = {}
    for field in fields:
        key = field["key"]
        raw = config.get(key, "")
        if raw and len(raw) > 12:
            masked[key] = raw[:4] + "****" + raw[-4:]
        elif raw and len(raw) > 4:
            masked[key] = raw[:4] + "****"
        else:
            masked[key] = "" if not raw else "****"
        masked[f"{key}_set"] = bool(raw)

    return {
        "code": 0,
        "data": {
            "code": platform.code,
            "name": platform.name,
            "masked": masked,
        },
    }


@router.put("/platforms/{code}/credentials")
async def update_platform_credentials(
    code: str,
    req: PlatformCredentials,
    db: AsyncSession = Depends(get_db),
):
    """更新指定平台的凭证配置"""
    from trendscope.api.models.database import Platform
    from sqlalchemy import select
    result = await db.execute(select(Platform).where(Platform.code == code))
    platform = result.scalar_one_or_none()
    if not platform:
        return {"code": 1002, "message": "平台不存在"}

    # 合并现有配置
    existing = platform.crawl_config or {}
    existing.update(req.config)
    platform.crawl_config = existing
    await db.flush()

    return {"code": 0, "message": f"{platform.name} 凭证已更新"}


@public_router.get("/credentials/export", include_in_schema=False)
async def export_credentials_as_env(
    db: AsyncSession = Depends(get_db),
):
    """导出所有平台凭证为环境变量格式（供 crawl_all.sh 调用）"""
    from trendscope.api.models.database import Platform
    from sqlalchemy import select
    result = await db.execute(select(Platform))
    platforms = result.scalars().all()

    env_map: dict[str, str] = {}
    for p in platforms:
        fields = _CREDENTIAL_FIELDS.get(p.code, [])
        config = p.crawl_config or {}
        for field in fields:
            env_var = field["env_var"]
            value = config.get(field["key"], "")
            if value:
                env_map[env_var] = value

    # 输出为 shell source-able 格式
    lines = []
    for var, val in env_map.items():
        escaped = val.replace("'", "'\\''")
        lines.append(f"export {var}='{escaped}'")
    text = "\n".join(lines)
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(text)




# ─── 采集实时状态（Task 17）───

@router.get("/crawl/status")
async def get_crawl_status(db: AsyncSession = Depends(get_db)):
    repo = AdminRepo(db)
    items = await repo.get_crawl_status()
    return {"code": 0, "data": {"items": items}}


# ─── 批量审核（Task 18）───

class BatchAuditReq(BaseModel):
    article_ids: list[int] = Field(..., min_length=1, max_length=100)
    status: str = Field(..., pattern=r"^(approved|rejected|pending)$")


@router.post("/articles/batch-audit")
async def batch_audit(
    req: BatchAuditReq,
    db: AsyncSession = Depends(get_db),
):
    repo = AdminRepo(db)
    count = await repo.batch_audit_articles(req.article_ids, req.status)
    return {"code": 0, "message": f"已审核 {count} 篇文章", "data": {"affected": count}}


# ─── 用户详情统计（Task 19）───

@router.get("/users/{user_id}/stats")
async def get_user_stats(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    repo = AdminRepo(db)
    stats = await repo.get_user_stats(user_id)
    return {"code": 0, "data": stats}
# ─── 敏感词管理（JSON 文件存储） ───

_SENSITIVE_WORDS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "sensitive_words.json"
)


def _ensure_data_dir():
    os.makedirs(os.path.dirname(_SENSITIVE_WORDS_FILE), exist_ok=True)


def _load_words() -> list[str]:
    _ensure_data_dir()
    if os.path.exists(_SENSITIVE_WORDS_FILE):
        with open(_SENSITIVE_WORDS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_words(words: list[str]):
    _ensure_data_dir()
    with open(_SENSITIVE_WORDS_FILE, "w", encoding="utf-8") as f:
        json.dump(words, f, ensure_ascii=False, indent=2)


class SensitiveWordReq(BaseModel):
    word: str = Field(..., min_length=1, max_length=100)


@router.get("/sensitive-words")
async def list_sensitive_words():
    return {"code": 0, "data": {"words": _load_words()}}


@router.post("/sensitive-words")
async def add_sensitive_word(req: SensitiveWordReq):
    words = _load_words()
    if req.word not in words:
        words.append(req.word)
        _save_words(words)
    return {"code": 0, "message": "添加成功", "data": {"words": words}}


@router.delete("/sensitive-words/{word:path}")
async def delete_sensitive_word(word: str):
    words = _load_words()
    if word in words:
        words.remove(word)
        _save_words(words)
    return {"code": 0, "message": "删除成功", "data": {"words": words}}
