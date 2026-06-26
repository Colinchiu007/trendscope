"""用户相关路由（Phase C: register/login 已下线，统一由 orchestrator 认证）"""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from trendscope.api.dependencies import get_user_service
from trendscope.api.middleware.auth import get_current_user
from trendscope.api.services.user_service import UserService

router = APIRouter()


class FavoriteReq(BaseModel):
    article_id: int


class SubscriptionReq(BaseModel):
    platform_id: int | None = None
    keywords: list[str] = []
    notify_email: bool = False


class UpdateProfileReq(BaseModel):
    nickname: str | None = None
    email: str | None = None
    phone: str | None = None
    avatar_url: str | None = None


# ─── 需要认证 ───

@router.get("/profile")
async def get_profile(
    user: dict = Depends(get_current_user),
    svc: UserService = Depends(get_user_service),
):
    try:
        data = await svc.get_profile(user["user_id"])
        return {"code": 0, "data": data}
    except ValueError as e:
        return {"code": 1002, "message": str(e)}


@router.put("/profile")
async def update_profile(
    req: UpdateProfileReq,
    user: dict = Depends(get_current_user),
    svc: UserService = Depends(get_user_service),
):
    try:
        data = await svc.update_profile(
            user["user_id"],
            nickname=req.nickname,
            email=req.email,
            phone=req.phone,
            avatar_url=req.avatar_url,
        )
        return {"code": 0, "data": data}
    except ValueError as e:
        return {"code": 1002, "message": str(e)}


@router.get("/favorites")
async def get_favorites(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: dict = Depends(get_current_user),
    svc: UserService = Depends(get_user_service),
):
    items, total = await svc.get_favorites(user["user_id"], page, page_size)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return {
        "code": 0,
        "data": {"items": items},
        "pagination": {"page": page, "page_size": page_size, "total": total, "total_pages": total_pages},
    }


@router.post("/favorites")
async def add_favorite(
    req: FavoriteReq,
    user: dict = Depends(get_current_user),
    svc: UserService = Depends(get_user_service),
):
    ok = await svc.add_favorite(user["user_id"], req.article_id)
    if not ok:
        return {"code": 1006, "message": "已收藏"}
    return {"code": 0, "message": "收藏成功"}


@router.delete("/favorites/{favorite_id}")
async def remove_favorite(
    favorite_id: int,
    user: dict = Depends(get_current_user),
    svc: UserService = Depends(get_user_service),
):
    ok = await svc.remove_favorite(user["user_id"], favorite_id)
    if not ok:
        return {"code": 1002, "message": "收藏不存在"}
    return {"code": 0, "message": "已取消收藏"}


@router.get("/subscriptions")
async def get_subscriptions(
    user: dict = Depends(get_current_user),
    svc: UserService = Depends(get_user_service),
):
    items = await svc.get_subscriptions(user["user_id"])
    return {"code": 0, "data": {"items": items}}


@router.post("/subscriptions")
async def create_subscription(
    req: SubscriptionReq,
    user: dict = Depends(get_current_user),
    svc: UserService = Depends(get_user_service),
):
    result = await svc.create_subscription(
        user["user_id"],
        platform_id=req.platform_id,
        keywords=req.keywords,
        notify_email=req.notify_email,
    )
    return {"code": 0, "message": "订阅创建成功", "data": result}


@router.delete("/subscriptions/{sub_id}")
async def delete_subscription(
    sub_id: int,
    user: dict = Depends(get_current_user),
    svc: UserService = Depends(get_user_service),
):
    ok = await svc.delete_subscription(user["user_id"], sub_id)
    if not ok:
        return {"code": 1002, "message": "订阅不存在"}
    return {"code": 0, "message": "已取消订阅"}


@router.get("/notifications")
async def get_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: dict = Depends(get_current_user),
    svc: UserService = Depends(get_user_service),
):
    items, total = await svc.get_notifications(user["user_id"], page, page_size)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return {
        "code": 0,
        "data": {"items": items},
        "pagination": {"page": page, "page_size": page_size, "total": total, "total_pages": total_pages},
    }
