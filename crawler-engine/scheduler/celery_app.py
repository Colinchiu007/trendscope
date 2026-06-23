"""Celery 应用配置"""
from celery import Celery

app = Celery(
    "trendscope",
    broker="redis://localhost:6379/1",
    backend="redis://localhost:6379/2",
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
)

# 自动发现任务
app.autodiscover_tasks(["scheduler"])
