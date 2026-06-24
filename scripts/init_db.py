#!/usr/bin/env python3
"""
初始化 TrendScope 数据库表 + 插入默认平台数据

用法:
  cd D:\Data\projects\trendscope
  python scripts\init_db.py
"""
import sys
import os
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

async def main():
    from trendscope.api.models.session import init_db, close_db
    from loguru import logger

    logger.info("初始化数据库表...")
    await init_db()
    logger.info("数据库表初始化完成 ✓")

    # 插入默认平台
    from trendscope.api.models.database import Platform
    from trendscope.api.models.session import _get_session_factory

    platforms = [
        {"code": "weibo", "name": "微博", "name_en": "Weibo", "category": "social", "crawl_interval": 60},
        {"code": "baidu", "name": "百度", "name_en": "Baidu", "category": "general", "crawl_interval": 180},
        {"code": "zhihu", "name": "知乎", "name_en": "Zhihu", "category": "knowledge", "crawl_interval": 180},
        {"code": "bilibili", "name": "B站", "name_en": "Bilibili", "category": "video", "crawl_interval": 180},
        {"code": "toutiao", "name": "今日头条", "name_en": "Toutiao", "category": "news", "crawl_interval": 300},
        {"code": "douyin", "name": "抖音", "name_en": "Douyin", "category": "video", "crawl_interval": 900},
        {"code": "xiaohongshu", "name": "小红书", "name_en": "Xiaohongshu", "category": "lifestyle", "crawl_interval": 900},
        {"code": "youtube", "name": "YouTube", "name_en": "YouTube", "category": "video", "crawl_interval": 900},
        {"code": "x_twitter", "name": "X/Twitter", "name_en": "X/Twitter", "category": "social", "crawl_interval": 1800},
        {"code": "weixin_article", "name": "微信公众号", "name_en": "WeChatArticle", "category": "article", "crawl_interval": 1800},
        {"code": "shipinhao", "name": "视频号", "name_en": "Shipinhao", "category": "video", "crawl_interval": 1800},
        {"code": "tiktok", "name": "TikTok", "name_en": "TikTok", "category": "video", "crawl_interval": 3600},
    ]

    async with _get_session_factory()() as session:
        from sqlalchemy import select
        for p in platforms:
            existing = await session.execute(select(Platform).where(Platform.code == p["code"]))
            if not existing.scalar_one_or_none():
                session.add(Platform(**p))
        await session.commit()

    existing_count = len(platforms)
    logger.info(f"平台数据已就绪 ({existing_count} 个) ✓")
    await close_db()

if __name__ == "__main__":
    asyncio.run(main())
