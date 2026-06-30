"""用户相关路由"""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from trendscope.api.dependencies import get_user_service
from trendscope.api.middleware.auth import get_current_user
from trendscope.api.services.user_service import UserService

router = APIRouter()


class SendSmsCodeReq(BaseModel):
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$", description="手机号")


class LoginBySmsReq(BaseModel):
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$", description="手机号")
    code: str = Field(..., min_length=6, max_length=6, description="验证码")


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


# ─── 公开（无需认证）───

@router.post("/send-sms-code")
async def send_sms_code(
    req: SendSmsCodeReq,
    svc: UserService = Depends(get_user_service),
):
    """发送短信验证码"""
    try:
        data = await svc.send_sms_code(req.phone)
        return {"code": 0, "message": data["message"]}
    except ValueError as e:
        return {"code": 1001, "message": str(e)}


@router.post("/login-by-sms")
async def login_by_sms(
    req: LoginBySmsReq,
    svc: UserService = Depends(get_user_service),
):
    """短信验证码登录"""
    try:
        data = await svc.login_by_sms(req.phone, req.code)
        return {"code": 0, "data": data}
    except ValueError as e:
        return {"code": 1001, "message": str(e)}





# ─── 邮箱注册 ───

class SendEmailCodeReq(BaseModel):
    email: str = Field(..., pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", description="邮箱")
    captcha: str | None = Field(None, min_length=1, max_length=10, description="图形验证码（预留）")


class RegisterReq(BaseModel):
    username: str = Field(..., min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_一-鿿]{3,64}$")
    password: str = Field(..., min_length=8, max_length=128)
    email: str = Field(..., pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    email_code: str = Field(..., min_length=6, max_length=6, description="邮箱验证码")
    phone: str | None = Field(None, pattern=r"^1[3-9]\d{9}$")


@router.post("/send-email-code")
async def send_email_code(
    req: SendEmailCodeReq,
    svc: UserService = Depends(get_user_service),
):
    """发送邮箱验证码"""
    try:
        data = await svc.send_email_code(req.email)
        return {"code": 0, "message": data["message"]}
    except ValueError as e:
        return {"code": 1001, "message": str(e)}


@router.post("/register")
async def register(
    req: RegisterReq,
    svc: UserService = Depends(get_user_service),
):
    """邮箱验证码注册"""
    try:
        data = await svc.register_with_email(
            username=req.username,
            password=req.password,
            email=req.email,
            email_code=req.email_code,
            phone=req.phone,
        )
        return {"code": 0, "data": data}
    except ValueError as e:
        return {"code": 1001, "message": str(e)}


# ─── 需认证 ───

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
            nickname=req.nickname, email=req.email,
            phone=req.phone, avatar_url=req.avatar_url,
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
        "code": 0, "data": {"items": items},
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
        "code": 0, "data": {"items": items},
        "pagination": {"page": page, "page_size": page_size, "total": total, "total_pages": total_pages},
    }




# ─── SSE 通知推送 ───

import json as _json
from fastapi.responses import StreamingResponse as _StreamingResponse


@router.get("/notifications/stream")
async def stream_notifications(
    user: dict = Depends(get_current_user),
    svc: UserService = Depends(get_user_service),
):
    """SSE 实时通知推送"""
    import asyncio

    async def event_stream():
        user_id = user["user_id"]
        last_check = None
        while True:
            try:
                items, _ = await svc.get_notifications(user_id, page=1, page_size=10)
                for item in items:
                    if last_check is None or item["id"] > last_check:
                        yield f"data: {_json.dumps(item, ensure_ascii=False)}\n\n"
                        last_check = item["id"] if last_check is None else max(last_check, item["id"])
                # Heartbeat
                yield ": heartbeat\n\n"
                await asyncio.sleep(15)
            except asyncio.CancelledError:
                break
            except Exception:
                yield f"data: {_json.dumps({'type': 'error', 'content': '连接异常'}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(30)

    return _StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )



# ─── 收藏文件夹 ───

class CreateFolderReq(BaseModel):
    name: str = Field(..., min_length=1, max_length=128, description="文件夹名称")


class UpdateFolderReq(BaseModel):
    name: str = Field(..., min_length=1, max_length=128, description="文件夹名称")


@router.get("/folders")
async def get_folders(
    user: dict = Depends(get_current_user),
    svc: UserService = Depends(get_user_service),
):
    items = await svc.get_folders(user["user_id"])
    return {"code": 0, "data": {"items": items}}


@router.post("/folders")
async def create_folder(
    req: CreateFolderReq,
    user: dict = Depends(get_current_user),
    svc: UserService = Depends(get_user_service),
):
    try:
        folder = await svc.create_folder(user["user_id"], req.name)
        return {"code": 0, "data": folder, "message": "文件夹创建成功"}
    except ValueError as e:
        return {"code": 1001, "message": str(e)}


@router.put("/folders/{folder_id}")
async def update_folder(
    folder_id: int,
    req: UpdateFolderReq,
    user: dict = Depends(get_current_user),
    svc: UserService = Depends(get_user_service),
):
    ok = await svc.update_folder(folder_id, user["user_id"], req.name)
    if not ok:
        return {"code": 1002, "message": "文件夹不存在"}
    return {"code": 0, "message": "文件夹已更新"}


@router.delete("/folders/{folder_id}")
async def delete_folder(
    folder_id: int,
    user: dict = Depends(get_current_user),
    svc: UserService = Depends(get_user_service),
):
    ok = await svc.delete_folder(folder_id, user["user_id"])
    if not ok:
        return {"code": 1002, "message": "文件夹不存在"}
    return {"code": 0, "message": "文件夹已删除"}

# ─── 密码修改 ───

class ChangePasswordReq(BaseModel):
    old_password: str = Field(..., min_length=1, description="旧密码")
    new_password: str = Field(..., min_length=8, max_length=128, description="新密码（至少8位）")


@router.put("/password")
async def change_password(
    req: ChangePasswordReq,
    user: dict = Depends(get_current_user),
    svc: UserService = Depends(get_user_service),
):
    """修改密码"""
    try:
        await svc.change_password(user["user_id"], req.old_password, req.new_password)
        return {"code": 0, "message": "密码修改成功"}
    except ValueError as e:
        return {"code": 1001, "message": str(e)}


# ─── 账号注销 ───


@router.delete("/account")
async def delete_account(
    user: dict = Depends(get_current_user),
    svc: UserService = Depends(get_user_service),
):
    """注销账号"""
    try:
        await svc.delete_account(user["user_id"])
        return {"code": 0, "message": "账号已注销"}
    except ValueError as e:
        return {"code": 1002, "message": str(e)}
