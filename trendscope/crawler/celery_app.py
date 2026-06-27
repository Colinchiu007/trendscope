"""Celery 应用配置 — 统一实例（合并了 legacy crawler-engine 的 beat_schedule）"""
import os
import sys

# 将 crawler-engine 目录加入 Python 路径（供懒加载爬虫和管道使用）
_crawler_path = os.path.join(os.path.dirname(__file__), "..", "..", "crawler-engine")
_crawler_path = os.path.abspath(_crawler_path)
if _crawler_path not in sys.path:
    sys.path.insert(0, _crawler_path)

from celery import Celery
from trendscope.api.config import settings

app = Celery(
    "trendscope",
    broker=settings.CELERY_BROKER,
    backend=settings.CELERY_BACKEND,
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=120,
    task_time_limit=180,
    imports=[
        "trendscope.crawler.tasks",
    ],
    # ─── 合并自 legacy crawler-engine/scheduler/beat_schedule.py ───
    beat_schedule={
        # T0 实时级 (60s)
        "crawl-weibo": {
            "task": "trendscope.crawler.tasks.crawl_platform",
            "schedule": 60.0,
            "args": ("weibo",),
        },
        # T1 高频级 (3-5min)
        "crawl-baidu": {
            "task": "trendscope.crawler.tasks.crawl_platform",
            "schedule": 180.0,
            "args": ("baidu",),
        },
        "crawl-zhihu": {
            "task": "trendscope.crawler.tasks.crawl_platform",
            "schedule": 180.0,
            "args": ("zhihu",),
        },
        "crawl-bilibili": {
            "task": "trendscope.crawler.tasks.crawl_platform",
            "schedule": 180.0,
            "args": ("bilibili",),
        },
        "crawl-toutiao": {
            "task": "trendscope.crawler.tasks.crawl_platform",
            "schedule": 300.0,
            "args": ("toutiao",),
        },
        # T2 标准级 (15min)
        "crawl-douyin": {
            "task": "trendscope.crawler.tasks.crawl_platform",
            "schedule": 900.0,
            "args": ("douyin",),
        },
        "crawl-xiaohongshu": {
            "task": "trendscope.crawler.tasks.crawl_platform",
            "schedule": 900.0,
            "args": ("xiaohongshu",),
        },
        "crawl-youtube": {
            "task": "trendscope.crawler.tasks.crawl_platform",
            "schedule": 900.0,
            "args": ("youtube",),
        },
        # T3 低频级 (30min-1h)
        "crawl-weixin": {
            "task": "trendscope.crawler.tasks.crawl_platform",
            "schedule": 1800.0,
            "args": ("weixin_article",),
        },
        "crawl-x-twitter": {
            "task": "trendscope.crawler.tasks.crawl_platform",
            "schedule": 1800.0,
            "args": ("x_twitter",),
        },
        "crawl-tiktok": {
            "task": "trendscope.crawler.tasks.crawl_platform",
            "schedule": 3600.0,
            "args": ("tiktok",),
        },
    },
)
