"""
⚠️ 已废弃 — beat_schedule 已合并到 trendscope.crawler.celery_app

此文件保留仅作为配置参考，实际调度由统一 Celery 实例的
`app.conf.beat_schedule` 管理。将在下一迭代中移除。
"""
import warnings
warnings.warn(
    "crawler-engine/scheduler/beat_schedule.py 已废弃，"
    "beat_schedule 已合并到 trendscope.crawler.celery_app",
    DeprecationWarning,
    stacklevel=2,
)
