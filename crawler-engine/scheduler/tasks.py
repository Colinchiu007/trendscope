"""采集任务入口"""
from datetime import datetime, timezone

from loguru import logger
from scheduler.celery_app import app
from spiders import get_spider
from pipeline import run_pipeline


@app.task(bind=True, max_retries=3)
def crawl_platform(self, platform_code: str):
    """采集指定平台的热榜数据"""
    logger.info(f"[采集开始] 平台: {platform_code}")

    spider = get_spider(platform_code)
    if spider is None:
        logger.error(f"[采集失败] 未找到平台爬虫: {platform_code}")
        return {"status": "failed", "error": "spider not found"}

    try:
        raw_data = spider.fetch_trending_list()
        processed_data = run_pipeline(platform_code, raw_data)
        logger.info(f"[采集完成] 平台: {platform_code}, 条目: {len(processed_data)}")
        return {
            "status": "success",
            "platform": platform_code,
            "items_count": len(processed_data),
            "finished_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"[采集异常] 平台: {platform_code}, 错误: {e}")
        # 指数退避重试: 60s, 120s, 240s
        countdown = 60 * (2 ** self.request.retries)
        raise self.retry(exc=e, countdown=countdown)
