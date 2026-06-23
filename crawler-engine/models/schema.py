"""SQLAlchemy 数据模型（与 Go GORM 模型保持一致）"""
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, Boolean,
    Float, DateTime, ForeignKey, JSON,
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
