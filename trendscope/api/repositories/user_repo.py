"""用户数据访问层"""
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from trendscope.api.models.database import User, UserFavorite, UserSubscription, Notification


class UserRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ─── 用户 CRUD ───

    async def find_by_id(self, user_id: int) -> User | None:
        stmt = select(User).where(User.id == user_id, User.status == "active")
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_username(self, username: str) -> User | None:
        stmt = select(User).where(User.username == username)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_phone(self, phone: str) -> User | None:
        stmt = select(User).where(User.phone == phone)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_account(self, account: str) -> User | None:
        """通过用户名/邮箱/手机号查找用户"""
        user = await self.find_by_username(account)
        if user:
            return user
        if "@" in account:
            user = await self.find_by_email(account)
            if user:
                return user
        user = await self.find_by_phone(account)
        return user

    async def create_user(self, username: str, password_hash: str,
                          email: str = None, phone: str = None,
                          nickname: str = None) -> User:
        user = User(
            username=username,
            email=email,
            phone=phone,
            password_hash=password_hash,
            nickname=nickname or username,
            role="user",
            status="active",
        )
        self.db.add(user)
        await self.db.flush()
        return user

    async def update_user(self, user_id: int, **kwargs) -> User | None:
        user = await self.find_by_id(user_id)
        if not user:
            return None
        for key, value in kwargs.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)
        await self.db.flush()
        return user

    # ─── 收藏 ───

    async def get_favorites(self, user_id: int, page: int = 1,
                            page_size: int = 20) -> tuple[list[UserFavorite], int]:
        base = select(UserFavorite).where(UserFavorite.user_id == user_id)
        count_stmt = select(func.count()).select_from(base.subquery())
        result = await self.db.execute(count_stmt)
        total = result.scalar() or 0

        stmt = base.order_by(UserFavorite.created_at.desc()) \
            .offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(stmt)
        items = list(result.scalars().all())
        return items, total

    async def add_favorite(self, user_id: int, article_id: int) -> bool:
        existing = await self.db.execute(
            select(UserFavorite)
            .where(UserFavorite.user_id == user_id, UserFavorite.article_id == article_id)
        )
        if existing.scalar_one_or_none():
            return False
        fav = UserFavorite(user_id=user_id, article_id=article_id)
        self.db.add(fav)
        await self.db.flush()
        return True

    async def remove_favorite(self, user_id: int, favorite_id: int) -> bool:
        fav = await self.db.get(UserFavorite, favorite_id)
        if not fav or fav.user_id != user_id:
            return False
        await self.db.delete(fav)
        await self.db.flush()
        return True

    # ─── 订阅 ───

    async def get_subscriptions(self, user_id: int) -> list[UserSubscription]:
        stmt = select(UserSubscription).where(
            UserSubscription.user_id == user_id,
            UserSubscription.is_active == True,
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_subscription(self, user_id: int, platform_id: int = None,
                                  keywords: list[str] = None,
                                  notify_email: bool = False) -> UserSubscription:
        sub = UserSubscription(
            user_id=user_id,
            platform_id=platform_id,
            keywords=keywords or [],
            notify_email=notify_email,
        )
        self.db.add(sub)
        await self.db.flush()
        return sub

    async def delete_subscription(self, user_id: int, sub_id: int) -> bool:
        sub = await self.db.get(UserSubscription, sub_id)
        if not sub or sub.user_id != user_id:
            return False
        await self.db.delete(sub)
        await self.db.flush()
        return True

    # ─── 通知 ───

    async def get_notifications(self, user_id: int, page: int = 1,
                                page_size: int = 20) -> tuple[list[Notification], int]:
        base = select(Notification).where(Notification.user_id == user_id)
        count_stmt = select(func.count()).select_from(base.subquery())
        result = await self.db.execute(count_stmt)
        total = result.scalar() or 0

        stmt = base.order_by(Notification.created_at.desc()) \
            .offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def create_notification(self, user_id: int, type_: str,
                                  title: str, content: str = None,
                                  reference_id: int = None) -> Notification:
        notif = Notification(
            user_id=user_id, type=type_, title=title,
            content=content, reference_id=reference_id,
        )
        self.db.add(notif)
        await self.db.flush()
        return notif
