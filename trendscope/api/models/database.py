"""SQLAlchemy 数据模型（与 init-db.sql 保持一致）"""
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, Boolean, Float,
    DateTime, ForeignKey, JSON,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def now_utc():
    return datetime.now(timezone.utc)


class Platform(Base):
    __tablename__ = "platforms"

    id = Column(Integer, primary_key=True)
    code = Column(String(32), unique=True, nullable=False)
    name = Column(String(64), nullable=False)
    name_en = Column(String(128))
    icon_url = Column(String(512))
    base_url = Column(String(512))
    category = Column(String(32), default="general")
    is_active = Column(Boolean, default=True)
    crawl_interval = Column(Integer, default=300)
    crawl_config = Column(JSON, default=dict)
    created_at = Column(DateTime, default=now_utc)
    updated_at = Column(DateTime, default=now_utc, onupdate=now_utc)


class TrendingTopic(Base):
    __tablename__ = "trending_topics"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    platform_id = Column(Integer, ForeignKey("platforms.id"), nullable=False)
    rank = Column(Integer, nullable=False)
    title = Column(String(512), nullable=False)
    hot_value = Column(String(128))
    hot_value_norm = Column(Float)
    topic_url = Column(String(2048))
    category = Column(String(64))
    snapshot_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=now_utc)

    platform = relationship("Platform")


class HotArticle(Base):
    __tablename__ = "hot_articles"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    platform_id = Column(Integer, ForeignKey("platforms.id"), nullable=False)
    title = Column(String(1024), nullable=False)
    summary = Column(Text)
    content_text = Column(Text)
    images = Column(JSON, default=list)
    video_url = Column(String(2048))
    author_name = Column(String(256))
    author_avatar = Column(String(512))
    source_url = Column(String(2048), nullable=False)
    read_count = Column(BigInteger, default=0)
    like_count = Column(BigInteger, default=0)
    comment_count = Column(BigInteger, default=0)
    share_count = Column(BigInteger, default=0)
    publish_at = Column(DateTime)
    status = Column(String(16), default="pending")
    snapshot_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=now_utc)
    updated_at = Column(DateTime, default=now_utc, onupdate=now_utc)

    platform = relationship("Platform")


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False)
    email = Column(String(256))
    phone = Column(String(20))
    password_hash = Column(String(256), nullable=False)
    nickname = Column(String(128))
    avatar_url = Column(String(512))
    role = Column(String(16), default="user")
    status = Column(String(16), default="active")
    created_at = Column(DateTime, default=now_utc)
    updated_at = Column(DateTime, default=now_utc, onupdate=now_utc)


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    key_hash = Column(String(256), unique=True, nullable=False)
    key_prefix = Column(String(16), nullable=False)
    name = Column(String(128))
    rate_limit = Column(Integer, default=100)
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=now_utc)


class CrawlLog(Base):
    __tablename__ = "crawl_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    platform_id = Column(Integer, ForeignKey("platforms.id"), nullable=False)
    status = Column(String(16), nullable=False, default="running")
    items_count = Column(Integer, default=0)
    error_message = Column(Text)
    duration_ms = Column(Integer)
    started_at = Column(DateTime, default=now_utc)
    finished_at = Column(DateTime)
    created_at = Column(DateTime, default=now_utc)


class UserFavorite(Base):
    __tablename__ = "user_favorites"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    article_id = Column(BigInteger, ForeignKey("hot_articles.id", ondelete="CASCADE"), nullable=False)
    folder_id = Column(BigInteger, default=0)
    created_at = Column(DateTime, default=now_utc)

    article = relationship("HotArticle")


class UserSubscription(Base):
    __tablename__ = "user_subscriptions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    platform_id = Column(Integer, ForeignKey("platforms.id", ondelete="SET NULL"), nullable=True)
    keywords = Column(JSON, default=list)
    notify_email = Column(Boolean, default=False)
    notify_webpush = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=now_utc)
    updated_at = Column(DateTime, default=now_utc, onupdate=now_utc)

    platform = relationship("Platform")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(32), nullable=False)
    title = Column(String(256), nullable=False)
    content = Column(Text)
    reference_id = Column(BigInteger)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=now_utc)


class ApiUsageLog(Base):
    __tablename__ = "api_usage_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    api_key_id = Column(Integer, ForeignKey("api_keys.id", ondelete="SET NULL"), nullable=True)
    endpoint = Column(String(256), nullable=False)
    method = Column(String(16), nullable=False)
    status_code = Column(Integer)
    ip_address = Column(String(64))
    created_at = Column(DateTime, default=now_utc)
