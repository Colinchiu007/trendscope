"""数据清洗模块"""


def clean_data(platform_code: str, raw_data: list[dict]) -> list[dict]:
    """清洗原始数据

    - 去除空标题/空排名
    - 去除 HTML 标签
    - 修正格式错误
    """
    cleaned = []
    for item in raw_data:
        title = (item.get("title") or "").strip()
        if not title:
            continue

        rank = item.get("rank", 0)
        if rank <= 0:
            continue

        # 去除标题中的 HTML 标签
        import re
        title = re.sub(r"<[^>]+>", "", title)
        title = title.strip()

        item["title"] = title
        cleaned.append(item)

    return cleaned
