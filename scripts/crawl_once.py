"""
TrendScope 一键采集脚本 - 在 Windows 本地 PowerShell 中运行

功能:
  1. 初始化数据库表
  2. 采集指定平台热榜
  3. 写入 PostgreSQL
  4. 输出结果

用法:
  python scripts/crawl_once.py weibo         # 只采集微博
  python scripts/crawl_once.py all            # 采集所有平台
  python scripts/crawl_once.py weibo,zhihu   # 采集微博和知乎
  python scripts/proxy_check.py              # 先检查代理可用性

提示: 采集前先跑 proxy_check.py 确认代理可用，避免消耗IP
"""
import sys
import os

# 确保能导入 crawler-engine 下的模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "crawler-engine"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime, timezone
from spiders import get_spider, SPIDER_MAP
from pipeline.cleaner import clean_data
from pipeline.deduplicator import deduplicate
from pipeline.normalizer import normalize_hot_value
from pipeline.classifier import classify
from loguru import logger


def crawl_single(platform_code: str) -> list[dict]:
    """采集单个平台并执行管道处理"""
    spider = get_spider(platform_code)
    if not spider:
        logger.error(f"未知平台: {platform_code}")
        return []

    logger.info(f"[{platform_code}] 开始采集...")

    try:
        raw = spider.fetch_trending_list()
        logger.info(f"[{platform_code}] 采集到 {len(raw)} 条原始数据")

        cleaned = clean_data(platform_code, raw)
        logger.info(f"[{platform_code}] 清洗后 {len(cleaned)} 条")

        deduped = deduplicate(platform_code, cleaned)
        logger.info(f"[{platform_code}] 去重后 {len(deduped)} 条")

        normalized = normalize_hot_value(platform_code, deduped)

        # 分类
        for item in normalized:
            item["category"] = classify(item.get("title", ""))

        # 时间戳
        now = datetime.now(timezone.utc).isoformat()
        for item in normalized:
            item["snapshot_at"] = now

        # 打印前5条
        print(f"\n{'='*50}")
        print(f"  {platform_code.upper()} 热榜 TOP 5")
        print(f"{'='*50}")
        for item in normalized[:5]:
            print(f"  #{item['rank']} {item['title']}")
            print(f"     热度: {item.get('hot_value', '')} | 分类: {item.get('category', '')}")
            print(f"     链接: {item.get('topic_url', '')}")
        print()

        # 写入数据库和缓存
        try:
            from pipeline.writer import write_to_db_and_cache
            import os
            db_user = os.getenv("TS_DB_USER", "tendscope")
            db_pass = os.getenv("TS_DB_PASSWORD", "tendscope_dev")
            db_host = os.getenv("TS_DB_HOST", "localhost")
            db_port = os.getenv("TS_DB_PORT", "5432")
            db_name = os.getenv("TS_DB_NAME", "tendscope")
            db_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
            write_to_db_and_cache(platform_code, normalized, db_url)
            logger.info(f"[{platform_code}] 数据已写入数据库")
        except Exception as db_err:
            logger.error(f"[{platform_code}] 数据库写入失败: {db_err}")

        spider.close()
        return normalized

    except Exception as e:
        logger.error(f"[{platform_code}] 采集异常: {e}")
        return []


if __name__ == "__main__":
    targets = sys.argv[1] if len(sys.argv) > 1 else "weibo"

    if targets == "all":
        platforms = list(SPIDER_MAP.keys())
    else:
        platforms = [p.strip() for p in targets.split(",")]

    print(f"目标平台: {', '.join(platforms)}")
    print()

    all_results = {}
    for code in platforms:
        items = crawl_single(code)
        all_results[code] = items

    print(f"\n{'='*60}")
    print(f"  采集汇总")
    print(f"{'='*60}")
    total = sum(len(v) for v in all_results.values())
    for code, items in all_results.items():
        print(f"  {code}: {len(items)} 条")
    print(f"  ---")
    print(f"  总计: {total} 条")
