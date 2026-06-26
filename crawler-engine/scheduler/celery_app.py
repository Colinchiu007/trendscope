"""
⚠️ 已废弃 — 统一 Celery 应用请使用 trendscope.crawler.celery_app

迁移指引:
  旧命令:
    celery -A crawler-engine.scheduler.celery_app worker ...
    celery -A crawler-engine.scheduler.celery_app beat ...
  新命令:
    celery -A trendscope.crawler.celery_app worker ...
    celery -A trendscope.crawler.celery_app beat ...

此文件仅作为向后兼容的 shim，将在下一迭代中移除。
"""
import warnings
warnings.warn(
    "crawler-engine/scheduler/celery_app.py 已废弃，"
    "请使用 trendscope.crawler.celery_app (统一 Celery 实例)",
    DeprecationWarning,
    stacklevel=2,
)

from trendscope.crawler.celery_app import app as celery_app

app = celery_app
