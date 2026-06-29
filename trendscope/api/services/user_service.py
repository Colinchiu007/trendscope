"""用户业务逻辑"""
import re

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from trendscope.api.middleware.auth import create_access_token, hash_password, verify_password
from trendscope.api.repositories.user_repo import UserRepo


class UserService:
    def __init__(self, db: AsyncSession):
        self.repo = UserRepo(db)

    # ─── 注册 ───

    async def register(self, username: str, password: str,
                       email: str = None, phone: str = None) -> dict:
        """用户注册"""
        # 校验用户名
        if not re.match(r"^[a-zA-Z0-9_一-鿿]{3,64}$", username):
            raise ValueError("用户名须为3-64位字母、数字、下划线或中文")

        if len(password) < 8:
            raise ValueError("密码至少8位")

        # 检查唯一性
        if await self.repo.find_by_username(username):
            raise ValueError("用户名已存在")
        if email and await self.repo.find_by_email(email):
            raise ValueError("邮箱已注册")
        if phone and await self.repo.find_by_phone(phone):
            raise ValueError("手机号已注册")

        # 创建用户
        hashed = hash_password(password)
        user = await self.repo.create_user(
            username=username,
            password_hash=hashed,
            email=email,
            phone=phone,
            nickname=username,
        )

        logger.info(f"[用户] 注册成功: {username} (id={user.id})")
        return {"id": user.id, "username": user.username, "role": user.role}

    # ─── 登录 ───

    async def login(self, account: str, password: str) -> dict:
        """密码登录"""
        user = await self.repo.find_by_account(account)
        if not user:
            raise ValueError("账号不存在")
        if user.status != "active":
            raise ValueError("账号已被禁用")

        if not verify_password(password, user.password_hash):
            raise ValueError("密码错误")

        token = create_access_token(user.id, user.username, user.role)
        logger.info(f"[用户] 登录成功: {user.username}")
        return {
            "access_token": token,
            "expires_in": 7200,
            "user": {
                "id": user.id,
                "username": user.username,
                "nickname": user.nickname,
                "role": user.role,
            },
        }

    async def login_by_sms(self, phone: str, code: str) -> dict:
        """短信验证码登录

        当前为预留接口，尚未集成 SMS 服务商。
        验证码校验逻辑将在接入具体 SMS 服务商后实现。

        待选集成方案（二选一）:
        1. 对接第三方 SMS 服务商（阿里云短信 / Twilio Verify），
           在 user_service 中增加 verify_sms_code(phone, code) 方法
        2. 使用 Redis 缓存验证码（发送至手机，5分钟有效期），
           此方式更轻量但安全性略低

        当前注册/登录主流程使用邮箱密码方式，短信登录为辅助通道。
        """
        raise NotImplementedError(
            "短信验证码登录尚未接入 SMS 服务商。"
            "当前支持邮箱密码登录。"
            "如需启用短信登录，请配置 SMS_PROVIDER 并实现验证码校验逻辑。"
        )

    # ─── 个人信息 ───

    async def get_profile(self, user_id: int) -> dict:
        user = await self.repo.find_by_id(user_id)
        if not user:
            raise ValueError("用户不存在")
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "phone": user.phone,
            "nickname": user.nickname,
            "avatar_url": user.avatar_url,
            "role": user.role,
            "created_at": user.created_at.isoformat() if user.created_at else "",
        }

    async def update_profile(self, user_id: int, **kwargs) -> dict:
        allowed = {"nickname", "email", "phone", "avatar_url"}
        updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
        user = await self.repo.update_user(user_id, **updates)
        if not user:
            raise ValueError("用户不存在")
        return await self.get_profile(user_id)

    # ─── 收藏 ───

    async def get_favorites(self, user_id: int, page: int = 1,
                            page_size: int = 20) -> tuple[list[dict], int]:
        items, total = await self.repo.get_favorites(user_id, page, page_size)
        result = []
        for fav in items:
            article = fav.article
            result.append({
                "id": fav.id,
                "article_id": fav.article_id,
                "folder_id": fav.folder_id,
                "created_at": fav.created_at.isoformat() if fav.created_at else "",
                "article": {
                    "title": article.title if article else "",
                    "platform_code": article.platform.code if article and article.platform else "",
                    "platform_name": article.platform.name if article and article.platform else "",
                    "source_url": article.source_url if article else "",
                    "summary": article.summary if article else "",
                    "like_count": article.like_count if article else 0,
                    "read_count": article.read_count if article else 0,
                } if article else None,
            })
        return result, total

    async def add_favorite(self, user_id: int, article_id: int) -> bool:
        return await self.repo.add_favorite(user_id, article_id)

    async def remove_favorite(self, user_id: int, favorite_id: int) -> bool:
        return await self.repo.remove_favorite(user_id, favorite_id)

    # ─── 订阅 ───

    async def get_subscriptions(self, user_id: int) -> list[dict]:
        subs = await self.repo.get_subscriptions(user_id)
        return [
            {
                "id": s.id,
                "platform_id": s.platform_id,
                "keywords": s.keywords,
                "notify_email": s.notify_email,
                "notify_webpush": s.notify_webpush,
                "created_at": s.created_at.isoformat() if s.created_at else "",
            }
            for s in subs
        ]

    async def create_subscription(self, user_id: int, platform_id: int = None,
                                  keywords: list[str] = None,
                                  notify_email: bool = False) -> dict:
        sub = await self.repo.create_subscription(
            user_id, platform_id, keywords, notify_email
        )
        return {
            "id": sub.id,
            "platform_id": sub.platform_id,
            "keywords": sub.keywords,
        }

    async def delete_subscription(self, user_id: int, sub_id: int) -> bool:
        return await self.repo.delete_subscription(user_id, sub_id)

    # ─── 通知 ───

    async def get_notifications(self, user_id: int, page: int = 1,
                                page_size: int = 20) -> tuple[list[dict], int]:
        items, total = await self.repo.get_notifications(user_id, page, page_size)
        result = [
            {
                "id": n.id, "type": n.type, "title": n.title,
                "content": n.content, "is_read": n.is_read,
                "reference_id": n.reference_id,
                "created_at": n.created_at.isoformat() if n.created_at else "",
            }
            for n in items
        ]
        return result, total
