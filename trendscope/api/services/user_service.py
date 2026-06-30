"""用户业务逻辑"""
import re

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from trendscope.api.middleware.auth import create_access_token, hash_password, verify_password
from trendscope.api.repositories.user_repo import UserRepo
from trendscope.api.cache.sms_cache import SmsCache


class UserService:
    def __init__(self, db: AsyncSession, sms_cache: SmsCache = None):
        if isinstance(db, UserRepo):
            self.repo = db
        else:
            self.repo = UserRepo(db)
        self.sms_cache = sms_cache or SmsCache(redis_client=None)

    # ─── 注册 ───

    async def register(self, username: str, password: str,
                       email: str = None, phone: str = None) -> dict:
        """用户注册"""
        if not re.match(r"^[a-zA-Z0-9_一-鿿]{3,64}$", username):
            raise ValueError("用户名须为3-64位字母、数字、下划线或中文")
        if len(password) < 8:
            raise ValueError("密码至少8位")
        if await self.repo.find_by_username(username):
            raise ValueError("用户名已存在")
        if email and await self.repo.find_by_email(email):
            raise ValueError("邮箱已注册")
        if phone and await self.repo.find_by_phone(phone):
            raise ValueError("手机号已注册")
        hashed = hash_password(password)
        user = await self.repo.create_user(
            username=username, password_hash=hashed,
            email=email, phone=phone, nickname=username,
        )
        logger.info(f"[用户] 注册成功: {username} (id={user.id})")
        return {"id": user.id, "username": user.username, "role": user.role}

    # ─── 密码登录 ───

    async def login(self, account: str, password: str) -> dict:
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
            "access_token": token, "expires_in": 7200,
            "user": {"id": user.id, "username": user.username,
                     "nickname": user.nickname, "role": user.role},
        }

    # ─── 短信验证码 ───

    async def send_sms_code(self, phone: str) -> dict:
        """生成并发送短信验证码（当前未集成真实 SMS 服务商）"""
        if not re.match(r"^1[3-9]\d{9}$", phone):
            raise ValueError("手机号格式不正确")
        code = self.sms_cache.generate_code()
        await self.sms_cache.set_code(phone, code)
        logger.info(f"[SMS] 验证码已发送至 {phone}: {code}")
        return {"message": "验证码已发送"}

    async def login_by_sms(self, phone: str, code: str) -> dict:
        """短信验证码登录"""
        if not re.match(r"^1[3-9]\d{9}$", phone):
            raise ValueError("手机号格式不正确")
        stored_code = await self.sms_cache.get_code(phone)
        if not stored_code:
            raise ValueError("验证码已过期或未发送，请重新获取")
        if stored_code != code:
            raise ValueError("验证码错误")
        await self.sms_cache.delete_code(phone)
        user = await self.repo.find_by_phone(phone)
        if not user:
            raise ValueError("该手机号未注册")
        if user.status != "active":
            raise ValueError("账号已被禁用")
        token = create_access_token(user.id, user.username, user.role)
        logger.info(f"[用户] 短信登录成功: {user.username} (phone={phone})")
        return {
            "access_token": token, "expires_in": 7200,
            "user": {"id": user.id, "username": user.username,
                     "nickname": user.nickname, "role": user.role},
        }

    # ─── 个人信息 ───

    async def get_profile(self, user_id: int) -> dict:
        user = await self.repo.find_by_id(user_id)
        if not user:
            raise ValueError("用户不存在")
        return {
            "id": user.id, "username": user.username,
            "email": user.email, "phone": user.phone,
            "nickname": user.nickname, "avatar_url": user.avatar_url,
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
                            page_size: int = 20) -> tuple:
        items, total = await self.repo.get_favorites(user_id, page, page_size)
        result = []
        for fav in items:
            article = fav.article
            result.append({
                "id": fav.id, "article_id": fav.article_id,
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

    async def get_subscriptions(self, user_id: int) -> list:
        subs = await self.repo.get_subscriptions(user_id)
        return [{"id": s.id, "platform_id": s.platform_id,
                 "keywords": s.keywords, "notify_email": s.notify_email,
                 "notify_webpush": s.notify_webpush,
                 "created_at": s.created_at.isoformat() if s.created_at else ""}
                for s in subs]

    async def create_subscription(self, user_id: int, platform_id: int = None,
                                  keywords: list[str] = None,
                                  notify_email: bool = False) -> dict:
        sub = await self.repo.create_subscription(
            user_id, platform_id, keywords, notify_email)
        return {"id": sub.id, "platform_id": sub.platform_id, "keywords": sub.keywords}

    async def delete_subscription(self, user_id: int, sub_id: int) -> bool:
        return await self.repo.delete_subscription(user_id, sub_id)

    # ─── 通知 ───

    async def get_notifications(self, user_id: int, page: int = 1,
                                page_size: int = 20) -> tuple:
        items, total = await self.repo.get_notifications(user_id, page, page_size)
        result = [{"id": n.id, "type": n.type, "title": n.title,
                    "content": n.content, "is_read": n.is_read,
                    "reference_id": n.reference_id,
                    "created_at": n.created_at.isoformat() if n.created_at else ""}
                  for n in items]
        return result, total



    # ─── 邮箱验证码 ───

    async def send_email_code(self, email: str) -> dict:
        """生成并发送邮箱验证码（当前未集成真实 SMTP 服务商）"""
        import re
        if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email):
            raise ValueError("邮箱格式不正确")
        # 复用 SmsCache 存储，使用 email 作为 key
        code = self.sms_cache.generate_code()
        await self.sms_cache.set_code(f"email:{email}", code)
        logger.info(f"[Email] 验证码已发送至 {email}: {code}")
        return {"message": "验证码已发送"}

    async def register_with_email(self, username: str, password: str, email: str,
                                  email_code: str, phone: str = None) -> dict:
        """邮箱验证码注册"""
        # 验证邮箱验证码
        stored_code = await self.sms_cache.get_code(f"email:{email}")
        if not stored_code:
            raise ValueError("验证码已过期或未发送，请重新获取")
        if stored_code != email_code:
            raise ValueError("验证码错误")
        await self.sms_cache.delete_code(f"email:{email}")
        # 调用已有的 register 逻辑
        return await self.register(username, password, email=email, phone=phone)

    # ─── 密码修改 ───

    async def change_password(self, user_id: int, old_password: str, new_password: str) -> None:
        """修改用户密码"""
        user = await self.repo.find_by_id(user_id)
        if not user:
            raise ValueError("用户不存在")
        if not verify_password(old_password, user.password_hash):
            raise ValueError("旧密码错误")
        hashed = hash_password(new_password)
        await self.repo.update_user(user_id, password_hash=hashed)
        logger.info(f"[用户] 密码修改成功: user_id={user_id}")

    # ─── 账号注销 ───

    async def delete_account(self, user_id: int) -> None:
        """注销账号（软删除：将 status 设为 deleted）"""
        user = await self.repo.find_by_id(user_id)
        if not user:
            raise ValueError("用户不存在")
        await self.repo.update_user(user_id, status="deleted")
        logger.info(f"[用户] 账号已注销: user_id={user_id}")


    # ─── 收藏文件夹 ───

    async def get_folders(self, user_id: int) -> list:
        folders = await self.repo.get_folders(user_id)
        return [{
            "id": f.id, "name": f.name, "sort_order": f.sort_order,
            "created_at": f.created_at.isoformat() if f.created_at else "",
        } for f in folders]

    async def create_folder(self, user_id: int, name: str) -> dict:
        folder = await self.repo.create_folder(user_id, name)
        return {"id": folder.id, "name": folder.name}

    async def update_folder(self, folder_id: int, user_id: int, name: str) -> bool:
        return await self.repo.update_folder(folder_id, user_id, name)

    async def delete_folder(self, folder_id: int, user_id: int) -> bool:
        return await self.repo.delete_folder(folder_id, user_id)

    # ─── 订阅通知触发（Task 16）───

    async def trigger_subscription_notifications(self, platform_id: int, title: str, article_id: int) -> int:
        """采集完成时触发订阅通知匹配"""
        matched = await self.repo.find_matching_subscriptions(platform_id, title)
        count = 0
        for sub in matched:
            await self.repo.create_notification(
                user_id=sub.user_id,
                type_="subscription_match",
                title=f"订阅关键词匹配: {title}",
                reference_id=article_id,
            )
            count += 1
        if count > 0:
            logger.info(f"[订阅] 关键词匹配触发 {count} 条通知 (platform={platform_id}, title={title})")
        return count
