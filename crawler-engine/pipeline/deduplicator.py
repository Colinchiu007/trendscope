"""去重模块 - 基于标题相似度去重"""

from difflib import SequenceMatcher


def deduplicate(platform_code: str, items: list[dict], threshold: float = 0.85) -> list[dict]:
    """按标题相似度去重

    Args:
        platform_code: 平台代码
        items: 数据列表
        threshold: 相似度阈值（默认 0.85）
    """
    if len(items) <= 1:
        return items

    seen = []
    result = []

    for item in items:
        title = item.get("title", "")
        is_dup = False

        for seen_title in seen:
            similarity = SequenceMatcher(None, title, seen_title).ratio()
            if similarity >= threshold:
                is_dup = True
                break

        if not is_dup:
            seen.append(title)
            result.append(item)

    return result
