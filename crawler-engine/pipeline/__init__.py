"""数据处理管道

处理流程: 清洗 → 去重 → 归一化 → 分类 → 写入
"""
from loguru import logger
from pipeline.cleaner import clean_data
from pipeline.deduplicator import deduplicate
from pipeline.normalizer import normalize_hot_value
from pipeline.writer import write_to_db_and_cache


def run_pipeline(platform_code: str, raw_data: list[dict]) -> list[dict]:
    """执行完整的数据处理管道"""
    if not raw_data:
        logger.warning(f"[管道] {platform_code} 无数据")
        return []

    # 1. 数据清洗
    cleaned = clean_data(platform_code, raw_data)
    logger.debug(f"[管道] {platform_code} 清洗后: {len(cleaned)} 条")

    # 2. 去重
    deduped = deduplicate(platform_code, cleaned)
    logger.debug(f"[管道] {platform_code} 去重后: {len(deduped)} 条")

    # 3. 热度归一化
    normalized = normalize_hot_value(platform_code, deduped)
    logger.debug(f"[管道] {platform_code} 归一化完成: {len(normalized)} 条")

    # 4. 写入数据库和缓存
    write_to_db_and_cache(platform_code, normalized)

    return normalized
