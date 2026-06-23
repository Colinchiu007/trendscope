"""采集任务定义"""
import os
import sys
from datetime import datetime, timezone

# 确保 crawler-engine 在路径中
_crawler_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "crawler-engine")
)
if _crawler_path not in sys.path:
    sys.path.insert(0, _crawler_path)

from celery.utils.log import get_task_logger
from trendscope.crawler.celery_app import app
from trendscope.api.config import settings

logger = get_task_logger(__name__)

# 懒加载爬虫和管道
def _get_spider(platform_code: str):
    from spiders import get_spider as _gs
    return _gs(platform_code)

def _run_pipeline(platform_code: str, items: list[dict]):
    from pipeline.writer import write_to_db_and_cache
    if not items:
        return

    write_to_db_and_cache(platform_code, items, db_url=settings.database_url_sync)

    # 管道联动：提取文章 URL 推送到 content-aggregator
    articles = [item.get("_article") for item in items if item.get("_article")]
    if articles:
        try:
            from trendscope.api.pipeline.bridge import get_pipeline_bridge
            bridge = get_pipeline_bridge()
            import asyncio
            count = asyncio.run(bridge.push_to_pipeline(articles, platform_code))
            if count:
                logger.info(f"[管道] {platform_code}: {count} 条推入内容管道")
        except Exception as e:
            logger.warning(f"[管道] 桥接失败: {e}")


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def crawl_platform(self, platform_code: str):
    """采集指定平台的热榜数据"""
    logger.info(f"[采集] 开始: {platform_code}")

    spider = _get_spider(platform_code)
    if spider is None:
        return {"status": "failed", "error": f"spider not found: {platform_code}"}

    try:
        raw_data = spider.safe_run()
        _run_pipeline(platform_code, raw_data)
        logger.info(f"[采集] 完成: {platform_code}, {len(raw_data)} 条")
        return {
            "status": "success",
            "platform": platform_code,
            "items_count": len(raw_data),
            "finished_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"[采集] 失败: {platform_code} - {e}")
        countdown = 60 * (2 ** self.request.retries)
        raise self.retry(exc=e, countdown=min(countdown, 600))


@app.task
def crawl_all_active():
    """采集所有启用平台"""
    codes = [
        "weibo", "baidu", "zhihu", "bilibili", "toutiao",
        "douyin", "xiaohongshu", "youtube",
        "x_twitter", "weixin_article", "shipinhao", "tiktok",
    ]
    for code in codes:
        crawl_platform.delay(code)
    return {"status": "queued", "platforms": codes}
