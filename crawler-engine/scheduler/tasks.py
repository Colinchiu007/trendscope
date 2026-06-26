"""
⚠️ 已废弃 — 采集任务统一在 trendscope.crawler.tasks 中定义

迁移指引:
  旧引用:  from scheduler.tasks import crawl_platform
  新引用:  from trendscope.crawler.tasks import crawl_platform

此文件仅作为向后兼容的 shim，将在下一迭代中移除。
"""
import warnings
warnings.warn(
    "crawler-engine/scheduler/tasks.py 已废弃，"
    "请使用 trendscope.crawler.tasks (统一任务定义)",
    DeprecationWarning,
    stacklevel=2,
)

from trendscope.crawler.tasks import crawl_platform  # noqa: F401
