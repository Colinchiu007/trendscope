"""Celery 应用配置"""
import os
import sys

# 将 crawler-engine 目录加入 Python 路径
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
    imports=["trendscope.crawler.tasks"],
)
