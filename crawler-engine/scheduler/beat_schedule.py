"""定时任务调度配置 - 12平台完整配置"""
beat_schedule = {
    # T0 实时级 (60s)
    "crawl-weibo": {
        "task": "scheduler.tasks.crawl_platform",
        "schedule": 60.0,
        "args": ("weibo",),
    },
    # T1 高频级 (3-5min)
    "crawl-baidu": {
        "task": "scheduler.tasks.crawl_platform",
        "schedule": 180.0,
        "args": ("baidu",),
    },
    "crawl-zhihu": {
        "task": "scheduler.tasks.crawl_platform",
        "schedule": 180.0,
        "args": ("zhihu",),
    },
    "crawl-bilibili": {
        "task": "scheduler.tasks.crawl_platform",
        "schedule": 180.0,
        "args": ("bilibili",),
    },
    "crawl-toutiao": {
        "task": "scheduler.tasks.crawl_platform",
        "schedule": 300.0,
        "args": ("toutiao",),
    },
    # T2 标准级 (15min)
    "crawl-douyin": {
        "task": "scheduler.tasks.crawl_platform",
        "schedule": 900.0,
        "args": ("douyin",),
    },
    "crawl-xiaohongshu": {
        "task": "scheduler.tasks.crawl_platform",
        "schedule": 900.0,
        "args": ("xiaohongshu",),
    },
    "crawl-youtube": {
        "task": "scheduler.tasks.crawl_platform",
        "schedule": 900.0,
        "args": ("youtube",),
    },
    # T3 低频级 (30min-1h)
    "crawl-weixin": {
        "task": "scheduler.tasks.crawl_platform",
        "schedule": 1800.0,
        "args": ("weixin_article",),
    },
    "crawl-x-twitter": {
        "task": "scheduler.tasks.crawl_platform",
        "schedule": 1800.0,
        "args": ("x_twitter",),
    },
    "crawl-shipinhao": {
        "task": "scheduler.tasks.crawl_platform",
        "schedule": 1800.0,
        "args": ("shipinhao",),
    },
    "crawl-tiktok": {
        "task": "scheduler.tasks.crawl_platform",
        "schedule": 3600.0,
        "args": ("tiktok",),
    },
}
