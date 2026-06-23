"""数据写入模块 - 将处理后的数据写入 PostgreSQL 和 Redis"""
from datetime import datetime, timezone

from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from models.schema import TrendingTopic, HotArticle, Platform, CrawlLog


def write_to_db_and_cache(platform_code: str, items: list[dict], db_url: str = None):
    """写入 PostgreSQL 并触发 Redis 缓存失效

    Args:
        platform_code: 平台代码
        items: 标准化数据列表
        db_url: 数据库连接 URL（从环境变量获取）
    """
    if not items:
        logger.warning(f"[写入] {platform_code}: 无数据")
        return 0

    if not db_url:
        db_url = "postgresql://trendscope:trendscope_dev@localhost:5432/trendscope"

    engine = create_engine(db_url)
    now = datetime.now(timezone.utc)
    written = 0

    with Session(engine) as session:
        # 查找平台 ID
        platform = session.query(Platform).filter(Platform.code == platform_code).first()
        if not platform:
            logger.error(f"[写入] 未找到平台: {platform_code}")
            engine.dispose()
            return 0

        platform_id = platform.id
        start_time = datetime.now(timezone.utc)

        try:
            for item in items:
                # 写入话题数据
                topic = TrendingTopic(
                    platform_id=platform_id,
                    rank=item.get("rank", 0),
                    title=item.get("title", ""),
                    hot_value=item.get("hot_value", ""),
                    hot_value_norm=item.get("hot_value_norm", 0.0),
                    topic_url=item.get("topic_url", ""),
                    category=item.get("category", "general"),
                    snapshot_at=now,
                )
                session.add(topic)
                written += 1

                # 如果有文章附加数据，写入文章表
                article_data = item.get("_article")
                if article_data:
                    article = HotArticle(
                        platform_id=platform_id,
                        title=article_data.get("title", item.get("title", "")),
                        summary=article_data.get("summary", ""),
                        images=article_data.get("images", []),
                        author_name=article_data.get("author_name", ""),
                        author_avatar=article_data.get("author_avatar", ""),
                        source_url=article_data.get("source_url", item.get("topic_url", "")),
                        read_count=article_data.get("read_count", 0),
                        like_count=article_data.get("like_count", 0),
                        comment_count=article_data.get("comment_count", 0),
                        publish_at=article_data.get("publish_at"),
                        status="pending",
                        snapshot_at=now,
                    )
                    session.add(article)

            # 写入采集日志
            elapsed_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
            log_entry = CrawlLog(
                platform_id=platform_id,
                status="success",
                items_count=written,
                duration_ms=elapsed_ms,
                started_at=start_time,
                finished_at=datetime.now(timezone.utc),
            )
            session.add(log_entry)

            session.commit()
            logger.info(f"[写入] {platform_code}: {written} 条存储成功, 耗时 {elapsed_ms}ms")

        except Exception as e:
            session.rollback()
            logger.error(f"[写入] {platform_code} 写入失败: {e}")
            # 记录失败日志
            try:
                log_entry = CrawlLog(
                    platform_id=platform_id,
                    status="failed",
                    error_message=str(e),
                    started_at=start_time,
                    finished_at=datetime.now(timezone.utc),
                )
                session.add(log_entry)
                session.commit()
            except Exception:
                pass
            raise
        finally:
            engine.dispose()

    # TODO: 通过 Redis pub/sub 通知缓存失效
    # redis_client.publish("trendscope:invalidate", platform_code)

    return written
